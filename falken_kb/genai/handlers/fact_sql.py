"""Fact-Handler: Frage → SQL → Postgres → Antwort.

Zweistufig:
1. Gemma generiert SQL aus der Frage (mit Schema-Context als System-Prompt)
2. Postgres führt aus, Result wird mit der Frage erneut an Gemma geschickt zur Synthese
"""
from __future__ import annotations

import logging
from typing import Any

from ...db import exec_sql
from ..dgx_client import DGXClient

logger = logging.getLogger(__name__)


SCHEMA_CONTEXT = """Du arbeitest mit einer PostgreSQL-DB (Schema: falken) mit folgenden Tabellen:

seasons (id uuid, label text z.B. '2022/23', league text z.B. 'DEL2'|'Oberliga Süd'|'Oberliga', start_date date, end_date date)
teams (id uuid, name text, short_name text, alt_names text[])
players (id uuid, name text, position char, nation text, birthdate date)
coaches (id uuid, name text, first_name text, last_name text, nation text, birthdate date)
games (id uuid, season_id fk, date timestamptz, game_type text "regular|playoff|playdown",
       home_team_id fk, away_team_id fk, home_score smallint, away_score smallint, overtime bool, shootout bool)
team_seasons (team_id fk, season_id fk, final_rank, points, wins, losses, goals_for, goals_against, playoff_result text)
player_seasons (id uuid, player_id fk, team_id fk, season_id fk, jersey_number, role)
player_stats (player_season_id fk PRIMARY KEY, goals, assists, points, pim, plus_minus)
goalie_stats (player_season_id fk PRIMARY KEY, wins, losses, gaa, save_pct, shutouts)
coach_tenures (id uuid, coach_id fk, team_id fk, role text z.B. 'Headcoach', start_date date, end_date date)
    ↑ KEIN season_id! Verknüpfung mit seasons über überlappenden Zeitraum:
    JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date
playoff_series (id uuid, season_id fk, round text z.B. 'Achtelfinale'|'Viertelfinale'|'Halbfinale'|'Finale'|'Play-Down R1'|'Play-Down R2',
                team_a_id fk, team_b_id fk, wins_a smallint, wins_b smallint, winner_team_id fk)
    ↑ Bei Playoff-Fragen IMMER diese Tabelle nutzen (NICHT games zählen!) — winner_team_id ist die zuverlässigste Quelle.

Convenience Views (BEREITS auf Heilbronner Falken gefiltert — KEIN WHERE team= nötig!):
falken_skater_stats (season text, league text, player text, position, nation, jersey_number, games_played, goals, assists, points, pim, plus_minus)
    ↑ Spalte 'team' EXISTIERT NICHT — die View enthält nur Falken-Spieler.
falken_goalie_stats (season, league, goalie, jersey_number, games_played, wins, losses, gaa, save_pct, shutouts)
season_standings (season text, league text, final_rank int, team text, games_played, wins, losses, ot_wins, ot_losses, points, goals_for, goals_against, goal_diff, playoff_result, league_tier, is_focus_team_season)
    ↑ Diese View enthält ALLE Teams — WHERE team='Heilbronner Falken' nötig.
    ↑ Für Trend-/Aggregat-Queries über Falken zusätzlich AND is_focus_team_season = TRUE (filtert Hintergrund-Saisons raus).

REGELN:
- NUR ein gültiges PostgreSQL SELECT-Statement, keine Erklärungen
- SQL-Keywords IMMER ENGLISCH: SELECT, FROM, WHERE, ORDER BY, GROUP BY, JOIN, LIMIT.
  Schreibe NIE deutsche Übersetzungen wie "ODER" (statt "ORDER") oder "VON" (statt "FROM").
- Tabellennamen GENAU wie unten dokumentiert — NICHT verdoppeln (z.B. "falken_skater_stats", NICHT "falken_skater_skater_stats").
- IMMER alle Tabellen-Namen in der Antwort (Spielergebnisse: Home- + Away-Teamname returnen, sonst kann der Synthesis-Step nicht zuordnen)
- Bei OR/AND IMMER Klammern setzen: `(A OR B) AND C` nicht `A OR B AND C`
- Single-Quotes sauber abschliessen, ein String-Wert pro WHERE-Klausel
- Schema-Prefix `falken.` ist NICHT nötig — search_path ist gesetzt
- IMMER `NULLS LAST` bei `ORDER BY ... DESC` für numerische Spalten (points, goals, gaa, etc.),
  und zusätzlich `WHERE <spalte> IS NOT NULL` wenn nur der/die Top-Eintrag gesucht ist —
  PostgreSQL sortiert NULLs sonst NACH OBEN (NULLS FIRST ist Default bei DESC).
- Bei Spielernamen IMMER `WHERE similarity(player, 'Vorname Nachname') > 0.3` nutzen
  (pg_trgm-Extension, behandelt Tippfehler — "Richie" matcht "Ritchie"). Beispiel:
  `WHERE similarity(player, 'Nolan Richie') > 0.3 ORDER BY similarity(player, 'Nolan Richie') DESC`.
  Fallback: `player ILIKE '%nachname%'` für exakte Substring-Matches.
  NIE `player = 'X'` (exact match) — schlägt bei jedem Tippfehler fehl.
  Dasselbe für coaches.name (`similarity(c.name, 'X') > 0.3`).

BEISPIELE (genau diesem Muster folgen):

-- Tabellenplatz einer Saison:
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2022/23';

-- Topscorer einer Saison (View ist pre-filtered — KEIN WHERE team!, NULLS LAST + IS NOT NULL!):
SELECT player, points, goals, assists FROM falken_skater_stats
WHERE season = '2022/23' AND points IS NOT NULL
ORDER BY points DESC NULLS LAST LIMIT 5;

-- Trainer einer Saison (via Date-Range-Overlap):
SELECT c.name, ct.role, ct.start_date, ct.end_date
FROM coach_tenures ct
JOIN coaches c ON c.id = ct.coach_id
JOIN teams t ON t.id = ct.team_id
JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date
WHERE t.name = 'Heilbronner Falken' AND s.label = '2022/23' AND ct.role = 'Headcoach';

-- Spielergebnis an einem Datum (Team-Namen IMMER returnen!).
-- WICHTIG: User schreibt Teams oft KURZ ("Memmingen" statt "ECDC Memmingen Indians").
-- Nutze deshalb ILIKE '%kurzname%' statt exact = OR IN — robust gegen Tippfehler & Abkürzungen.
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout
FROM games g
JOIN teams ht ON ht.id = g.home_team_id
JOIN teams at ON at.id = g.away_team_id
WHERE g.date::date = '2026-02-27'
  AND (ht.name ILIKE '%Heilbronner%' OR at.name ILIKE '%Heilbronner%')
  AND (ht.name ILIKE '%Memmingen%' OR at.name ILIKE '%Memmingen%');
-- ↑ ILIKE '%kurzname%' funktioniert für: "Memmingen" → "ECDC Memmingen Indians",
-- "Bayreuth" → "Bayreuth Tigers", "Selb" → "VER Selber Wölfe", etc.

-- Alle Saisons in einer Liga:
SELECT DISTINCT season FROM season_standings WHERE team = 'Heilbronner Falken' AND league = 'Oberliga Süd' ORDER BY season;

-- Playoff-Serie: wer gewann (Falken vs Team X in Saison Y):
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b,
       wt.name AS winner
FROM playoff_series ps
JOIN teams ta ON ta.id = ps.team_a_id
JOIN teams tb ON tb.id = ps.team_b_id
LEFT JOIN teams wt ON wt.id = ps.winner_team_id
JOIN seasons s ON s.id = ps.season_id
WHERE s.label = '2021/22'
  AND ('Heilbronner Falken' IN (ta.name, tb.name))
  AND ('Löwen Frankfurt' IN (ta.name, tb.name))
  AND ps.round = 'Halbfinale';

-- Trend-Aggregat: punkteschlechteste Falken-Saison letzte 10 Jahre:
SELECT season, points FROM season_standings
WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE
  AND season >= '2015/16'
ORDER BY points ASC LIMIT 1;

-- Trend-Aggregat: höchste Punktzahl aller Zeiten:
SELECT season, points FROM season_standings
WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE
ORDER BY points DESC NULLS LAST LIMIT 1;

-- "Beste Topscorer-Leistung in X Jahren" (eine Saison mit Höchst-Punktwert):
SELECT player, season, points, goals, assists FROM falken_skater_stats
WHERE points IS NOT NULL AND season >= '2015/16'
ORDER BY points DESC NULLS LAST LIMIT 5;
-- ↑ TOP 5 zurückgeben, damit Synthesis Ranking präsentieren kann.

-- "Bester Karriere-Topscorer in X Jahren" (Summe der Punkte über Saisons hinweg):
SELECT player, SUM(points) AS career_points,
       SUM(goals) AS career_goals, SUM(assists) AS career_assists,
       COUNT(DISTINCT season) AS seasons
FROM falken_skater_stats
WHERE points IS NOT NULL AND season >= '2015/16'
GROUP BY player ORDER BY career_points DESC NULLS LAST LIMIT 5;

-- Spieler-Stats-Lookup (FUZZY-MATCH gegen Tippfehler via pg_trgm):
SELECT season, player, points, goals, assists,
       similarity(player, 'Nolan Richie') AS sim
FROM falken_skater_stats
WHERE similarity(player, 'Nolan Richie') > 0.3 AND points IS NOT NULL
ORDER BY similarity(player, 'Nolan Richie') DESC, season DESC LIMIT 10;
-- ↑ IMMER similarity()>0.3 bei Spielernamen — matcht auch "Richie" auf "Ritchie".
-- Nur wenn das nichts liefert, fallback auf ILIKE '%nachname%'.
"""

