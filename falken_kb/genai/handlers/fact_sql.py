"""Fact-Handler: Frage → SQL → Postgres → Antwort.

Zweistufig:
1. Gemma generiert SQL aus der Frage (mit Schema-Context als System-Prompt)
2. Postgres führt aus, Result wird mit der Frage erneut an Gemma geschickt zur Synthese
"""
from __future__ import annotations

import logging
import re
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
playoff_series (id uuid, season_id fk, round text, team_a_id fk, team_b_id fk,
                wins_a smallint, wins_b smallint, winner_team_id fk)
    ↑ Bei Playoff-Fragen IMMER diese Tabelle nutzen (NICHT games zählen!) — winner_team_id ist die zuverlässigste Quelle.
    ↑ `round` enthält GENAU diese Schreibweisen: 'Pre Play-Off', 'Achtelfinale',
      'Viertelfinale', 'Halbfinale', 'Finale', 'Play-Down R1', 'Play-Down R2',
      'Spiel um Pl.3'. Varianten wie 'Pre-Playoff' oder 'Playoffs' matchen NICHT.
    ↑ Sind Saison UND beide Teams bekannt, den Runden-Filter WEGLASSEN — die Serie
      ist damit schon eindeutig, und ein falsch geratener Runden-Name liefert 0 Zeilen.

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
- Liga-Namen NIE exakt vergleichen: die Oberliga steht als 'Oberliga Süd' bzw.
  'Oberliga Nord' in der DB. Also `league LIKE 'Oberliga%'`, nicht `= 'Oberliga'`.
- Die DB enthält BEIDES: gespielte Partien (mit Score) und den Spielplan der
  kommenden Saison (Score NULL). Welche Hälfte gemeint ist, entscheidet die Frage
  — und die beiden folgenden Regeln schließen einander AUS. NIE beide zugleich
  anwenden, das ergibt garantiert 0 Zeilen:
  (a) Frage nach ERGEBNISSEN/Statistik ("wie endete", "wie viele Tore",
      "in der aktuellen Saison"): `WHERE g.home_score IS NOT NULL`, und
      "aktuelle Saison" ist
      `(SELECT max(season) FROM season_standings WHERE games_played > 0)`.
  (b) Frage nach TERMINEN ("wann spielen", "wann ist das nächste Spiel",
      "Spielplan", "diese Saison gegen X"): `WHERE g.home_score IS NULL`
      — und dann KEIN zusätzlicher Saison-Filter über max(season), denn die
      offenen Spiele liegen per Definition in der noch nicht gespielten Saison.
- "zuletzt"/"wann war der letzte …" heißt CHRONOLOGISCH sortieren
  (`ORDER BY season DESC`), nicht nach dem gefragten Wert.
- `season` ist TEXT im Format 'YYYY/YY' — NIE `season::int` (kippt mit
  "invalid input syntax for type integer"). Für Jahresvergleiche
  `LEFT(season, 4)::int` benutzen oder direkt Strings vergleichen
  (`season >= '2016/17'` funktioniert, weil das Format sortierbar ist).
- Bei `SELECT DISTINCT` darf ORDER BY nur Spalten aus der SELECT-Liste nutzen.
- "Wie viele Spiele hat eine Saison?" meint Spiele PRO TEAM →
  `games_played` aus season_standings, nicht COUNT(*) über games.

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

-- Trend-Aggregat: punkteschlechteste Falken-Saison der letzten 10 Jahre.
-- "letzte N Jahre" = die letzten N Saisons MIT Daten (kein festes Jahr raten,
-- sonst fällt je nach Grenze die gesuchte Saison aus dem Fenster):
WITH letzte AS (
  SELECT season, points FROM season_standings
  WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE
    AND points IS NOT NULL
  ORDER BY season DESC LIMIT 10
)
SELECT season, points FROM letzte ORDER BY points ASC LIMIT 1;

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

-- Längste Trainer-Amtszeit AM STÜCK (coach_tenures hat eine Zeile PRO SAISON,
-- deshalb erst zusammenhängende Amtszeiten verschmelzen — sonst gewinnt jeder,
-- der eine einzelne lange Saison hatte):
WITH t AS (
  SELECT c.name, ct.start_date, ct.end_date,
         LAG(ct.end_date) OVER (PARTITION BY ct.coach_id ORDER BY ct.start_date) AS prev_end
  FROM coach_tenures ct
  JOIN coaches c ON c.id = ct.coach_id
  JOIN teams tm ON tm.id = ct.team_id
  WHERE tm.name = 'Heilbronner Falken'
), marked AS (
  SELECT *, CASE WHEN prev_end IS NULL OR start_date - prev_end > 180 THEN 1 ELSE 0 END AS new_spell
  FROM t
), spells AS (
  SELECT *, SUM(new_spell) OVER (PARTITION BY name ORDER BY start_date
                                 ROWS UNBOUNDED PRECEDING) AS spell_no
  FROM marked
)
SELECT name, MIN(start_date) AS von, MAX(end_date) AS bis,
       COUNT(*) AS saisons, MAX(end_date) - MIN(start_date) AS tage
