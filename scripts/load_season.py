"""Lädt eine beliebige Saison (Spielplan + Tabelle) aus hockeydata.

Ersetzt das fest verdrahtete `bootstrap_current_season.py`: divisionIds ändern
sich jede Saison, also nimmt dieses Skript sie als Argument — oder findet sie
selbst über `GetDivisionInfo`.

    # Divisionen einer Saison anzeigen (nichts schreiben):
    python3 scripts/load_season.py --discover 2026/27

    # Saison laden:
    python3 scripts/load_season.py --season 2026/27 --league "Oberliga Süd" --division 21614

Spiele ohne Ergebnis (Spielplan der kommenden Saison) werden mit NULL-Score
geladen — damit beantwortet die KB auch "Wann spielen die Falken gegen X?".
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.ingestion.hockeydata_client import HockeydataClient  # noqa: E402
from falken_kb.ingestion.loaders import (  # noqa: E402
    upsert_games_from_schedule,
    upsert_season,
    upsert_team_seasons_from_standings,
)
from falken_kb.logging_setup import setup_logging  # noqa: E402

LEAGUE_IDS = {"oberliga": 150}
TIER_BY_LEAGUE = {"Oberliga Süd": 3, "Oberliga Nord": 3, "DEL2": 2}


async def discover(season_label: str, league_id: int) -> None:
    """Zeigt Saison- und Division-IDs — der Handgriff zum Saisonstart."""
    async with HockeydataClient() as c:
        seasons = await c.get_seasons(league_id)
        match = [s for s in seasons if season_label in (s.get("seasonName") or "")]
        if not match:
            print(f"Keine Saison '{season_label}' in league {league_id}.")
            print("Verfügbar:", [s.get("seasonName") for s in seasons])
            return
        season_id = match[0]["seasonId"]
        print(f"Saison {season_label}: seasonId={season_id}")
        info = await c.get_division_info(season_id, league_id)
        teams = {t["id"]: t.get("longname") for t in info.get("teams", [])}
        for d in info.get("divisions", []):
            n = len(d.get("teams") or [])
            flag = "✓" if d.get("isCalculated") else "·"
            print(f"  {flag} divisionId={d['id']:6} {d['divisionName']:32} {n:2} Teams")
            if any("Heilbronn" in (teams.get(t) or "") for t in (d.get("teams") or [])):
                hits = [teams[t] for t in d["teams"] if "Heilbronn" in (teams.get(t) or "")]
                print(f"      → enthält {', '.join(hits)}")


async def load(season_label: str, league: str, division_id: int, league_id: int) -> None:
    tier = TIER_BY_LEAGUE.get(league, 3)
    async with HockeydataClient() as c:
        seasons = await c.get_seasons(league_id)
        match = [s for s in seasons if season_label in (s.get("seasonName") or "")]
        season_hd_id = match[0]["seasonId"] if match else division_id

        season_uuid = upsert_season(season_label, league, tier, season_hd_id)
        print(f"Saison {season_label} / {league} (uuid={season_uuid[:8]}…, hd={season_hd_id})")

        schedule = await c.get_schedule(division_id)
        played = sum(1 for g in schedule if g.get("homeTeamScore") is not None)
        n_games = upsert_games_from_schedule(season_uuid, schedule, game_type="regular")
        print(f"  Spielplan (div={division_id}): {n_games} Spiele verarbeitet "
              f"({played} mit Ergebnis, {len(schedule) - played} noch offen)")

        try:
            standings = await c.get_standings(division_id)
            n_teams = upsert_team_seasons_from_standings(season_uuid, standings)
            print(f"  Tabelle: {n_teams} Teams")
        except Exception as e:
            print(f"  Tabelle: noch nicht verfügbar ({str(e)[:80]})")

    print("\nDanach empfohlen: python3 scripts/merge_known_duplicates.py "
          "(neue Team-Schreibweisen zusammenführen)")


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", metavar="SAISON", help="nur Divisionen anzeigen, z.B. 2026/27")
    ap.add_argument("--season", help="Saison-Label, z.B. 2026/27")
    ap.add_argument("--league", default="Oberliga Süd")
    ap.add_argument("--division", type=int, help="divisionId aus --discover")
    ap.add_argument("--league-id", type=int, default=LEAGUE_IDS["oberliga"])
    args = ap.parse_args()

    if args.discover:
        asyncio.run(discover(args.discover, args.league_id))
        return
    if not (args.season and args.division):
        ap.error("--season und --division nötig (oder --discover benutzen)")
    asyncio.run(load(args.season, args.league, args.division, args.league_id))


if __name__ == "__main__":
    main()
