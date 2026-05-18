"""Loader: EliteProspects → Supabase.

Idempotenter Upsert via RPCs. Falken-Team wird einmal angelegt,
player+player_season+player_stats werden zu jedem Player gemerged.
"""
from __future__ import annotations

import logging
from typing import Any

from ...db import rpc, supabase, _with_retry, exec_sql
from ..loaders import upsert_season, upsert_team
from .elite_prospects import fetch_season_stats

logger = logging.getLogger(__name__)


# DEL2 vs Oberliga: Falken waren in DEL2 2007/08-2022/23, danach Oberliga Süd
def _league_for_season(label: str) -> tuple[str, int]:
    """('2022/23') → ('DEL2', 2). ('2024/25') → ('Oberliga Süd', 3)."""
    year_start = int(label.split("/")[0])
    if year_start >= 2023:
        return ("Oberliga Süd", 3)
    return ("DEL2", 2)


def _upsert_player(name: str, position: str | None, ep_url: str) -> str:
    """Returns player UUID. Nutzt PostgREST direct (umgeht exec_sql DDL-Filter)."""
    # Lookup via REST (verhindert False-Positive bei Namen wie "Grant Toulmin")
    res = supabase().table("falken_players").select("id").eq("name", name).limit(1).execute()
    if res.data:
        return res.data[0]["id"]
    ins = supabase().table("falken_players").insert({
        "name": name,
        "position": position,
        "source_ids": {"eliteprospects": ep_url},
    }).execute()
    return ins.data[0]["id"]


def _upsert_player_season(player_id: str, team_id: str, season_id: str) -> str:
    """Returns player_season UUID."""
    res = (supabase().table("falken_player_seasons").select("id")
           .eq("player_id", player_id).eq("team_id", team_id).eq("season_id", season_id)
           .limit(1).execute())
    if res.data:
        return res.data[0]["id"]
    ins = supabase().table("falken_player_seasons").insert({
        "player_id": player_id,
        "team_id": team_id,
        "season_id": season_id,
        "source_ids": {"eliteprospects": True},
    }).execute()
    return ins.data[0]["id"]


def _upsert_player_stats(player_season_id: str, p: dict[str, Any]) -> None:
    payload = {
        "player_season_id": player_season_id,
        "games_played": p.get("games_played"),
        "goals": p.get("goals"),
        "assists": p.get("assists"),
        # points wird im Schema als GENERATED Column berechnet
        "pim": p.get("pim"),
        "plus_minus": p.get("plus_minus"),
    }
    # Upsert: erst löschen, dann insert (für die GENERATED column)
    try:
        supabase().table("falken_player_stats").upsert(payload, on_conflict="player_season_id").execute()
    except Exception as e:
        logger.warning("player_stats upsert failed for %s: %s", player_season_id, e)


async def load_falken_season_from_ep(season_label: str) -> dict[str, int]:
    """Lädt eine Falken-Saison komplett von EliteProspects in die DB."""
    league, tier = _league_for_season(season_label)
    print(f"\n=== EliteProspects: Falken {season_label} ({league}) ===")

    data = await fetch_season_stats(season_label)
    if not data["players"]:
        print(f"  ⚠️  Keine Player-Daten für {season_label}")
        return {"players": 0, "goalies": 0}

    season_uuid = upsert_season(season_label, league, tier, hockeydata_season_id=0)
    team_uuid = upsert_team("Heilbronner Falken", "HEI", hockeydata_team_id=None)

    n_players = 0
    for p in data["players"]:
        if not p.get("name"):
            continue
        player_uuid = _upsert_player(p["name"], p.get("position"), p.get("ep_url", ""))
        ps_uuid = _upsert_player_season(player_uuid, team_uuid, season_uuid)
        _upsert_player_stats(ps_uuid, p)
        n_players += 1

    print(f"  ✓ {n_players} Players geladen")
    return {"players": n_players, "goalies": 0}


async def backfill_all_falken_seasons(seasons: list[str]) -> dict[str, dict[str, int]]:
    """Bulk-Backfill aller angegebenen Saisons."""
    results: dict[str, dict[str, int]] = {}
    for s in seasons:
        try:
            results[s] = await load_falken_season_from_ep(s)
        except Exception as e:
            logger.error("Backfill failed für %s: %s", s, e)
            results[s] = {"error": str(e)}
    return results


if __name__ == "__main__":
    import asyncio
    from ...logging_setup import setup_logging
    setup_logging()

    # Alle 10 Saisons der letzten Dekade
    seasons = [
        "2015/16", "2016/17", "2017/18", "2018/19", "2019/20",
        "2020/21", "2021/22", "2022/23", "2023/24", "2024/25",
    ]
    results = asyncio.run(backfill_all_falken_seasons(seasons))
    print("\n=== Zusammenfassung ===")
    for s, r in results.items():
        print(f"  {s}: {r}")
