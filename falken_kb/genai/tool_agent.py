"""1-Step-Tool-Agent für DGX-Gemma (statt schwerem ReAct-Loop).

Pipeline:
1. LLM klassifiziert Frage + wählt EIN primäres Tool (oder Sequence)
2. Tool(s) werden ausgeführt
3. LLM bekommt alle Results + synthetisiert Antwort

Max 3 Tools pro Frage (z.B. Multi-Hop: web → lookup_player → final).
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from .dgx_client import DGXClient
from .tools import TOOLS

logger = logging.getLogger(__name__)

# Schmaler Plan-Schema: LLM gibt 1-3 sequenzielle Tool-Calls aus
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "tool_calls": {
            "type": "array",
            "description": "1-3 Tool-Calls in Reihenfolge. Spätere können Output von früheren referenzieren via $1.field",
            "items": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "enum": list(TOOLS.keys())},
                    "args": {"type": "object"},
                },
                "required": ["tool", "args"],
            },
        },
    },
    "required": ["reasoning", "tool_calls"],
}

PLAN_PROMPT_TPL = """Du bist HORST, Falken-Eishockey-Assistent. Plane welche Tools die User-Frage beantworten.

TOOLS (alle verfügbar):
- query_falken_db(question): natursprachliche DB-Frage (Saisons, Spiele, Trainer, Spieler-Stats, Playoffs)
- lookup_player(name): direkter Spieler-Lookup per Name (fuzzy, robust)
- search_falken_news(query): RSS-News-Artikel (Trainer-Bekanntgabe, Transfers, Kader)
- search_web(query): Tavily Web-Search (externe Welt: Restaurant-Besitzer, Ex-Profis, lokale Personen)

STRATEGIE:
- Pure DB-Fragen (Saisons, Stats, Spielergebnisse, Playoffs, Trainer einer Saison) → 1× query_falken_db
- "Wer ist <Person>?" → news + ggf. web (parallel)
- Multi-Hop (z.B. "Besitzer von X spielte wann bei Falken") → web ZUERST, dann lookup_player
- News/Transfer/aktuelle Themen → search_falken_news (oder web als Backup)

