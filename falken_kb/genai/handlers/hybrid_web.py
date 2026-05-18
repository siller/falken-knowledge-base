"""Hybrid-Web-Handler: Web-Search → DB-Lookup → Synthesis.

Für Multi-Hop-Fragen wie "Wann hat der Besitzer der Tenno Sushi Bar bei
den Falken gespielt?" — Web findet 'Besitzer = X', DB liefert dann
Falken-Stats für X.

Performance-Optimierungen:
- Sub-Lookups via ThreadPoolExecutor parallel (vorher: sequenziell)
- Direkter SQL-Template für Player-Lookup statt LLM-SQL-Generation
- Kein Router-Classify für Sub-Queries (wissen schon dass es fact ist)
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ...db import exec_sql
from ..dgx_client import DGXClient
from ..web_search import tavily_search

logger = logging.getLogger(__name__)


def _direct_player_lookup(name: str) -> dict[str, Any]:
    """Direkter SQL-Lookup ohne LLM — spart 5-15s pro Person.

    Sucht nach Spieler via pg_trgm Fuzzy-Match. Returnt alle Saisons +
    Aggregat-Stats wenn gefunden.
    """
    safe_name = name.replace("'", "''")
    try:
        rows = exec_sql(
            f"SELECT season, player, points, goals, assists, games_played, "
            f"similarity(player, '{safe_name}') AS sim "
            f"FROM falken_skater_stats "
            f"WHERE similarity(player, '{safe_name}') > 0.3 AND points IS NOT NULL "
            f"ORDER BY sim DESC, season DESC LIMIT 10"
        )
        if not rows:
            # Auch goalie-Tabelle probieren
            rows = exec_sql(
                f"SELECT season, goalie AS player, wins, losses, gaa, save_pct, games_played, "
                f"similarity(goalie, '{safe_name}') AS sim "
                f"FROM falken_goalie_stats "
                f"WHERE similarity(goalie, '{safe_name}') > 0.3 "
                f"ORDER BY sim DESC, season DESC LIMIT 10"
            )
        return {"person": name, "rows": rows, "found": bool(rows)}
    except Exception as e:
        logger.warning("Direct-lookup für %s failed: %s", name, str(e)[:120])
        return {"person": name, "rows": [], "found": False, "error": str(e)[:120]}


def answer_web_research(question: str, client: DGXClient | None = None) -> dict[str, Any]:
    c = client or DGXClient()

    # Schritt 1: Web-Search
    web = tavily_search(question, max_results=5)
    if web.get("error") and not web.get("results"):
        # NICHT crashen — leeres Result returnen damit Fallback bei Bedarf
        # noch zu fact gehen kann
        return {
            "category": "web_research",
            "answer": "Web-Recherche aktuell nicht verfügbar — bitte versuche es später nochmal.",
            "error": web["error"],
            "web_results": [],
            "db_findings": [],
            "people_identified": [],
        }

    # Schritt 2: Personen-Identifikation via LLM aus Web-Snippets
    snippets = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\n{r['content']}"
        for i, r in enumerate(web["results"][:5])
    )
    extract_prompt = f"""Aus den folgenden Web-Quellen: identifiziere alle Personen
(Vor- + Nachname, falls erkennbar) die in einer Heilbronner-Falken-Eishockey-
Datenbank nachgeschlagen werden könnten. Auch Spitznamen → Vollnamen ableiten
wenn der Kontext es zulässt (z.B. "Tommy" + "war Falken-Profi" → suche auch
nach "Thomas" Spielern).

Antworte JSON-only:
{{
  "key_facts_from_web": "1-2 Sätze: was Web ergeben hat",
  "people_to_lookup": ["Voller Name 1", "Voller Name 2", ...],
  "needs_db_lookup": true/false
}}

Frage: {question}

Web-Quellen:
{snippets}

Web-Summary: {web.get('answer','')}"""

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
    people = (extract.get("people_to_lookup", []) or [])[:5]  # max 5
    needs_db = extract.get("needs_db_lookup", False)

    # Schritt 3: DB-Lookups PARALLEL via ThreadPool + direkter SQL (kein LLM)
    # Spart pro Person ~15-25s gegenüber sequentiellem fact_sql.
    db_findings: list[dict[str, Any]] = []
    if needs_db and people:
        logger.info("Parallele direct-lookups für %d Personen", len(people))
        with ThreadPoolExecutor(max_workers=min(5, len(people))) as pool:
            results = list(pool.map(_direct_player_lookup, people))
        for r in results:
            if r["found"]:
                # Kompakter Stats-String
                rows = r["rows"][:5]
                summary = "; ".join(
                    f"{row.get('season','?')}: " + (
                        f"{row.get('points','?')}P/{row.get('goals','?')}G/{row.get('assists','?')}A"
                        if 'points' in row else
                        f"{row.get('wins','?')}W/{row.get('losses','?')}L GAA={row.get('gaa','?')}"
                    )
                    for row in rows
                )
                db_findings.append({
                    "person": r["person"],
                    "db_answer": f"Gefunden: {rows[0].get('player', r['person'])}. Saisons: {summary}",
                    "db_rows": rows,
                })
            else:
                db_findings.append({
                    "person": r["person"],
                    "db_answer": "Nicht in Falken-DB",
                    "db_rows": [],
                })

    # Schritt 4: Finale Synthese (single LLM call)
    db_summary = "\n".join(
        f"- {f['person']}: {f['db_answer']}"
        for f in db_findings
    ) or "(keine Personen identifiziert oder keine DB-Treffer)"

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
