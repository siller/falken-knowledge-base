"""Backfill falken.goalie_stats aus hockeydata LeaderGoalKeepers.

Ablösung der ersten Fassung, die drei Fehler hatte:

1. **Team-Filter über Kürzel**: `{"HNF", "HEC", "HCF"}` — "HEC" ist aber das
   Kürzel der *Höchstadt Alligators*, und die Falken laufen je nach Saison als
   "HNF_" (mit Unterstrich). Ergebnis: fremde Torhüter in der Falken-Historie,
   echte fehlten. Jetzt wird über die teamId gefiltert (47011, ab 2026/27 70543).
2. **Falsches Spiele-Feld**: `gamesPlayed` ist die Anzahl Spiele der *Mannschaft*,
   die Einsätze des Torhüters stehen in `gamePlayedIn`.
3. **Geratene divisionIds**: die Sub-Divisions kommen jetzt aus `GetDivisionInfo`
   statt aus einem Offset-Suchfenster.

    python3 scripts/backfill_goalie_stats.py --dry-run
    python3 scripts/backfill_goalie_stats.py --purge-stale
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, supabase  # noqa: E402
from falken_kb.ingestion.hockeydata_client import HockeydataClient, HockeydataError  # noqa: E402
from falken_kb.logging_setup import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)

OBERLIGA_LEAGUE_ID = 150
# hockeydata führt den Klub nach der Insolvenz unter neuer teamId weiter.
FALKEN_TEAM_IDS = {47011, 70543}


# hockeydata-divisionType: 21 = Gruppen-Hauptrunde (Oberliga Süd/Nord),
# 22/30/40 = Playoff-Ebenen, 13 = Abschlusstabelle. Für die Saison-Statistik
# eines Torhüters zählt die Hauptrunde — sonst überschreibt eine
# Achtelfinal-Serie mit 2 Einsätzen die 32 Spiele der Hauptrunde.
REGULAR_SEASON_DIVISION_TYPE = 21


async def falken_divisions(c: HockeydataClient) -> list[tuple[str, int]]:
    """(Saison-Label, divisionId) — je Saison die Hauptrunde mit Falken-Beteiligung."""
    out: list[tuple[str, int]] = []
    for s in await c.get_seasons(OBERLIGA_LEAGUE_ID):
        label = (s.get("seasonName") or "").replace("Saison ", "")
        try:
            info = await c.get_division_info(s["seasonId"], OBERLIGA_LEAGUE_ID)
        except HockeydataError as e:
            logger.debug("  %s: %s", label, str(e)[:80])
            continue
        candidates = [
            d for d in info.get("divisions", [])
            if FALKEN_TEAM_IDS & set(d.get("teams") or [])
            and d.get("divisionType") == REGULAR_SEASON_DIVISION_TYPE
        ]
        for d in candidates:
            out.append((label, d["id"]))
            logger.info("  %s → division %d (%s)", label, d["id"], d["divisionName"])
    return out


def _player_uuid(name: str, hd_id: int | None) -> str:
    safe = name.replace("'", "''")
    existing = exec_sql(f"SELECT id FROM players WHERE name = '{safe}'")
    if existing:
        return existing[0]["id"]
    res = supabase().table("falken_players").insert({
        "name": name,
        "position": "G",
        "source_ids": {"hockeydata": str(hd_id)} if hd_id else {},
    }).execute()
    return res.data[0]["id"]


def _player_season_uuid(player_id: str, season_id: str, team_id: str, jersey: int | None) -> str:
    existing = exec_sql(
        f"SELECT id FROM player_seasons WHERE player_id='{player_id}' "
        f"AND season_id='{season_id}' AND team_id='{team_id}'"
    )
    if existing:
        return existing[0]["id"]
    res = supabase().table("falken_player_seasons").insert({
        "player_id": player_id,
        "team_id": team_id,
        "season_id": season_id,
        "jersey_number": jersey,
        "role": "goalie",
    }).execute()
    return res.data[0]["id"]


def _stats_payload(g: dict[str, Any], player_season_id: str) -> dict[str, Any]:
    shots = g.get("shotsAgainst")
    ga = g.get("goalsAgainst")
    sv_raw = g.get("savePercentage")
    playing_time = g.get("playingTime")  # Sekunden
    return {
        "player_season_id": player_season_id,
        "games_played": g.get("gamePlayedIn"),   # NICHT gamesPlayed (= Teamspiele)
        "shutouts": g.get("shutOuts"),
        "goals_against": ga,
        "shots_against": shots,
        "saves": (shots - ga) if (shots is not None and ga is not None) else None,
        "gaa": g.get("goalsAgainstAverage"),
        "save_pct": sv_raw / 100.0 if isinstance(sv_raw, (int, float)) and sv_raw > 1 else sv_raw,
        "minutes_played": int(playing_time / 60) if isinstance(playing_time, (int, float)) else None,
    }


async def run(dry_run: bool, purge_stale: bool) -> None:
    falken_uuid = exec_sql("SELECT id FROM teams WHERE name='Heilbronner Falken'")[0]["id"]
    seasons = {
        (s["label"], s["league"]): s["id"]
        for s in exec_sql("SELECT label, league, id FROM seasons")
    }

    loaded: list[tuple[str, str]] = []   # (Saison, Spielername)
    touched_seasons: set[str] = set()

    async with HockeydataClient() as c:
        for label, div in await falken_divisions(c):
            season_uuid = seasons.get((label, "Oberliga Süd")) or seasons.get((label, "DEL2"))
            if not season_uuid:
                print(f"  ⚠ Saison {label} nicht in der DB — übersprungen")
                continue
            try:
                goalies = await c.get_leader_goalies(div)
            except HockeydataError as e:
                print(f"  {label} div {div}: keine Torhüter-Daten ({str(e)[:60]})")
                continue

            falken = [g for g in goalies if g.get("teamId") in FALKEN_TEAM_IDS]
            print(f"  {label} (div {div}): {len(falken)} Falken-Torhüter von {len(goalies)}")
            touched_seasons.add(season_uuid)

            for g in falken:
                name = " ".join(
                    p for p in (g.get("playerFirstname"), g.get("playerMiddlename"),
                                g.get("playerLastname")) if p
                ).strip()
                if not name:
                    continue
                gp = g.get("gamePlayedIn")
                print(f"     {name:28} {gp or 0:2} Einsätze  GAA {g.get('goalsAgainstAverage')}  "
                      f"SV% {g.get('savePercentage')}")
                loaded.append((label, name))
                if dry_run:
                    continue
                pid = _player_uuid(name, g.get("id"))
                psid = _player_season_uuid(pid, season_uuid, falken_uuid, g.get("playerJerseyNr"))
                supabase().table("falken_goalie_stats").upsert(
                    _stats_payload(g, psid), on_conflict="player_season_id"
                ).execute()

    if purge_stale and not dry_run and touched_seasons:
        # Altbestand aus den neu geladenen Saisons wegräumen: Einträge, die jetzt
        # nicht mehr bestätigt werden, stammen aus dem fehlerhaften Kürzel-Filter.
        keep = {(label, name) for label, name in loaded}
        for season_uuid in touched_seasons:
            rows = exec_sql(f"""
                SELECT gs.player_season_id, p.name, s.label
                FROM goalie_stats gs
                JOIN player_seasons ps ON ps.id = gs.player_season_id
                JOIN players p ON p.id = ps.player_id
                JOIN seasons s ON s.id = ps.season_id
                WHERE ps.season_id = '{season_uuid}'
            """)
            for r in rows:
                if (r["label"], r["name"]) not in keep:
                    supabase().table("falken_goalie_stats").delete().eq(
                        "player_season_id", r["player_season_id"]
                    ).execute()
                    print(f"  ✗ entfernt (nicht bestätigt): {r['name']} {r['label']}")

    print(f"\n{len(loaded)} Torhüter-Saisons {'gefunden' if dry_run else 'geschrieben'}.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--purge-stale", action="store_true",
                    help="nicht bestätigte Alt-Einträge der geladenen Saisons löschen")
    args = ap.parse_args()
    asyncio.run(run(args.dry_run, args.purge_stale))


if __name__ == "__main__":
    main()
