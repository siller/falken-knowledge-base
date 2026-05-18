"""RSS-Loader für heilbronner-falken.de + stimme.de Newsfeeds.

Holt aktuelle Falken-News, extrahiert Title + Body + pubDate, chunked + embeddet
und upserted in falken_articles. Idempotent über URL-Conflict.

Aufruf: python3 -m falken_kb.ingestion.scrapers.falken_news
"""
from __future__ import annotations

import logging
import re
from html import unescape
from typing import Any

import feedparser

from ...db import supabase
from ...genai.dgx_client import DGXClient
from .wikipedia_loader import chunk_text

logger = logging.getLogger(__name__)


FEEDS = [
    ("heilbronner-falken", "https://www.heilbronner-falken.de/feed/"),
    # stimme.de: spezifischer Falken-Tag-Feed
    ("stimme", "https://www.stimme.de/sport/heilbronner-falken/feed/"),
]


def _strip_html(html: str) -> str:
    """Entferne HTML-Tags + Entities, normalisiere Whitespace."""
    no_tags = re.sub(r"<[^>]+>", " ", html or "")
    text = unescape(no_tags)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_falken_relevant(title: str, body: str) -> bool:
    """Quick-Filter für stimme.de o.ä. (heilbronner-falken.de ist immer relevant)."""
    keywords = ("falken", "heilbronner ec", "hec ", "del2", "oberliga süd")
    blob = (title + " " + body[:500]).lower()
    return any(k in blob for k in keywords)


def load_feed(source_label: str, url: str, dgx: DGXClient, max_items: int = 50) -> dict[str, Any]:
    """Hole einen RSS-Feed, parse alle Items, upsert + embedde."""
    logger.info("RSS holen: %s (%s)", source_label, url)
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        logger.warning("Feed-Parse failed: %s — %s", url, feed.bozo_exception)
        return {"source": source_label, "items_total": 0, "loaded": 0, "skipped": 0, "errors": 0}

    items_total = len(feed.entries)
    loaded = skipped = errors = 0

    for entry in feed.entries[:max_items]:
        url_e = entry.get("link") or entry.get("id")
        title = _strip_html(entry.get("title", ""))
        body_html = entry.get("content", [{}])[0].get("value") if entry.get("content") else entry.get("summary", "")
        body = _strip_html(body_html)
        published = entry.get("published") or entry.get("updated") or None

        if not url_e or not title or len(body) < 80:
            skipped += 1
            continue
        if source_label == "stimme" and not _is_falken_relevant(title, body):
            skipped += 1
            continue

        # Body kann lang sein → chunken (gleicher Pattern wie wikipedia)
        chunks = chunk_text(body, max_chars=1500)
        for i, chunk in enumerate(chunks):
            chunk_url = url_e if i == 0 else f"{url_e}#chunk-{i}"
            try:
                emb = dgx.embed_one(chunk)
                supabase().table("falken_articles").upsert({
                    "source": source_label,
                    "url": chunk_url,
                    "title": title if i == 0 else f"{title} (Teil {i+1})",
                    "body": chunk,
                    "published_at": published,
                    "embedding": emb,
                }, on_conflict="url").execute()
            except Exception as e:
                logger.warning("Insert failed (%s, chunk %d): %s", title[:60], i, str(e)[:160])
                errors += 1
        loaded += 1

    logger.info("  %s: %d items, %d loaded, %d skipped, %d errors", source_label, items_total, loaded, skipped, errors)
    return {"source": source_label, "items_total": items_total, "loaded": loaded, "skipped": skipped, "errors": errors}


def backfill_all() -> dict[str, dict[str, Any]]:
    dgx = DGXClient()
    out: dict[str, dict[str, Any]] = {}
    for label, url in FEEDS:
        try:
            out[label] = load_feed(label, url, dgx)
        except Exception as e:
            logger.error("Feed-Load failed (%s): %s", label, e)
            out[label] = {"source": label, "error": str(e)}
    return out


if __name__ == "__main__":
    import json
    from ...logging_setup import setup_logging
    setup_logging()
    results = backfill_all()
    print("\n=== RSS-Backfill Zusammenfassung ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))
