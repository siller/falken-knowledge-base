"""eishockey-statistiken.de — Falken-Saisonhistorie + Trainer + Zuschauer + Playoffs.

Eine einzige Seite gibt die komplette Falken-Geschichte zurück:
  https://www.eishockey-statistiken.de/index.php/121-oberliga-sued-clubs/257-heilbronner-falken

Wichtige Tabellen (siehe Inspection):
  [3] 56 rows: Saisonhistorie (Saison, Liga, Plazierung, Tore, Punkte, Play-Off, Trainer, Zuschauer)
  [4] 47 rows: Playoff-/Playdown-Paarungen (Saison, Serie, Paarung, Sp1..Sp7)
  [5] 31 rows: Zuschauerentwicklung
  [0] 34 rows: Torhüter-Historie
"""
from __future__ import annotations

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from ._base import Scraper

logger = logging.getLogger(__name__)


FALKEN_URL = "https://www.eishockey-statistiken.de/index.php/121-oberliga-sued-clubs/257-heilbronner-falken"


class EishockeyStatistikenScraper(Scraper):
    source = "eishockey_statistiken"
    rate_limit_sec = 2.0
    rate_jitter_sec = 0.5


def _parse_int(s: str) -> int | None:
    try:
        # "1.234" → 1234
        return int(s.replace(".", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _parse_season_label(s: str) -> str | None:
    """'2022/23' or '2022/2023' → '2022/23'."""
    m = re.match(r"(\d{4})\s*/\s*(\d{2,4})", s.strip())
    if not m:
        return None
    yr1 = m.group(1)
    yr2 = m.group(2)
    if len(yr2) == 4:
        yr2 = yr2[-2:]
    return f"{yr1}/{yr2}"


async def fetch_falken_history() -> dict[str, Any]:
    async with EishockeyStatistikenScraper() as s:
        html = await s.get(FALKEN_URL)

    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    seasons: list[dict[str, Any]] = []
    playoffs: list[dict[str, Any]] = []

    for t in tables:
        rows = t.find_all("tr")
        if not rows:
            continue
        first_row = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        if len(first_row) < 3:
            continue

        # Saisonhistorie-Tabelle: ['Saison', 'Liga', 'Plazierung', 'Tore', 'Punkte', 'Play-Off', 'Trainer', 'Zuschauer']
        if first_row[0].lower() in ("saison",) and "liga" in first_row[1].lower():
            for r in rows[1:]:
                cells = [c.get_text(strip=True) for c in r.find_all("td")]
                if len(cells) < 6:
                    continue
                season_lbl = _parse_season_label(cells[0])
                if not season_lbl:
                    continue
                seasons.append({
                    "season": season_lbl,
                    "league": cells[1],
                    "final_rank": _parse_int(cells[2]),
                    "tore": cells[3],         # "150:135" Format
                    "points": _parse_int(cells[4]),
                    "playoff_result": cells[5] if len(cells) > 5 else None,
                    "coach": cells[6] if len(cells) > 6 else None,
                    "attendance_avg": _parse_int(cells[7]) if len(cells) > 7 else None,
                })

        # Playoff-Paarungs-Tabelle: ['Saison', 'Serie', 'Paarung', '', 'Sp1'..'Sp7']
        elif first_row[0].lower() == "saison" and len(first_row) > 2 and "paarung" in first_row[2].lower():
            for r in rows[1:]:
                cells = [c.get_text(strip=True) for c in r.find_all("td")]
                if len(cells) < 5:
                    continue
                season_lbl = _parse_season_label(cells[0])
                if not season_lbl:
                    continue
                playoffs.append({
                    "season": season_lbl,
                    "round": cells[1],
                    "matchup": cells[2],
                    "results": cells[4:],  # Sp1..Sp7
                })

    return {
        "url": FALKEN_URL,
        "seasons": seasons,
        "playoffs": playoffs,
    }


if __name__ == "__main__":
    import asyncio, json
    from ...logging_setup import setup_logging
    setup_logging()
    res = asyncio.run(fetch_falken_history())
    print(f"\nSeasons gefunden: {len(res['seasons'])}")
    for s in res['seasons'][:15]:
        print(f"  {s['season']:<10} {s['league'][:25]:<25} Platz {s['final_rank']:>3} | {s['points']:>3}P | Trainer: {(s['coach'] or '?')[:30]}")
    print(f"\nPlayoff-Paarungen: {len(res['playoffs'])}")
    for p in res['playoffs'][:5]:
        print(f"  {p['season']} {p['round']:<20} {p['matchup'][:40]}")
