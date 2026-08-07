"""Orchestrator: Frage rein → Klassifikation → passenden Handler → Antwort raus."""
from __future__ import annotations

import logging
from typing import Any

import os
from ..config import settings
from .dgx_client import DGXClient
from .handlers.fact_sql import answer_fact
from .handlers.hybrid_web import answer_web_research
from .handlers.narrative_rag import answer_narrative
from .handlers.trend_chart import answer_trend
from .router import classify
from .web_search import suche_aktiv
from .tool_agent import answer_with_tools


def _use_tool_agent() -> bool:
    """Tool-Agent default OFF.

    DGX-Gemma kann ReAct-Loop ohne native tool-use-API nicht stabil. Die simple
    1-step DB-Heuristik (direkt fact_sql) übernimmt _is_clearly_db_only.
    Multi-Hop läuft über das bewährte hybrid_web (war 91.9% Pass-Rate).
    Per Env USE_TOOL_AGENT=true wieder aktivierbar zum Experimentieren.
    """
    return os.environ.get("USE_TOOL_AGENT", "false").lower() in ("true", "1", "yes")


def _is_simple_db_question(question: str) -> bool:
    """Heuristik: klare DB-Frage (Saison/Stats/Spieler) ohne externe Entitäten."""
    q = question.lower()
    external_terms = ("besitzer", "inhaber", "restaurant", "bar ", "sushi", "firma",
                       "bürgermeister", "geschäftsführer", "ceo", "wer ist ",
                       "neueste", "verpflichtet", "transfer", "wer arbeitet")
    if any(t in q for t in external_terms):
        return False
    # Eine Jahreszahl allein reichte früher für den Shortcut — damit landete
    # "Was ist 2026 mit der Insolvenz passiert?" im SQL-Handler, obwohl die
    # Antwort in den News-Artikeln steht. Jetzt braucht es ein Statistik-Wort,
    # und erzählende Fragen sind ausgenommen.
    if _looks_narrative(q):
        return False
    return any(w in q for w in (
        "tabellenplatz", "platz beend", "punkte", "tore", "saison",
        "topscorer", "trainer", "playoff", "spielergebnis", "ergebnis",
        "liga", "del2", "oberliga", "spielten", "spielte",
        "wie viele", "in welcher saison", "siege", "niederlagen",
    ))

logger = logging.getLogger(__name__)


_NARRATIVE_HINTS = (
    "news", "neueste", "aktuelle nachricht", "bekannt", "wer ist ",
    "verpflichtet", "transfer", "saison plan", "fan", "newsletter",
    "kader", "neuverpflichtung", "rolle",
    # Vereinsgeschehen abseits der Statistik — dazu steht alles in den
    # News-Artikeln, nichts in den Spiel-/Stats-Tabellen:
    "insolvenz", "insolvent", "lizenz", "warum", "wieso", "weshalb",
    "passiert", "hintergrund", "zukunft", "vertrag", "verletz",
    "stimmung", "geschäftsstelle", "sponsor", "dauerkarte", "halle",
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


def _aktuelle_frage(text: str) -> str:
    """Bei Folgefragen nur die eigentliche Frage fürs Routing verwenden.

    WHY: Das UI stellt Folgefragen den vorherigen Dialog voran, damit Pronomen
    aufgelöst werden können. Fürs Routing ist dieser Kontext aber Gift — nach
    der Frage nach der "Tenno Sushi Bar" enthielt jede Folgefrage das Wort
    "Sushi" und landete in der Web-Recherche, auch wenn sie reine
    Datenbank-Statistik betraf.
    """
    marker = "FOLGEFRAGE"
    if marker in text:
        rest = text.rsplit(marker, 1)[1]
        # Format: "FOLGEFRAGE (…Hinweis…): <die eigentliche Frage>"
        return rest.split("):", 1)[-1].strip() or text
    return text


def answer(question: str, context: str | None = None) -> dict[str, Any]:
    """Top-Level-Antwortroutine mit Hybrid-Fallback:
    Wenn fact-Handler keine Daten findet UND die Frage narrativ klingt
    (News, "wer ist X", "bekannt über") → automatisch RAG-Fallback.

    `context` (vorheriger Dialog) geht an die Handler, damit Folgefragen
    auflösbar bleiben — die Routing-Entscheidung trifft aber ausschließlich
    die aktuelle Frage.
    """
    client = DGXClient()

    if context:
        routing_frage = question
        question = (
            f"{context}\n\nFOLGEFRAGE (bezieht sich auf den obigen Kontext, "
            f"resolve Pronomen + 'besser/schlechter/auch' anhand des Kontexts): {question}"
        )
    else:
        # Alt-Aufrufer (und die noch laufende Cloud-Version) schicken den
        # Kontext eingebettet — hier wieder herausziehen.
        routing_frage = _aktuelle_frage(question)

    # SHORTCUT 1: simple DB-Frage → direkt fact_sql ohne Router (~30s, schnellster Pfad)
    if _is_simple_db_question(routing_frage):
        logger.info("Heuristik: simple DB-Frage → direkter fact_sql")
        result = answer_fact(question, client)
        result["classification"] = {"category": "fact", "confidence": 1.0, "reason": "direct DB heuristic"}
        return result

    # OPTIONAL: Tool-Agent (experimental, default off)
    if _use_tool_agent():
        logger.info("Routing via Tool-Agent (experimental)")
        result = answer_with_tools(question, client)
        result["classification"] = {"category": "tool_agent", "confidence": 1.0, "reason": "tool-agent mode active"}
        return result

    # ── Standard-Routing: Klassifikator + Keyword-Hints + Hybrid-Fallback ──
    classification = classify(routing_frage, client)
    category = classification["category"]

    # Hybrid-Routing:
    # 1) Wenn Frage klingt nach Web-Research (Lokal/Firma/externe Person):
    #    direkt web_research_handler (wenn Tavily konfiguriert)
    # 2) Sonst: normaler Handler nach category
    # 3) Fallback bei leerem Result: narrative_rag (für News) ODER web_research (für externe Lookup)
    # suche_aktiv() kennt auch den Aus-Zustand, den der Frage-Dienst setzt —
    # sonst liefe die Frage in den Web-Handler und käme mit 'nicht verfügbar'
    # zurück, statt aus Datenbank und News beantwortet zu werden.
    hat_websuche = suche_aktiv()
    is_web_question = _looks_web_research(routing_frage)

    if is_web_question and hat_websuche:
        logger.info("Routing zu web_research (Frage erwähnt externe Entität)")
        result = answer_web_research(question, client)
        category = "web_research"
    elif category == "fact":
        result = answer_fact(question, client)
        if _fact_returned_empty(result):
            # Fallback zu narrative (RAG-Articles), NIE auto zu web_research:
            # web_research ist teuer (Tavily-Call + Multi-LLM) und liefert für
            # rein DB-orientierte Fragen "Wie viele Saisons in DEL2?" nichts
            # sinnvolles. Lieber ehrlich "keine Daten" als Web fehl-triggern.
            #
            # Der RAG-Versuch läuft jetzt immer (ein Embedding + Vektor-Suche,
            # ~1 s) und nicht mehr nur bei narrativ klingenden Fragen: die
            # Stichwortliste traf zu oft daneben, und das Ergebnis wird ohnehin
            # nur übernommen, wenn die Suche Quellen liefert.
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
