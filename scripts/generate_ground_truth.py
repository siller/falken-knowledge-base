"""Generiert AUTOMATISCH eine umfangreiche Ground-Truth-Datei aus DB-Inhalten.

WICHTIG: Diese Tests prüfen Schema-interne Konsistenz, NICHT externe Wahrheit.
Externe Validierung passiert über cross_source_diff.py und die handgeprüften
Tests in ground_truth_manual.yaml.

Verwendung:
  python3 scripts/generate_ground_truth.py > tests/ground_truth_auto.yaml
"""
import sys
import yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql


def generate() -> list[dict]:
    checks = []

    # =================================================================
    # A) FALKEN-SAISON-PLATZIERUNGEN (alle Saisons mit final_rank)
    # =================================================================
    for r in exec_sql("""
        SELECT s.label, s.league, ts.final_rank, ts.points
        FROM falken.team_seasons ts
        JOIN falken.seasons s ON s.id = ts.season_id
        JOIN falken.teams t ON t.id = ts.team_id
        WHERE t.name = 'Heilbronner Falken' AND ts.final_rank IS NOT NULL
        ORDER BY s.label DESC
    """):
        cid = "rank_" + r["label"].replace("/", "_")
        expected = {"final_rank": r["final_rank"]}
        if r["points"]:
            expected["points"] = r["points"]
        checks.append({
            "id": cid,
            "description": f"Falken {r['label']} {r['league']}: Platz {r['final_rank']}" +
                           (f", {r['points']}P" if r["points"] else ""),
            "source": "team_seasons (cross-validated)",
            "query": f"SELECT final_rank, points FROM falken.season_standings "
                     f"WHERE team='Heilbronner Falken' AND season='{r['label']}' AND league='{r['league']}'",
            "expected": [expected]
        })

    # =================================================================
    # B) TOPSCORER PRO SAISON (aus EP)
    # =================================================================
    for r in exec_sql("""
        SELECT season, player, points, goals, assists FROM (
            SELECT season, player, points, goals, assists,
                   ROW_NUMBER() OVER (PARTITION BY season ORDER BY points DESC NULLS LAST, goals DESC) AS rn
            FROM falken.falken_skater_stats
            WHERE points IS NOT NULL
        ) x WHERE rn = 1 ORDER BY season DESC
    """):
        cid = "topscorer_" + r["season"].replace("/", "_")
        checks.append({
            "id": cid,
            "description": f"Topscorer {r['season']}: {r['player']}, {r['points']}P ({r['goals']}G+{r['assists']}A)",
            "source": "EliteProspects",
            "query": f"SELECT player, points FROM falken.falken_skater_stats "
                     f"WHERE season='{r['season']}' ORDER BY points DESC NULLS LAST LIMIT 1",
            "expected": [{"player": r["player"], "points": r["points"]}]
        })

    # =================================================================
    # C) ANZAHL HAUPTRUNDEN-SPIELE PRO SAISON
    # =================================================================
    for r in exec_sql("""
        SELECT s.label, s.league, COUNT(*) as n
        FROM falken.games g
        JOIN falken.seasons s ON s.id = g.season_id
        JOIN falken.teams ht ON ht.id = g.home_team_id
        JOIN falken.teams at ON at.id = g.away_team_id
        WHERE g.game_type = 'regular'
          AND (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
        GROUP BY s.label, s.league
        HAVING COUNT(*) >= 40
        ORDER BY s.label DESC
    """):
        cid = "games_count_" + r["label"].replace("/", "_") + "_" + r["league"][:5].lower().replace(" ", "")
        checks.append({
            "id": cid,
            "description": f"{r['league']} {r['label']} Falken-Hauptrunde: {r['n']} Spiele",
            "source": "games table",
            "query": f"SELECT COUNT(*) as n FROM falken.games g "
                     f"JOIN falken.seasons s ON s.id=g.season_id "
                     f"JOIN falken.teams ht ON ht.id=g.home_team_id "
                     f"JOIN falken.teams at ON at.id=g.away_team_id "
                     f"WHERE s.label='{r['label']}' AND s.league='{r['league']}' "
                     f"AND g.game_type='regular' "
                     f"AND (ht.name='Heilbronner Falken' OR at.name='Heilbronner Falken')",
            "expected": [{"n": r["n"]}]
        })

    # =================================================================
    # D) PLAYOFF-SERIEN-AUSGÄNGE
    # =================================================================
    for r in exec_sql("""
        SELECT s.label, ps.round, ta.name AS team_a, tb.name AS team_b,
               ps.wins_a, ps.wins_b, tw.name AS winner
        FROM falken.playoff_series ps
        JOIN falken.seasons s ON s.id = ps.season_id
        JOIN falken.teams ta ON ta.id = ps.team_a_id
        JOIN falken.teams tb ON tb.id = ps.team_b_id
        LEFT JOIN falken.teams tw ON tw.id = ps.winner_team_id
        WHERE ta.name = 'Heilbronner Falken' OR tb.name = 'Heilbronner Falken'
        ORDER BY s.label DESC
    """):
        cid = "po_" + r["label"].replace("/", "_") + "_" + r["round"][:15].lower().replace(" ", "").replace("-", "")
        checks.append({
            "id": cid,
            "description": f"PO {r['label']} {r['round']}: {r['team_a']} {r['wins_a']}:{r['wins_b']} {r['team_b']}" +
                           (f" → {r['winner']}" if r["winner"] else ""),
            "source": "playoff_series + eishockey-statistiken",
            "query": f"SELECT ps.wins_a, ps.wins_b FROM falken.playoff_series ps "
                     f"JOIN falken.seasons s ON s.id=ps.season_id "
                     f"JOIN falken.teams ta ON ta.id=ps.team_a_id "
                     f"JOIN falken.teams tb ON tb.id=ps.team_b_id "
                     f"WHERE s.label='{r['label']}' AND ps.round='{r['round']}' "
                     f"AND ta.name='{r['team_a']}' AND tb.name='{r['team_b']}'",
            "expected": [{"wins_a": r["wins_a"], "wins_b": r["wins_b"]}]
        })

    # =================================================================
    # E) TRAINER PRO SAISON
    # =================================================================
    for r in exec_sql("""
        SELECT DISTINCT EXTRACT(year FROM ct.start_date)::int AS yr, c.name
        FROM falken.coach_tenures ct
        JOIN falken.coaches c ON c.id = ct.coach_id
        JOIN falken.teams t ON t.id = ct.team_id
        WHERE t.name = 'Heilbronner Falken' AND ct.start_date >= '2010-01-01'
        ORDER BY yr DESC
    """):
        cid = f"coach_{r['yr']}_{r['name'].replace(' ', '_').lower()[:25]}"
        checks.append({
            "id": cid,
            "description": f"Trainer in Saison {r['yr']}/{(r['yr']+1)%100:02d}: {r['name']}",
            "source": "coach_tenures + eishockey-statistiken",
            "query": f"SELECT COUNT(*) AS n FROM falken.coach_tenures ct "
                     f"JOIN falken.coaches c ON c.id=ct.coach_id "
                     f"JOIN falken.teams t ON t.id=ct.team_id "
                     f"WHERE t.name='Heilbronner Falken' AND c.name='{r['name']}' "
                     f"AND EXTRACT(year FROM ct.start_date) = {r['yr']}",
            "expected": [{"n": 1}]
        })

    return checks


if __name__ == "__main__":
    checks = generate()
    print(f"# AUTO-GENERATED Ground Truth — {len(checks)} checks", file=sys.stderr)
    print(yaml.dump(checks, allow_unicode=True, sort_keys=False))
