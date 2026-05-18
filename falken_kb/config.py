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

    # Web-Search (Tavily — für Multi-Hop-Fragen mit Web-Recherche)
    tavily_api_key: str = ""

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
