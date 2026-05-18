"""Validation-Framework für die Wissensbasis.

Drei Ebenen:
1. CONSISTENCY CHECKS — Schema-interne Plausibilität (z.B. W+L+OT == GP)
2. COVERAGE REPORT — was haben wir, was fehlt
3. GROUND TRUTH TESTS — Vergleich mit manuell verifizierten Fakten (tests/ground_truth.yaml)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .db import exec_sql

logger = logging.getLogger(__name__)

GROUND_TRUTH_FILE = Path(__file__).resolve().parent.parent / "tests" / "ground_truth.yaml"


# ============================================================================
# 1. CONSISTENCY CHECKS — schemainterne Plausibilität
# ============================================================================

def check_team_seasons_arithmetic() -> list[dict[str, Any]]:
    """In team_seasons sollte gilt: wins + losses + ot_wins + ot_losses ≤ games_played."""
    bad = exec_sql("""
        SELECT t.name, s.label, s.league,
               ts.games_played, ts.wins, ts.losses, ts.ot_wins, ts.ot_losses,
               (COALESCE(ts.wins,0)+COALESCE(ts.losses,0)+COALESCE(ts.ot_wins,0)+COALESCE(ts.ot_losses,0)) AS sum_wl
        FROM falken.team_seasons ts
        JOIN falken.teams t ON t.id = ts.team_id
        JOIN falken.seasons s ON s.id = ts.season_id
        WHERE ts.games_played IS NOT NULL
          AND (COALESCE(ts.wins,0)+COALESCE(ts.losses,0)+COALESCE(ts.ot_wins,0)+COALESCE(ts.ot_losses,0))
              != ts.games_played
        ORDER BY s.label DESC, t.name
        LIMIT 30
    """)
    return bad


def check_player_stats_consistency() -> list[dict[str, Any]]:
    """In player_stats: goals + assists muss == points sein (das ist auch der STORED GENERATED)."""
    bad = exec_sql("""
        SELECT p.name, s.label,
               pst.goals, pst.assists, pst.points
        FROM falken.player_stats pst
        JOIN falken.player_seasons ps ON ps.id = pst.player_season_id
        JOIN falken.players p ON p.id = ps.player_id
        JOIN falken.seasons s ON s.id = ps.season_id
        WHERE pst.points != (COALESCE(pst.goals,0) + COALESCE(pst.assists,0))
        LIMIT 30
    """)
    return bad


def check_games_date_in_season_window() -> list[dict[str, Any]]:
    """Spieldatum sollte zwischen August der Saison und Mai des Folgejahres liegen.

    Testspiele/Cups starten oft im August (Vorbereitungsphase). Nur Juni+Juli
    sollten frei sein. Friendlies werden zusätzlich aus dem Check ausgenommen,
    weil sie auch außerhalb der Saison stattfinden können.
    """
    bad = exec_sql("""
        SELECT g.date::date AS date, s.label, g.game_type, ht.name AS home, at.name AS away
        FROM falken.games g
        JOIN falken.seasons s ON s.id = g.season_id
        JOIN falken.teams ht ON ht.id = g.home_team_id
        JOIN falken.teams at ON at.id = g.away_team_id
        WHERE g.date IS NOT NULL
          AND g.game_type IN ('regular', 'playoff', 'playdown')
          AND (
            EXTRACT(year FROM g.date)::int NOT IN (
                (split_part(s.label, '/', 1))::int,
                (split_part(s.label, '/', 1))::int + 1
            )
            OR (EXTRACT(month FROM g.date) BETWEEN 6 AND 7)
          )
        LIMIT 30
    """)
    return bad


def check_team_dedup_remaining() -> list[dict[str, Any]]:
    """Suche verbleibende potenzielle Team-Duplikate (fuzzy)."""
    from .ingestion.dedup import find_duplicate_teams_in_db
    return find_duplicate_teams_in_db(min_score=88)


def run_consistency_checks() -> dict[str, list]:
    return {
        "team_seasons_arithmetic": check_team_seasons_arithmetic(),
        "player_stats_consistency": check_player_stats_consistency(),
        "games_date_in_season_window": check_games_date_in_season_window(),
        "team_dedup_remaining": check_team_dedup_remaining(),
    }


# ============================================================================
# 2. COVERAGE REPORT — was haben wir, was fehlt
# ============================================================================

def coverage_falken_games_per_season() -> list[dict[str, Any]]:
    """Falken-Spiele pro Saison + Game-Type."""
    return exec_sql("""
        SELECT s.label, s.league,
               SUM(CASE WHEN g.game_type='regular' THEN 1 ELSE 0 END) AS hauptrunde,
               SUM(CASE WHEN g.game_type='playoff' THEN 1 ELSE 0 END) AS playoff,
               SUM(CASE WHEN g.game_type='playdown' THEN 1 ELSE 0 END) AS playdown,
               SUM(CASE WHEN g.game_type='friendly' THEN 1 ELSE 0 END) AS friendly,
               SUM(CASE WHEN g.game_type='other' THEN 1 ELSE 0 END) AS other,
               COUNT(*) AS total
        FROM falken.games g
        JOIN falken.seasons s ON s.id = g.season_id
        JOIN falken.teams ht ON ht.id = g.home_team_id
        JOIN falken.teams at ON at.id = g.away_team_id
        WHERE (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
        GROUP BY s.label, s.league
        ORDER BY s.label DESC
    """)


def coverage_player_stats_per_season() -> list[dict[str, Any]]:
    return exec_sql("""
        SELECT s.label,
               COUNT(DISTINCT ps.player_id) AS n_players,
               SUM(CASE WHEN pst.points IS NOT NULL THEN 1 ELSE 0 END) AS with_stats
        FROM falken.seasons s
        JOIN falken.player_seasons ps ON ps.season_id = s.id
        JOIN falken.teams t ON t.id = ps.team_id
        LEFT JOIN falken.player_stats pst ON pst.player_season_id = ps.id
        WHERE t.name = 'Heilbronner Falken'
        GROUP BY s.label
        ORDER BY s.label DESC
    """)


def coverage_team_seasons_per_season() -> list[dict[str, Any]]:
    return exec_sql("""
        SELECT s.label, s.league, ts.final_rank, ts.points, ts.playoff_result
        FROM falken.team_seasons ts
        JOIN falken.seasons s ON s.id = ts.season_id
        JOIN falken.teams t ON t.id = ts.team_id
        WHERE t.name = 'Heilbronner Falken'
        ORDER BY s.label DESC
    """)


def expected_hauptrunde_count(season_label: str, league: str) -> int | None:
    """Erwartete Hauptrunden-Spielanzahl pro Saison/Liga (verifiziert via del-2.org Modi-Doku).

    DEL2:
    - 2017/18: 14 Teams, **48 Spiele/Team** (3-fach Hin/Rück)
    - 2018/19-2019/20, 2021/22+: 14 Teams, **52 Spiele/Team** (4-fach Hin/Rück)
    - 2020/21: Corona-verkürzt, 49 Spiele
    - 2014/15-2016/17: 14 Teams, 52 Spiele

    Oberliga Süd:
    - 2024/25: **13 Teams, 48 Spiele/Team** (4-fach Hin/Rück bei 13 Teams)
    - 2025/26: 14 Teams, 52 Spiele/Team
    """
    yr = int(season_label.split("/")[0])
    if league == "DEL2":
        if yr == 2017: return 48  # bestätigter Modus
        if yr == 2020: return 49  # Corona
        if 2018 <= yr <= 2023: return 52
        if 2014 <= yr <= 2016: return 52
    if league == "Oberliga Süd":
        if yr == 2024: return 48  # 13 Teams
        if yr >= 2025: return 52  # 14 Teams
    return None


def coverage_gaps() -> dict[str, list]:
    """Findet Saisons wo erwartete vs tatsächliche Spielzahl divergiert."""
    games = coverage_falken_games_per_season()
    gaps = []
    for r in games:
        expected = expected_hauptrunde_count(r["label"], r["league"])
        if expected is not None and r["hauptrunde"] != expected:
            gaps.append({
                "season": r["label"],
                "league": r["league"],
                "expected_hauptrunde": expected,
                "actual_hauptrunde": r["hauptrunde"],
                "diff": expected - r["hauptrunde"],
            })
    return gaps


# ============================================================================
# 3. GROUND TRUTH TESTS — gegen manuell verifizierte Fakten
# ============================================================================

def run_ground_truth() -> list[dict[str, Any]]:
    """Lädt tests/ground_truth.yaml und prüft jedes Item gegen die DB."""
    if not GROUND_TRUTH_FILE.exists():
        return [{"error": f"Ground-Truth-Datei fehlt: {GROUND_TRUTH_FILE}"}]
    checks = yaml.safe_load(GROUND_TRUTH_FILE.read_text())
    results = []
    for c in checks:
        try:
            actual = exec_sql(c["query"].strip())
            ok = _matches(actual, c["expected"])
            results.append({
                "id": c["id"],
                "description": c["description"],
                "source": c.get("source", "?"),
                "pass": ok,
                "actual": actual,
                "expected": c["expected"],
            })
        except Exception as e:
            results.append({
                "id": c["id"],
                "description": c["description"],
                "pass": False,
                "error": str(e)[:200],
            })
    return results


def _matches(actual: list[dict], expected: list[dict]) -> bool:
    """Vergleicht actual vs expected: jede Zeile in expected muss in actual vorkommen."""
    if not expected:
        return True
    if not actual:
        return False
    for exp_row in expected:
        found = False
        for act_row in actual:
            if all(act_row.get(k) == v for k, v in exp_row.items()):
                found = True
                break
        if not found:
            return False
    return True


# ============================================================================
# MAIN — Audit-Report
# ============================================================================

def full_audit() -> None:
    print("=" * 70)
    print("FALKEN KNOWLEDGE BASE — AUDIT REPORT")
    print("=" * 70)

    print("\n## 1. CONSISTENCY CHECKS")
    cc = run_consistency_checks()
    for name, bad in cc.items():
        status = f"✓ OK" if not bad else f"✗ {len(bad)} Verletzungen"
        print(f"  {name:<35} {status}")
        for b in bad[:5]:
            print(f"      {b}")

    print("\n## 2. COVERAGE REPORT — Falken-Spiele pro Saison")
    for r in coverage_falken_games_per_season():
        print(f"  {r['label']:<8} {r['league'][:14]:<14} HR={r['hauptrunde']:>3} PO={r['playoff']:>2} PD={r['playdown']:>2} FR={r['friendly']:>2} OTH={r['other']:>2} TOTAL={r['total']:>3}")

    print("\n## 3. COVERAGE GAPS — fehlende/verminderte Spielzahlen")
    gaps = coverage_gaps()
    if not gaps:
        print("  ✓ Keine Lücken über Plan-Schwellen")
    for g in gaps:
        print(f"  ⚠ {g['season']} {g['league']}: erwartet {g['expected_hauptrunde']} HR, haben {g['actual_hauptrunde']} (Diff: {g['diff']})")

    print("\n## 4. COVERAGE — Player-Stats")
    for r in coverage_player_stats_per_season():
        print(f"  {r['label']}: {r['n_players']} Spieler, {r['with_stats']} mit Stats")

    print("\n## 5. GROUND TRUTH — manuell verifizierte Fakten")
    gt = run_ground_truth()
    passed = sum(1 for r in gt if r.get("pass"))
    failed = sum(1 for r in gt if not r.get("pass"))
    print(f"\n  {passed}/{len(gt)} PASS, {failed} FAIL")
    for r in gt:
        marker = "✓" if r.get("pass") else "✗"
        print(f"\n  {marker} [{r['id']}] {r['description']}")
        if not r.get("pass"):
            print(f"      ERWARTET: {r.get('expected')}")
            print(f"      AKTUELL:  {r.get('actual')}")
            if r.get("error"):
                print(f"      FEHLER:   {r['error']}")


if __name__ == "__main__":
    full_audit()
