"""Räumt Phantom-Ergebnisse auf, die aus hockeydata-Rohdaten entstanden sind.

Zwei Muster, beide aus derselben Ursache: die API liefert für nicht gespielte
Partien `homeTeamScore=0/awayTeamScore=0` statt `null` (erkennbar nur an
`gameStatus=0`) und legt Tabellenzeilen mit 0 Spielen und Rang 1 an.

1. **0:0-Spiele** → Score auf NULL. Ein echtes 0:0 kann es in DEL2/Oberliga
   nicht geben: Unentschieden werden per Overtime/Penaltyschießen entschieden,
   der Sieger bekommt ein Tor gutgeschrieben. Jedes 0:0 in der DB ist also eine
   angesetzte, nicht gespielte Partie (meist Testspiele im August).
2. **Tabellenzeilen ohne Spiel** → `final_rank` auf NULL, sonst steht jedes Team
   der kommenden Saison auf "Platz 1".

Der Loader (`ingestion/loaders.py`) erzeugt beides seit dem gameStatus-Fix nicht
mehr; dieses Skript repariert den Altbestand und ist beliebig oft ausführbar.

    python3 scripts/fix_phantom_results.py --dry-run
    python3 scripts/fix_phantom_results.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, supabase  # noqa: E402
from falken_kb.logging_setup import setup_logging  # noqa: E402


def fix_zero_zero_games(dry_run: bool) -> int:
    rows = exec_sql("SELECT id FROM games WHERE home_score = 0 AND away_score = 0")
    print(f"  0:0-Spiele: {len(rows)}")
    if not rows or dry_run:
        return len(rows)
    for chunk_start in range(0, len(rows), 100):
        ids = [r["id"] for r in rows[chunk_start:chunk_start + 100]]
        supabase().table("falken_games").update(
            {"home_score": None, "away_score": None}
        ).in_("id", ids).execute()
    return len(rows)


def fix_phantom_standings(dry_run: bool) -> int:
    # WICHTIG: `games_played = 0` und `games_played IS NULL` sind NICHT dasselbe.
    # 0 kommt aus einer hockeydata-Tabelle vor dem ersten Spieltag (Phantom).
    # NULL steht bei den historischen Saisons vor 2013, für die es nur Rang und
    # Punkte gibt, keine Spielzahl — deren Rang ist echt und muss bleiben.
    rows = exec_sql("""
        SELECT ts.team_id, ts.season_id, s.label
        FROM team_seasons ts
        JOIN seasons s ON s.id = ts.season_id
        WHERE ts.games_played = 0
          AND (ts.final_rank IS NOT NULL OR ts.points IS NOT NULL)
    """)
    print(f"  Tabellenzeilen ohne gespieltes Spiel: {len(rows)}")
    if not rows or dry_run:
        return len(rows)
    for r in rows:
        # Auch Punkte/Siege auf NULL: eine 0 ist hier keine Leistung, sondern
        # "noch nicht gespielt". Als 0 gespeichert gewinnt die kommende Saison
        # sonst jede Frage nach der schlechtesten Saison.
        supabase().table("falken_team_seasons").update({
            "final_rank": None, "points": None, "wins": None, "losses": None,
            "ot_wins": None, "ot_losses": None, "goals_for": None, "goals_against": None,
        }).eq("team_id", r["team_id"]).eq("season_id", r["season_id"]).execute()
    return len(rows)


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("Phantom-Ergebnisse:" + (" (dry-run)" if args.dry_run else ""))
    g = fix_zero_zero_games(args.dry_run)
    t = fix_phantom_standings(args.dry_run)
    verb = "gefunden" if args.dry_run else "bereinigt"
    print(f"\n{g} Spiele + {t} Tabellenzeilen {verb}.")


if __name__ == "__main__":
    main()
