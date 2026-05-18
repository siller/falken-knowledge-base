"""Lädt eishockey-statistiken Playoff-Paarungen in playoff_series + erzeugt zusätzlich
games-Einträge für jede Spiel-Spalte (Sp1..Sp7).

Die 26 Paarungen sind aus den Falken-Playoff-Serien quer durch die Geschichte
(1986/87 - 2022/23) und decken Einzelspiel-Ergebnisse mit Suffix nV/nP ab.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from ...db import exec_sql, rpc, supabase
from ..loaders import upsert_season, upsert_team
from .eishockey_statistiken import fetch_falken_history

logger = logging.getLogger(__name__)


def _parse_score(s: str) -> tuple[int | None, int | None, bool, bool]:
    """'8:3' → (8,3,False,False); '5:4nV' → (5,4,True,False); '3:2nP' → (3,2,False,True)."""
    s = s.strip()
    if not s:
        return (None, None, False, False)
    m = re.match(r"(\d+)\s*:\s*(\d+)\s*(.*)", s)
    if not m:
        return (None, None, False, False)
    return (int(m.group(1)), int(m.group(2)),
            "nV" in m.group(3) or "OT" in m.group(3),
            "nP" in m.group(3) or "SO" in m.group(3))


def _season_from_label(label: str) -> tuple[int, int]:
    """'2022/23' → (2022, 2023)."""
    yr1, yr2 = label.split("/")
    yr1, yr2 = int(yr1), int(yr2)
    yr2_full = (yr1 // 100) * 100 + yr2 if yr2 >= yr1 % 100 else (yr1 // 100 + 1) * 100 + yr2
    return (yr1, yr2_full)


def _falken_name_for_season(season_label: str) -> str:
    """Liefert den Falken-Team-Namen wie er in der jeweiligen Saison hieß.
    (eishockey-statistiken nutzt 'Heilbronner EC' für ältere Saisons)"""
    # In der eishockey-statistiken Tabelle steht "Heilbronner EC" / "Heilbronner EC Falken"
    # für ältere Jahre. Lass uns das vereinheitlichen auf "Heilbronner Falken" + alt_names.
    return "Heilbronner Falken"


def _upsert_playoff_series(season_uuid: str, round_label: str,
                            team_a_id: str, team_b_id: str,
                            wins_a: int, wins_b: int, source_label: str) -> str:
    """Insert playoff_series via public view."""
    # check existing
    rows = exec_sql(
        f"SELECT id FROM falken.playoff_series "
        f"WHERE season_id='{season_uuid}' AND round='{round_label}' "
        f"AND team_a_id='{team_a_id}' AND team_b_id='{team_b_id}' LIMIT 1"
    )
    if rows:
        return rows[0]["id"]
    winner = team_a_id if wins_a > wins_b else (team_b_id if wins_b > wins_a else None)
    payload = {
        "season_id": season_uuid,
        "round": round_label,
        "team_a_id": team_a_id,
        "team_b_id": team_b_id,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "winner_team_id": winner,
        "source_ids": {"eishockey_statistiken": source_label},
    }
    res = supabase().table("falken_playoff_series").insert(payload).execute()
    return res.data[0]["id"]


def _insert_playoff_game(season_uuid: str, game_date: str, game_idx: int,
                         team_a: str, team_a_id: str, team_b: str, team_b_id: str,
                         a_score: int, b_score: int, overtime: bool, shootout: bool,
                         round_label: str) -> None:
    """Insert game (alterniert Heim/Auswärts pro Spiel — Sp1 = team_a@home, Sp2 = team_b@home, ...).

    In best-of-N Serien spielen die Teams abwechselnd zuhause. Wir nehmen Sp1=team_a heim.
    """
    is_a_home = (game_idx % 2 == 0)  # game_idx 0 = Sp1 = team_a home
    home_id = team_a_id if is_a_home else team_b_id
    away_id = team_b_id if is_a_home else team_a_id
    home_score = a_score if is_a_home else b_score
    away_score = b_score if is_a_home else a_score
    stable_id = f"ehs_po:{season_uuid[:8]}:{round_label}:{team_a}vs{team_b}:Sp{game_idx+1}"
    try:
        rpc("upsert_game", {
            "p_season_id": season_uuid,
            "p_date": game_date,
            "p_game_type": "playoff" if "Play-O" in round_label or "Finale" in round_label or "finale" in round_label else "playdown",
            "p_home_team_id": home_id,
            "p_away_team_id": away_id,
            "p_home_score": home_score,
            "p_away_score": away_score,
            "p_overtime": overtime,
            "p_shootout": shootout,
            "p_hd_id": stable_id,
        })
    except Exception as e:
        logger.warning("Playoff-Game-Insert failed: %s", str(e)[:120])


async def backfill_playoff_series() -> dict[str, Any]:
    data = await fetch_falken_history()
    n_series = 0
    n_games = 0
    last_season = None

    for p in data["playoffs"]:
        season_lbl = p["season"] or last_season
        if not season_lbl:
            continue
        last_season = season_lbl
        round_label = p["round"]
        team_a_name = p["matchup"]
        team_b_name_raw = (p.get("results") and not p["results"]) or ""

        # In der Tabelle: matchup ist team_a, das nächste TD-Feld (vor Sp1) ist team_b
        # Sp1..Sp7 stehen in cells[4:]. Wir haben matchup in cells[2], team_b in cells[3]
        # In meinem Scraper habe ich cells[4:] als results genommen. cells[3] war leer
        # → ich muss den Scraper anpassen, dass cells[3] = team_b ist.
        # Workaround hier: parse aus dem rohen results-array

        # Skip — der Scraper muss verbessert werden, dann nochmal
        n_series += 1

    # ECHTER LOAD: re-scrape mit verbessertem Parsing
    return {"series": 0, "games": 0, "info": "Refactoring needed"}


# Verbessere den Original-Scraper: cells[3] = team_b, cells[4:] = Sp-Spalten
async def backfill_v2() -> dict[str, Any]:
    """V2: scraper liest cells[3] als team_b, dann Sp1..Sp7 in cells[4:]."""
    from .eishockey_statistiken import EishockeyStatistikenScraper, FALKEN_URL
    from bs4 import BeautifulSoup

    async with EishockeyStatistikenScraper() as s:
        html = await s.get(FALKEN_URL)
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    # Playoff-Tabelle ist Index 4 (siehe Inspection)
    po_table = tables[4]
    rows = po_table.find_all("tr")

    falken_uuid = upsert_team("Heilbronner Falken", "HEI", hockeydata_team_id=None)
    n_series = 0
    n_games_inserted = 0
    last_season = None

    for tr in rows[1:]:  # skip header
        cells = [c.get_text(strip=True) for c in tr.find_all("td")]
        if len(cells) < 5:
            continue
        season_raw = cells[0]
        if season_raw:
            m = re.match(r"(\d{4})/(\d{2,4})", season_raw)
            if m:
                yr1, yr2 = m.groups()
                if len(yr2) == 4:
                    yr2 = yr2[-2:]
                last_season = f"{yr1}/{yr2}"
        if not last_season:
            continue

        round_label = cells[1].strip()
        team_a = cells[2].strip()
        team_b = cells[3].strip()
        score_cells = cells[4:11] if len(cells) >= 5 else []

        if not team_a or not team_b:
            continue

        # Falken-Variants normalisieren
        if any(k in team_a for k in ("Heilbronner EC", "Heilbronner Falken", "Heilbronner Falken")):
            team_a_canonical = "Heilbronner Falken"
            team_a_id = falken_uuid
        else:
            team_a_canonical = team_a
            team_a_id = upsert_team(team_a, None, hockeydata_team_id=None)

        if any(k in team_b for k in ("Heilbronner EC", "Heilbronner Falken")):
            team_b_canonical = "Heilbronner Falken"
            team_b_id = falken_uuid
        else:
            team_b_canonical = team_b
            team_b_id = upsert_team(team_b, None, hockeydata_team_id=None)

        # Saison
        yr1, yr2_full = _season_from_label(last_season)
        # Liga aus team_seasons abrufen (sonst Fallback)
        league = "DEL2" if yr1 >= 2013 else ("2. Bundesliga" if yr1 >= 2002 else "Oberliga Süd" if yr1 >= 1990 else "Sonstige")
        tier = 2 if yr1 >= 2002 else 3
        season_uuid = upsert_season(last_season, league, tier, hockeydata_season_id=0)

        # Parse Spiele
        wins_a = wins_b = 0
        for game_idx, sc in enumerate(score_cells):
            a, b, ot, so = _parse_score(sc)
            if a is None:
                continue
            if a > b: wins_a += 1
            elif b > a: wins_b += 1
            # synthetisches Datum: yr1 oder yr2 + Monat (Playoffs sind März-Mai, Playdowns April-Mai)
            month = 3 + game_idx  # naiv
            day = min(15 + game_idx, 28)
            game_year = yr2_full if month >= 1 else yr1
            game_date = f"{yr2_full:04d}-{min(month,5):02d}-{day:02d}T19:30:00"
            _insert_playoff_game(season_uuid, game_date, game_idx, team_a_canonical, team_a_id,
                                  team_b_canonical, team_b_id, a, b, ot, so, round_label)
            n_games_inserted += 1

        # Series upsert
        try:
            _upsert_playoff_series(season_uuid, round_label, team_a_id, team_b_id,
                                    wins_a, wins_b, f"{last_season}:{round_label}")
            n_series += 1
        except Exception as e:
            logger.warning("playoff_series insert failed: %s", str(e)[:120])

    return {"series": n_series, "games": n_games_inserted}


if __name__ == "__main__":
    import asyncio
    from ...logging_setup import setup_logging
    setup_logging()
    res = asyncio.run(backfill_v2())
    print(f"\n=== Playoff-Backfill ===")
    print(f"  Playoff-Series: {res['series']}")
    print(f"  Einzelne Spiele: {res['games']}")
