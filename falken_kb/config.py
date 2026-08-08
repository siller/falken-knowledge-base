"""Zentrale Config — alle Env-Werte gehen hierüber."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase / Postgres
    supabase_url: str = "https://supabase.siller.io"
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # hockeydata
    hockeydata_api_key: str = "3c5a99d835fcb70156d40cd60d03f350"
    hockeydata_referer: str = "deb-online.live"
    hockeydata_base_url: str = "https://api.hockeydata.net"
    hockeydata_rate_limit_sec: float = 2.5
    hockeydata_rate_jitter_sec: float = 0.5

    # LLM (DGX-namespace, jetzt OpenRouter)
    dgx_base_url: str = "https://openrouter.ai/api/v1"
    dgx_api_key: str = ""
    dgx_chat_model: str = "deepseek/deepseek-v4-flash:free"
    dgx_chat_fallbacks: str = ""  # comma-separated, optional
    dgx_embed_model: str = "text-embedding-3-small"
    dgx_embed_dim: int = 768
    # Ohne eigenen Wert wartet die openai-Bibliothek 600 Sekunden pro Aufruf und
    # wiederholt zweimal — eine hängende DGX blockiert damit eine halbe Stunde.
    dgx_timeout_sec: float = 30.0

    # Web-Search für Multi-Hop-Fragen und den News-Harvest.
    # Gemessen am 25.07.2026 über unsere sechs Standard-Queries (Treffer auf
    # vertrauenswürdigen Domains): Exa 40/48, Tavily allgemein 22/48,
    # Tavily mit topic=news 3/48. Exa ist zudem gut doppelt so schnell,
    # kostet aber ~$0,007 pro Suche — Tavily bleibt als Gratis-Fallback.
    # provider: "auto" (Exa wenn Key da, sonst Tavily) | "exa" | "tavily"
    # provider zusätzlich "aus": schaltet die Websuche still, ohne Schlüssel zu entfernen
    web_search_provider: str = "auto"
    exa_api_key: str = ""
    tavily_api_key: str = ""

    # Gemeinsames Geheimnis der Frage-Schnittstelle. Sie ist nur für den
    # Convex-Dienst gedacht; ohne gesetzten Wert nimmt sie keine Fragen an.
    api_token: str = ""
    # Harte Grenze je Anfrage an die Schnittstelle. Bewusst unter den 45 Sekunden,
    # die die App wartet: der Aufrufer soll eine klare Absage bekommen statt in
    # sein eigenes Zeitlimit zu laufen.
    api_zeitgrenze_sec: float = 40.0
    api_sammel_max: int = 10
    # Wie viele Fragen des Sammelaufrufs gleichzeitig laufen. Default 1, also
    # nacheinander — gemessen am 08.08.2026 mit vier echten Spieltagsfragen:
    # nacheinander 28,3 s gesamt (12,3 · 7,9 · 3,7 · 4,4 s je Frage),
    # vierfach parallel 30,4 s gesamt (30,3 · 24,8 · 18,5 · 19,4 s).
    # Die DGX ist der Engpass; Gleichzeitigkeit verschiebt nur die Warteschlange
    # und würde einer parallel laufenden Fan-Frage die Antwortzeit verderben.
    api_sammel_parallel: int = 1
    # Gesamtgrenze des Sammelaufrufs. Zehn Fragen à 40 s wären über sechs
    # Minuten — der nächtliche Vorrat verträgt das, ein versehentlich großer
    # Aufruf aus Convex nicht. Was bis dahin fertig ist, wird geliefert.
    api_sammel_gesamt_sec: float = 180.0

    # Scraping
    proxy_pool_url: str = ""
    proxy_pool_user: str = ""
    proxy_pool_pass: str = ""
    scraper_rate_limit_sec: float = 2.5
    scraper_rate_jitter_sec: float = 0.5
    scraper_user_agent: str = "FalkenKnowledgeBase/0.1 (research, mark@siller.ai)"

    # Falken
    falken_team_id: str = ""
    falken_team_name: str = "Heilbronner Falken"

    # Pfade
    cache_dir: Path = REPO_ROOT / "cache"


settings = Settings()


def reload_settings() -> Settings:
    """Re-instantiate Settings from current os.environ + mutate the global
    `settings` object so existing `from .config import settings` references
    pick up new values without needing re-import.

    Streamlit-Cloud-Bug: secrets werden NACH initialem module-import in env
    geschoben — settings wäre sonst stale. Wird vom UI nach Secrets-Load
    aufgerufen.
    """
    fresh = Settings()
    for k, v in fresh.model_dump().items():
        setattr(settings, k, v)
    return settings
