"""del-2.org Spielplan-Scraper — KOMPLETTE DEL2-Historie 2007/08 bis 2025/26.

del-2.org organisiert Spielpläne über `round`-Parameter (round=1 bis ~149):
- Pro Saison: Hauptrunde, Testspiele, Playoffs, Playdowns, Cups
- Pro Round: Tabelle mit Datum, Zeit, Heim, Ergebnis, Gast, Spieltag

Liefert ~3.000–5.000 historische DEL2-Spiele insgesamt.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from ._base import Scraper

logger = logging.getLogger(__name__)


BASE = "https://www.del-2.org/spielplan/?round={round_id}"
SEASONS_URL = "https://www.del-2.org/spielplan?round=1"  # Page mit allen Round-Optionen


class Del2OrgScraper(Scraper):
    source = "del2_org"
    rate_limit_sec = 2.5
    rate_jitter_sec = 0.5


def parse_round_label(label: str) -> tuple[str | None, str | None]:
    """'2022/2023 - Hauptrunde' → ('2022/23', 'Hauptrunde')."""
    m = re.match(r"(\d{4})/(\d{4})\s*-\s*(.+)", label)
    if not m:
        return (None, None)
    yr1, yr2, kind = m.group(1), m.group(2), m.group(3).strip()
    return (f"{yr1}/{yr2[-2:]}", kind)


def round_type_to_game_type(round_kind: str) -> str:
    k = round_kind.lower()
    if "hauptrunde" in k or "vorrunde" in k or "qualifikationsrunde" in k:
        return "regular"
    if "testspiel" in k or "cup" in k or "turnier" in k or "challenge" in k or "legends" in k:
        return "friendly"
    if "playoff" in k:
        return "playoff"
    if "playdown" in k or "abstiegsrunde" in k:
        return "playdown"
    return "other"


async def list_rounds() -> list[tuple[int, str, str, str]]:
    """Holt die Liste aller Rounds: [(round_id, season_label, kind, full_label), ...]."""
    async with Del2OrgScraper() as s:
        html = await s.get(SEASONS_URL)
    soup = BeautifulSoup(html, "lxml")
    rounds: list[tuple[int, str, str, str]] = []
    for o in soup.find_all("option"):
        val = o.get("value", "")
        txt = o.get_text(strip=True)
        m = re.search(r"round=(\d+)", val)
        if not m:
            continue
        round_id = int(m.group(1))
        season, kind = parse_round_label(txt)
        if season and kind:
            rounds.append((round_id, season, kind, txt))
    return rounds


def parse_game_row(cells: list[str]) -> dict[str, Any] | None:
    """['Fr, 16.09.22', '19:30', 'ESV Kaufbeuren', '2 - 1', 'EC Kassel Huskies', '1', '', ''] → game dict."""
    if len(cells) < 5:
        return None
    date_str = cells[0]
    time_str = cells[1]
    home = cells[2]
    result = cells[3]
    away = cells[4]
    spieltag = cells[5] if len(cells) > 5 else None

    if not home or not away or home == "Heim":  # Header-Zeile überspringen
        return None

    # Datum: "Fr, 16.09.22" → "2022-09-16"
    m_date = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2})", date_str)
    if not m_date:
        return None
    dd, mm, yy = m_date.groups()
    year = 2000 + int(yy)
    iso_date = f"{year:04d}-{int(mm):02d}-{int(dd):02d}"
    # Zeit
    m_time = re.match(r"(\d{1,2}):(\d{2})", time_str)
    iso_dt = f"{iso_date}T{int(m_time.group(1)):02d}:{m_time.group(2)}:00" if m_time else f"{iso_date}T19:30:00"

    # Ergebnis "2 - 1" oder "5 - 4 (nV)" oder "3 - 2 nP"
    m_score = re.match(r"(\d+)\s*[-:]\s*(\d+)", result.strip())
    if m_score:
        home_score = int(m_score.group(1))
        away_score = int(m_score.group(2))
    else:
        home_score = away_score = None

    overtime = bool(re.search(r"\bnV\b|\bOT\b", result))
    shootout = bool(re.search(r"\bnP\b|\bSO\b", result))

    return {
        "date": iso_dt,
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "overtime": overtime,
        "shootout": shootout,
        "spieltag": spieltag,
    }


async def fetch_round(round_id: int) -> list[dict[str, Any]]:
    """Holt alle Spiele einer Round."""
    async with Del2OrgScraper() as s:
        html = await s.get(BASE.format(round_id=round_id))
    soup = BeautifulSoup(html, "lxml")
    games: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        for r in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in r.find_all("td")]
            g = parse_game_row(cells)
            if g:
                games.append(g)
    return games


if __name__ == "__main__":
    import asyncio, json
    from ...logging_setup import setup_logging
    setup_logging()

    async def main():
        rounds = await list_rounds()
        print(f"Total rounds: {len(rounds)}")
        # Show seasons
        seasons = sorted(set(r[1] for r in rounds))
        print(f"Saisons: {seasons}")

        # Sample: round 133 (Hauptrunde 2022/23)
        games = await fetch_round(133)
        print(f"\nRound 133 (Hauptrunde 22/23): {len(games)} Spiele")
        for g in games[:5]:
            print(f"  {g['date'][:16]}: {g['home_team']} {g['home_score']}:{g['away_score']} {g['away_team']} (Sp{g.get('spieltag','')})")

    asyncio.run(main())
