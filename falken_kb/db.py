"""DB-Zugriff via Supabase REST + RPC (kein direkter Postgres-Connect nötig).

Hintergrund: Wir nutzen den service_role-Key, gehen über PostgREST. Für
Gemma-generiertes SQL gibt es eine RPC `exec_sql`, für pgvector-Suche `search_articles`.
Für Upserts in Tabellen nutzen wir entweder PostgREST-Upsert (kein RPC nötig) oder
spezielle Upsert-RPCs (für Conflict-Handling mit JSONB-Merge).
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from supabase import Client, create_client

from .config import settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def _new_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY nicht in .env gesetzt")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def supabase() -> Client:
    global _client
    if _client is None:
        _client = _new_client()
    return _client


def _reset_client() -> None:
    """Nach HTTP/2-Flake o.ä.: alte Connection wegwerfen, neue beim nächsten Call."""
    global _client
    _client = None


def _with_retry(fn, max_attempts: int = 3):
    """Wrap eine Supabase-Operation mit Retry bei Connection-Errors."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except (httpx.LocalProtocolError, httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadError) as e:
            logger.warning("Supabase HTTP-Flake (attempt %d/%d): %s", attempt, max_attempts, str(e)[:120])
            _reset_client()
            if attempt >= max_attempts:
                raise
            time.sleep(0.5 * attempt)


def sanitize_llm_sql(query: str) -> str:
    """Cleanup typischer LLM-Fehler bevor SQL an Postgres geht.

    - Whitespace-Normalisierung + trailing-semicolon weg
    - Deutsche Keywords → Englisch (ODER BY → ORDER BY, VON → FROM)
    - MySQL-Funktionen → PostgreSQL (YEAR(CURDATE())→EXTRACT, NOW(), DATE_SUB)
    - Doppelte Tokens (JOIN x JOIN x ON, AND AND, points,points,)
    - Spalten-Tippfehler (player_name → player, goalie_name → goalie)
    - Doppelte Tabellennamen (falken_skater_skater_stats)
    - Kaputte Strings ('2008/ '2008/09')
    """
    import re as _re
    q = query.strip().rstrip(";").strip()
    q = _re.sub(r"\s+", " ", q)

    # Deutsche SQL-Keywords → englisch (word boundaries, case-insensitive)
    keyword_fixes = {
        r"\bODER\s+BY\b": "ORDER BY",
        r"\bGRUPPE\s+VON\b": "GROUP BY",
        r"\bVON\s+(?=falken_|coach_|player_|games\b|teams\b|seasons\b)": "FROM ",
        r"\bWAEHLE\b": "SELECT",
        r"\bWO\b": "WHERE",
    }
    for pat, repl in keyword_fixes.items():
        q = _re.sub(pat, repl, q, flags=_re.IGNORECASE)

    # MySQL → PostgreSQL
    q = _re.sub(r"\bYEAR\s*\(\s*CURDATE\s*\(\s*\)\s*\)", "EXTRACT(YEAR FROM CURRENT_DATE)", q, flags=_re.IGNORECASE)
    q = _re.sub(r"\bCURDATE\s*\(\s*\)", "CURRENT_DATE", q, flags=_re.IGNORECASE)
    q = _re.sub(r"\bNOW\s*\(\s*\)", "CURRENT_TIMESTAMP", q, flags=_re.IGNORECASE)

    # Doppelte Tokens: "JOIN teams ht JOIN teams ht ON" → "JOIN teams ht ON"
    q = _re.sub(
        r"\bJOIN\s+(\w+)\s+(\w+)\s+JOIN\s+\1\s+\2\s+ON\b",
        r"JOIN \1 \2 ON",
        q, flags=_re.IGNORECASE,
    )
    # Doppelter "ON ... ON" am gleichen JOIN: "ON c.id = ct.coach_id JOIN ... ON c.id = ON c.id = ct"
    q = _re.sub(r"\bON\s+([^=]+=\s*\w+\.\w+)\s+ON\s+\1", r"ON \1", q, flags=_re.IGNORECASE)
    # "FROM x FROM x" → "FROM x"
    q = _re.sub(r"\bFROM\s+(\w+)\s+FROM\s+\1\b", r"FROM \1", q, flags=_re.IGNORECASE)
    # "AND AND" → "AND"
    q = _re.sub(r"\bAND\s+AND\b", "AND", q, flags=_re.IGNORECASE)

    # Doppelte Tabellennamen-Segmente: "falken_skater_skater_stats" → "falken_skater_stats"
    q = _re.sub(r"\bfalken_skater_skater_stats\b", "falken_skater_stats", q)
    q = _re.sub(r"\bfalken_goalie_goalie_stats\b", "falken_goalie_stats", q)
    q = _re.sub(r"\bfalken_player_player_seasons\b", "falken_player_seasons", q)
    # generisches Pattern wo "word_word_X" mit derselben "word_" vorkommt
    q = _re.sub(r"\b((?:falken|player|goalie|coach|team)_)\1(\w+)", r"\1\2", q)

    # Spalten-Tippfehler
    column_fixes = {
        r"\bplayer_name\b": "player",
        r"\bgoalie_name\b": "goalie",
        r"\bteam_name\b": "team",
        r"\bcoach_name\b": "name",  # in coaches table column is 'name'
    }
    for pat, repl in column_fixes.items():
        q = _re.sub(pat, repl, q)

    # Doppelte Spalten in SELECT: "SELECT a, b, a, b FROM" — vereinfacht erkennen
    # Pattern: "x, y, x, y" wo x und y einfache Identifier sind
    q = _re.sub(r"\bSELECT\s+(\w+),\s*(\w+),\s*\1,\s*\2\b", r"SELECT \1, \2", q, flags=_re.IGNORECASE)

    # Kaputte String-Literals: "'2008/ '2008/09'" → "'2008/09'"
    q = _re.sub(r"'(\d{4})/\s+'(\d{4}/\d{2})'", r"'\2'", q)

    return q.strip()


def exec_sql(query: str) -> list[dict[str, Any]]:
    """Führt SELECT/WITH/EXPLAIN via RPC aus, returnt Liste von Dicts.

    Wendet erst `sanitize_llm_sql` an (auto-fix typischer LLM-Fehler).
    """
    cleaned = sanitize_llm_sql(query)
    if cleaned != query.strip().rstrip(";").strip():
        logger.info("SQL auto-sanitized:\n  raw:    %s\n  clean:  %s", query[:200], cleaned[:200])
    res = _with_retry(lambda: supabase().rpc("exec_sql", {"query_text": cleaned}).execute())
    data = res.data
    return data if isinstance(data, list) else []


def vector_search(embedding: list[float], top_k: int = 6) -> list[dict[str, Any]]:
    res = _with_retry(lambda: supabase().rpc("search_articles", {
        "query_embedding": embedding, "match_count": top_k,
    }).execute())
    return res.data or []


def rpc(name: str, params: dict[str, Any]) -> Any:
    """Convenience für RPC-Aufrufe (z.B. upsert_season, upsert_team etc.)."""
    res = _with_retry(lambda: supabase().rpc(name, params).execute())
    return res.data


def select_first(table: str, filters: dict[str, Any] | None = None) -> dict[str, Any] | None:
    def call():
        q = supabase().table(table).select("*")
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        return q.limit(1).execute()
    res = _with_retry(call)
    rows = res.data or []
    return rows[0] if rows else None
