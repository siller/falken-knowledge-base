"""Backfill Oberliga Süd Playoffs 2023/24 + 2024/25 via Falken-Web hockeydata-Key.

WHY: Der DEB-Standard-Key (3c5a99..., referer deb-online.live) gibt für diese
Saisons keine Playoff-Divisionen zurück (KnockoutStage = no content). Mit dem
Falken-Web-Key (d9a998..., referer heilbronner-falken.de) ist es zugänglich:
- 23/24 Playoffs: divisionId=13020, 13 Falken-Spiele Feb-Apr 2024
- 24/25 Playoffs: divisionId=15806, 14 Falken-Spiele Feb-Apr 2025

Lädt die Spiele als game_type='playoff' und konstruiert playoff_series-Einträge
durch Gruppierung Team-Pair → Wins/Losses.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from falken_kb.db import exec_sql, rpc, supabase
from falken_kb.ingestion.loaders import upsert_team
from falken_kb.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

import os
FALKEN_WEB_KEY = os.environ.get("HOCKEYDATA_FALKEN_KEY", "")
FALKEN_WEB_REF = os.environ.get("HOCKEYDATA_FALKEN_REF", "heilbronner-falken.de")
if not FALKEN_WEB_KEY:
    raise RuntimeError("HOCKEYDATA_FALKEN_KEY env-var nicht gesetzt — Loader funktioniert nicht.")

# (Saison-Label, Liga, PO-divisionId, hockeydata-seasonId)
PLAYOFF_DIVS = [
    ("2023/24", "Oberliga Süd", 13020, 13018),
    ("2024/25", "Oberliga Süd", 15806, 15804),
]


async def fetch_schedule(div_id: int) -> list[dict]:
    url = "https://api.hockeydata.net/data/ih/Schedule"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, params={
            "apiKey": FALKEN_WEB_KEY,
            "divisionId": div_id,
            "referer": FALKEN_WEB_REF,
        })
        r.raise_for_status()
        data = r.json()
    return data["data"]["rows"]


def round_from_gamename(game_name: str) -> str:
    """Aus 'OLS_HEI_BAY_HF1_001' -> 'Halbfinale' (best-effort)."""
    if not game_name:
        return "Playoff"
    parts = game_name.upper()
    if "_F" in parts and ("FIN" in parts or "_F1" in parts or "_F2" in parts):
        return "Finale"
    if "HF" in parts or "SF" in parts:
        return "Halbfinale"
    if "VF" in parts or "QF" in parts:
        return "Viertelfinale"
    if "AF" in parts or "OF" in parts or "ROUND1" in parts or "_R1" in parts:
        return "Achtelfinale"
    if "PPO" in parts or "PRE" in parts:
        return "Pre Play-Off"
    return "Playoff"


async def backfill_one(season_label: str, league: str, po_div: int,
                       hockeydata_season_id: int) -> dict:
    print(f"\n=== {season_label} {league} (div={po_div}) ===")
    rows = await fetch_schedule(po_div)
    print(f"  Spiele insgesamt: {len(rows)}")

    # Find season UUID
    season_rows = exec_sql(
        f"SELECT id FROM seasons WHERE label = '{season_label}' "
        f"AND league = '{league.replace(chr(39), chr(39)+chr(39))}'"
    )
    if not season_rows:
        print(f"  ⚠ Saison {season_label} {league} nicht in DB")
        return {"season": season_label, "error": "season_not_found"}
    season_uuid = season_rows[0]["id"]

    # Upsert all games
    games_inserted = 0
    games_skipped = 0
    falken_games = []
    by_pair: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for g in rows:
        home_name = g.get("homeTeamLongName")
        away_name = g.get("awayTeamLongName")
        home_score = g.get("homeTeamScore")
        away_score = g.get("awayTeamScore")
        sched_iso = g.get("scheduledGameStart")
        if not home_name or not away_name or not sched_iso:
            games_skipped += 1
            continue
        # Skip Spiele ohne Resultat (nicht gespielt)
        if home_score is None or away_score is None:
            games_skipped += 1
            continue

        home_uuid = upsert_team(home_name, g.get("homeTeamShortName"),
                                hockeydata_team_id=g.get("homeTeamId"))
        away_uuid = upsert_team(away_name, g.get("awayTeamShortName"),
                                hockeydata_team_id=g.get("awayTeamId"))

        scoreInfo = (g.get("scoreInfo") or "")
        # gameName endet auf "OT"/"SO" oder hat finalDecidedAfter='OT'|'SO'
        decided = (g.get("finalDecidedAfter") or "").upper()
        ot = decided == "OT" or "OT" in scoreInfo
        so = decided == "SO" or "SO" in scoreInfo

        rpc("upsert_game", {
            "p_season_id": season_uuid,
            "p_date": sched_iso,
            "p_game_type": "playoff",
            "p_home_team_id": home_uuid,
            "p_away_team_id": away_uuid,
            "p_home_score": home_score,
            "p_away_score": away_score,
            "p_overtime": ot,
            "p_shootout": so,
            "p_hd_id": str(g.get("id")) if g.get("id") else None,
        })
        games_inserted += 1

        is_falken = (g.get("homeTeamId") == 47011 or g.get("awayTeamId") == 47011)
        if is_falken:
            falken_games.append({
                "date": sched_iso[:10],
                "home": home_name, "away": away_name,
                "score": f"{home_score}:{away_score}",
                "round": round_from_gamename(g.get("gameName", "")),
                "home_id": home_uuid, "away_id": away_uuid,
                "home_score": home_score, "away_score": away_score,
                "game_name": g.get("gameName", ""),
            })

        # Group by team-pair (canonicalized) for series-aggregation
        pair = tuple(sorted([home_uuid, away_uuid]))
        by_pair[pair].append({
            "home_uuid": home_uuid, "away_uuid": away_uuid,
            "home_score": home_score, "away_score": away_score,
            "round": round_from_gamename(g.get("gameName", "")),
        })

    print(f"  Spiele upserted: {games_inserted} (skipped: {games_skipped})")
    print(f"  Falken-Playoff-Spiele: {len(falken_games)}")
    for fg in falken_games:
        print(f"    {fg['date']} {fg['home']} {fg['score']} {fg['away']} [{fg['round']}] ({fg['game_name']})")

    # Construct playoff_series: only Falken-related pairs
    falken_uuid = exec_sql("SELECT id FROM teams WHERE name='Heilbronner Falken'")[0]["id"]
    series_count = 0
    for pair, games_list in by_pair.items():
        if falken_uuid not in pair:
            continue
        # Round = most common round of games (heuristic)
        rounds = [g["round"] for g in games_list]
        round_label = max(set(rounds), key=rounds.count)
        team_a, team_b = pair
        wins_a = sum(1 for g in games_list
                     if (g["home_uuid"] == team_a and g["home_score"] > g["away_score"])
                     or (g["away_uuid"] == team_a and g["away_score"] > g["home_score"]))
        wins_b = sum(1 for g in games_list
                     if (g["home_uuid"] == team_b and g["home_score"] > g["away_score"])
                     or (g["away_uuid"] == team_b and g["away_score"] > g["home_score"]))
        winner = team_a if wins_a > wins_b else (team_b if wins_b > wins_a else None)

        # Insert into playoff_series via supabase table (no RPC available)
        existing = exec_sql(
            f"SELECT id FROM playoff_series WHERE season_id='{season_uuid}' "
            f"AND ((team_a_id='{team_a}' AND team_b_id='{team_b}') "
            f"  OR (team_a_id='{team_b}' AND team_b_id='{team_a}')) "
            f"AND round = '{round_label}'"
        )
        if existing:
            continue
        record = {
            "season_id": season_uuid,
            "round": round_label,
            "team_a_id": team_a,
            "team_b_id": team_b,
            "wins_a": wins_a,
            "wins_b": wins_b,
            "winner_team_id": winner,
            "game_ids": [],
            "source_ids": {"hockeydata_falken_web": f"{season_label}_div{po_div}_{round_label}"},
        }
        try:
            supabase().table("falken_playoff_series").insert(record).execute()
            series_count += 1
        except Exception as e:
            logger.warning("playoff_series insert failed: %s", str(e)[:160])

    print(f"  playoff_series: {series_count} neue Serien")
    return {"season": season_label, "games": games_inserted, "falken_games": len(falken_games),
            "series": series_count}


async def main():
    results = []
    for label, league, div, sid in PLAYOFF_DIVS:
        r = await backfill_one(label, league, div, sid)
        results.append(r)
    print("\n=== Summary ===")
    for r in results: print(f"  {r}")


if __name__ == "__main__":
    asyncio.run(main())
