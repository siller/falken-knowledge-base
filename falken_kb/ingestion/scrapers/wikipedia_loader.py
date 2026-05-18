"""Lädt Wikipedia-Saison-Artikel als Articles in die DB inkl. Embedding."""
from __future__ import annotations

import logging
from typing import Any

from ...db import supabase
from ...genai.dgx_client import DGXClient
from .wikipedia import fetch_season_context

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    """Teile lange Artikel in Sub-Chunks für besseren RAG-Recall."""
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) > max_chars:
            if current.strip():
                chunks.append(current.strip())
            current = paragraph
        else:
            current = (current + "\n\n" + paragraph) if current else paragraph
    if current.strip():
        chunks.append(current.strip())
    return chunks


async def load_wikipedia_season(season_label: str, dgx: DGXClient | None = None) -> dict[str, Any]:
    dgx = dgx or DGXClient()
    articles_loaded = 0
    chunks_total = 0

    pages = await fetch_season_context(season_label)
    if not pages:
        logger.info("Wikipedia: keine Artikel für %s", season_label)
        return {"season": season_label, "articles": 0, "chunks": 0}

    for title, body in pages.items():
        # chunken + embedden + insert
        chunks = chunk_text(body, max_chars=1500)
        for i, chunk in enumerate(chunks):
            url = f"https://de.wikipedia.org/wiki/{title.replace(' ', '_')}#chunk-{i}"
            emb = dgx.embed_one(chunk)
            try:
                supabase().table("falken_articles").upsert({
                    "source": "wikipedia",
                    "url": url,
                    "title": title,
                    "body": chunk,
                    "embedding": emb,
                }, on_conflict="url").execute()
                chunks_total += 1
            except Exception as e:
                logger.warning("Article insert failed (%s, chunk %d): %s", title, i, e)
        articles_loaded += 1

    logger.info("Wikipedia: %d Artikel, %d Chunks für %s geladen", articles_loaded, chunks_total, season_label)
    return {"season": season_label, "articles": articles_loaded, "chunks": chunks_total}


async def backfill_wikipedia_all(seasons: list[str]) -> dict[str, dict[str, Any]]:
    dgx = DGXClient()
    results: dict[str, dict[str, Any]] = {}
    for s in seasons:
        try:
            results[s] = await load_wikipedia_season(s, dgx)
        except Exception as e:
            logger.error("Wikipedia-Backfill failed für %s: %s", s, e)
            results[s] = {"error": str(e)}
    return results


if __name__ == "__main__":
    import asyncio
    from ...logging_setup import setup_logging
    setup_logging()
    seasons = [
        "2015/16", "2016/17", "2017/18", "2018/19", "2019/20",
        "2020/21", "2021/22", "2022/23", "2023/24", "2024/25",
    ]
    results = asyncio.run(backfill_wikipedia_all(seasons))
    print("\n=== Wikipedia-Backfill Zusammenfassung ===")
    for s, r in results.items():
        print(f"  {s}: {r}")
