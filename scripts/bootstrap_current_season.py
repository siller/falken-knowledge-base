"""Lädt aktuelle Saison komplett in die DB.

Aktuell: Heilbronner Falken spielen in Oberliga Süd (divisionId 18655, teamId 47011).
DEL2-Erfassung kommt später, wenn die korrekte divisionId verifiziert ist
(deb-online.live exposed nur Oberliga/Jugend-IDs; del-2.org rendert ohne hockeydata-Widgets).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.logging_setup import setup_logging  # noqa: E402
from falken_kb.ingestion.hockeydata_client import HockeydataClient  # noqa: E402
from falken_kb.ingestion.loaders import (  # noqa: E402
    upsert_games_from_schedule,
    upsert_season,
    upsert_team_seasons_from_standings,
)


# Verifizierte Werte (Stand 2026-05-17)
OBERLIGA_LEAGUE_ID = 150
OBERLIGA_SUED_DIV_25_26 = 18655    # Oberliga Süd 2025/26 — Falken spielen hier
FALKEN_TEAM_ID = 47011


async def load_oberliga_current() -> None:
    """Lädt aktuelle Oberliga-Süd-Saison."""
    print("\n=== Oberliga Süd (aktuelle Saison) ===")
    async with HockeydataClient() as c:
        seasons = await c.get_seasons(OBERLIGA_LEAGUE_ID)
        # nimm die jüngste Saison
        current = seasons[-1]
        season_label = current["seasonName"].replace("Saison ", "")
        season_uuid = upsert_season(season_label, "Oberliga Süd", 3, current["seasonId"])
        print(f"  Saison: {season_label} (uuid={season_uuid[:8]}…)")

        # Tabelle
        standings = await c.get_standings(OBERLIGA_SUED_DIV_25_26)
        n_teams = upsert_team_seasons_from_standings(season_uuid, standings)
        print(f"  Tabelle (div={OBERLIGA_SUED_DIV_25_26}): {n_teams} Teams geladen")

        # Spielplan komplett
        schedule = await c.get_schedule(OBERLIGA_SUED_DIV_25_26)
        n_games = upsert_games_from_schedule(season_uuid, schedule, game_type="regular")
        print(f"  Spielplan: {n_games} neue Spiele aus {len(schedule)} im Schedule")


async def main() -> None:
    setup_logging()
    await load_oberliga_current()
    print("\nFertig. Test gleich via Streamlit oder direkt mit:")
    print("  python3 -c \"from falken_kb.db import exec_sql; print(exec_sql('SELECT * FROM falken.season_standings LIMIT 20'))\"")


if __name__ == "__main__":
    asyncio.run(main())
