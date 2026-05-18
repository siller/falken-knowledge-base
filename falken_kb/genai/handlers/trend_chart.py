"""Trend-Handler: Frage → SQL → Chart-Spec (Vega-Lite) + Antwort."""
from __future__ import annotations

import json
import logging
from typing import Any

from ...db import exec_sql
from ..dgx_client import DGXClient

logger = logging.getLogger(__name__)


CHART_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string", "description": "SELECT für Trend-Daten (Spalten: x, y, optional series)"},
        "chart_type": {"type": "string", "enum": ["line", "bar", "area"]},
        "x_label": {"type": "string"},
        "y_label": {"type": "string"},
        "title": {"type": "string"},
    },
    "required": ["sql", "chart_type", "x_label", "y_label", "title"],
    "additionalProperties": False,
}


def answer_trend(question: str, client: DGXClient | None = None) -> dict[str, Any]:
    c = client or DGXClient()
    # SQL + Chart-Konfig generieren
    schema_context = """Du erzeugst PostgreSQL für ein Trend-Diagramm zur Heilbronner-Falken-Eishockey-DB.

Verfügbare Views (Schema 'falken', search_path gesetzt — KEIN Prefix nötig):
- falken_skater_stats (season text '2022/23', league text, player text, position, nation, jersey_number, games_played, goals, assists, points, pim, plus_minus)
    ↑ BEREITS auf Falken-Spieler gefiltert — KEIN WHERE team= nötig, KEINE 'team'-Spalte!
- falken_goalie_stats (season, league, goalie, jersey_number, games_played, wins, losses, gaa, save_pct, shutouts)
- season_standings (season text, league text, final_rank int, team text, games_played, wins, losses, ot_wins, ot_losses, points, goals_for, goals_against, goal_diff, playoff_result, league_tier, is_focus_team_season bool)
    ↑ Enthält ALLE Teams — IMMER `team = 'Heilbronner Falken'` für Falken-Trends!

REGELN:
- NUR PostgreSQL-Syntax (NICHT MySQL: kein YEAR(), kein CURDATE(), kein DATE_SUB).
  Für aktuelle Jahre: `CURRENT_DATE` oder die Saison-Spalte direkt als TEXT vergleichen.
- season ist TEXT '2022/23' — vergleiche als String: `season >= '2015/16'` funktioniert lexikographisch
- Spaltennamen exakt wie oben: 'player' (NICHT 'player_name'), 'goalie' (NICHT 'goalie_name')
- SELECT-Spalten heißen 'x', 'y', optional 'series' (für Multi-Line/Gruppen)
- ORDER BY x ASC
- Bei aggregaten ohne Series → series weglassen
- Bei NULL-Werten in y: WHERE y IS NOT NULL ODER ORDER BY y DESC NULLS LAST

BEISPIELE:

-- Punkte-Entwicklung Falken über die Jahre:
SELECT season AS x, points AS y FROM season_standings
WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE
  AND points IS NOT NULL ORDER BY season ASC;

-- Topscorer-Entwicklung (letzte 10 Jahre, Top-Scorer pro Saison):
SELECT season AS x, MAX(points) AS y FROM falken_skater_stats
WHERE season >= '2015/16' AND points IS NOT NULL
GROUP BY season ORDER BY season ASC;

-- Tore-Verteilung der Top-5 aller Saisons (mit series):
SELECT season AS x, points AS y, player AS series FROM falken_skater_stats
WHERE points IS NOT NULL ORDER BY season ASC;
"""
    cfg = c.chat_with_schema(
        messages=[
            {"role": "system", "content": schema_context},
            {"role": "user", "content": question},
        ],
        json_schema=CHART_SCHEMA,
        schema_name="ChartSpec",
        max_tokens=600,
        temperature=0.05,
    )
    sql = cfg.get("sql", "").strip()
    if not sql:
        logger.error("Trend-SQL-Generation fehlgeschlagen für: %s — Output: %s", question[:80], cfg)
        return {
            "category": "trend",
            "sql": "",
            "rows": [],
            "answer": "Konnte für diese Trend-Frage kein SQL erzeugen (Modell-Output unvollständig).",
            "error": "sql_generation_failed",
        }

    try:
        rows = exec_sql(sql)
    except Exception as e:
        # Retry mit Hinweis bei Syntax-Fehler
        if "syntax error" in str(e).lower() or "does not exist" in str(e).lower():
            logger.warning("Trend-SQL-Fehler bei try1, retry: %s", str(e)[:120])
            hint = (f"Vorheriger Versuch scheiterte mit Fehler '{str(e)[:150]}'. "
                    "Spaltennamen exakt verwenden ('player' statt 'player_name', 'goalie' statt 'goalie_name'). "
                    "PostgreSQL, KEIN MySQL.")
            cfg2 = c.chat_with_schema(
                messages=[
                    {"role": "system", "content": schema_context},
                    {"role": "user", "content": f"{question}\n\nHINWEIS: {hint}"},
                ],
                json_schema=CHART_SCHEMA, schema_name="ChartSpec",
                max_tokens=600, temperature=0.2,
            )
            sql2 = (cfg2.get("sql", "") or "").strip()
            if sql2:
                try:
                    rows = exec_sql(sql2)
                    sql = sql2
                    cfg = cfg2
                except Exception as e2:
                    return {
                        "category": "trend", "sql": sql2, "rows": [],
                        "answer": f"⚠️  Konnte das Diagramm nicht erzeugen (SQL-Fehler nach Retry: {e2}).",
                        "error": str(e2),
                    }
            else:
                return {
                    "category": "trend", "sql": sql, "rows": [],
                    "answer": f"⚠️  Konnte das Diagramm nicht erzeugen (SQL-Fehler: {e}).",
                    "error": str(e),
                }
        else:
            return {
                "category": "trend", "sql": sql, "rows": [],
                "answer": f"⚠️  Konnte das Diagramm nicht erzeugen (SQL-Fehler: {e}).",
                "error": str(e),
            }

    chart_type = cfg.get("chart_type", "line")
    vega_spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": cfg.get("title", ""),
        "data": {"values": rows},
        "mark": chart_type,
        "encoding": {
            "x": {"field": "x", "type": "ordinal" if chart_type == "bar" else "temporal", "title": cfg.get("x_label", "")},
            "y": {"field": "y", "type": "quantitative", "title": cfg.get("y_label", "")},
        },
    }
    if rows and "series" in rows[0]:
        vega_spec["encoding"]["color"] = {"field": "series", "type": "nominal"}

    answer = c.chat(
        messages=[
            {"role": "system", "content": "Beschreibe den Trend in 1-2 Sätzen auf Deutsch."},
            {"role": "user", "content": f"Frage: {question}\nDaten: {json.dumps(rows[:30])}"},
        ],
        max_tokens=200,
        temperature=0.3,
    )

    return {
        "category": "trend",
        "sql": sql,
        "rows": rows,
        "chart_spec": vega_spec,
        "answer": answer.strip(),
    }