FROM spells GROUP BY name, spell_no
ORDER BY tage DESC NULLS LAST LIMIT 5;

-- Heim- vs. Auswärtsbilanz (eine Zeile pro Falken-Spiel, aus Falken-Sicht):
WITH fg AS (
  SELECT s.label AS season,
         CASE WHEN ht.name = 'Heilbronner Falken' THEN 'Heim' ELSE 'Auswärts' END AS ort,
         CASE WHEN ht.name = 'Heilbronner Falken' THEN g.home_score ELSE g.away_score END AS tore,
         CASE WHEN ht.name = 'Heilbronner Falken' THEN g.away_score ELSE g.home_score END AS gegentore
  FROM games g
  JOIN teams ht ON ht.id = g.home_team_id
  JOIN teams at ON at.id = g.away_team_id
  JOIN seasons s ON s.id = g.season_id
  WHERE (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
    AND g.home_score IS NOT NULL AND g.game_type = 'regular'
)
SELECT ort, COUNT(*) AS spiele,
       COUNT(*) FILTER (WHERE tore > gegentore) AS siege,
       COUNT(*) FILTER (WHERE tore < gegentore) AS niederlagen,
       SUM(tore) AS tore, SUM(gegentore) AS gegentore
FROM fg WHERE season = '2025/26' GROUP BY ort;

-- "Wer war am häufigsten Topscorer?" (pro Saison den Besten bestimmen, dann zählen):
WITH ranked AS (
  SELECT season, player, points,
         ROW_NUMBER() OVER (PARTITION BY season ORDER BY points DESC NULLS LAST) AS rn
  FROM falken_skater_stats WHERE points IS NOT NULL
)
SELECT player, COUNT(*) AS topscorer_saisons
FROM ranked WHERE rn = 1
GROUP BY player ORDER BY topscorer_saisons DESC LIMIT 5;

-- "Wie viele Spiele hat eine Saison?" = Spiele PRO TEAM (nicht alle Partien
-- der Liga zusammenzählen — das wären bei 14 Teams das 7-fache):
SELECT season, games_played
FROM season_standings
WHERE league = 'DEL2' AND games_played > 0
ORDER BY season DESC LIMIT 3;

-- Auf-/Abstieg = Ligawechsel zwischen zwei aufeinanderfolgenden Saisons
-- (es gibt KEINE Spalte "Abstieg" — league_tier: 2 = DEL2, 3 = Oberliga):
WITH l AS (
  SELECT season, league, league_tier,
         LAG(league_tier) OVER (ORDER BY season) AS prev_tier,
         LAG(league) OVER (ORDER BY season) AS prev_league
  FROM season_standings
  WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND games_played > 0
)
SELECT season, prev_league AS von_liga, league AS nach_liga,
       CASE WHEN league_tier > prev_tier THEN 'Abstieg' ELSE 'Aufstieg' END AS wechsel
FROM l WHERE prev_tier IS NOT NULL AND league_tier <> prev_tier
ORDER BY season DESC;

-- Torhüter-Bestwerte (goalie_stats: GAA klein = gut, save_pct groß = gut):
SELECT season, goalie, games_played, gaa, save_pct, shutouts
FROM falken_goalie_stats
WHERE gaa IS NOT NULL AND games_played >= 10
ORDER BY gaa ASC LIMIT 5;

-- "In der aktuellen Saison …" — IMMER auf die letzte Saison MIT Ergebnissen
-- beziehen (der Spielplan der kommenden Saison steht schon in der DB):
SELECT s.label AS season, MAX(g.home_score + g.away_score) AS meiste_tore
FROM games g
JOIN teams ht ON ht.id = g.home_team_id
JOIN teams at ON at.id = g.away_team_id
JOIN seasons s ON s.id = g.season_id
WHERE (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
  AND g.home_score IS NOT NULL
  AND s.label = (SELECT max(season) FROM season_standings
                 WHERE team = 'Heilbronner Falken' AND games_played > 0)
GROUP BY s.label;

-- Nächstes Spiel / Spielplan der kommenden Saison (noch ohne Ergebnis).
-- Datum IMMER mit to_char formatieren — roh kommt ein ISO-Zeitstempel wie
-- '2026-10-23T19:30:00+00:00' in der Antwort an, was niemand lesen will:
SELECT to_char(g.date, 'DD.MM.YYYY HH24:MI') AS termin,
       CASE g.game_type WHEN 'friendly' THEN 'Testspiel'
                        WHEN 'playoff'  THEN 'Playoff'
                        ELSE 'Hauptrunde' END AS spieltyp,
       ht.name AS home_team, at.name AS away_team
FROM games g
JOIN teams ht ON ht.id = g.home_team_id
JOIN teams at ON at.id = g.away_team_id
WHERE g.home_score IS NULL AND g.date > now()
  AND (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
ORDER BY g.date ASC LIMIT 5;

-- Alle Termine gegen einen bestimmten Gegner in der laufenden Spielzeit.
-- "diese Saison" heißt bei Terminfragen die Saison MIT offenen Spielen
-- (`home_score IS NULL`) — nicht die letzte abgeschlossene.
-- IMMER den Spieltyp mitliefern: im August/September stehen Testspiele im
-- Plan, und die als Punktspiele auszugeben wäre irreführend.
SELECT to_char(g.date, 'DD.MM.YYYY HH24:MI') AS termin,
       CASE g.game_type WHEN 'friendly' THEN 'Testspiel'
                        WHEN 'playoff'  THEN 'Playoff'
                        ELSE 'Hauptrunde' END AS spieltyp,
       ht.name AS home_team, at.name AS away_team
FROM games g
JOIN teams ht ON ht.id = g.home_team_id
JOIN teams at ON at.id = g.away_team_id
WHERE g.home_score IS NULL
  AND (ht.name ILIKE '%Heilbronner%' OR at.name ILIKE '%Heilbronner%')
  AND (ht.name ILIKE '%Stuttgart%' OR at.name ILIKE '%Stuttgart%')
ORDER BY g.date ASC;

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


# Saison-Filter, der auf die letzte Saison MIT Ergebnissen auflöst.
# Fängt die üblichen Formulierungen ab, mit und ohne Tabellen-Alias.
_SEASON_WITH_RESULTS_FILTER = re.compile(
    r"\s+AND\s+\w*\.?(?:label|season)\s*=\s*\(\s*SELECT\s+max\(\s*season\s*\)"
    r".*?games_played\s*>\s*0\s*\)",
    re.IGNORECASE | re.DOTALL,
)


def _drop_conflicting_season_filter(sql: str) -> str | None:
    """Entfernt den 'letzte Saison mit Ergebnissen'-Filter aus Termin-Queries.

    WHY: Beide Bedingungen einzeln sind richtig, zusammen ergeben sie immer eine
    leere Menge — offene Termine (`home_score IS NULL`) liegen naturgemäß NICHT
    in der letzten Saison mit Ergebnissen. Das Modell kombinierte sie trotz
    gegenteiliger Anweisung im Prompt reproduzierbar, deshalb hier im Code.

    Returnt das bereinigte SQL oder None, wenn nichts zu tun war.
    """
    if not re.search(r"home_score\s+IS\s+NULL", sql, re.IGNORECASE):
        return None
    cleaned = _SEASON_WITH_RESULTS_FILTER.sub("", sql)
    return cleaned if cleaned != sql else None


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

    # Terminfrage ohne Treffer? Dann prüfen, ob sich die Query selbst blockiert
    # (offene Spiele UND Saison-mit-Ergebnissen gefiltert) und einmal ohne den
    # widersprüchlichen Filter ausführen.
    if sql and not err and not rows:
        repaired = _drop_conflicting_season_filter(sql)
        if repaired:
            logger.info("Terminfrage ohne Treffer — Saison-Filter widerspricht "
                        "'home_score IS NULL', führe ohne ihn erneut aus")
            try:
                rows = exec_sql(repaired)
                sql = repaired
            except Exception as e:  # noqa: BLE001 — Provider-/DB-Fehler untypisiert
                logger.warning("Reparierte Query schlug fehl: %s", str(e)[:120])

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
                    "Bei Terminlisten (Spielplan, 'wann spielen') JEDEN gelieferten Termin nennen — "
                    "eine Auswahl daraus wäre für Fans irreführend. Testspiele dabei als solche "
                    "kennzeichnen, sonst hält man sie für Punktspiele. "
                    "Bei mehr als 3 Sätzen Inhalt darfst du die Termine als Aufzählung schreiben. "
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
