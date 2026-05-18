"""200+ Test-Fragen für die GenAI-Pipeline.

Jede Frage hat:
- question: die Frage in natürlicher Sprache (für GenAI)
- expected_facts: Liste der erwarteten Fakten die in der Antwort vorkommen müssen
- category: zur Klassifikation
- difficulty: easy/medium/hard
"""
from __future__ import annotations
from typing import Any


def generate_questions(db_facts: dict) -> list[dict]:
    """Generiert die Test-Fragen anhand DB-Inhalt.

    db_facts: Dict mit aktuellen DB-Werten, generiert via SQL.
    """
    questions: list[dict[str, Any]] = []

    # ========================================================
    # KATEGORIE 1: Saison-Endplatz (45 Fragen — 1 pro Saison)
    # ========================================================
    for season, info in db_facts["seasons_rank"].items():
        q = f"Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison {season}?"
        questions.append({
            "id": f"q_rank_{season.replace('/', '_')}",
            "category": "saison_platz",
            "difficulty": "easy",
            "question": q,
            "expected_facts": [str(info["final_rank"])],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 2: Saison-Punkte (45 Fragen)
    # ========================================================
    for season, info in db_facts["seasons_points"].items():
        q = f"Wie viele Punkte holten die Falken in der Saison {season}?"
        questions.append({
            "id": f"q_pts_{season.replace('/', '_')}",
            "category": "saison_punkte",
            "difficulty": "easy",
            "question": q,
            "expected_facts": [str(info["points"])],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 3: Topscorer pro Saison (12 Fragen, 1 pro EP-Saison)
    # ========================================================
    for season, info in db_facts["topscorer"].items():
        q = f"Wer war Topscorer der Falken in der Saison {season}?"
        questions.append({
            "id": f"q_top_{season.replace('/', '_')}",
            "category": "topscorer",
            "difficulty": "easy",
            "question": q,
            "expected_facts": [info["player"]],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 4: Trainer pro Saison (22 Fragen)
    # ========================================================
    for entry in db_facts["coaches"]:
        season = entry["season"]
        q = f"Wer war Trainer der Heilbronner Falken in der Saison {season}?"
        questions.append({
            "id": f"q_coach_{season.replace('/', '_')}_{entry['coach'].split()[-1]}",
            "category": "trainer",
            "difficulty": "easy",
            "question": q,
            "expected_facts": [entry["coach"]],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 5: Liga-Zugehörigkeit (45 Fragen)
    # ========================================================
    for season, info in db_facts["seasons_league"].items():
        q = f"In welcher Liga spielten die Heilbronner Falken in der Saison {season}?"
        questions.append({
            "id": f"q_league_{season.replace('/', '_')}",
            "category": "liga",
            "difficulty": "easy",
            "question": q,
            "expected_facts": [info["league"]],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 6: Spezifische Spielergebnisse (20 Fragen)
    # ========================================================
    for game in db_facts["specific_games"][:20]:
        q = f"Welches Ergebnis hatte das Spiel zwischen {game['home']} und {game['away']} am {game['date']}?"
        questions.append({
            "id": f"q_game_{game['date'].replace('-', '')}",
            "category": "spielergebnis",
            "difficulty": "medium",
            "question": q,
            "expected_facts": [f"{game['home_score']}:{game['away_score']}",
                                f"{game['home_score']}-{game['away_score']}",
                                f"{game['home_score']} zu {game['away_score']}"],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 7: Playoff-Resultate (20 Fragen)
    # ========================================================
    for series in db_facts["playoff_results"]:
        q = (f"Wer gewann die {series['round']}-Serie zwischen Falken und "
             f"{series['opponent']} in der Saison {series['season']}?")
        questions.append({
            "id": f"q_po_{series['season'].replace('/', '_')}_{series['round'][:10].lower().replace(' ', '')}",
            "category": "playoff",
            "difficulty": "medium",
            "question": q,
            "expected_facts": [series["winner"]],
            "expected_category": "fact",
        })

    # ========================================================
    # KATEGORIE 8: Trends / Aggregate (15 Fragen)
    # ========================================================
    trend_questions = [
        ("Welches war die punkteschlechteste Falken-Saison der letzten 10 Jahre?",
         ["2015/16", "36"], "trend"),
        ("In welcher Saison hatten die Falken die meisten Punkte?",
         ["2006/07", "108"], "trend"),
        ("Wie viele DEL2-Saisons haben die Falken insgesamt gespielt?",
         ["10"], "fact"),
        ("Wann war der letzte Falken-Abstieg aus der DEL2?",
         ["2022/23"], "fact"),
        ("Welcher Spieler hat die meisten Falken-Saisons als Topscorer?",
         ["Dylan Wruck"], "fact"),
        ("Wie viele Saisons spielten die Falken in der Oberliga in den letzten Jahren?",
         ["3"], "fact"),
        ("In welcher Saison war die Hauptrunde am kürzesten (wegen Corona)?",
         ["2020/21", "49"], "fact"),
        ("Welcher Trainer hatte die längste Amtszeit bei den Falken?",
         ["Rico Rossi"], "fact"),
        ("Wie viele Trainer hatten die Falken in der DEL2-Zeit (2013-2023)?",
         [], "trend"),
        ("Was war das höchste Falken-Tor-Ergebnis in der aktuellen Saison?",
         ["11"], "fact"),
        ("In welcher Saison wurden die Falken Oberliga-Meister?",
         ["2006/07"], "fact"),
        ("Wann hatten die Falken zuletzt mehr als 100 Punkte?",
         ["2006/07", "108"], "fact"),
        ("Wer war Topscorer in der letzten Oberliga-Süd-Saison?",
         ["Wernerson Libäck", "Ritchie"], "fact"),
        ("Wie viele unterschiedliche Trainer hatten die Falken seit 1980?",
         [], "trend"),
        ("Welche Liga ist die zweite deutsche Eishockey-Liga heute?",
         ["DEL2"], "fact"),
    ]
    for q, facts, cat in trend_questions:
        questions.append({
            "id": f"q_trend_{len([x for x in questions if x.get('category') == 'trend'])+1:03d}",
            "category": "trend",
            "difficulty": "medium",
            "question": q,
            "expected_facts": facts,
            "expected_category": cat,
        })

    # ========================================================
    # KATEGORIE 9: Vergleiche zwischen Teams (10 Fragen)
    # ========================================================
    comparison_questions = [
        ("Wie oft haben die Falken in der Saison 2025/26 gegen Bayreuth gespielt?",
         ["4"]),
        ("Welches war das höchste Falken-Heim-Ergebnis gegen Bayreuth?",
         ["11"]),
        ("Wann haben die Falken zuletzt im Halbfinale gespielt?",
         ["2021/22", "2023/24"]),
        ("Gegen welches Team verloren die Falken 2022/23 in den Playdowns?",
         ["Bayreuth"]),
        ("Wer wurde Hauptrundensieger der Oberliga Süd 2024/25?",
         ["Heilbronner Falken", "Falken"]),
        ("Wie viele Spiele hat die DEL2 in einer normalen Saison?",
         ["52"]),
        ("Hat Stefan Della Rovere mehr als 30 Punkte in 2022/23?",
         ["38"]),
        ("Wie viele Punkte hatten die Falken in 2019/20?",
         ["84"]),
        ("Welche Saisons hatte Dylan Wruck mehr als 75 Punkte?",
         ["2019/20", "2020/21"]),
        ("Wer war Falken-Topscorer in der Klassenerhaltsaison 2015/16?",
         ["Adam Brace"]),
    ]
    for q, facts in comparison_questions:
        questions.append({
            "id": f"q_compare_{len([x for x in questions if x.get('category') == 'vergleich'])+1:03d}",
            "category": "vergleich",
            "difficulty": "medium",
            "question": q,
            "expected_facts": facts,
            "expected_category": "fact",
        })

    return questions


def gather_db_facts() -> dict:
    """Holt alle Fakten aus der DB die wir für die Fragen brauchen."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from falken_kb.db import exec_sql

    # Seasons + Rank + Points + League
    seasons_rank = {}
    seasons_points = {}
    seasons_league = {}
    for r in exec_sql("""
        SELECT s.label, s.league, ts.final_rank, ts.points
        FROM falken.team_seasons ts
        JOIN falken.seasons s ON s.id = ts.season_id
        JOIN falken.teams t ON t.id = ts.team_id
        WHERE t.name = 'Heilbronner Falken'
        ORDER BY s.label DESC
    """):
        season = r["label"]
        if r["final_rank"] is not None:
            seasons_rank[season] = {"final_rank": r["final_rank"]}
        if r["points"] is not None:
            seasons_points[season] = {"points": r["points"]}
        seasons_league[season] = {"league": r["league"]}

    # Topscorer pro Saison
    topscorer = {}
    for r in exec_sql("""
        SELECT season, player, points FROM (
            SELECT season, player, points,
                   ROW_NUMBER() OVER (PARTITION BY season ORDER BY points DESC NULLS LAST) AS rn
            FROM falken.falken_skater_stats WHERE points IS NOT NULL
        ) x WHERE rn = 1
    """):
        topscorer[r["season"]] = {"player": r["player"], "points": r["points"]}

    # Coaches mit Saison
    coaches = []
    for r in exec_sql("""
        SELECT DISTINCT EXTRACT(year FROM ct.start_date)::int AS yr, c.name AS coach
        FROM falken.coach_tenures ct
        JOIN falken.coaches c ON c.id = ct.coach_id
        JOIN falken.teams t ON t.id = ct.team_id
        WHERE t.name = 'Heilbronner Falken' AND ct.start_date >= '2010-01-01'
        ORDER BY yr DESC
    """):
        yr = r["yr"]
        season = f"{yr}/{(yr+1)%100:02d}"
        coaches.append({"season": season, "coach": r["coach"]})

    # Konkrete Spiele mit Datum + Score
    specific_games = []
    for r in exec_sql("""
        SELECT g.date::date::text AS date, ht.name AS home, g.home_score, g.away_score, at.name AS away
        FROM falken.games g
        JOIN falken.teams ht ON ht.id = g.home_team_id
        JOIN falken.teams at ON at.id = g.away_team_id
        WHERE g.game_type IN ('regular', 'playoff', 'playdown')
          AND (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
          AND g.home_score IS NOT NULL AND g.away_score IS NOT NULL
          AND ABS(g.home_score - g.away_score) >= 4
        ORDER BY g.date DESC LIMIT 40
    """):
        specific_games.append({
            "date": r["date"], "home": r["home"], "away": r["away"],
            "home_score": r["home_score"], "away_score": r["away_score"],
        })

    # Playoff-Ergebnisse
    playoff_results = []
    for r in exec_sql("""
        SELECT s.label AS season, ps.round, ta.name AS team_a, tb.name AS team_b,
               ps.wins_a, ps.wins_b, tw.name AS winner
        FROM falken.playoff_series ps
        JOIN falken.seasons s ON s.id = ps.season_id
        JOIN falken.teams ta ON ta.id = ps.team_a_id
        JOIN falken.teams tb ON tb.id = ps.team_b_id
        LEFT JOIN falken.teams tw ON tw.id = ps.winner_team_id
        WHERE (ta.name = 'Heilbronner Falken' OR tb.name = 'Heilbronner Falken')
          AND s.label >= '2010/11' AND tw.name IS NOT NULL
        ORDER BY s.label DESC LIMIT 25
    """):
        opp = r["team_b"] if r["team_a"] == "Heilbronner Falken" else r["team_a"]
        playoff_results.append({
            "season": r["season"], "round": r["round"], "opponent": opp, "winner": r["winner"],
        })

    return {
        "seasons_rank": seasons_rank,
        "seasons_points": seasons_points,
        "seasons_league": seasons_league,
        "topscorer": topscorer,
        "coaches": coaches,
        "specific_games": specific_games,
        "playoff_results": playoff_results,
    }


if __name__ == "__main__":
    import yaml
    facts = gather_db_facts()
    questions = generate_questions(facts)
    print(yaml.dump(questions, allow_unicode=True, sort_keys=False))