Output: JSON mit "reasoning" + "tool_calls" (Liste 1-3 Tools).
"""


def _is_clearly_db_only(question: str) -> bool:
    """Heuristik: ist das eine klare DB-Frage (kein Web/News nötig)?

    Triggers: erwähnt Saison-Jahr ODER bekannte Stats-Begriffe.
    NEGATIV-Trigger: erwähnt externe Entitäten (besitzer, restaurant, firma).
    """
    import re
    q = question.lower()
    # Negativ-Filter zuerst: wenn externe Entitäten erwähnt → KEINE pure DB
    external_terms = ("besitzer", "inhaber", "restaurant", "bar ", "sushi", "firma",
                       "bürgermeister", "geschäftsführer", "ceo", "wer ist ",
                       "neueste", "news", "verpflichtet", "transfer")
    if any(t in q for t in external_terms):
        return False
    # Positiv-Trigger
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", q)) or bool(re.search(r"\d{2}/\d{2}", q))
    has_stats_word = any(w in q for w in (
        "tabellenplatz", "platz beend", "punkte", "tore", "saison",
        "topscorer", "trainer", "playoff", "spielergebnis", "ergebnis",
        "liga", "del2", "oberliga", "spielten", "spielte",
        "wie viele", "in welcher saison", "siege", "niederlagen",
    ))
    return has_year or has_stats_word


def answer_with_tools(question: str, client: DGXClient | None = None) -> dict[str, Any]:
    c = client or DGXClient()
    t_start = time.time()

    # SHORTCUT: simple DB-Frage → direkt fact_sql, ohne Plan-Step + Final-Synth
    # Spart ~30-40s pro Frage (~50% der Tool-Agent-Zeit)
    if _is_clearly_db_only(question):
        from .handlers.fact_sql import answer_fact
        logger.info("Heuristik: pure DB-Frage erkannt → direkter fact_sql, skip Plan")
        r = answer_fact(question, c)
        dt = time.time() - t_start
        return {
            "category": "tool_agent",
            "answer": r.get("answer", ""),
            "tool_trace": [{
                "step": 1, "tool": "query_falken_db (direct)",
                "args": {"question": question},
                "result_summary": f"✓ {len(r.get('rows',[]))} rows",
                "reasoning": "Heuristik: klare DB-Frage, kein Plan-Step nötig",
            }],
            "iterations": 1,
            "planner_reasoning": "skip (heuristic shortcut)",
            "sql": r.get("sql"),
            "rows": r.get("rows"),
        }

    # ITERATIVES ReAct max 3 steps. Args werden basierend auf vorherigen
    # Tool-Resultaten generiert (kritisch für Multi-Hop wie Tenno-Beispiel).
    trace: list[dict[str, Any]] = []
    tool_results: list[dict[str, Any]] = []
    reasoning = ""

    STEP_SCHEMA = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string", "description": "Was tust du als nächstes und warum"},
            "next_action": {"type": "string", "enum": ["use_tool", "done"]},
            "tool": {"type": "string", "enum": list(TOOLS.keys()) + [""]},
            "args": {"type": "object"},
        },
        "required": ["reasoning", "next_action"],
    }

    for step in range(3):  # max 3 iterations
        # Baue messages: system + question + bisherige tool-results
        prior_results = ""
        if tool_results:
            prior_results = "\n\nBISHERIGE TOOL-RESULTATE:\n" + "\n\n".join(
                f"[Step {i+1}] {r['tool']}({json.dumps(r['args'], ensure_ascii=False)}):\n"
                f"{json.dumps(r['result'], ensure_ascii=False, default=str)[:1200]}"
                for i, r in enumerate(tool_results)
            )

        step_decision = c.chat_with_schema(
            messages=[
                {"role": "system", "content": PLAN_PROMPT_TPL + "\n\nDu bist in Step " + str(step+1) + " von max 3."},
                {"role": "user", "content": f"FRAGE: {question}{prior_results}\n\nWas tust du jetzt? next_action=use_tool ODER done."},
            ],
            json_schema=STEP_SCHEMA, schema_name="StepDecision",
            max_tokens=400, temperature=0.1,
        )

        action = step_decision.get("next_action", "done")
        reasoning = step_decision.get("reasoning", "")

        if action == "done":
            trace.append({"step": step + 1, "tool": "(done)", "reasoning": reasoning, "result_summary": "→ Synthese"})
            break

        tool_name = step_decision.get("tool", "")
        tool_args = step_decision.get("args", {}) or {}
        entry = {"step": step + 1, "tool": tool_name, "args": tool_args, "reasoning": reasoning}

        if tool_name not in TOOLS:
            entry["error"] = f"Tool '{tool_name}' nicht verfügbar"
            entry["result_summary"] = entry["error"]
            trace.append(entry)
            break

        try:
            result = TOOLS[tool_name]["fn"](**tool_args)
            entry["result"] = result
            entry["result_summary"] = _summarize(result)
            tool_results.append({"tool": tool_name, "args": tool_args, "result": result})
        except TypeError as e:
            entry["error"] = f"Args mismatch: {e}"
            entry["result_summary"] = entry["error"]
        except Exception as e:
            entry["error"] = str(e)[:200]
            entry["result_summary"] = "ERROR: " + str(e)[:80]
        trace.append(entry)

    # Schritt 3: Final-Synthese
    results_str = "\n\n".join(
        f"[Tool {i+1}: {r['tool']}({json.dumps(r['args'], ensure_ascii=False)})]\n"
        f"{json.dumps(r['result'], ensure_ascii=False, default=str)[:1500]}"
        for i, r in enumerate(tool_results)
    ) or "(keine Tool-Resultate)"

    synth = c.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Beantworte die User-Frage in 1-3 Sätzen auf Deutsch, basierend AUSSCHLIESSLICH "
                    "auf den Tool-Resultaten. Übernimm Zahlen, Namen, Datumsangaben wörtlich. "
                    "Erfinde nichts dazu. Wenn die Tools nichts ergeben haben, sage ehrlich 'keine Daten gefunden'. "
                    "Erwähne keine Tool-Namen oder SQL-Details in der Antwort. "
                    "Bei Spielergebnissen: Format 'Heimteam X:Y Auswärtsteam' (Heim-Score zuerst)."
                ),
            },
            {
                "role": "user",
                "content": f"FRAGE: {question}\n\nTOOL-RESULTATE:\n{results_str}",
            },
        ],
        max_tokens=400,
        temperature=0.2,
    )

    dt = time.time() - t_start
    logger.info("Tool-Agent fertig in %.1fs (%d tools)", dt, len(tool_results))

    return {
        "category": "tool_agent",
        "answer": synth.strip(),
        "tool_trace": trace,
        "iterations": len(tool_results),
        "planner_reasoning": reasoning,
    }


def _summarize(r: dict[str, Any]) -> str:
    err = r.get("error")
    if err:
        return f"ERROR: {str(err)[:80]}"
    if "found" in r and not r["found"]:
        return "✗ nichts gefunden"
    if "row_count" in r:
        return f"✓ {r['row_count']} rows; answer={(r.get('answer','') or '')[:60]}"
    if "seasons" in r:
        return f"✓ {len(r.get('seasons',[]))} Saisons; player={r.get('player_name','?')}"
    if "snippets" in r:
        return f"✓ {len(r.get('snippets',[]))} Web-Snippets"
    if "source_count" in r:
        return f"✓ {r.get('source_count',0)} News-Articles"
    return "✓ ok"
