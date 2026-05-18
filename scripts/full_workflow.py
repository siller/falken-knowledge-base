"""Master-Workflow: nach jedem Daten-Load automatisch durchlaufen.

1. Team-Dedup (merge known duplicates)
2. Auto-Standings aus games (für neue Saisons)
3. Ground-Truth-Validation (alle 188 Tests)
4. Konsistenz-Audit (4 Checks)

Aufruf nach jedem Load:
    python3 scripts/full_workflow.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_script(name: str) -> int:
    p = subprocess.run(
        ["python3", str(ROOT / "scripts" / name)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    print(p.stdout[-2000:] if p.stdout else "")
    if p.stderr:
        print("STDERR:", p.stderr[-1000:], file=sys.stderr)
    return p.returncode


def main() -> None:
    print("=" * 60)
    print("FALKEN KB — FULL WORKFLOW")
    print("=" * 60)

    print("\n## 1. Team-Dedup (bekannte Duplikate mergen)")
    run_script("merge_known_duplicates.py")

    print("\n## 2. Auto-Standings aus games berechnen")
    run_script("compute_standings_from_games.py")

    print("\n## 3. Liga-Korrektur (Playoff-Spiele in richtige Liga)")
    run_script("fix_playoff_league_assignment.py")

    print("\n## 4. Saisons-Metadata (Source-IDs, OL-Rename)")
    run_script("fix_seasons_metadata.py")

    print("\n## 5. Ground-Truth-Validation (188 Tests)")
    run_script("run_all_ground_truth.py")

    print("\n## 6. Auto-Ground-Truth neu generieren (für nächsten Run)")
    res = subprocess.run(
        ["python3", str(ROOT / "scripts" / "generate_ground_truth.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    (ROOT / "tests" / "ground_truth_auto.yaml").write_text(res.stdout)
    print("  ✓ ground_truth_auto.yaml aktualisiert")

    print("\n=== WORKFLOW DONE ===")


if __name__ == "__main__":
    main()
