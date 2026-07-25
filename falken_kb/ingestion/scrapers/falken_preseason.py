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
from ...genai.web_search import web_search
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
    "Heilbronner Falken Pre-Season Derby Testspiel Termin",
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
    # Über die gemeinsame Web-Suche (Exa, sonst Tavily): der Verein kündigt
    # Nachmeldungen in eigenen Beiträgen an — das Pre-Season-Derby gegen
    # Bietigheim etwa stand nicht im Sammel-Artikel.
    for query in SEARCH_QUERIES:
        res = web_search(query, max_results=8, max_chars=200)
        for item in res.get("results") or []:
            u = item.get("url") or ""
            if CLUB_DOMAIN in u and u not in urls:
                urls.append(u)
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


MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
# "Am Samstag, den 05. September, kommt es … gegen die Bietigheim Steelers.
#  Spielbeginn ist um 16:00 Uhr"
PROSA_DATUM_RE = re.compile(r"den\s+(\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)", re.IGNORECASE)
PROSA_ZEIT_RE = re.compile(r"(?:Spielbeginn|Beginn|Anpfiff|Puckdrop)[^.]{0,40}?(\d{1,2})[:.](\d{2})\s*Uhr",
                           re.IGNORECASE)
PROSA_GEGNER_RE = re.compile(r"gegen\s+(?:die|den|das)?\s*([A-ZÄÖÜ][\w\-äöüß]*(?:\s+[A-ZÄÖÜ][\w\-äöüß]*){0,3})")


def parse_prose_fixture(text: str, jahr_hinweis: int) -> dict[str, Any] | None:
    """Einzeltermin aus einem Fließtext-Beitrag.

    WHY: Nachmeldungen kommen nicht in der Tabellenform, sondern als Meldung —
    das Derby gegen Bietigheim etwa stand nur so auf der Seite und fehlte
    deshalb im Spielplan. Bewusst streng: fehlt Datum, Uhrzeit, Gegner oder
    ein eindeutiges Heim-/Auswärts-Signal, wird nichts geraten.
    """
    d = PROSA_DATUM_RE.search(text)
    z = PROSA_ZEIT_RE.search(text)
    g = PROSA_GEGNER_RE.search(text)
    if not (d and z and g):
        return None
    monat = MONATE.get(d.group(2).lower())
    if not monat:
        return None
    gegner = g.group(1).strip()
    if CANONICAL.lower() in gegner.lower() or "falken" in gegner.lower():
        return None

    tief = text.lower()
    heim = "in heilbronn" in tief or "heilbronner eishalle" in tief
    auswaerts = "zu gast bei" in tief or "reisen nach" in tief or "gastiert" in tief
    if heim == auswaerts:  # kein eindeutiges Signal
        return None

    # Saison-Logik: Sommer-Termine gehören zum Jahr der Ankündigung
    jahr = jahr_hinweis if monat >= 7 else jahr_hinweis + 1
    try:
        dt = datetime(jahr, monat, int(d.group(1)), int(z.group(1)), int(z.group(2)))
    except ValueError:
        return None
    return {"date": dt,
            "home": CANONICAL if heim else gegner,
            "away": gegner if heim else CANONICAL}


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
        text = _plain_text(r.text)
        gefunden = parse_fixtures(text)
        if not gefunden:
            # Kein Tabellen-Format? Dann als Einzelmeldung versuchen.
            jahr = int(m.group(1)) if (m := re.search(r'"datePublished":"(\d{4})', r.text)) else datetime.now().year
            einzel = parse_prose_fixture(text, jahr)
            if einzel:
                gefunden = [einzel]
        for f in gefunden:
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
