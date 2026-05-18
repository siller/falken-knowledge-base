"""Smoke-Test für DGX-Client: Chat, Structured-Output, Embeddings.

Aufruf: `python3 -m falken_kb.genai.smoke_test`
"""
from __future__ import annotations

import logging

from ..logging_setup import setup_logging
from .dgx_client import DGXClient

logger = logging.getLogger(__name__)


def run() -> None:
    setup_logging()
    c = DGXClient()
    logger.info("Chat-Model: %s | Embed-Model: %s (%d dim)", c.chat_model, c.embed_model, c.embed_dim)

    # ---- 1. Plain chat ----
    answer = c.chat(
        messages=[
            {"role": "system", "content": "Antworte knapp auf Deutsch."},
            {"role": "user", "content": "Was ist die Heimspielstätte der Heilbronner Falken?"},
        ],
        max_tokens=80,
    )
    logger.info("Chat: %s", answer.strip())

    # ---- 2. Structured output (Frage-Klassifikation) ----
    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["fact", "narrative", "trend"]},
            "reason": {"type": "string"},
        },
        "required": ["category", "reason"],
        "additionalProperties": False,
    }
    classification = c.chat_with_schema(
        messages=[
            {
                "role": "system",
                "content": (
                    "Klassifiziere die Frage in eine der Kategorien:\n"
                    "- fact: nach einem konkreten Wert/Fakt suchend (Topscorer, Ergebnis, Datum)\n"
                    "- narrative: nach Hintergrund/Geschichte/Verlauf fragend\n"
                    "- trend: nach Entwicklung über Zeit, Vergleich, Aggregat fragend"
                ),
            },
            {"role": "user", "content": "Wer war Topscorer der Falken in 2018/19?"},
        ],
        json_schema=schema,
        schema_name="QuestionClassification",
    )
    logger.info("Structured: %s", classification)

    # ---- 3. Embeddings ----
    embs = c.embed(["Heilbronner Falken Eishockey", "Mannheim Adler"])
    logger.info("Embeddings: 2 vectors, dim=%d (1st sample: %s)", len(embs[0]), embs[0][:3])


if __name__ == "__main__":
    run()
