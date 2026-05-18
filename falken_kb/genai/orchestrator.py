"""Orchestrator: Frage rein → Klassifikation → passenden Handler → Antwort raus."""
from __future__ import annotations

import logging
from typing import Any

from ..config import settings
from .dgx_client import DGXClient
from .handlers.fact_sql import answer_fact
from .handlers.hybrid_web import answer_web_research
from .handlers.narrative_rag import answer_narrative
from .handlers.trend_chart import answer_trend
from .router import classify

logger = logging.getLogger(__name__)


_NARRATIVE_HINTS = (
    "news", "neueste", "aktuelle nachricht", "bekannt", "wer ist ",
    "verpflichtet", "transfer", "saison plan", "fan", "newsletter",
    "kader", "neuverpflichtung", "rolle",
)

# Indikatoren für Multi-Hop-Fragen die externe Web-Recherche brauchen:
# Lokalität (Restaurant/Bar in Heilbronn etc.), Beruf, "wer besitzt/leitet X",
# politische/öffentliche Personen die in Falken-DB nicht stehen.
_WEB_RESEARCH_HINTS = (
    "besitzer", "inhaber", "geschäftsführer", "ceo", "vorstand",
    "restaurant", "bar ", "sushi", "pizzeria", "café", "kneipe",
    "firma", "unternehmen", "betreibt", "leitet die",
    "bürgermeister", "ob ", "oberbürgermeister",
    "wer arbeitet ", "wer leitet ", "wo arbeitet ",
)


def _looks_narrative(question: str) -> bool:
    q = question.lower()
    return any(h in q for h in _NARRATIVE_HINTS)


def _looks_web_research(question: str) -> bool:
    """Frage erwähnt eine externe Entität, die nicht in der Falken-DB sein kann
    (Lokal, Firma, Person außerhalb der Eishockey-Welt) — Web-Search braucht."""
    q = question.lower()
    return any(h in q for h in _WEB_RESEARCH_HINTS)


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

    # Hybrid-Routing:
    # 1) Wenn Frage klingt nach Web-Research (Lokal/Firma/externe Person):
    #    direkt web_research_handler (wenn Tavily konfiguriert)
    # 2) Sonst: normaler Handler nach category
    # 3) Fallback bei leerem Result: narrative_rag (für News) ODER web_research (für externe Lookup)
    has_tavily = bool(settings.tavily_api_key)
    is_web_question = _looks_web_research(question)

    if is_web_question and has_tavily:
        logger.info("Routing zu web_research (Frage erwähnt externe Entität)")
        result = answer_web_research(question, client)
        category = "web_research"
    elif category == "fact":
        result = answer_fact(question, client)
        if _fact_returned_empty(result):
            # Fallback NUR zu narrative (RAG-Articles), NIE auto zu web_research:
            # web_research ist teuer (Tavily-Call + Multi-LLM) und liefert für
            # rein DB-orientierte Fragen "Wie viele Saisons in DEL2?" nichts
            # sinnvolles. Lieber ehrlich "keine Daten" als Web fehl-triggern.
            if _looks_narrative(question):
                logger.info("Hybrid-Fallback: fact leer, retry mit narrative_rag")
                narrative_result = answer_narrative(question, client)
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