SQL_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string", "description": "PostgreSQL SELECT-Statement"},
        "explanation": {"type": "string", "description": "Kurze Begründung in Deutsch (max 1 Satz)"},
    },
    "required": ["sql", "explanation"],
    "additionalProperties": False,
}


def _generate_and_run_sql(question: str, c: DGXClient, attempt_label: str,
                          extra_hint: str = "", temperature: float = 0.05
                          ) -> tuple[str, list[Any] | None, str | None]:
    """Single try: SQL erzeugen + ausführen. Returns (sql, rows, error_msg)."""
    user_msg = question if not extra_hint else f"{question}\n\nHINWEIS: {extra_hint}"
    sql_result = c.chat_with_schema(
        messages=[
            {"role": "system", "content": SCHEMA_CONTEXT},
            {"role": "user", "content": user_msg},
        ],
        json_schema=SQL_SCHEMA,
        schema_name="SqlGeneration",
        max_tokens=1000,
        temperature=temperature,
    )
    sql = (sql_result.get("sql", "") or "").strip()
    if not sql:
        return ("", None, "sql_generation_failed")
    logger.info("[%s] Generiertes SQL: %s", attempt_label, sql)
    try:
        rows = exec_sql(sql)
        return (sql, rows, None)
    except Exception as e:
        return (sql, None, str(e))


