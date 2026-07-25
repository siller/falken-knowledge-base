"""Korrigiert die Trainer-Historie 2024/25 – 2026/27.

Befund (Web-Recherche + EliteProspects-Staff-History, 25.07.2026):
  * Der Trainer heißt **Frank** Petrozza, nicht "Francesco" — in Phase 9 wurde
    der Vorname geraten und nie geprüft.
  * Petrozza betreute die Falken bis 2024/25; im Februar 2025 wurde bekannt,
    dass er nicht verlängert.
  * 2025/26 übernahm **Niko Eronen** (vorgestellt August 2025). In der DB stand
    fälschlich wieder Petrozza — ebenfalls eine Phase-9-Annahme.
  * 2026/27 übernimmt **Jason O'Leary**; Steffen Ziesche hatte zugesagt, trat
    die Stelle aber nicht an.

Idempotent: bestehende Einträge werden erkannt und nicht dupliziert.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, rpc, supabase  # noqa: E402
from falken_kb.logging_setup import setup_logging  # noqa: E402

FALKEN_TEAM = "Heilbronner Falken"

# (Trainer, Rolle, Saisonstart, Saisonende, Quelle)
TENURES = [
    ("Niko Eronen", "Headcoach", "2025-08-01", "2026-05-31", "hockeyweb.de/heilbronner-falken.de"),
    ("Jason O'Leary", "Headcoach", "2026-08-01", "2027-05-31", "heilbronner-falken.de/stimme.de"),
]

# Falsche Tenure-Einträge, die ersetzt werden (Trainer, start_date)
DELETE_TENURES = [
    ("Francesco Petrozza", "2025-09-01"),  # 25/26 war Eronen
]


def main() -> None:
    setup_logging()
    team_id = exec_sql(f"SELECT id FROM teams WHERE name = '{FALKEN_TEAM}'")[0]["id"]

    # 1. Vorname korrigieren
    wrong = exec_sql("SELECT id, name FROM coaches WHERE name = 'Francesco Petrozza'")
    if wrong:
        existing_right = exec_sql("SELECT id FROM coaches WHERE name = 'Frank Petrozza'")
        if existing_right:
            print("  'Frank Petrozza' existiert bereits — Tenures umhängen")
            supabase().table("falken_coach_tenures").update(
                {"coach_id": existing_right[0]["id"]}
            ).eq("coach_id", wrong[0]["id"]).execute()
            supabase().table("falken_coaches").delete().eq("id", wrong[0]["id"]).execute()
        else:
            supabase().table("falken_coaches").update(
                {"name": "Frank Petrozza", "first_name": "Frank", "last_name": "Petrozza"}
            ).eq("id", wrong[0]["id"]).execute()
            print("  Umbenannt: 'Francesco Petrozza' → 'Frank Petrozza'")

    # 2. Falsche Tenures entfernen
    for name, start in DELETE_TENURES:
        rows = exec_sql(
            "SELECT ct.id FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id "
            f"WHERE c.name IN ('{name}', 'Frank Petrozza') AND ct.start_date = '{start}'"
        )
        for r in rows:
            supabase().table("falken_coach_tenures").delete().eq("id", r["id"]).execute()
            print(f"  Entfernt: Tenure ab {start} ({name})")

    # 3. Korrekte Tenures setzen
    for name, role, start, end, source in TENURES:
        coach_id = rpc("upsert_coach", {"p_name": name})
        rpc("upsert_coach_tenure", {
            "p_coach_id": coach_id,
            "p_team_id": team_id,
            "p_role": role,
            "p_start": start,
            "p_end": end,
            "p_source": source,
        })
        print(f"  Gesetzt: {name} ({role}) {start} – {end}")

    print("\nTrainer-Historie jetzt:")
    for r in exec_sql(
        "SELECT c.name, ct.start_date::text s, ct.end_date::text e FROM coach_tenures ct "
        "JOIN coaches c ON c.id = ct.coach_id ORDER BY ct.start_date DESC LIMIT 6"
    ):
        print(f"  {r['s']} – {r['e']}  {r['name']}")


if __name__ == "__main__":
    main()
