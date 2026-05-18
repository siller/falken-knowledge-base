"""hockeydata-API-Client.

DEB-Key (öffentlich) + Referer `deb-online.live` + Rate-Limit 1 Req / 2-3 Sek.

Endpoints (Pfad-Konvention `/data/ih/{Endpoint}`):
- Schedule, Standings, LeaderFieldPlayers, LeaderGoalKeepers
- GetTeamDetails, GetGameReport, GetAllPlayers, GetPlayerDetails
- GetPlayerCareerStats, KnockoutStage, GamePlayByPlay

Plus Discovery (Pfad `/data/api/{Endpoint}`): GetSports, GetLeagues, GetSeasons
und (`/data/ih/{Endpoint}` mit `id`-Param) `GetDivisionInfo`.

Status-Codes:
  1  = Ok
 -1  = Guid not found (Key existiert nicht)
  3,4 = ApiKey invalid (Referer falsch)
 -8  = Not calculated (Division-ID ist Wrapper, kein berechneter Wettbewerb)
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)


class HockeydataError(Exception):
    """Allgemeiner API-Fehler (statusId < 0)."""


class HockeydataNotCalculated(HockeydataError):
    """statusId = -8: die abgefragte Division wurde nicht berechnet (Saison-Wrapper statt Wettbewerb)."""


class HockeydataAuthError(HockeydataError):
    """statusId 3/4/-1: Key oder Referer falsch."""


@dataclass
class RateLimiter:
    """Asynchroner Rate-Limiter: maximal 1 Request alle `min_interval` Sekunden (mit Jitter)."""

    min_interval: float
    jitter: float
    _last_call: float = 0.0
    _lock: asyncio.Lock = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self.min_interval - (now - self._last_call) + random.uniform(0, self.jitter)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()


class HockeydataClient:
    """Async-Client mit Rate-Limit, Retry und Status-Code-Mapping."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = settings.hockeydata_base_url
        self.api_key = settings.hockeydata_api_key
        self.referer = settings.hockeydata_referer
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = client is None
        self._limiter = RateLimiter(
            min_interval=settings.hockeydata_rate_limit_sec,
            jitter=settings.hockeydata_rate_jitter_sec,
        )

    async def __aenter__(self) -> "HockeydataClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._owns_client:
            await self._client.aclose()

    # ---- low-level ----

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        reraise=True,
    )
    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        await self._limiter.wait()
        params = {
            "apiKey": self.api_key,
            "referer": self.referer,
            "lang": "en",   # ohne lang liefern manche Endpoints leeres data
            **params,
        }
        url = f"{self.base_url}{path}"
        logger.debug("GET %s params=%s", path, {k: v for k, v in params.items() if k != "apiKey"})
        resp = await self._client.get(url, params=params)
        # 400 wirft hockeydata-API für "no content available" — als leerer body behandeln
        if resp.status_code == 400 and "no content" in resp.text.lower():
            raise HockeydataError(f"no content for {path}")
        # 500 ist bei dieser API meist "Division existiert nicht" — kein Retry sinnvoll
        if resp.status_code == 500:
            raise HockeydataError(f"server error 500 for {path} (likely invalid divisionId)")
        if resp.status_code >= 502:
            resp.raise_for_status()  # echte Server-Probleme → retry
        body = resp.json()
        status = body.get("statusId")
        if status == 1:
            return body
        msg = body.get("statusMsg") or "unknown"
        if status in (3, 4, -1):
            raise HockeydataAuthError(f"{msg} (statusId={status}) for {path}")
        if status == -8:
            raise HockeydataNotCalculated(f"{msg} (statusId={status}) for {path}")
        raise HockeydataError(f"{msg} (statusId={status}) for {path}")

    def _rows(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        """Konventionsmethode: viele Endpoints geben `data.rows` zurück."""
        data = body.get("data") or {}
        if isinstance(data, list):
            return data
        return data.get("rows", []) if isinstance(data, dict) else []

    # ---- Discovery (öffentlich) ----

    async def get_sports(self) -> list[dict[str, Any]]:
        b = await self._request("/data/api/GetSports", {})
        return b["data"]

    async def get_leagues(self, sport: str = "icehockey") -> list[dict[str, Any]]:
        b = await self._request("/data/api/GetLeagues", {"sport": sport})
        return b["data"]

    async def get_seasons(self, league_id: int, sport: str = "icehockey") -> list[dict[str, Any]]:
        b = await self._request("/data/api/GetSeasons", {"sport": sport, "leagueId": league_id})
        return b["data"]

    async def get_division_info(self, season_id: int, league_id: int, sport: str = "icehockey") -> dict[str, Any]:
        """Liefert Sub-Divisions einer Saison (Grunddurchgang, Playoffs, Playdowns).

        Achtung: Manche Saisons liefern leere `divisions` und `teams`-Arrays — das ist
        kein Bug, sondern eine Begrenzung des Keys (siehe Plan-Doku).
        """
        b = await self._request(
            "/data/ih/GetDivisionInfo",
            {"id": season_id, "leagueId": league_id, "seasonId": season_id, "sport": sport},
        )
        return b["data"]

    # ---- Daten-Endpoints (per divisionId) ----

    async def get_standings(self, division_id: int) -> list[dict[str, Any]]:
        b = await self._request("/data/ih/Standings", {"divisionId": division_id})
        return self._rows(b)

    async def get_schedule(self, division_id: int) -> list[dict[str, Any]]:
        b = await self._request("/data/ih/Schedule", {"divisionId": division_id})
        return self._rows(b)

    async def get_leader_field_players(self, division_id: int, team_id: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"divisionId": division_id}
        if team_id:
            params["teamId"] = team_id
        b = await self._request("/data/ih/LeaderFieldPlayers", params)
        return self._rows(b)

    async def get_leader_goalies(self, division_id: int, team_id: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"divisionId": division_id}
        if team_id:
            params["teamId"] = team_id
        b = await self._request("/data/ih/LeaderGoalKeepers", params)
        return self._rows(b)

    async def get_team_details(self, division_id: int, team_id: int) -> dict[str, Any]:
        b = await self._request("/data/ih/GetTeamDetails", {"divisionId": division_id, "teamId": team_id})
        return b["data"]

    async def get_all_players(self, division_id: int) -> list[dict[str, Any]]:
        b = await self._request("/data/ih/GetAllPlayers", {"divisionId": division_id})
        return self._rows(b)

    async def get_player_details(self, player_id: int) -> dict[str, Any]:
        b = await self._request("/data/ih/GetPlayerDetails", {"playerId": player_id})
        return b["data"]

    async def get_player_career(self, player_id: int) -> dict[str, Any]:
        b = await self._request("/data/ih/GetPlayerCareerStats", {"playerId": player_id})
        return b["data"]

    async def get_game_report(self, game_id: str) -> dict[str, Any]:
        b = await self._request("/data/ih/GetGameReport", {"gameId": game_id})
        return b["data"]

    async def get_play_by_play(self, game_id: str) -> dict[str, Any]:
        b = await self._request("/data/ih/GamePlayByPlay", {"gameId": game_id})
        return b["data"]

    async def get_knockout_stage(self, division_id: int) -> dict[str, Any]:
        b = await self._request("/data/ih/KnockoutStage", {"divisionId": division_id})
        return b["data"]