def answer_fact(question: str, client: DGXClient | None = None) -> dict[str, Any]:
    c = client or DGXClient()
    # Stotter-Bug-Schutz: LLMs verdoppeln manchmal Tokens ("ODER BY" oder
    # "JOIN teams ht JOIN teams ht"). Bei Syntax-Fehler einmal retry mit
    # höherer Temperatur + Hinweis.
    sql, rows, err = _generate_and_run_sql(question, c, "try1", temperature=0.05)
    if err and err != "sql_generation_failed" and "syntax error" in err.lower():
        logger.warning("SQL-Syntax-Fehler bei try1, retry mit Hinweis: %s", err[:120])
        hint = ("Schreibe das SQL sorgfältig — keine doppelten Tokens "
                "(NICHT 'JOIN teams ht JOIN teams ht ON' o.ä.), "
                "keine deutschen Keywords (NICHT 'ODER BY'), "
                "keine verschachtelten Quotes.")
        sql, rows, err = _generate_and_run_sql(question, c, "try2", extra_hint=hint, temperature=0.2)

    if not sql:
        return {
            "category": "fact",
            "sql": "",
            "rows": [],
            "answer": "Konnte für diese Frage kein SQL erzeugen (Modell-Output unvollständig).",
            "error": "sql_generation_failed",
        }
    if err:
        logger.error("SQL-Fehler (final): %s", err)
        return {
            "category": "fact",
            "sql": sql,
            "rows": [],
            "answer": f"⚠️  Konnte die Frage nicht beantworten (SQL-Fehler: {err}).",
            "error": err,
        }

    # Schritt 3: Antwort synthetisieren
    rows_str = "\n".join(str(r) for r in rows[:30])  # max 30 Zeilen Kontext
    synth = c.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Beantworte die Frage auf Deutsch in 1-3 Sätzen anhand der DB-Resultate. "
                    "Übernimm Zahlen, Namen und Datumsangaben WORTWÖRTLICH aus den Daten — "
                    "erfinde nichts dazu. "
                    "WICHTIG: Wenn die DB-Resultate Daten enthalten (auch nur 1 Zeile), nutze sie SELBSTBEWUSST. "
                    "Sage NICHT 'unzureichend' oder 'es liegen keine Daten vor' wenn der relevante Wert "
                    "in den Resultaten steht — die SQL-Query wurde genau für diese Frage formuliert. "
                    "Bei Top-N-Listen ist der ERSTE Eintrag die direkte Antwort, weitere geben Kontext. "
                    "Nur wenn die Liste WIRKLICH LEER ist (0 Zeilen), sage 'keine Daten'. "
                    "WICHTIG bei Spielergebnissen: Format IMMER "
                    "'<Heimteam> <home_score>:<away_score> <Auswärtsteam>' "
                    "(Heim-Score zuerst, NICHT Sieger-Score zuerst). "
                    "Beispiel: 'ECDC Memmingen 7:2 Heilbronner Falken (Memmingen war Heimteam, gewann)'. "
                    "Erwähne keine SQL-Details."
                ),
            },
            {
                "role": "user",
                "content": f"Frage: {question}\n\nDB-Resultate:\n{rows_str if rows else '(keine Daten)'}",
            },
        ],
        max_tokens=300,
        temperature=0.3,
    )

    return {
        "category": "fact",
        "sql": sql,
        "rows": rows,
        "answer": synth.strip(),
    }
