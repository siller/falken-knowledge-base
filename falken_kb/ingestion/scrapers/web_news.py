"""News-Harvester über Web-Suche — Ersatz für die toten RSS-Feeds der Lokalpresse.

WHY: `heilbronner-falken.de/feed/` liefert nur die letzten 10 Artikel, und die
RSS-Feeds von stimme.de / hockeyweb.de sind kaputt (kein valides XML mehr, Stand
Juli 2026). Damit fehlten der KB genau die Geschichten, die eine Saison ausmachen —
z.B. die Insolvenz im Januar 2026.

Statt pro Portal einen brüchigen HTML-Scraper zu bauen, suchen wir nach
Falken-Themen (Exa, sonst Tavily — siehe `genai/web_search.py`), holen den
Artikeltext mit und embedden ihn in dieselbe `articles`-Tabelle wie die
RSS-Artikel.

Aufruf:
    python3 -m falken_kb.ingestion.scrapers.web_news              # Standard-Queries
    python3 -m falken_kb.ingestion.scrapers.web_news --query "..." # gezielt
"""
from __future__ import annotations

import argparse
import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from ...config import settings
from ...db import supabase
from ...genai.dgx_client import DGXClient
from ...genai.web_search import web_search
from .wikipedia_loader import chunk_text

logger = logging.getLogger(__name__)

# Themen, die eine Falken-Saison erzählen. Bewusst breit: doppelte Treffer
# werden über die URL erkannt und kosten nur einen Upsert.
DEFAULT_QUERIES = [
    "Heilbronner Falken Insolvenz Spielbetrieb",
    "Heilbronner Falken Lizenz Oberliga",
    "Heilbronner Falken Kader Neuzugänge",
    "Heilbronner Falken Trainer",
    "Heilbronner Falken Saison Playoffs",
    "Heilbronner Falken Spielbericht Oberliga Süd",
]

# Quellen, denen wir vertrauen. Alles andere wird verworfen — zu "Falken"
# liefern Suchmaschinen sonst auch US-Sport (foxsports, yahoo, nhl.com).
ALLOWED_DOMAINS = (
    "heilbronner-falken.de",
    "stimme.de",
    "echo24.de",
    "hockeyweb.de",
    "eishockey-magazin.de",
    "del-2.org",
    "oberliga.de",
    "rosenheim24.de",
    "inbayreuth.de",
    "frankenpost.de",
    "sport1.de",
    "eishockeynews.de",
    "swr.de",
    "merkur.de",
    "euroherz.de",
)

MIN_BODY_CHARS = 200


def _strip_html(text: str) -> str:
    """HTML/Markdown-Rohtext → Fließtext.

    WHY: Die Anbieter liefern Seitentext als Markdown, gespickt mit Navigations-Links
    (`[Politik](https://…)`). Solche URLs zerlegt der Tokenizer in sehr viele
    Tokens — 1.200 Zeichen Link-Suppe sprengen das 512-Token-Limit von
    nomic-embed-text und der Embedding-Call endet in HTTP 500. Also raus damit,
    was der RAG-Qualität ohnehin guttut.
    """
    text = text or ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)      # Bilder
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)   # [Text](url) → Text
    text = re.sub(r"https?://\S+", " ", text)              # nackte URLs
    text = re.sub(r"[*_#>`|]{1,}", " ", text)              # Markdown-Deko
    return re.sub(r"\s+", " ", text).strip()


def _domain(url: str) -> str:
    return (urlparse(url).netloc or "").removeprefix("www.")


def _is_relevant(title: str, body: str) -> bool:
    blob = (title + " " + body[:800]).lower()
    return "falken" in blob or "heilbronner ec" in blob


