"""Routing-Layer: klassifiziert eine User-Frage in fact/narrative/trend."""
from __future__ import annotations

import logging
from typing import Literal

from .dgx_client import DGXClient

logger = logging.getLogger(__name__)

QuestionCategory = Literal["fact", "narrative", "trend"]


CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["fact", "narrative", "trend"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
    "required": ["category", "confidence", "reason"],
    "additionalProperties": False,
}

CLASSIFICATION_PROMPT = """Klassifiziere die Frage zu Heilbronner-Falken-Eishockeydaten in EINE Kategorie:

- "fact" — fragt nach EINEM konkreten Datenpunkt oder einer kurzen Liste, OHNE Visualisierung.
  Beispiele: Topscorer einer Saison, Ergebnis eines Spiels, Tabellenplatz, Trainer,
  Geburtsdatum, "wer hat am meisten X" über mehrere Saisons (Single-Aggregat-Antwort),
  "wann zuletzt", "wie viele Saisons in Liga X", "Playoff-Sieger einer Serie".
  Antwort = Zahl/Name/kurzer Satz.

- "trend" — fragt explizit nach DIAGRAMM, GRAFIK oder ZEITREIHE über mehrere Saisons.
  Beispiele: "zeige Entwicklung X als Chart", "Punkte-Verlauf über die Jahre",
  "Zuschauerschnitt im Vergleich pro Saison als Diagramm".
  IM ZWEIFEL: lieber fact wählen wenn das Wort "Chart", "Diagramm", "Grafik",
  "Visualisierung" oder "Verlauf zeigen" NICHT vorkommt.

- "narrative" — fragt nach Hintergrund, Geschichte, "warum/wie verlief".
  Beispiele: "warum sind sie abgestiegen", "wie verlief Saison X",
  "was war besonders an Spielzeit Y", "wer war der prägende Trainer".
  Antwort = mehrere kontextuelle Sätze.

WICHTIG: "Wer war der beste Topscorer in den letzten 10 Jahren?" = **fact**
(eine konkrete Antwort, kein Chart). Auch "in welcher Saison" + Aggregat = fact.

Antworte NUR mit JSON gemäß Schema, keine zusätzlichen Erklärungen."""


def classify(question: str, client: DGXClient | None = None) -> dict:
    c = client or DGXClient()
    result = c.chat_with_schema(
        messages=[
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {"role": "user", "content": question},
        ],
        json_schema=CLASSIFICATION_SCHEMA,
        schema_name="QuestionClassification",
        max_tokens=200,
        temperature=0.1,
    )
    category = result.get("category")
    if category not in ("fact", "narrative", "trend"):
        # Fallback: bei kaputtem LLM-Output ist "fact" die häufigste richtige Wahl
        # für unsere Falken-Fragen (Tabellenplätze, Spielergebnisse, Trainer etc.)
        logger.warning("Klassifikation fehlgeschlagen für %r (got=%r), fallback=fact", question[:80], result)
        return {"category": "fact", "confidence": 0.0, "reason": "fallback after classifier failure"}
    confidence = result.get("confidence", 0.0)
    logger.info("Frage klassifiziert: %s → %s (%.0f%%)", question[:60], category, confidence * 100)
    return {"category": category, "confidence": confidence, "reason": result.get("reason", "")}
