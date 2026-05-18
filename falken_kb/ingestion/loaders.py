"""Loader: hockeydata-Responses → Supabase via REST/RPC.

Nutzt die Upsert-RPCs aus migration 0003_rpcs.sql (kein direkter Postgres-Connect nötig).
"""
from __future__ import annotations

import logging
from typing import Any

from ..db import rpc
from .hockeydata_client import HockeydataClient

logger = logging.getLogger(__name__)


def upsert_season(label: str, league: str, league_tier: int, hockeydata_season_id: int) -> str:
    """Upsert Season, return UUID."""
    return rpc("upsert_season", {
        "p_label": label,
        "p_league": league,
        "p_league_tier": league_tier,
        "p_hockeydata_id": str(hockeydata_season_id),
    })


def upsert_team(name: str, short_name: str | None = None, hockeydata_team_id: int | None = None) -> str:
    return rpc("upsert_team", {
        "p_name": name,
        "p_short_name": short_name,
        "p_hockeydata_id": str(hockeydata_team_id) if hockeydata_team_id is not None else None,
    })


def _pick(d: dict, *keys: str) -> Any:
    """Hockeydata-API ist inkonsistent: teamLongname (lowercase) in Standings,
    homeTeamLongName (CamelCase) im Schedule. Probiere alle Varianten."""
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


def upsert_team_seasons_from_standings(season_id: str, standings_rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in standings_rows:
        name = _pick(row, "teamLongname", "teamLongName", "teamShortname", "teamShortName")
        if not name:
            logger.warning("Standings-Row ohne Team-Namen, skip: %s", str(row)[:120])
            continue
        team_uuid = upsert_team(
            name=name,
            short_name=_pick(row, "teamShortname", "teamShortName"),
            hockeydata_team_id=row.get("id"),
        )
        rpc("upsert_team_season", {
            "p_team_id": team_uuid,
            "p_season_id": season_id,
            "p_rank": row.get("tableRank"),
            "p_gp": row.get("gamesPlayed"),
            "p_wins": row.get("gamesWon"),
            "p_losses": row.get("gamesLost"),
            "p_ot_wins": row.get("gamesWonInOt"),
            "p_ot_losses": row.get("gamesLostInOt"),
            "p_points": row.get("points"),
            "p_gf": row.get("goalsFor"),
            "p_ga": row.get("goalsAgainst"),
            "p_hd_id": str(row.get("id")) if row.get("id") is not None else None,
        })
        count += 1
    return count


def upsert_games_from_schedule(season_id: str, schedule_rows: list[dict[str, Any]], game_type: str = "regular") -> int:
    count = 0
    skipped = 0
    for m in schedule_rows:
        home_name = _pick(m, "homeTeamLongName", "homeTeamLongname", "homeTeamShortName", "homeTeamShortname")
        away_name = _pick(m, "awayTeamLongName", "awayTeamLongname", "awayTeamShortName", "awayTeamShortname")
        if not home_name or not away_name:
            skipped += 1
            continue
        home_uuid = upsert_team(
            name=home_name,
            short_name=_pick(m, "homeTeamShortName", "homeTeamShortname"),
            hockeydata_team_id=m.get("homeTeamId"),
        )
        away_uuid = upsert_team(
            name=away_name,
            short_name=_pick(m, "awayTeamShortName", "awayTeamShortname"),
            hockeydata_team_id=m.get("awayTeamId"),
        )
        # scheduledGameStart ist im ISO-Format; scheduledDate ist nur das Datum (oft Dict)
        sched_iso = m.get("scheduledGameStart")
        if not sched_iso:
            sched = m.get("scheduledDate")
            if isinstance(sched, dict):
                sched_iso = sched.get("value") or sched.get("formattedLong")
            else:
                sched_iso = sched
        if not sched_iso:
            skipped += 1
            continue
        rpc("upsert_game", {
            "p_season_id": season_id,
            "p_date": sched_iso,
            "p_game_type": game_type,
            "p_home_team_id": home_uuid,
            "p_away_team_id": away_uuid,
            "p_home_score": m.get("homeTeamScore"),
            "p_away_score": m.get("awayTeamScore"),
            "p_overtime": bool(m.get("scoreInfo") in ("OT", "OTW", "OTL")),
            "p_shootout": bool(m.get("scoreInfo") in ("SO", "SOW", "SOL")),
            "p_hd_id": str(m.get("id")) if m.get("id") else None,
        })
        # upsert_game gibt einen boolean zurück, der zwischen supabase-py-Versionen
        # unterschiedlich serialisiert wird. Wir zählen schlicht alle attempts;
        # echte Duplikate werden im SQL (WHERE NOT EXISTS) erkannt und ignoriert.
        count += 1
    if skipped:
        logger.info("  %d Spiele übersprungen (fehlende Teamdaten/Datum)", skipped)
    return count


async def load_current_season(league_id: int, league_name: str, league_tier: int, division_id: int) -> dict[str, int]:
    """Komplett-Load einer Saison: Tabelle + Spielplan."""
    async with HockeydataClient() as c:
        seasons = await c.get_seasons(league_id)
        current = seasons[-1] if seasons else None
        if not current:
            raise RuntimeError(f"Keine Saisons für leagueId={league_id}")

        season_label = current["seasonName"].replace("Saison ", "")
        season_uuid = upsert_season(season_label, league_name, league_tier, current["seasonId"])

        standings = await c.get_standings(division_id)
        n_teams = upsert_team_seasons_from_standings(season_uuid, standings)

        schedule = await c.get_schedule(division_id)
        n_games = upsert_games_from_schedule(season_uuid, schedule)

        return {"season_uuid": season_uuid, "n_teams": n_teams, "n_games": n_games}
