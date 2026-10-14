"""Täglicher Sync — hält die Wissensbasis aktuell, ohne dass jemand dran denken muss.

WHY: Bis Juli 2026 lief jeder Load von Hand. Ergebnis: letztes Spiel in der DB war
vom 08.03.2026, letzter Artikel vom 13.05.2026 — die KB veraltete lautlos, während
die App weiter selbstbewusst antwortete. Dieses Skript ist der Gegenentwurf.

Schritte:
  1. News-RSS (heilbronner-falken.de)
  2. Web-News-Harvest über Tavily (Lokalpresse, deren RSS-Feeds tot sind)
  3. Spiele + Tabelle der laufenden Saison (nur wenn eine divisionId hinterlegt ist)
  4. Spielerstatistik der Falken in der laufenden Saison (hockeydata)
  5. Aktualität — der Lauf wird rot, wenn Ergebnisse oder Tabelle hängen

Alle Schritte sind idempotent und einzeln abschaltbar:
    python3 scripts/sync_daily.py                  # alles
    python3 scripts/sync_daily.py --skip-games     # nur News
    python3 scripts/sync_daily.py --news-days 7    # kleineres Zeitfenster
"""
from __future__ import annotations

import argparse
import logging
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql  # noqa: E402
from falken_kb.logging_setup import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)

# Laufende Saison. Die divisionId wechselt jede Saison und wird einmal ermittelt:
#   python3 scripts/load_season.py --discover 2027/28
# None → Spiel-Sync wird übersprungen.
CURRENT_SEASON_LABEL = "2026/27"
CURRENT_SEASON_LEAGUE = "Oberliga Süd"
CURRENT_SEASON_DIVISION_ID: int | None = 21614


def sync_news_rss() -> dict:
    from falken_kb.ingestion.scrapers.falken_news import backfill_all

    return backfill_all()


def sync_news_web(days: int) -> dict:
    from falken_kb.ingestion.scrapers.web_news import DEFAULT_QUERIES, harvest

    return harvest(DEFAULT_QUERIES, max_results=10, days=days)


def sync_preseason() -> dict:
    """Testspiele von der Vereinsseite — hockeydata kennt nur den Ligabetrieb.

    Der Verein meldet die Termine in Wellen nach, deshalb läuft das täglich mit.
    """
    from falken_kb.ingestion.scrapers.falken_preseason import harvest

    return harvest()


async def sync_games() -> dict:
    from falken_kb.ingestion.hockeydata_client import HockeydataClient
    from falken_kb.ingestion.loaders import (
        upsert_games_from_schedule,
        upsert_season,
        upsert_team_seasons_from_standings,
    )

    if CURRENT_SEASON_DIVISION_ID is None:
        return {"skipped": "keine divisionId für die laufende Saison hinterlegt"}

    season_uuid = upsert_season(
        CURRENT_SEASON_LABEL,
        CURRENT_SEASON_LEAGUE,
        league_tier=3,  # Oberliga; DEL2 wäre 2
        hockeydata_season_id=CURRENT_SEASON_DIVISION_ID,
    )
    async with HockeydataClient() as client:
        schedule = await client.get_schedule(CURRENT_SEASON_DIVISION_ID)
        games = upsert_games_from_schedule(season_uuid, schedule)
        standings = await client.get_standings(CURRENT_SEASON_DIVISION_ID)
        teams = upsert_team_seasons_from_standings(season_uuid, standings)

    # hockeydata legt neue Team-Schreibweisen an (2026/27: "Heilbronner EC Falken"
    # mit neuer teamId) — ohne Merge zerfällt die Vereinshistorie.
    import subprocess

    root = Path(__file__).resolve().parent.parent
    merged = subprocess.run(
        [sys.executable, str(root / "scripts" / "merge_known_duplicates.py")],
        capture_output=True, text=True, cwd=str(root),
    )
    tail = [ln for ln in merged.stdout.splitlines() if "Total:" in ln]
    return {"games": games, "team_seasons": teams, "dedup": tail[0] if tail else "ok"}


