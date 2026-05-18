"""Backfill falken.goalie_stats aus hockeydata LeaderGoalKeepers.

Strategie:
1. Für jede Saison mit hockeydata-divisionId: LeaderGoalKeepers(divId, teamId=47011)
2. Für jede Goalie-Row: Player + Player_Season finden/anlegen + goalie_stats upsert.

Idempotent — über player_season_id PRIMARY KEY.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from falken_kb.db import supabase, exec_sql
from falken_kb.ingestion.hockeydata_client import HockeydataClient, HockeydataError
from falken_kb.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

FALKEN_API_ID = 47011

# Erprobte Falken-Regular-Season divisionIds aus Probe
# (Format: season_label, league, regular_season_divisionId)
KNOWN_DIVISIONS: list[tuple[str, str, int]] = [
    ("2025/26", "Oberliga Süd", 18552),  # 6 teams, mit Falken
    ("2024/25", "Oberliga Süd", 15881),  # 13 teams, 3 Falken-Goalies
    ("2023/24", "Oberliga Süd", 13220),  # 5 teams, mit Falken (vermutlich Aufstiegsrunde)
    ("2022/23", "DEL2", 10922),         # placeholder — Falken in 300-Window nicht gefunden
    ("2021/22", "DEL2", 9617),          # 5 teams, mit Falken (vermutlich PO/Playdown)
]


async def discover_falken_division(c: HockeydataClient, season_id: int, window: int = 100) -> int | None:
    """Findet die Division mit Falken-Beteiligung im Offset-Range."""
    for offset in range(window):
        candidate = season_id + offset
        try:
            rows = await c.get_standings(candidate)
            team_names = [r.get("teamLongname") or r.get("teamLongName", "") for r in rows]
            if any("Heilbronner Falken" in n for n in team_names):
                logger.info("  Falken-Division discovered: %d (%d teams)", candidate, len(rows))
                return candidate
        except HockeydataError:
            continue
        except Exception as e:
            logger.debug("  divId=%d err: %s", candidate, str(e)[:80])
    return None


def upsert_falken_player(name: str, position: str | None, hockeydata_player_id: int | None) -> str:
    """Find or create player. Returns player UUID."""
    # Naive: by name match (Falken-Namen sind unique genug)
    existing = exec_sql(f"SELECT id FROM players WHERE name = '{name.replace(chr(39), chr(39)+chr(39))}'")
    if existing:
        return existing[0]["id"]
    # Insert new
    res = supabase().table("falken_players").insert({
        "name": name,
        "position": position or "G",
        "source_ids": {"hockeydata": str(hockeydata_player_id)} if hockeydata_player_id else {},
    }).execute()
    return res.data[0]["id"]


def find_or_create_player_season(player_id: str, season_id: str, falken_team_uuid: str,
                                   jersey: int | None) -> str:
    """Find or create player_season for this player+season+team."""
    existing = exec_sql(
        f"SELECT id FROM player_seasons WHERE player_id='{player_id}' "
        f"AND season_id='{season_id}' AND team_id='{falken_team_uuid}'"
    )
    if existing:
        return existing[0]["id"]
    res = supabase().table("falken_player_seasons").insert({
        "player_id": player_id,
        "team_id": falken_team_uuid,
        "season_id": season_id,
        "jersey_number": jersey,
        "role": "goalie",
    }).execute()
    return res.data[0]["id"]


FALKEN_SHORTNAMES = {"HNF", "HEC", "HCF"}  # über die Jahre variabel


async def backfill_one_season(c: HockeydataClient, season_label: str, league: str,
                               div_id: int, falken_team_uuid: str, season_uuid: str) -> dict[str, Any]:
    # Server-seitiger teamId-Filter funktioniert NICHT in LeaderGoalKeepers
    # → client-seitig per teamShortname filtern (HNF/HEC/HCF).
    try:
        all_goalies = await c.get_leader_goalies(div_id)
    except HockeydataError as e:
        return {"season": season_label, "div": div_id, "error": f"API: {e}"}

    falken_goalies = [g for g in all_goalies if (g.get("teamShortname") or "") in FALKEN_SHORTNAMES]

    if not falken_goalies:
        return {"season": season_label, "div": div_id, "goalies_total": len(all_goalies), "falken_goalies": 0}

    upserted = 0
    for g in falken_goalies:
        last = g.get("playerLastname") or ""
        first = g.get("playerFirstname") or ""
        mid = g.get("playerMiddlename") or ""
        name_parts = [first, mid, last]
        name = " ".join(p for p in name_parts if p).strip()
        if not name:
            continue
        hd_player_id = g.get("id")
        jersey = g.get("playerJerseyNr")

        player_uuid = upsert_falken_player(name, "G", hd_player_id)
        ps_uuid = find_or_create_player_season(player_uuid, season_uuid, falken_team_uuid, jersey)

        # goalie_stats: aus hockeydata-Schema mappen
        # gameWinsRegular + gameWinsOvertime = wins; gameLostRegular = losses; gameLostOvertime = ot_losses
        wins = (g.get("gameWinsRegular") or 0) + (g.get("gameWinsOvertime") or 0)
        losses = g.get("gameLostRegular") or 0
        ot_losses = g.get("gameLostOvertime") or 0
        # save_pct: Hockeydata gibt z.B. 92.0 → wir speichern 0.920
        sv_pct_raw = g.get("savePercentage")
        save_pct = sv_pct_raw / 100.0 if isinstance(sv_pct_raw, (int, float)) and sv_pct_raw > 1 else sv_pct_raw
        # minutes_played: playingTime ist in Sekunden
        pt = g.get("playingTime")
        minutes_played = int(pt / 60) if isinstance(pt, (int, float)) else None
        shots = g.get("shotsAgainst")
        ga = g.get("goalsAgainst")
        saves = (shots - ga) if (shots is not None and ga is not None) else None

        try:
            supabase().table("falken_goalie_stats").upsert({
                "player_season_id": ps_uuid,
                "games_played": g.get("gamesPlayed"),
                "wins": wins,
                "losses": losses,
                "ot_losses": ot_losses,
                "shutouts": g.get("shutOuts"),
                "goals_against": ga,
                "saves": saves,
                "shots_against": shots,
                "gaa": g.get("goalsAgainstAverage"),
                "save_pct": save_pct,
                "minutes_played": minutes_played,
            }, on_conflict="player_season_id").execute()
            upserted += 1
        except Exception as e:
            logger.warning("  goalie_stats upsert failed for %s: %s", name, str(e)[:160])
    return {"season": season_label, "div": div_id, "goalies_total": len(all_goalies),
            "falken_goalies": len(falken_goalies), "upserted": upserted}


async def main() -> None:
    # Falken Team-UUID
    teams = exec_sql("SELECT id FROM teams WHERE name='Heilbronner Falken'")
    falken_uuid = teams[0]["id"]

    # Season-UUIDs mit hockeydata-IDs
    seasons = exec_sql("""
        SELECT label, league, id, source_ids
        FROM seasons WHERE is_focus_team_season=TRUE AND source_ids->>'hockeydata' != '0'
        ORDER BY start_date DESC NULLS LAST""")
    print(f"Seasons mit hockeydata-IDs: {len(seasons)}")

    label_to_uuid = {(s["label"], s["league"]): s["id"] for s in seasons}

    async with HockeydataClient() as c:
        results = []
        for label, league, div in KNOWN_DIVISIONS:
            season_uuid = label_to_uuid.get((label, league))
            if not season_uuid:
                print(f"  ⚠ Season {label} ({league}) nicht in DB, skip")
                continue
            print(f"\n--- {label} {league}, div={div} ---")
            r = await backfill_one_season(c, label, league, div, falken_uuid, season_uuid)
            print(f"  → {r}")
            results.append(r)

        # 25/26 div discovery (Falken-Beteiligung)
        s2526 = label_to_uuid.get(("2025/26", "Oberliga Süd"))
        if s2526:
            seasons_api = await c.get_seasons(150)
            for s in seasons_api:
                if "2025/26" in s.get("seasonName", ""):
                    sid = s["seasonId"]
                    print(f"\n--- Discover Falken-div for 25/26 (seasonId={sid}) ---")
                    div = await discover_falken_division(c, sid, window=100)
                    if div:
                        r = await backfill_one_season(c, "2025/26", "Oberliga Süd", div, falken_uuid, s2526)
                        print(f"  → {r}")
                        results.append(r)
                    break

    print("\n=== Goalie-Stats Backfill — Summary ===")
    for r in results:
        print(f"  {r}")


if __name__ == "__main__":
    asyncio.run(main())
