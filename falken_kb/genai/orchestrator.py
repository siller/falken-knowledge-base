"""Orchestrator: Frage rein → Klassifikation → passenden Handler → Antwort raus."""
from __future__ import annotations

import logging
from typing import Any

from .dgx_client import DGXClient
from .handlers.fact_sql import answer_fact
from .handlers.narrative_rag import answer_narrative
from .handlers.trend_chart import answer_trend
from .router import classify

logger = logging.getLogger(__name__)


_NARRATIVE_HINTS = (
    "news", "neueste", "aktuelle nachricht", "bekannt", "wer ist ",
    "verpflichtet", "transfer", "saison plan", "fan", "newsletter",
    "kader", "neuverpflichtung", "rolle",
)


def _looks_narrative(question: str) -> bool:
    """Heuristik: hat die Frage typische narrative-Trigger?"""
    q = question.lower()
    return any(h in q for h in _NARRATIVE_HINTS)


def _fact_returned_empty(result: dict[str, Any]) -> bool:
    """Sagt der fact-Handler 'keine Daten' oder hat SQL-Fehler?"""
    ans = (result.get("answer", "") or "").lower()
    rows = result.get("rows", []) or []
    err = result.get("error")
    if err:
        return True
    if not rows:
        return True
    no_data_phrases = ("keine daten", "keine informationen", "liegen keine", "enthalten keine")
    return any(p in ans for p in no_data_phrases)


def answer(question: str) -> dict[str, Any]:
    """Top-Level-Antwortroutine mit Hybrid-Fallback:
    Wenn fact-Handler keine Daten findet UND die Frage narrativ klingt
    (News, "wer ist X", "bekannt über") → automatisch RAG-Fallback.
    """
    client = DGXClient()
    classification = classify(question, client)
    category = classification["category"]

    if category == "fact":
        result = answer_fact(question, client)
        # Hybrid-Fallback: fact lieferte nichts UND Frage klingt narrativ → RAG retry
        if _fact_returned_empty(result) and _looks_narrative(question):
            logger.info("Hybrid-Fallback: fact lieferte nichts, retry mit narrative_rag")
            narrative_result = answer_narrative(question, client)
            # nur überschreiben wenn RAG echte Sources findet
            if narrative_result.get("sources"):
                narrative_result["fact_attempt"] = {"sql": result.get("sql"), "rows_count": len(result.get("rows", []))}
                result = narrative_result
                category = "narrative"
    elif category == "narrative":
        result = answer_narrative(question, client)
    elif category == "trend":
        result = answer_trend(question, client)
    else:
        result = {"category": "unknown", "answer": "Frage konnte nicht klassifiziert werden."}

    result["classification"] = classification
    return result
