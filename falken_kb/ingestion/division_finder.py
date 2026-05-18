"""Findet aktuelle DEL2-/Oberliga-Sub-Division-IDs durch HTML-Scrape von deb-online.live.

Die Liga-Plattform deb-online.live (DEL2) und ihre Schwesterseiten haben die
korrekten divisionIds in ihren Tabellen-/Spielplan-URLs eingebettet. Da die
hockeydata-API keinen sauberen Pfad bietet, an diese IDs zu kommen
(GetSeasons liefert nur Saison-Wrapper, die "Not calculated" sind), scrapen
wir die Liga-Plattform.

Ergebnis wird ge-caching damit wir das nicht ständig wiederholen müssen.
"""
from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from .hockeydata_client import HockeydataClient, HockeydataError

logger = logging.getLogger(__name__)


DEL2_PAGES = [
    "https://deb-online.live/del2-tabelle/",
    "https://deb-online.live/del2-spielplan/",
    "https://deb-online.live/del2-topscorer/",
]
OBERLIGA_SUED_PAGES = [
    "https://deb-online.live/oberliga-sued-tabelle/",
    "https://deb-online.live/oberliga-sued-spielplan/",
]

DIV_ID_RE = re.compile(r"divisionId=(\d+)")
DIVISION_CACHE = settings.cache_dir / "current_divisions.json"


def _scrape_division_ids(pages: list[str]) -> set[int]:
    ids: set[int] = set()
    headers = {
        # Browser-Header — deb-online.live antwortet auf "python-httpx" mit 403
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    with httpx.Client(timeout=20.0, headers=headers, follow_redirects=True) as h:
        for url in pages:
            try:
                r = h.get(url)
                # WordPress liefert oft 404-Status mit vollem Content — Content trotzdem auswerten
                if r.text:
                    found = set(int(m.group(1)) for m in DIV_ID_RE.finditer(r.text))
                    if found:
                        logger.debug("  %s → %d IDs", url, len(found))
                        ids |= found
                    elif r.status_code >= 400:
                        logger.warning("HTTP %d auf %s, kein divisionId gefunden", r.status_code, url)
                else:
                    logger.warning("HTTP %d auf %s (leer)", r.status_code, url)
            except httpx.HTTPError as e:
                logger.warning("Konnte %s nicht laden: %s", url, e)
    return ids


async def _classify_division(client: HockeydataClient, div_id: int) -> dict | None:
    """Probiert Standings + Schedule + KnockoutStage und klassifiziert anhand der Response."""
    try:
        teams = await client.get_standings(div_id)
        matches = await client.get_schedule(div_id)
        try:
            knockout = await client.get_knockout_stage(div_id)
            has_knockout = bool(knockout and (isinstance(knockout, dict) and knockout))
        except HockeydataError:
            has_knockout = False
    except HockeydataError:
        return None

    if not teams and not matches:
        return None

    sample_match = matches[0] if matches else {}
    return {
        "divisionId": div_id,
        "n_teams": len(teams),
        "n_matches": len(matches),
        "has_knockout": has_knockout,
        "first_match_date": sample_match.get("scheduledDate"),
        "round_type": sample_match.get("roundType") or sample_match.get("phase"),
    }


def _classify_role(info: dict) -> str:
    """Heuristik: aus n_teams + n_matches + has_knockout → Rolle ableiten."""
    n_teams = info["n_teams"]
    n_matches = info["n_matches"]
    if info["has_knockout"]:
        return "playoffs" if n_teams >= 6 else "playdowns"
    if n_teams >= 10 and n_matches > 100:
        return "regular_season"
    if n_teams < 6 and n_matches < 30:
        return "playdowns"
    if n_teams >= 4 and n_matches < 50:
        return "playoffs"
    return "unknown"


async def find_current_divisions(league: str = "DEL2") -> dict[str, int]:
    """Scrape deb-online.live + klassifiziere → mapping {role -> divisionId}.

    `league`: "DEL2" oder "OberligaSüd"
    """
    if DIVISION_CACHE.exists():
        cache = json.loads(DIVISION_CACHE.read_text())
        if league in cache:
            logger.info("Division-Cache hit für %s", league)
            return cache[league]
    else:
        cache = {}

    pages = DEL2_PAGES if league == "DEL2" else OBERLIGA_SUED_PAGES
    candidates = _scrape_division_ids(pages)
    logger.info("Gefundene divisionId-Kandidaten für %s: %s", league, sorted(candidates))

    classified: dict[str, int] = {}
    async with HockeydataClient() as client:
        for did in sorted(candidates):
            info = await _classify_division(client, did)
            if not info:
                logger.debug("  div=%d: keine Daten", did)
                continue
            role = _classify_role(info)
            logger.info(
                "  div=%d: %s (%d Teams, %d Matches, KO=%s, type=%s)",
                did, role, info["n_teams"], info["n_matches"], info["has_knockout"], info["round_type"],
            )
            if role != "unknown" and role not in classified:
                classified[role] = did

    cache[league] = classified
    DIVISION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DIVISION_CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True))
    return classified


if __name__ == "__main__":
    import asyncio
    from ..logging_setup import setup_logging
    setup_logging()
    for liga in ["DEL2", "OberligaSüd"]:
        print(f"\n=== {liga} ===")
        print(asyncio.run(find_current_divisions(liga)))