async def sync_skater_stats() -> dict:
    """Scorerliste der Falken — sonst kennt HORST nur die Vorsaison als "aktuell"."""
    from falken_kb.ingestion.hockeydata_client import HockeydataClient, HockeydataError
    from falken_kb.ingestion.loaders import (
        falken_team_ids,
        upsert_season,
        upsert_skater_stats_from_leaders,
        upsert_team,
    )

    if CURRENT_SEASON_DIVISION_ID is None:
        return {"skipped": "keine divisionId für die laufende Saison hinterlegt"}

    season_uuid = upsert_season(CURRENT_SEASON_LABEL, CURRENT_SEASON_LEAGUE, league_tier=3,
                                hockeydata_season_id=CURRENT_SEASON_DIVISION_ID)
    async with HockeydataClient() as client:
        tabelle = await client.get_standings(CURRENT_SEASON_DIVISION_ID)
        ids = falken_team_ids(tabelle)
        if not ids:
            raise RuntimeError("Falken nicht in der hockeydata-Tabelle gefunden")
        try:
            leaders = await client.get_leader_field_players(CURRENT_SEASON_DIVISION_ID)
        except HockeydataError:
            # Vor dem ersten Spieltag gibt es noch keine Scorerliste. Mitten in
            # der Saison ist derselbe Fehler dagegen ein echter Ausfall.
            if any(r.get("gamesPlayed") for r in tabelle if r.get("id") is not None and int(r["id"]) in ids):
                raise
            return {"skipped": "noch keine Scorerliste (Saison nicht gestartet)"}
    # Mit teamId — ohne sie überschriebe der Upsert die hockeydata-ID mit null.
    team_uuid = upsert_team("Heilbronner Falken", hockeydata_team_id=max(ids))
    return {"spieler": upsert_skater_stats_from_leaders(season_uuid, team_uuid, leaders, ids)}


def current_season_problems() -> list[str]:
    from falken_kb.ingestion.loaders import aktualitaets_probleme

    saison = f"(SELECT id FROM seasons WHERE label = '{CURRENT_SEASON_LABEL}' AND league = '{CURRENT_SEASON_LEAGUE}')"
    offen = exec_sql(
        f"SELECT count(*) c FROM games WHERE season_id = {saison} AND game_type <> 'friendly' "
        "AND home_score IS NULL AND date < now() - interval '2 days'"
    )[0]["c"]
    tabelle = exec_sql(
        "SELECT max(ts.games_played) FILTER (WHERE t.name = 'Heilbronner Falken') falken, "
        f"max(ts.games_played) liga FROM team_seasons ts JOIN teams t ON t.id = ts.team_id "
        f"WHERE ts.season_id = {saison}"
    )[0]
    return aktualitaets_probleme(offen, tabelle["falken"], tabelle["liga"])


def freshness_report() -> dict:
    return {
        # Nur gespielte Partien — angesetzte Spiele haben keinen Score und
        # würden die Aktualität sonst schönrechnen.
        "letztes_ergebnis": exec_sql(
            "SELECT max(date)::text v FROM games WHERE home_score IS NOT NULL"
        )[0]["v"],
        "naechstes_spiel": exec_sql(
            "SELECT min(date)::text v FROM games WHERE home_score IS NULL AND date > now()"
        )[0]["v"],
        "letzter_artikel": exec_sql("SELECT max(published_at)::text v FROM articles")[0]["v"],
        "artikel_gesamt": exec_sql("SELECT count(*) c FROM articles")[0]["c"],
        "spiele_gesamt": exec_sql("SELECT count(*) c FROM games")[0]["c"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-news", action="store_true")
    ap.add_argument("--skip-games", action="store_true")
    ap.add_argument("--news-days", type=int, default=30)
    args = ap.parse_args()

    failures: list[str] = []

    if not args.skip_news:
        print("\n## RSS-News")
        try:
            print("  ", sync_news_rss())
        except Exception:
            failures.append("news_rss")
            traceback.print_exc()

        print("\n## Web-News (Tavily)")
        try:
            out = sync_news_web(args.news_days)
            print("   Status:", out["stats"], f"| neu: {len(out['loaded'])}")
        except Exception:
            failures.append("news_web")
            traceback.print_exc()

    if not args.skip_games:
        print("\n## Spiele + Tabelle")
        try:
            import asyncio

            print("  ", asyncio.run(sync_games()))
        except Exception:
            failures.append("games")
            traceback.print_exc()

        print("\n## Spielerstatistik")
        try:
            import asyncio

            print("  ", asyncio.run(sync_skater_stats()))
        except Exception:
            failures.append("skater_stats")
            traceback.print_exc()

        print("\n## Testspiele (Vereinsseite)")
        try:
            print("  ", sync_preseason())
        except Exception:
            failures.append("preseason")
            traceback.print_exc()

    print("\n## Aktualität")
    for k, v in freshness_report().items():
        print(f"   {k:18} {v}")
    if not args.skip_games:
        try:
            probleme = current_season_problems()
        except Exception:
            probleme = ["Prüfung der laufenden Saison fehlgeschlagen"]
            traceback.print_exc()
        for problem in probleme:
            print(f"   ⚠ {problem}")
        if probleme:
            failures.append("aktualitaet")

    if failures:
        print(f"\n⚠ Fehlgeschlagene Schritte: {', '.join(failures)}")
        return 1
    print("\n✓ Sync ohne Fehler")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
