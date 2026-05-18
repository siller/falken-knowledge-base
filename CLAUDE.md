# CLAUDE.md — Falken Knowledge Base

Anweisungen für Claude Code (claude.ai/code) bei der Arbeit an diesem Repo.

## Projektübersicht

GenAI-basierte Wissensdatenbank über die Heilbronner Falken (Eishockey). Sammelt Daten aus mehreren Quellen (hockeydata-API, EliteProspects, Wikipedia, Lokalpresse), normalisiert sie in einem graph-fähigen Postgres-Schema, und beantwortet Fan-Fragen über einen GenAI-Layer auf Basis von Gemma (self-hosted).

**Aktueller Status:** Phase 1 (Supabase-MVP mit 10-Jahres-Backfill).
**Geplant:** Phase 2 (Neo4j-Layer als Add-on auf bestehendes Schema).

## Stack

- **Datenbank:** Self-hosted Supabase auf `https://supabase.siller.io` (Postgres 15 + pgvector + PostgREST). Migrationen über `psql` mit `$DATABASE_URL` aus `.env`.
- **LLM:** Eigene DGX-Inference (`https://pgxapi.siller.io/v1`), OpenAI-kompatibel
  - Chat: `gemma-4-31B`
  - Embeddings: `nomic-embed-text` (768d)
- **Sprache:** Python 3.11+, dependencies via `pyproject.toml`
- **Ingestion-Orchestrator:** Python-Skripte + optional n8n auf siller.io
- **Test-UI:** Streamlit (`frontend/streamlit_app.py`)

## Wichtige Datenquellen

| Quelle | Endpunkt | Daten | Rate-Limit |
|---|---|---|---|
| hockeydata API | `api.hockeydata.net/data/ih/*` | DEL2 2021/22-24/25 + Oberliga 2018/19-25/26 strukturiert | 1 Req / 2-3 Sek (jitter) |
| EliteProspects | HTML scrape | DEL2 2007/08-2020/21 (Roster, Stats) | gleich |
| eishockey-statistiken.de | HTML scrape | Topscorer-Historie, Zuschauer | gleich |
| rodi-db.de | HTML scrape | Per-Season-Kader DEL2 | gleich |
| Wikipedia | MediaWiki API | Saison-Kontext (Trainer, Verletzungen, Transfers) | sanft |
| del-2.org / heilbronner-falken.de / stimme.de | RSS / Sitemap | News-Artikel (für RAG) | gleich |

## hockeydata-API-Auth

DEB-Key (öffentlich bekannt): `3c5a99d835fcb70156d40cd60d03f350`
Referer: `deb-online.live`
Statuscodes:
- `1=Ok`
- `-1=Guid not found` (Key existiert nicht)
- `3/4=ApiKey invalid` (Referer falsch)
- `-8=Not calculated` (Division-ID ist Wrapper, nicht echte Division)

Sub-Division-IDs (Grunddurchgang / Playoffs) müssen pro Saison einzeln ermittelt werden — siehe `ingestion/loaders/seasons.py`.

## Architektur-Prinzipien

### Graph-ready Schema (für Phase 2)

Das Postgres-Schema in `supabase/migrations/` ist explizit so designed, dass Phase 2 (Neo4j-Layer) als reines Add-on funktioniert:
- Alle Entity-IDs sind UUIDs
- Knoten-Tabellen (singular: `seasons`, `teams`, `players`, `games`, `coaches`, `articles`) werden Neo4j-Labels
- Kanten-Tabellen (`player_seasons`, `coach_tenures`, `game_participations`, ...) werden Neo4j-Relationships
- `sync_log` (Trigger auf allen Tabellen) tracked Mutationen — Phase 2 polled diesen Log und repliziert nach Neo4j ohne Phase-1-Code anzufassen
- `docs/graph-model.md` dokumentiert die exakte Mapping

**Beim Schema-Erweitern in dieser Phase: Naming-Konvention einhalten.**
- Foreign Keys: `{entity}_id`
- Kanten-Tabellen: `{from_entity}_{rel_verb_or_noun}` (z.B. `player_seasons` für PLAYED_FOR)
- Source-IDs aus externen Systemen: `source_ids JSONB` (z.B. `{"hockeydata": "uuid", "eliteprospects": 12345}`)

### Politely scrape mit Cache

- `cache/{source}/{url_hash}.html` — alle erfolgreichen Fetches werden lokal gecacht
- Bei jeder Schema-Iteration parsen wir aus dem Cache, kein erneuter Fetch
- VPN-Proxy-Pool für historische Backfills (User-Entscheidung, siehe Plan)
- Rate-Limit 1 Req / 2-3 Sek mit Jitter ±0.5s — auch durch VPN
- Bei 429/5xx: exponential backoff mit IP-Rotation

### LLM ohne Tool-Use

Gemma hat kein natives Function-Calling wie Claude. Wir lösen mit:
1. **Router** (klein, schnell): Klassifiziert Frage in `fact` / `narrative` / `trend` via JSON-Schema-Output
2. **Handler pro Kategorie:**
   - `fact` → SQL-Generation via JSON-Schema, Postgres-Exec, Synthesis-Step
   - `narrative` → pgvector Top-K → Synthesis
   - `trend` → SQL + Vega-Lite-Spec

## Code-Konventionen

- Type hints überall (Python 3.11+ Syntax: `list[str]`, `X | None`)
- `pydantic.BaseModel` für API-Responses und DB-DTOs
- `pydantic_settings.BaseSettings` für Env-Config (zentral in `config.py`)
- Strukturiertes Logging via `logging` (kein print)
- Async für I/O (httpx, asyncpg/psycopg)
- Tests in `tests/`, pytest

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run migrations
python3 -m supabase.run_migrations

# Backfill aktuelle Saison
python3 -m ingestion.sync_current_season

# Backfill historisch (alle 10 Saisons)
python3 -m ingestion.backfill_historic

# Eval-Suite
python3 -m genai.eval

# Test-UI
streamlit run frontend/streamlit_app.py
```

## Beim Erweitern beachten

- Neue Datenquelle → `ingestion/scrapers/{name}.py` plus Eintrag im Tier-Doc
- Neues Entity → Migration + Update auf `sync_log`-Trigger + Eintrag in `docs/graph-model.md`
- Neue Frageklasse → Handler in `genai/handlers/` + Eintrag in `genai/router.py`-Schema
- Antwortqualität gefallen → Eval-Suite (`genai/eval.py`) ausführen, vor Commit Score über 70% halten