def suche_artikel(query: str, max_results: int = 8, days: int = 400) -> list[dict[str, Any]]:
    """Artikel-Kandidaten über den konfigurierten Such-Anbieter (Exa, sonst Tavily).

    Der frühere Weg — Tavily mit `topic: "news"` — war messbar die schlechteste
    Variante: von 48 Treffern lagen nur 3 auf einer vertrauenswürdigen Domain
    (Tavily allgemein 22, Exa 40). Deshalb läuft die Suche jetzt über
    `web_search`, das Exa bevorzugt und bei Bedarf auf Tavily zurückfällt.

    `days` bleibt in der Signatur, wird von Exa aber nicht als Filter benutzt —
    die Relevanzsortierung liefert dort ohnehin die passenden Artikel zuerst.
    """
    res = web_search(query, max_results=max_results, max_chars=4000)
    if res.get("error") and not res.get("results"):
        logger.warning("Suche fehlgeschlagen für '%s': %s", query, res["error"])
        return []
    # Auf das Format bringen, das ingest_result erwartet
    return [
        {
            "url": x.get("url", ""),
            "title": x.get("title", ""),
            "raw_content": x.get("content", ""),
            "content": x.get("content", ""),
            "published_date": x.get("published"),
        }
        for x in (res.get("results") or [])
    ]


def ingest_result(res: dict[str, Any], dgx: DGXClient) -> str:
    """Ein Suchtreffer → 0..n Artikel-Chunks in der DB. Returnt Status-Label."""
    url = res.get("url") or ""
    title = _strip_html(res.get("title") or "")
    body = _strip_html(res.get("raw_content") or res.get("content") or "")
    published = res.get("published_date") or None

    domain = _domain(url)
    if not url or not title:
        return "skip_empty"
    if domain not in ALLOWED_DOMAINS:
        return f"skip_domain:{domain}"
    if len(body) < MIN_BODY_CHARS:
        return "skip_short"
    if not _is_relevant(title, body):
        return "skip_offtopic"

    existing = supabase().table("falken_articles").select("url").eq("url", url).execute()
    if existing.data:
        return "exists"

    for i, chunk in enumerate(chunk_text(body, max_chars=1200)):
        chunk_url = url if i == 0 else f"{url}#chunk-{i}"
        emb = dgx.embed_one(chunk)
        supabase().table("falken_articles").upsert({
            "source": domain,
            "url": chunk_url,
            "title": title if i == 0 else f"{title} (Teil {i + 1})",
            "body": chunk,
            "published_at": published,
            "embedding": emb,
        }, on_conflict="url").execute()
    return "loaded"


def harvest(queries: list[str], max_results: int = 8, days: int = 400) -> dict[str, Any]:
    dgx = DGXClient()
    stats: dict[str, int] = {}
    loaded_urls: list[str] = []
    for q in queries:
        results = suche_artikel(q, max_results=max_results, days=days)
        logger.info("'%s' → %d Treffer", q, len(results))
        for res in results:
            try:
                status = ingest_result(res, dgx)
            except Exception as e:
                logger.warning("Ingest failed (%s): %s", (res.get("url") or "")[:80], str(e)[:160])
                status = "error"
            key = status.split(":")[0]
            stats[key] = stats.get(key, 0) + 1
            if status == "loaded":
                loaded_urls.append(res.get("url", ""))
                logger.info("  + %s (%s)", (res.get("title") or "")[:70], _domain(res.get("url", "")))
    return {"stats": stats, "loaded": loaded_urls}


def main() -> None:
    from ...logging_setup import setup_logging

    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", action="append", help="eigene Query (mehrfach möglich)")
    ap.add_argument("--days", type=int, default=400, help="Zeitfenster in Tagen")
    ap.add_argument("--max-results", type=int, default=8)
    args = ap.parse_args()

    out = harvest(args.query or DEFAULT_QUERIES, max_results=args.max_results, days=args.days)
    print("\n=== Web-News-Harvest ===")
    print("Status:", out["stats"])
    print(f"Neu geladen: {len(out['loaded'])}")
    for u in out["loaded"]:
        print("  ", u)


if __name__ == "__main__":
    main()
