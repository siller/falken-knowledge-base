"""Loader: del-2.org Spielpläne → Supabase.

Lädt alle 83 Rounds (2007/08 bis 2025/26 DEL2-Historie) komplett in die DB.
Pro Round: ~50–366 Spiele, je nach Wettbewerbsart.
"""
from __future__ import annotations

import logging
from typing import Any

from ...db import rpc
from ..loaders import upsert_season, upsert_team
from .del2_org import fetch_round, list_rounds, round_type_to_game_type

logger = logging.getLogger(__name__)


# DEL2-Tier ist 2 (zweithöchste Liga), für Saisons vor DEL2-Brand (2007-2013) war es "2. Bundesliga"
LEAGUE_BY_YEAR_RANGE: list[tuple[int, int, str, int]] = [
    # (start_year, end_year, league_name, tier)
    (2013, 2099, "DEL2", 2),
    (2007, 2012, "2. Bundesliga", 2),
]


def league_for_season(season_label: str) -> tuple[str, int]:
    """'2022/23' → ('DEL2', 2)."""
    yr = int(season_label.split("/")[0])
    for start, end, name, tier in LEAGUE_BY_YEAR_RANGE:
        if start <= yr <= end:
            return (name, tier)
    return ("DEL2", 2)


async def load_round(round_id: int, season_label: str, kind: str) -> dict[str, Any]:
    """Lädt eine einzelne Round in die DB."""
    league_name, league_tier = league_for_season(season_label)
    season_uuid = upsert_season(season_label, league_name, league_tier, hockeydata_season_id=0)
    game_type = round_type_to_game_type(kind)

    games = await fetch_round(round_id)
    if not games:
        return {"round_id": round_id, "season": season_label, "kind": kind, "games": 0}

    inserted = 0
    skipped = 0
    for g in games:
        try:
            home_uuid = upsert_team(g["home_team"], None, hockeydata_team_id=None)
            away_uuid = upsert_team(g["away_team"], None, hockeydata_team_id=None)
            # Stable game-key: kombiniert Datum + Home + Away (round_id+spieltag wäre auch ok)
            stable_id = f"del2org:{season_label}:{g['date'][:10]}:{g['home_team']}:{g['away_team']}".replace("'", "")
            rpc("upsert_game", {
                "p_season_id": season_uuid,
                "p_date": g["date"],
                "p_game_type": game_type,
                "p_home_team_id": home_uuid,
                "p_away_team_id": away_uuid,
                "p_home_score": g["home_score"],
                "p_away_score": g["away_score"],
                "p_overtime": g["overtime"],
                "p_shootout": g["shootout"],
                "p_hd_id": stable_id,
            })
            inserted += 1
        except Exception as e:
            logger.warning("Game-Insert failed: %s vs %s am %s: %s",
                           g.get("home_team"), g.get("away_team"), g.get("date"), str(e)[:100])
            skipped += 1
    return {"round_id": round_id, "season": season_label, "kind": kind,
            "games_total": len(games), "inserted": inserted, "skipped": skipped}


async def backfill_all_del2_org(only_seasons: set[str] | None = None) -> dict[str, Any]:
    """Backfill aller verfügbaren Rounds. only_seasons filtert optional."""
    rounds = await list_rounds()
    total_games = 0
    by_season: dict[str, dict[str, int]] = {}

    for round_id, season, kind, label in rounds:
        if only_seasons and season not in only_seasons:
            continue
        res = await load_round(round_id, season, kind)
        total_games += res.get("inserted", 0)
        by_season.setdefault(season, {"rounds": 0, "games": 0})
        by_season[season]["rounds"] += 1
        by_season[season]["games"] += res.get("inserted", 0)
        print(f"  [r{round_id:>3}] {season} {kind:<25} → {res.get('inserted',0):>3} / {res.get('games_total',0):>3} Spiele")

    return {"total_games_inserted": total_games, "by_season": by_season}


if __name__ == "__main__":
    import asyncio
    from ...logging_setup import setup_logging
    setup_logging()
    # Defaults: alle Saisons. Mit only_seasons={"2022/23","2021/22"} kann man eingrenzen
    res = asyncio.run(backfill_all_del2_org())
    print(f"\n=== Total games inserted: {res['total_games_inserted']} ===")
    for season, stats in sorted(res['by_season'].items()):
        print(f"  {season}: {stats['rounds']} rounds, {stats['games']} games")
