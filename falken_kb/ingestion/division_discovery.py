"""Findet die korrekten Sub-Division-IDs (Grunddurchgang, Playoffs, Playdowns)
für eine gegebene Saison.

Hintergrund: `GetSeasons` liefert nur Saison-Wrapper-IDs. Auf diesen ist
`Standings` / `Schedule` "Not calculated" (statusId=-8). Die echten
Wettbewerbs-Divisions haben separate IDs, die der Saison sequentiell folgen.

Strategie:
1. Versuche, ob die Saison-ID selbst funktioniert (für simple Wettbewerbe)
2. Sonst: probiere IDs in einem Fenster nach der seasonId und prüfe, welche
   `Standings`/`Schedule` mit `statusId=1` liefern
3. Cache Ergebnisse, da Discovery rate-limit-teuer ist

Output: Mapping {label -> divisionId}, z.B.:
  {"regular_season": 10915, "playoffs": 10918, "playdowns": 10919}
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ..config import settings
from .hockeydata_client import HockeydataClient, HockeydataError, HockeydataNotCalculated

logger = logging.getLogger(__name__)

DISCOVERY_CACHE = settings.cache_dir / "division_discovery.json"


def load_cache() -> dict[str, dict[str, int]]:
    if not DISCOVERY_CACHE.exists():
        return {}
    return json.loads(DISCOVERY_CACHE.read_text())


def save_cache(data: dict[str, dict[str, int]]) -> None:
    DISCOVERY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERY_CACHE.write_text(json.dumps(data, indent=2, sort_keys=True))


async def discover_divisions(
    client: HockeydataClient,
    season_id: int,
    search_window: int = 20,
) -> dict[str, int | None]:
    """Probiert IDs in [season_id, season_id+search_window], findet die mit funktionierender Standings.

    Heuristik zur Klassifikation:
    - Größte Teamzahl + spielt am längsten → regular_season
    - Verbleibende mit kürzerer Periode + 4-8 Teams → playoffs
    - 2-4 Teams + endet nach playoffs → playdowns
    """
    cache = load_cache()
    key = str(season_id)
    if key in cache:
        logger.info("Division-Discovery cache hit für seasonId=%d", season_id)
        return cache[key]

    results: list[tuple[int, int, str]] = []  # (divisionId, num_teams, sample_label)
    for offset in range(search_window):
        candidate_id = season_id + offset
        try:
            teams = await client.get_standings(candidate_id)
            if teams:
                # Sample-Label aus Schedule probieren (für game_type-Erkennung)
                try:
                    matches = await client.get_schedule(candidate_id)
                    sample = matches[0] if matches else {}
                    label = sample.get("roundType", sample.get("phase", ""))
                except Exception:
                    label = ""
                logger.info(
                    "  ✓ divisionId=%d hat %d Teams (label=%s)", candidate_id, len(teams), label
                )
                results.append((candidate_id, len(teams), label or ""))
        except HockeydataNotCalculated:
            continue
        except HockeydataError as e:
            logger.debug("  divisionId=%d skipped: %s", candidate_id, e)
            continue

    # Sehr simple Heuristik (verfeinert sich mit echten Daten)
    classified: dict[str, int | None] = {
        "regular_season": None,
        "playoffs": None,
        "playdowns": None,
    }
    if results:
        # größtes Team-Set = Grunddurchgang
        results.sort(key=lambda x: x[1], reverse=True)
        classified["regular_season"] = results[0][0]
        # restliche Teams nach Größe absteigend: nächstes wird playoffs, danach playdowns
        for divid, n_teams, _label in results[1:]:
            if classified["playoffs"] is None and n_teams >= 4:
                classified["playoffs"] = divid
            elif classified["playdowns"] is None and 2 <= n_teams <= 6:
                classified["playdowns"] = divid

    cache[key] = classified  # type: ignore[assignment]
    save_cache(cache)
    return classified
