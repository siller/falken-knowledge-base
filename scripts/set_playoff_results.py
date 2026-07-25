"""Füllt `team_seasons.playoff_result` für die Falken.

WHY: Nach dem Playoff-Backfill stehen zwar die Serien in `playoff_series`, aber
`team_seasons.playoff_result` blieb für 2023/24-2025/26 leer. Genau dieses Feld
beantwortet aber Fragen wie "Wie weit kamen die Falken 2024/25?".

Ableitung: tiefste erreichte Runde aus `playoff_series`; Finale gewonnen → "Meister".
Sonderfälle (kein Playoff-Antritt) über OVERRIDES.

Idempotent: überschreibt nur leere Werte, außer --force.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, supabase
from falken_kb.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Reihenfolge = "Tiefe" der Runde. Höher = weiter gekommen.
ROUND_DEPTH = {
    "Pre Play-Off": 1,
    "Achtelfinale": 2,
    "Achtefinale": 2,  # Tippfehler-Variante in Altdaten
    "Playoff": 2,
    "Viertelfinale": 3,
    "Halbfinale": 4,
    "Spiel um Pl.3": 4,
    "Spiel um Pl.5": 3,
    "Finale": 5,
}

# Saisons, die sich nicht aus playoff_series ableiten lassen.
OVERRIDES: dict[str, str] = {
    # Insolvenzantrag im Januar 2026; die Falken verzichteten trotz Platz 5 in
    # der Oberliga Süd auf die Playoff-Teilnahme, die Saison endete am 27.02.2026.
    "2025/26": "Nicht teilgenommen (Insolvenz)",
}


def falken_id() -> str:
    return exec_sql("SELECT id FROM teams WHERE name='Heilbronner Falken'")[0]["id"]


def derive_from_series(season_label: str, falken_uuid: str) -> str | None:
    rows = exec_sql(f"""
        SELECT ps.round, ps.team_a_id, ps.team_b_id, ps.winner_team_id, ps.wins_a, ps.wins_b
        FROM playoff_series ps
        JOIN seasons s ON s.id = ps.season_id
        WHERE s.label = '{season_label}'
          AND (ps.team_a_id = '{falken_uuid}' OR ps.team_b_id = '{falken_uuid}')
    """)
    # Serien ohne gespielte Partie (0:0, kein Sieger) zählen nicht: das ist der
    # Fall 2019/20, wo die DEL2-Playoffs wegen Corona vor Serienbeginn abgesagt
    # wurden. Daraus "Viertelfinale erreicht" abzuleiten wäre falsch.
    rows = [r for r in rows if (r["wins_a"] or 0) + (r["wins_b"] or 0) > 0]
    if not rows:
        return None
    deepest = max(rows, key=lambda r: ROUND_DEPTH.get(r["round"], 0))
    if deepest["round"] == "Finale" and deepest["winner_team_id"] == falken_uuid:
        return "Meister"
    return deepest["round"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="auch belegte Werte überschreiben")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fid = falken_id()
    rows = exec_sql(f"""
        SELECT s.label, s.league, ts.season_id, ts.playoff_result, ts.final_rank
        FROM team_seasons ts
        JOIN seasons s ON s.id = ts.season_id
        WHERE ts.team_id = '{fid}'
        ORDER BY s.label DESC
    """)

    updated = 0
    for r in rows:
        current = (r["playoff_result"] or "").strip()
        if current and current != "---" and not args.force:
            continue
        new = OVERRIDES.get(r["label"]) or derive_from_series(r["label"], fid)
        if not new or new == current:
            continue
        print(f"  {r['label']} ({r['league']}): '{current}' → '{new}'")
        if not args.dry_run:
            supabase().table("falken_team_seasons").update(
                {"playoff_result": new}
            ).eq("team_id", fid).eq("season_id", r["season_id"]).execute()
        updated += 1

    print(f"\n{updated} Saisons aktualisiert{' (dry-run)' if args.dry_run else ''}.")


if __name__ == "__main__":
    main()
