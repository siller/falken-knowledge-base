"""Testspiele (Vorbereitung) von heilbronner-falken.de.

WHY: hockeydata führt nur den Ligabetrieb. Die Vorbereitungsspiele im August
stehen ausschließlich auf der Vereinsseite — ohne diesen Loader kennt die KB
den Saisonstart nicht und antwortet auf "Wann spielen die Falken das nächste
Mal?" mit dem ersten Hauptrundenspiel, obwohl vorher sechs Testspiele laufen.

Der Verein veröffentlicht die Termine in Wellen ("Nun stehen die ersten Termine
fest"), deshalb ist der Loader idempotent und wird täglich mitgelaufen.

Format auf der Seite:  23.08.2026 | Füchse Duisburg – HEC Falken | 15:00 Uhr

Aufruf:
    python3 -m falken_kb.ingestion.scrapers.falken_preseason --dry-run
"""
from __future__ import annotations

import argparse
import logging
import re
from datetime import datetime
from html import unescape
from typing import Any

import httpx

from ...config import settings
from ...db import exec_sql, rpc
from ..loaders import upsert_season, upsert_team

logger = logging.getLogger(__name__)

CLUB_DOMAIN = "heilbronner-falken.de"

# Seiten, auf denen der Verein die Vorbereitung ankündigt. Ergänzt wird die
# Liste zur Laufzeit über eine Tavily-Suche, damit auch Nachmeldungen unter
# neuer URL gefunden werden.
SEED_URLS = [
    "https://www.heilbronner-falken.de/vorbereitungsprogramm-der-hec-falken-steht-fest",
    "https://www.heilbronner-falken.de/vorbereitungsprogramm-der-heilbronner-falken-steht",
]

SEARCH_QUERIES = [
    "Heilbronner Falken Vorbereitungsprogramm Testspiele Termine",
    "HEC Falken Vorbereitungsspiele Termine",
]

# "23.08.2026 | Füchse Duisburg – HEC Falken | 15:00 Uhr"
FIXTURE_RE = re.compile(
    r"(\d{2}\.\d{2}\.\d{4})\s*\|\s*([^|]{3,60}?)\s*\|\s*(\d{1,2})[:.](\d{2})\s*Uhr"
)
# Trennzeichen zwischen den Teams: Gedankenstrich, Bindestrich oder "vs"
TEAM_SPLIT_RE = re.compile(r"\s+(?:–|—|-|vs\.?|gegen)\s+", re.IGNORECASE)

# Schreibweisen des eigenen Klubs auf der Vereinsseite
OWN_NAMES = ("hec falken", "heilbronner falken", "heilbronner ec falken", "falken")
CANONICAL = "Heilbronner Falken"


def _plain_text(html: str) -> str:
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)))


def _canonical_team(name: str) -> str:
    """'HEC Falken' -> 'Heilbronner Falken'; andere Namen unverändert lassen."""
    n = name.strip(" .-–—")
    return CANONICAL if n.lower() in OWN_NAMES else n


def _season_label(dt: datetime) -> str:
    """23.08.2026 -> '2026/27' (Saison beginnt im Sommer)."""
    start = dt.year if dt.month >= 7 else dt.year - 1
    return f"{start}/{str(start + 1)[-2:]}"


def _candidate_urls() -> list[str]:
    urls = list(SEED_URLS)
    if not settings.tavily_api_key:
        return urls
    for query in SEARCH_QUERIES:
        try:
            with httpx.Client(timeout=30) as c:
                r = c.post("https://api.tavily.com/search", json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": 8,
                    "search_depth": "basic",
                })
                r.raise_for_status()
                for item in r.json().get("results") or []:
                    u = item.get("url") or ""
                    if CLUB_DOMAIN in u and u not in urls:
                        urls.append(u)
        except httpx.HTTPError as e:
            logger.warning("Tavily-Suche fehlgeschlagen: %s", str(e)[:120])
    return urls


def parse_fixtures(text: str) -> list[dict[str, Any]]:
    """Alle Termin-Zeilen einer Seite, gefiltert auf Falken-Beteiligung."""
    out: list[dict[str, Any]] = []
    for datum, paarung, stunde, minute in FIXTURE_RE.findall(text):
        teams = TEAM_SPLIT_RE.split(paarung)
        if len(teams) != 2:
            continue
        home, away = (_canonical_team(t) for t in teams)
        if CANONICAL not in (home, away):
            continue
        try:
            dt = datetime.strptime(f"{datum} {stunde}:{minute}", "%d.%m.%Y %H:%M")
        except ValueError:
            continue
        out.append({"date": dt, "home": home, "away": away})
    return out


def harvest(dry_run: bool = False) -> dict[str, Any]:
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    for url in _candidate_urls():
        try:
            r = httpx.get(url, timeout=30, follow_redirects=True,
                          headers={"User-Agent": settings.scraper_user_agent})
            if r.status_code != 200:
                continue
        except httpx.HTTPError as e:
            logger.warning("%s: %s", url, str(e)[:100])
            continue
        for f in parse_fixtures(_plain_text(r.text)):
            key = (f["date"].isoformat(), f["home"], f["away"])
            seen.setdefault(key, f)

    fixtures = sorted(seen.values(), key=lambda f: f["date"])
    geladen = 0
    for f in fixtures:
        label = _season_label(f["date"])
        print(f"  {f['date']:%d.%m.%Y %H:%M}  {f['home']} – {f['away']}  [{label}]")
        if dry_run:
            continue
        # Zu einem Label gibt es mehrere Saison-Zeilen (2025/26 existiert als
        # DEL2 UND als Oberliga Süd). Für ein Falken-Testspiel zählt die Liga,
        # in der die Falken gespielt haben — dafür ist is_focus_team_season da.
        # Ohne diese Sortierung landete das Spiel alphabetisch bei "DEL2".
        rows = exec_sql(
            f"SELECT id, league FROM seasons WHERE label = '{label}' "
            "ORDER BY is_focus_team_season DESC NULLS LAST, league LIMIT 1"
        )
        if not rows:
            logger.warning("Saison %s nicht in der DB — Testspiel übersprungen", label)
            continue
        season_uuid = rows[0]["id"]
        rpc("upsert_game", {
            "p_season_id": season_uuid,
            "p_date": f["date"].isoformat(),
            "p_game_type": "friendly",
            "p_home_team_id": upsert_team(f["home"]),
            "p_away_team_id": upsert_team(f["away"]),
            # Termin ohne Ergebnis — Scores kommen erst nach dem Spiel dazu.
            "p_home_score": None,
            "p_away_score": None,
            "p_overtime": False,
            "p_shootout": False,
            "p_hd_id": f"falkenweb:preseason:{f['date']:%Y-%m-%d}:{f['home']}:{f['away']}",
        })
        geladen += 1

    return {"gefunden": len(fixtures), "geladen": geladen}


def main() -> None:
    from ...logging_setup import setup_logging

    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("Testspiele von heilbronner-falken.de:")
    out = harvest(dry_run=args.dry_run)
    print(f"\n{out['gefunden']} Termine gefunden, {out['geladen']} geschrieben"
          f"{' (dry-run)' if args.dry_run else ''}.")


if __name__ == "__main__":
    main()
