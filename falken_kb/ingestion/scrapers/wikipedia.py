"""Wikipedia-Scraper für Falken-Saison-Kontext.

Nutzt die offizielle MediaWiki Action API — kein HTML-Scraping, kein VPN,
keine ToS-Probleme. Wikipedia ist ein verlässlicher Cross-Reference für
Trainer-Wechsel, Verletzungen, Notable-Transfers etc.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from ._base import Scraper, cache_get, cache_put

logger = logging.getLogger(__name__)


# Wikipedia-Saison-Artikel folgen einem festen Schema:
# https://de.wikipedia.org/wiki/Heilbronner_Falken/Saison_2022/23
# https://de.wikipedia.org/wiki/DEL2_2022/23
BASE_URL = "https://de.wikipedia.org/w/api.php"


class WikipediaScraper(Scraper):
    source = "wikipedia"
    rate_limit_sec = 0.5  # Wikipedia ist tolerant, aber höflich bleiben
    rate_jitter_sec = 0.2

    async def get_page(self, title: str) -> dict[str, Any]:
        """Holt einen Wikipedia-Artikel als Wikitext + Plaintext.

        Beispiel-Titel:
          - "Heilbronner Falken"
          - "DEL2 2022/23"
          - "Saison 2018/19 der DEL2"
        """
        cached_key = f"{BASE_URL}?title={title}"
        cached = cache_get(self.source, cached_key)
        if cached:
            import json
            return json.loads(cached)

        await self._wait()
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts|info",
            "explaintext": "1",  # Plain text statt HTML
            "exsectionformat": "plain",
            "redirects": "1",
        }
        resp = await self._client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        first_page = next(iter(pages.values())) if pages else {}
        result = {
            "title": first_page.get("title"),
            "pageid": first_page.get("pageid"),
            "extract": first_page.get("extract", ""),
            "missing": "missing" in first_page,
        }
        import json
        cache_put(self.source, cached_key, json.dumps(result))
        logger.info("Wikipedia: %s (%d chars, missing=%s)",
                    result["title"], len(result["extract"]), result["missing"])
        return result

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Sucht nach Wikipedia-Artikeln zu einem Begriff."""
        await self._wait()
        resp = await self._client.get(BASE_URL, params={
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
        })
        resp.raise_for_status()
        return resp.json().get("query", {}).get("search", [])


# Bekannte Falken-Saison-Wikipedia-Titel-Patterns
FALKEN_SEASON_TITLES = [
    # Direkter Falken-Saison-Artikel (selten gepflegt)
    "Heilbronner Falken/Saison {label_short}",
    # DEL2-Saison-Artikel (für Liga-Kontext)
    "DEL2 {label_short}",
    "Saison {label_short} der DEL2",
    "DEL2-Saison {label_short}",
    # Oberliga
    "Oberliga (Eishockey) {label_short}",
]


def label_variants(label: str) -> list[str]:
    """Generiert URL-kompatible Saison-Label-Varianten.

    Input: "2022/23"
    Output: ["2022/23", "2022-23", "2022%2F23", ...]
    """
    out = [label]
    # 2022/23 → 2022_23, 2022-23
    out.append(label.replace("/", "_"))
    out.append(label.replace("/", "-"))
    # 2022/23 → 2022/2023 (volle Jahreszahl)
    m = re.match(r"(\d{4})/(\d{2})$", label)
    if m:
        full_2nd = str(int(m.group(1)) // 100) + m.group(2)  # 2022/2023
        out.append(f"{m.group(1)}/{full_2nd}")
    return out


async def fetch_season_context(season_label: str) -> dict[str, str]:
    """Aggregiert Saison-Kontext aus mehreren Wikipedia-Quellen.

    Returns dict mit jedem erfolgreich geholten Artikel.
    """
    results: dict[str, str] = {}
    async with WikipediaScraper() as w:
        for label in label_variants(season_label):
            for pattern in FALKEN_SEASON_TITLES:
                title = pattern.format(label_short=label)
                try:
                    page = await w.get_page(title)
                    if not page["missing"] and page["extract"]:
                        results[title] = page["extract"]
                except httpx.HTTPError as e:
                    logger.debug("Wikipedia miss for '%s': %s", title, e)
                    continue
    return results


if __name__ == "__main__":
    import asyncio
    from ...logging_setup import setup_logging
    setup_logging()
    res = asyncio.run(fetch_season_context("2022/23"))
    print(f"\nGefundene Artikel: {len(res)}")
    for title, body in res.items():
        print(f"\n=== {title} ({len(body)} chars) ===")
        print(body[:600])
        print("…")
