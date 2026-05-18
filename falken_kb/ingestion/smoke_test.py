"""Smoke-Test: ruft alle wichtigen hockeydata-Endpoints einmal ab.

Aufruf: `python3 -m falken_kb.ingestion.smoke_test`
"""
from __future__ import annotations

import asyncio
import logging

from ..logging_setup import setup_logging
from .hockeydata_client import HockeydataClient, HockeydataError, HockeydataNotCalculated

logger = logging.getLogger(__name__)

# Bekannte IDs
DEL2_LEAGUE_ID = 301
OBERLIGA_LEAGUE_ID = 150
DEL2_SEASON_2022_23 = 10914   # Abstiegssaison
DEL2_SEASON_2024_25 = 16549   # aktuelle DEL2-Saison
SAMPLE_GAME_ID = "6c137e7d-ee82-4e94-8493-54e5201a14c9"  # aus User-Beispiel


async def run() -> None:
    setup_logging()
    async with HockeydataClient() as c:
        # ---- Discovery ----
        sports = await c.get_sports()
        logger.info("GetSports: %d sport(s) — %s", len(sports), sports)

        leagues = await c.get_leagues()
        del2 = next((l for l in leagues if l["leagueId"] == DEL2_LEAGUE_ID), None)
        oberliga = next((l for l in leagues if l["leagueId"] == OBERLIGA_LEAGUE_ID), None)
        logger.info("GetLeagues: %d total. DEL2=%s, Oberliga=%s", len(leagues), del2, oberliga)

        del2_seasons = await c.get_seasons(DEL2_LEAGUE_ID)
        logger.info("DEL2 seasons via API: %s", [s["seasonName"] for s in del2_seasons])

        oberliga_seasons = await c.get_seasons(OBERLIGA_LEAGUE_ID)
        logger.info("DEB-Oberliga seasons via API: %s", [s["seasonName"] for s in oberliga_seasons])

        # ---- Division-Info (Hierarchie) ----
        try:
            div_info = await c.get_division_info(DEL2_SEASON_2024_25, DEL2_LEAGUE_ID)
            sub_divs = div_info.get("divisions", [])
            teams = div_info.get("teams", [])
            logger.info("Division-Info 2024/25: sub-divisions=%d, teams=%d", len(sub_divs), len(teams))
        except HockeydataError as e:
            logger.warning("DivisionInfo fehlgeschlagen: %s", e)

        # ---- Per-Spiel-Daten (das große Geschütz) ----
        try:
            report = await c.get_game_report(SAMPLE_GAME_ID)
            keys = list(report.keys())
            home_goals = len(report.get("homeGoals", []))
            away_goals = len(report.get("awayGoals", []))
            home_players = len(report.get("homeFieldPlayers", []))
            actions = len(report.get("gameActions", []))
            logger.info(
                "GetGameReport (%s): keys=%s, home_goals=%d, away_goals=%d, home_players=%d, gameActions=%d",
                SAMPLE_GAME_ID,
                len(keys),
                home_goals,
                away_goals,
                home_players,
                actions,
            )
        except HockeydataError as e:
            logger.warning("GameReport fehlgeschlagen: %s", e)

        # ---- Standings einer berechneten Division ----
        # Die Saison-Wrapper-IDs liefern "Not calculated", wir versuchen es zur Demo trotzdem
        try:
            teams = await c.get_standings(DEL2_SEASON_2022_23)
            logger.info("Standings 2022/23 (Wrapper): %d Teams", len(teams))
        except HockeydataNotCalculated as e:
            logger.info("Standings 2022/23 (Wrapper) erwartungsgemäß: %s", e)

        logger.info("Smoke-Test fertig.")


if __name__ == "__main__":
    asyncio.run(run())
