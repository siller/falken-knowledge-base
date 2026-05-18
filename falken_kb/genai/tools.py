"""Tools für den Tool-Use-Agent.

Jedes Tool ist eine simple Python-Function mit klarer Signature + docstring.
Das LLM bekommt diese als JSON-Schema und wählt selbst welche es aufruft.
"""
from __future__ import annotations

import logging
from typing import Any

from ..db import exec_sql, supabase
from .handlers.fact_sql import answer_fact
from .handlers.narrative_rag import answer_narrative
from .web_search import tavily_search

logger = logging.getLogger(__name__)


def tool_query_falken_db(question: str) -> dict[str, Any]:
    """Beantworte eine Frage aus der Falken-Eishockey-Datenbank.

    Nutzt die fact-SQL-Pipeline: LLM erzeugt SQL aus der Frage, führt es gegen
    Supabase aus, synthetisiert eine deutsche Antwort. Nutze für ALLE Fragen
    zu Falken-Saisons, Spielen, Trainern, Spielerstatistiken, Playoffs.

    Args:
        question: Die natursprachliche Frage (z.B. "Wer war Topscorer 2024/25?")

    Returns:
        {answer, sql, rows, found: bool}
    """
    try:
        r = answer_fact(question)
        answer = r.get("answer", "")
        rows = r.get("rows", []) or []
        found = bool(rows) and "keine daten" not in answer.lower()
        return {
            "answer": answer[:500],
            "sql": (r.get("sql") or "")[:500],
            "row_count": len(rows),
            "first_rows": rows[:3],
            "found": found,
        }
    except Exception as e:
        return {"answer": f"DB-Error: {str(e)[:200]}", "found": False, "error": str(e)[:200]}


def tool_lookup_player(name: str) -> dict[str, Any]:
    """Suche einen Spieler bei den Falken via Fuzzy-Match (pg_trgm).

    Nutze wenn du einen konkreten Namen hast und alle Saisons + Stats
    für genau diesen Spieler willst. Funktioniert auch mit Tippfehlern
    oder Spitznamen (z.B. "Tommy" matcht "Thomas").

    Args:
        name: Vollname oder Teilname (z.B. "Nolan Ritchie", "Wruck")

    Returns:
        {found, player_name, seasons: [{season, points, goals, ...}]}
    """
    safe = name.replace("'", "''")
    try:
        rows = exec_sql(
            f"SELECT season, player, points, goals, assists, games_played, "
            f"similarity(player, '{safe}') AS sim "
            f"FROM falken_skater_stats "
            f"WHERE similarity(player, '{safe}') > 0.3 AND points IS NOT NULL "
            f"ORDER BY sim DESC, season DESC LIMIT 15"
        )
        if not rows:
            rows = exec_sql(
                f"SELECT season, goalie AS player, wins, losses, gaa, save_pct, games_played, "
                f"similarity(goalie, '{safe}') AS sim "
                f"FROM falken_goalie_stats "
                f"WHERE similarity(goalie, '{safe}') > 0.3 "
                f"ORDER BY sim DESC, season DESC LIMIT 15"
            )
        return {
            "found": bool(rows),
            "player_name": rows[0].get("player") if rows else None,
            "seasons": rows[:10],
            "match_score": float(rows[0].get("sim", 0)) if rows else 0,
        }
    except Exception as e:
        return {"found": False, "error": str(e)[:200]}


def tool_search_falken_news(query: str) -> dict[str, Any]:
    """Suche in den lokalen Falken-News-Artikeln (heilbronner-falken.de RSS).

    Nutze für Fragen zu aktuellen News, Neuverpflichtungen, Kader-Änderungen,
    Trainer-Bekanntgaben, etc. NICHT für statistische Datenbank-Fragen.

    Args:
        query: Suchbegriff oder Frage (z.B. "neueste Verpflichtungen", "wer ist Steffen Ziesche")

    Returns:
        {found, answer, source_count, sources: [{title, source, date}]}
    """
    try:
        r = answer_narrative(query)
        sources = r.get("sources") or []
        return {
            "found": bool(sources),
            "answer": r.get("answer", "")[:600],
            "source_count": len(sources),
            "sources": [{"title": s.get("title",""), "source": s.get("source","")} for s in sources[:5]],
        }
    except Exception as e:
        return {"found": False, "error": str(e)[:200]}


def tool_search_web(query: str) -> dict[str, Any]:
    """Suche im Internet (Tavily Web-Search) — für externe Welt-Info.

    Nutze wenn die Frage Information OUTSIDE der Falken-Welt braucht:
    Personen die nicht (mehr) Spieler sind aber irgendwie mit Falken verbunden,
    Lokal/Restaurant-Besitzer, aktuelle Welt-Events, etc.

    Args:
        query: Web-Suchbegriff (kurz + spezifisch — englisch oft besser)

    Returns:
        {found, summary, snippets: [{title, url, content}]}
    """
    try:
        r = tavily_search(query, max_results=5)
        return {
            "found": bool(r.get("results")),
            "summary": r.get("answer", "")[:500],
            "snippets": [
                {"title": x["title"], "url": x["url"], "content": x["content"][:300]}
                for x in r.get("results", [])[:5]
            ],
            "error": r.get("error"),
        }
    except Exception as e:
        return {"found": False, "error": str(e)[:200]}


# Tool-Registry (Name → Function + JSON-Schema fürs LLM)
TOOLS: dict[str, dict[str, Any]] = {
    "query_falken_db": {
        "fn": tool_query_falken_db,
        "description": "Frage natursprachlich an die Falken-DB (Saisons, Spiele, Trainer, Spieler-Stats, Playoffs). IMMER zuerst probieren bei DB-relevanten Fragen.",
        "args": {"question": "Die Frage (deutsch)"},
    },
    "lookup_player": {
        "fn": tool_lookup_player,
        "description": "Lookup eines konkreten Spielers per Name (Fuzzy-Match, robust gegen Tippfehler + Spitznamen).",
        "args": {"name": "Spielername"},
    },
    "search_falken_news": {
        "fn": tool_search_falken_news,
        "description": "Durchsuche lokale Falken-News-Artikel (heilbronner-falken.de RSS) für aktuelle Vereinsthemen, Transfers, Kader.",
        "args": {"query": "Suchbegriff"},
    },
    "search_web": {
        "fn": tool_search_web,
        "description": "Web-Suche via Tavily für externe Welt-Info (Restaurant-Besitzer, ehemalige Profis außerhalb DB, Lokal-News).",
        "args": {"query": "Web-Suchbegriff (kurz, präzise)"},
    },
}


def get_tools_description() -> str:
    """Lesbare Tool-Liste fürs LLM-Prompt."""
    lines = []
    for name, t in TOOLS.items():
        args_desc = ", ".join(f"{k}: {v}" for k, v in t["args"].items())
        lines.append(f"- {name}({args_desc}): {t['description']}")
    return "\n".join(lines)
