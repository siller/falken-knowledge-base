"""ReAct-Style Tool-Use-Agent für DGX-Gemma (via JSON-Mode statt nativem tool-use).

Loop: LLM denkt → schlägt Tool vor → wir führen aus → LLM bekommt Resultat → bis 'final'.
Max 5 Iterationen Safety.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .dgx_client import DGXClient
from .tools import TOOLS, get_tools_description

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string", "description": "Kurze Begründung was du als nächstes tust"},
        "action": {"type": "string", "enum": ["use_tool", "final"], "description": "use_tool wenn du noch mehr Info brauchst, final wenn du antworten kannst"},
        "tool_name": {"type": "string", "description": "Name des Tools (nur wenn action=use_tool)"},
        "tool_args": {"type": "object", "description": "Argumente für das Tool (nur wenn action=use_tool)"},
        "final_answer": {"type": "string", "description": "Finale Antwort an User (nur wenn action=final)"},
    },
    "required": ["thought", "action"],
}


def answer_with_tools(question: str, client: DGXClient | None = None) -> dict[str, Any]:
    """ReAct-Loop: LLM nutzt Tools bis Antwort fertig."""
    c = client or DGXClient()

    system_prompt = f"""Du bist HORST, der Assistent für die Heilbronner Falken (Eishockey).
Beantworte die Frage indem du Tools nutzt. Du kannst MEHRERE Tools nacheinander aufrufen.

VERFÜGBARE TOOLS:
{get_tools_description()}

STRATEGIE:
- DB-Fragen (Stats, Saisons, Trainer, Spielergebnisse, Playoffs) → IMMER zuerst query_falken_db
- Wenn DB nichts findet UND Frage über News/Kader/Trainer-Bekanntgabe → search_falken_news
- Wenn Frage externe Info braucht (Person außerhalb DB, Restaurant-Besitzer, Welt-Event) → search_web
- Bei konkretem Namen → lookup_player (fuzzy match)
- Multi-Hop: chain Tools (z.B. search_web findet Namen → lookup_player für Stats)

WICHTIG:
- Erfinde keine Fakten — nutze NUR Tool-Resultate als Quelle
- Wenn Tools nichts ergeben: ehrlich sagen "keine Daten"
- Halte action="final" + final_answer kurz (2-4 Sätze)

JSON-Format:
{{"thought": "...", "action": "use_tool", "tool_name": "...", "tool_args": {{...}}}}
ODER
{{"thought": "...", "action": "final", "final_answer": "..."}}
"""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    trace: list[dict[str, Any]] = []

    for iteration in range(MAX_ITERATIONS):
        # LLM-Entscheidung holen
        decision = c.chat_with_schema(
            messages=messages,
            json_schema=ACTION_SCHEMA,
            schema_name="ToolDecision",
            max_tokens=600,
            temperature=0.1,
        )

        thought = decision.get("thought", "")
        action = decision.get("action", "final")
        trace_entry: dict[str, Any] = {"iteration": iteration + 1, "thought": thought, "action": action}

        if action == "final" or iteration == MAX_ITERATIONS - 1:
            final = decision.get("final_answer") or "(LLM gab keine finale Antwort)"
            trace_entry["final_answer"] = final[:200]
            trace.append(trace_entry)
            return {
                "category": "tool_agent",
                "answer": final.strip(),
                "tool_trace": trace,
                "iterations": iteration + 1,
            }

        # Tool ausführen
        tool_name = decision.get("tool_name", "")
        tool_args = decision.get("tool_args", {}) or {}
        trace_entry["tool_name"] = tool_name
        trace_entry["tool_args"] = tool_args

        if tool_name not in TOOLS:
            tool_result = {"error": f"Tool '{tool_name}' existiert nicht. Verfügbar: {list(TOOLS.keys())}"}
        else:
            try:
                tool_result = TOOLS[tool_name]["fn"](**tool_args)
            except TypeError as e:
                tool_result = {"error": f"Falsche Args für {tool_name}: {e}"}
            except Exception as e:
                tool_result = {"error": f"Tool-Fehler: {str(e)[:200]}"}

        trace_entry["tool_result_summary"] = _summarize_result(tool_result)
        trace.append(trace_entry)

        # Tool-Resultat an LLM zurückgeben für nächste Iteration
        messages.append({
            "role": "assistant",
            "content": json.dumps({"thought": thought, "action": "use_tool", "tool_name": tool_name, "tool_args": tool_args}, ensure_ascii=False),
        })
        messages.append({
            "role": "user",
            "content": f"TOOL-RESULTAT für {tool_name}:\n{json.dumps(tool_result, ensure_ascii=False, default=str)[:2000]}\n\nWas tust du als nächstes? Antworte JSON.",
        })

    # Sollte nicht erreicht werden (break in loop)
    return {
        "category": "tool_agent",
        "answer": "Maximale Tool-Iterationen erreicht ohne finale Antwort.",
        "tool_trace": trace,
        "iterations": MAX_ITERATIONS,
    }


def _summarize_result(result: dict[str, Any]) -> str:
    """Kompakte 1-Liner-Zusammenfassung für UI/Logging."""
    err = result.get("error")
    if err:
        return f"ERROR: {str(err)[:80]}"
    if "found" in result:
        if result["found"]:
            if "row_count" in result:
                return f"✓ {result['row_count']} rows"
            if "seasons" in result:
                return f"✓ {len(result.get('seasons',[]))} Saisons"
            if "snippets" in result:
                return f"✓ {len(result.get('snippets',[]))} Web-Snippets"
            if "source_count" in result:
                return f"✓ {result['source_count']} Articles"
            return "✓ found"
        return "✗ nichts gefunden"
    return str(result)[:80]
