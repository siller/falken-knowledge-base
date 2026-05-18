"""Narrative-Handler: Frage → pgvector Top-K Artikel → Antwort."""
from __future__ import annotations

import logging
from typing import Any

from ...db import vector_search
from ..dgx_client import DGXClient

logger = logging.getLogger(__name__)


def answer_narrative(question: str, client: DGXClient | None = None, top_k: int = 6) -> dict[str, Any]:
    c = client or DGXClient()
    q_emb = c.embed_one(question)

    rows = vector_search(q_emb, top_k=top_k)

    if not rows:
        return {
            "category": "narrative",
            "sources": [],
            "answer": "Noch keine passenden Artikel in der Wissensdatenbank gefunden.",
        }

    context = "\n\n".join(
        f"[{i+1}] {r['title']} ({r['source']}, {r.get('published_at','?')}):\n{r['excerpt']}"
        for i, r in enumerate(rows)
    )

    synth = c.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Du bist ein Eishockey-Wissensbasis-Assistent für die Heilbronner Falken. "
                    "Beantworte die Frage auf Deutsch in 3-6 Sätzen. Nutze NUR die unten zitierten Quellen. "
                    "Wenn die Quellen die Frage nicht abdecken, sage das ehrlich. "
                    "Erwähne in Klammern die Quellen-Nummern, z.B. [1], [3]."
                ),
            },
            {"role": "user", "content": f"Frage: {question}\n\nQuellen:\n{context}"},
        ],
        max_tokens=500,
        temperature=0.4,
    )

    return {
        "category": "narrative",
        "sources": [{"title": r["title"], "source": r["source"], "date": str(r.get("published_at",""))} for r in rows],
        "answer": synth.strip(),
    }
