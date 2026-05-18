"""Tavily Web-Search-Wrapper. Returnt LLM-freundliches Format."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


def tavily_search(
    query: str,
    max_results: int = 5,
    include_answer: bool = True,
    search_depth: str = "basic",
) -> dict[str, Any]:
    """Web-Search via Tavily.

    Returnt dict mit:
      - 'answer' (kurze AI-Summary, kann leer sein)
      - 'results' [{'title','url','content'}, ...]
      - 'error' (nur wenn fehlgeschlagen)
    """
    api_key = settings.tavily_api_key
    if not api_key:
        return {"error": "TAVILY_API_KEY nicht gesetzt", "results": [], "answer": ""}

    try:
        with httpx.Client(timeout=20) as c:
            r = c.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": include_answer,
                    "max_results": max_results,
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        logger.warning("Tavily-Fehler: %s", str(e)[:200])
        return {"error": str(e)[:200], "results": [], "answer": ""}

    return {
        "answer": data.get("answer") or "",
        "results": [
            {
                "title": x.get("title", ""),
                "url": x.get("url", ""),
                "content": x.get("content", "")[:500],
            }
            for x in (data.get("results") or [])
        ],
        "error": None,
    }
