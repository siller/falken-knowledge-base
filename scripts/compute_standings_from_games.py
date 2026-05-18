"""Berechnet team_seasons-Einträge aus den vorhandenen games-Daten.

Sinnvoll für Saisons, bei denen wir Spiele aus del-2.org haben aber keine
gefetchte Standings-Tabelle (z.B. DEL2 23/24, 24/25, 25/26).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, rpc


def compute_for_season(season_id: str, season_label: str, league: str) -> int:
    """Berechnet aus games-Daten dieser Saison W/L/Points pro Team."""
    # OT-Regeln DEL2/Oberliga: regulärer Sieg = 3P, OT/SO-Sieg = 2P, OT/SO-Niederlage = 1P, Niederlage = 0P
    rows = exec_sql(f"""
        WITH game_results AS (
            SELECT
                CASE WHEN home_score > away_score THEN home_team_id
                     WHEN away_score > home_score THEN away_team_id
                END AS winner_id,
                CASE WHEN home_score > away_score THEN away_team_id
                     WHEN away_score > home_score THEN home_team_id
                END AS loser_id,
                overtime, shootout, home_team_id, away_team_id
            FROM falken.games
            WHERE season_id = '{season_id}'
              AND game_type = 'regular'
              AND home_score IS NOT NULL AND away_score IS NOT NULL
        ),
        team_stats AS (
            SELECT t.id AS team_id,
                   COUNT(*) AS gp,
                   SUM(CASE WHEN gr.winner_id = t.id AND NOT (gr.overtime OR gr.shootout) THEN 1 ELSE 0 END) AS wins_reg,
                   SUM(CASE WHEN gr.winner_id = t.id AND (gr.overtime OR gr.shootout) THEN 1 ELSE 0 END) AS wins_ot,
                   SUM(CASE WHEN gr.loser_id = t.id AND (gr.overtime OR gr.shootout) THEN 1 ELSE 0 END) AS losses_ot,
                   SUM(CASE WHEN gr.loser_id = t.id AND NOT (gr.overtime OR gr.shootout) THEN 1 ELSE 0 END) AS losses_reg
            FROM falken.teams t
            JOIN game_results gr ON gr.home_team_id = t.id OR gr.away_team_id = t.id
            GROUP BY t.id
        )
        SELECT team_id, gp, wins_reg, wins_ot, losses_reg, losses_ot,
               (wins_reg * 3 + wins_ot * 2 + losses_ot * 1) AS points
        FROM team_stats
        ORDER BY points DESC, wins_reg DESC
    """)

    # Compute goals_for / goals_against per team
    goals = exec_sql(f"""
        SELECT t.id AS team_id,
            SUM(CASE WHEN g.home_team_id = t.id THEN g.home_score
                     WHEN g.away_team_id = t.id THEN g.away_score ELSE 0 END) AS gf,
            SUM(CASE WHEN g.home_team_id = t.id THEN g.away_score
                     WHEN g.away_team_id = t.id THEN g.home_score ELSE 0 END) AS ga
        FROM falken.teams t
        JOIN falken.games g ON g.home_team_id = t.id OR g.away_team_id = t.id
        WHERE g.season_id = '{season_id}'
          AND g.game_type = 'regular'
          AND g.home_score IS NOT NULL AND g.away_score IS NOT NULL
        GROUP BY t.id
    """)
    goals_map = {r["team_id"]: (r["gf"], r["ga"]) for r in goals}

    n = 0
    for rank, r in enumerate(rows, start=1):
        gf, ga = goals_map.get(r["team_id"], (None, None))
        rpc("upsert_team_season_full", {
            "p_team_id": r["team_id"],
            "p_season_id": season_id,
            "p_rank": rank,
            "p_gp": r["gp"],
            "p_wins": r["wins_reg"],
            "p_losses": r["losses_reg"],
            "p_ot_wins": r["wins_ot"],
            "p_ot_losses": r["losses_ot"],
            "p_points": r["points"],
            "p_gf": gf,
            "p_ga": ga,
            "p_playoff_result": None,
            "p_source": f"computed_from_games:{league}:{season_label}",
        })
        n += 1
    return n


def main():
    # Saisons mit Games aber ohne (oder unvollständigen) team_seasons
    candidates = exec_sql("""
        SELECT s.id, s.label, s.league,
               (SELECT COUNT(*) FROM falken.games WHERE season_id = s.id AND game_type='regular') AS n_games,
               (SELECT COUNT(*) FROM falken.team_seasons WHERE season_id = s.id) AS n_ts
        FROM falken.seasons s
        WHERE EXISTS (SELECT 1 FROM falken.games WHERE season_id = s.id AND game_type='regular')
        ORDER BY s.label DESC
    """)

    for c in candidates:
        if c["n_games"] < 50:
            continue  # zu wenig Spiele für sinnvolle Standings
        if c["n_ts"] >= 10:
            print(f"  ⊘ {c['label']:<8} {c['league']:<15}: hat schon {c['n_ts']} team_seasons (skip)")
            continue
        n = compute_for_season(c["id"], c["label"], c["league"])
        print(f"  ✓ {c['label']:<8} {c['league']:<15}: {n} team_seasons aus {c['n_games']} games berechnet")


if __name__ == "__main__":
    main()
