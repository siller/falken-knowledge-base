"""Hybrid-Web-Handler: Web-Search → DB-Lookup → Synthesis.

Für Multi-Hop-Fragen wie "Wann hat der Besitzer der Tenno Sushi Bar bei
den Falken gespielt?" — Web findet 'Besitzer = X', DB liefert dann
Falken-Stats für X.
"""
from __future__ import annotations

import logging
from typing import Any

from ..dgx_client import DGXClient
from ..web_search import tavily_search
from .fact_sql import answer_fact

logger = logging.getLogger(__name__)


def answer_web_research(question: str, client: DGXClient | None = None) -> dict[str, Any]:
    c = client or DGXClient()

    # Schritt 1: Web-Search
    web = tavily_search(question, max_results=5)
    if web.get("error") and not web.get("results"):
        return {
            "category": "web_research",
            "answer": f"Web-Search nicht verfügbar: {web['error']}",
            "error": web["error"],
            "web_results": [],
        }

    # Schritt 2: LLM extrahiert die "key facts" + identifiziert ggf. Personen die
    # in der Falken-DB nachgeschlagen werden sollten.
    snippets = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\n{r['content']}"
        for i, r in enumerate(web["results"][:5])
    )
    extract_prompt = f"""Aus den folgenden Web-Quellen: identifiziere alle Personen oder Konzepte,
die in einer Heilbronner-Falken-Eishockey-Datenbank nachgeschlagen werden könnten.
Antworte mit JSON:
{{
  "key_facts_from_web": "kurze Faktensammlung aus dem Web",
  "people_to_lookup": ["Name1", "Name2"],
  "needs_db_lookup": true/false
}}

Frage: {question}

Web-Quellen:
{snippets}

Web-Summary (falls vorhanden): {web.get('answer','')}"""

    extract = c.chat_with_schema(
        messages=[{"role": "user", "content": extract_prompt}],
        json_schema={
            "type": "object",
            "properties": {
                "key_facts_from_web": {"type": "string"},
                "people_to_lookup": {"type": "array", "items": {"type": "string"}},
                "needs_db_lookup": {"type": "boolean"},
            },
            "required": ["key_facts_from_web", "people_to_lookup", "needs_db_lookup"],
        },
        schema_name="WebExtract",
        max_tokens=500,
        temperature=0.1,
    )

    web_facts = extract.get("key_facts_from_web", "")
    people = extract.get("people_to_lookup", []) or []
    needs_db = extract.get("needs_db_lookup", False)

    # Schritt 3: DB-Lookups (über fact-Handler für jede Person)
    db_findings: list[dict[str, Any]] = []
    if needs_db and people:
        for person in people[:3]:  # max 3 lookups
            sub_question = f"Hat {person} jemals bei den Heilbronner Falken gespielt? Wenn ja, wann und mit welchen Stats?"
            try:
                db_result = answer_fact(sub_question, c)
                db_findings.append({
                    "person": person,
                    "sub_question": sub_question,
                    "db_answer": db_result.get("answer", ""),
                    "db_rows": db_result.get("rows", []),
                })
            except Exception as e:
                logger.warning("DB-Lookup für %s fehlgeschlagen: %s", person, e)

    # Schritt 4: Finale Synthese
    db_summary = "\n\n".join(
        f"DB-Lookup '{f['person']}': {f['db_answer']}"
        for f in db_findings
    ) or "(keine DB-Treffer für die im Web identifizierten Personen)"

    synth = c.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Du beantwortest die Frage in 2-4 Sätzen auf Deutsch, indem du "
                    "Web-Recherche-Ergebnisse UND DB-Lookups kombinierst. "
                    "Übernimm Fakten WORTWÖRTLICH aus den Quellen, erfinde nichts. "
                    "Wenn beides nichts klar ergibt, sage das ehrlich. "
                    "Erwähne in Klammern Web-Quellen [1], [2] etc."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Frage: {question}\n\n"
                    f"WEB-FAKTEN:\n{web_facts}\n\n"
                    f"WEB-SNIPPETS:\n{snippets}\n\n"
                    f"DB-BEFUNDE:\n{db_summary}"
                ),
            },
        ],
        max_tokens=400,
        temperature=0.3,
    )

    return {
        "category": "web_research",
        "answer": synth.strip(),
        "web_results": web["results"],
        "web_answer_summary": web.get("answer", ""),
        "people_identified": people,
        "db_findings": db_findings,
    }
