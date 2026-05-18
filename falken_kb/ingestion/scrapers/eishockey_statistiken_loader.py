"""Loader: eishockey-statistiken.de → Supabase.

Lädt:
- seasons (alle 44 Saisons, auch ältere Ligen wie LLBW, OLS, etc.)
- team_seasons (Platzierung, Punkte, Tore, Playoff-Ergebnis)
- coaches + coach_tenures (Trainer pro Saison)
"""
from __future__ import annotations

import logging
import re
from typing import Any

from ...db import rpc
from ..loaders import upsert_season, upsert_team
from .eishockey_statistiken import fetch_falken_history

logger = logging.getLogger(__name__)


LEAGUE_NORMALIZE: dict[str, tuple[str, int]] = {
    "LLBW": ("Landesliga BaWü", 5),
    "BWL": ("Baden-Württemberg-Liga", 5),
    "RLSW": ("Regionalliga Süd-West", 4),
    "OLM": ("Oberliga Mitte", 3),
    "OLN": ("Oberliga Nord", 3),
    "OLS": ("Oberliga Süd", 3),
    "Oberliga Süd": ("Oberliga Süd", 3),
    "Oberliga": ("Oberliga", 3),
    "2.BLS": ("2. Bundesliga Süd", 2),
    "2.BL": ("2. Bundesliga", 2),
    "1.BLS": ("1. Bundesliga Süd", 1),
    "HPL": ("Hockey Premier League", 2),
    "DEL2": ("DEL2", 2),
    "DEL": ("DEL", 1),
}


def normalize_league(raw: str) -> tuple[str, int]:
    raw = raw.strip()
    for key, val in LEAGUE_NORMALIZE.items():
        if raw.upper().startswith(key.upper()):
            return val
    return (raw, 99)


def parse_goals(s: str | None) -> tuple[int | None, int | None]:
    if not s: return (None, None)
    m = re.match(r"(\d+)\s*:\s*(\d+)", s.strip())
    if not m: return (None, None)
    return (int(m.group(1)), int(m.group(2)))


def _split_coaches(s: str | None) -> list[str]:
    if not s or s.strip() in ("---", "?"):
        return []
    parts = re.split(r"\s*/\s*", s)
    cleaned = []
    for p in parts:
        p = p.replace("†", "").strip()
        if p and p != "---":
            cleaned.append(p)
    return cleaned


def _season_dates(season_lbl: str) -> tuple[str, str]:
    """'2022/23' → ('2022-09-01', '2023-05-31')."""
    yr1, yr2 = season_lbl.split("/")
    yr1, yr2 = int(yr1), int(yr2)
    # Saison 19/20 → end_yr = 2020; 99/00 → 2000
    yr2_full = (yr1 // 100) * 100 + yr2 if yr2 >= yr1 % 100 else (yr1 // 100 + 1) * 100 + yr2
    return (f"{yr1:04d}-09-01", f"{yr2_full:04d}-05-31")


async def backfill_falken_history() -> dict[str, Any]:
    data = await fetch_falken_history()
    falken_uuid = upsert_team("Heilbronner Falken", "HEI", hockeydata_team_id=None)

    n_seasons = 0
    n_team_seasons = 0
    n_coaches = 0
    n_tenures = 0
    skipped = []

    for s in data["seasons"]:
        season_lbl = s["season"]
        if not season_lbl:
            continue
        league_name, league_tier = normalize_league(s["league"])
        if league_name.startswith("- Spielpause"):
            skipped.append(season_lbl)
            continue

        season_uuid = upsert_season(season_lbl, league_name, league_tier, hockeydata_season_id=0)
        n_seasons += 1

        gf, ga = parse_goals(s.get("tore"))
        try:
            rpc("upsert_team_season_full", {
                "p_team_id": falken_uuid,
                "p_season_id": season_uuid,
                "p_rank": s.get("final_rank"),
                "p_gp": None, "p_wins": None, "p_losses": None,
                "p_ot_wins": None, "p_ot_losses": None,
                "p_points": s.get("points"),
                "p_gf": gf, "p_ga": ga,
                "p_playoff_result": s.get("playoff_result"),
                "p_source": "eishockey_statistiken",
            })
            n_team_seasons += 1
        except Exception as e:
            logger.warning("team_season failed für %s: %s", season_lbl, e)

        # Coaches
        for coach_name in _split_coaches(s.get("coach")):
            try:
                coach_uuid = rpc("upsert_coach", {"p_name": coach_name})
                n_coaches += 1
                start_d, end_d = _season_dates(season_lbl)
                rpc("upsert_coach_tenure", {
                    "p_coach_id": coach_uuid,
                    "p_team_id": falken_uuid,
                    "p_role": "Headcoach",
                    "p_start": start_d,
                    "p_end": end_d,
                    "p_source": f"eishockey_statistiken:{season_lbl}",
                })
                n_tenures += 1
            except Exception as e:
                logger.warning("coach insert failed (%s, %s): %s", coach_name, season_lbl, e)

    return {
        "seasons_loaded": n_seasons,
        "team_seasons": n_team_seasons,
        "coach_attempts": n_coaches,
        "tenures": n_tenures,
        "skipped": skipped,
        "playoffs_raw": len(data["playoffs"]),
    }


if __name__ == "__main__":
    import asyncio
    from ...logging_setup import setup_logging
    setup_logging()
    res = asyncio.run(backfill_falken_history())
    print(f"\n=== Falken-Historie geladen ===")
    print(f"  Saisons: {res['seasons_loaded']}")
    print(f"  Team-Saisons: {res['team_seasons']}")
    print(f"  Coach-Inserts: {res['coach_attempts']}")
    print(f"  Coach-Tenures: {res['tenures']}")
    print(f"  Spielpause-skipped: {res['skipped']}")
    print(f"  Playoffs raw (nicht geladen): {res['playoffs_raw']}")
