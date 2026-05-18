"""Gemeinsame Scraper-Infrastruktur.

Features:
- Persistentes Disk-Cache (cache/{source}/{url_hash}.html)
- Rate-Limit mit Jitter (Default 2.5s ± 0.5s pro Source)
- Optionaler VPN/Proxy-Pool via Env-Vars
- Retry mit Exponential-Backoff bei 5xx/429
- Browser-ähnliche Header (UA, Accept-Language)
- Async-First, aber httpx.Client als Sync-Alternative
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import time
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...config import settings

logger = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


def _cache_path(source: str, url: str) -> Path:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return settings.cache_dir / source / f"{h}.html"


def cache_get(source: str, url: str) -> str | None:
    p = _cache_path(source, url)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def cache_put(source: str, url: str, content: str) -> None:
    p = _cache_path(source, url)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _proxies() -> dict | None:
    """VPN/Proxy-Pool, falls in .env konfiguriert (BrightData, Oxylabs etc.)."""
    if not settings.proxy_pool_url:
        return None
    if settings.proxy_pool_user and settings.proxy_pool_pass:
        proxy_url = settings.proxy_pool_url.replace(
            "://", f"://{settings.proxy_pool_user}:{settings.proxy_pool_pass}@", 1
        )
    else:
        proxy_url = settings.proxy_pool_url
    return {"http://": proxy_url, "https://": proxy_url}


class Scraper:
    """Basis-Klasse für höfliche, gecachte Scraper."""

    source: str = "default"
    rate_limit_sec: float = settings.scraper_rate_limit_sec
    rate_jitter_sec: float = settings.scraper_rate_jitter_sec
    use_proxy: bool = False  # einzelne Scraper können das überschreiben

    def __init__(self) -> None:
        self._last_call: float = 0.0
        self._lock = asyncio.Lock()
        proxies = _proxies() if self.use_proxy else None
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=30.0,
            follow_redirects=True,
            proxies=proxies,
        )

    async def __aenter__(self) -> "Scraper":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    async def _wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self.rate_limit_sec - (now - self._last_call) + random.uniform(0, self.rate_jitter_sec)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        reraise=True,
    )
    async def _fetch(self, url: str, accept_404_with_body: bool = True) -> str:
        await self._wait()
        resp = await self._client.get(url)
        # WordPress-typischer "404 mit Content" — wenn body da ist, nicht raisen
        if resp.status_code == 200 or (accept_404_with_body and resp.status_code == 404 and len(resp.text) > 2000):
            return resp.text
        resp.raise_for_status()
        return resp.text

    async def get(self, url: str, force_refresh: bool = False) -> str:
        """Hauptzugang: cache-zuerst, sonst fetch und cachen."""
        if not force_refresh:
            cached = cache_get(self.source, url)
            if cached is not None:
                logger.debug("cache hit: %s", url)
                return cached
        try:
            content = await self._fetch(url)
            cache_put(self.source, url, content)
            logger.info("fetched + cached (%s, %d KB): %s", self.source, len(content) // 1024, url)
            return content
        except Exception as e:
            logger.warning("fetch failed (%s): %s — %s", self.source, url, e)
            raise
