# HORST — Technische Übersicht

## Architektur (3-Tier + GenAI-Layer)

```
┌────────────── PRESENTATION ──────────────┐
│ Streamlit UI (falken-knowledge-base.    │
│ streamlit.app), passwort-geschützt,     │
│ Multi-Turn-Chat, Falken-Design          │
└──────────────────┬───────────────────────┘
                   │
┌────────────── ORCHESTRATION ─────────────┐
│ Smart Routing:                          │
│  1. Heuristik-Shortcut (DB-only)        │
│  2. LLM-Classify (fact/narrative/trend) │
│  3. Hybrid-Fallback-Chains              │
└──────────────────┬───────────────────────┘
                   │
┌──────────── HANDLERS (4) ────────────────┐
│ fact_sql · narrative_rag · trend_chart  │
│ hybrid_web (Multi-Hop Web+DB)           │
└──┬─────────┬─────────────┬───────────────┘
   │         │             │
   ▼         ▼             ▼
┌────────┬────────────┬───────────────┐
│ DGX    │ Supabase   │ Tavily        │
│ Gemma  │ Postgres + │ Web-Search    │
│ + Embed│ pgvector   │ + Hockeydata  │
└────────┴────────────┴───────────────┘
```

## Stack

| Layer | Technologie |
|---|---|
| **UI** | Streamlit 1.37+ (Python), Custom-CSS im Falken-Design |
| **Hosting** | Streamlit Community Cloud (free) |
| **Auth** | Shared-Password (Streamlit-Secret `app_password`) |
| **Orchestrator** | Python, pydantic-settings für Config |
| **LLM (Chat)** | DGX-Gemma via `https://pgxapi.siller.io/v1` (OpenAI-API-kompatibel) |
| **LLM (Embeddings)** | nomic-embed-text via DGX, 768d |
| **DB** | self-hosted Supabase `https://supabase.siller.io` |
| **DB-Erweiterungen** | pgvector (RAG), pg_trgm (Fuzzy-Match), Sync-Log-Trigger |
| **Web-Search** | Tavily API (1k Calls/Monat free) |
| **Daten-Quellen** | hockeydata.net API + RSS heilbronner-falken.de |

## Pipeline-Komponenten

### Heuristik-Shortcut (`orchestrator._is_simple_db_question`)
- Regex: erkennt Saison-Jahr (`2022/23`, `2024`) + Stats-Wörter (`tabellenplatz`, `topscorer`, `trainer`...)
- Negativ-Filter: schließt Fragen mit externen Entitäten aus (`besitzer`, `restaurant`...)
- Bei Match → direkt `fact_sql`, kein Router-LLM-Call (spart 5-10s)

### Router (`router.classify`)
- LLM-basiert: Gemma klassifiziert in `fact` / `narrative` / `trend`
- Optional Tool-Agent-Mode (experimental, default off — DGX-Gemma ohne native tool-use-API)

### Handler `fact_sql`
1. Schema-Context-Prompt (Tabellen + Beispiel-Queries)
2. Gemma generiert SQL (JSON-Mode, structured output)
3. **SQL-Sanitizer** (`db.sanitize_llm_sql`) fixt typische LLM-Fehler:
   - Deutsche Keywords (`ODER BY` → `ORDER BY`)
   - MySQL-Funktionen (`YEAR(CURDATE())` → `EXTRACT(YEAR FROM CURRENT_DATE)`)
   - Doppelte Tokens (`JOIN x JOIN x` → `JOIN x`)
   - Tippfehler (`player_name` → `player`)
4. Retry mit Hinweis bei Syntax-Error
5. SQL läuft via Supabase RPC `exec_sql` (SELECT-only mit Hard-Cap)
6. Synthesis-LLM-Call mit verschärften Anti-Halluzinations-Regeln

### Handler `narrative_rag`
- Embedding der Frage (nomic-embed-text)
- pgvector Top-K-Search auf `articles`
- Synthesis-Prompt mit Quellen-Zitaten

### Handler `hybrid_web`
- Tavily-Web-Search (5 Snippets)
- LLM extrahiert Personen → parallele `lookup_player`-Calls (ThreadPool)
- Synthesis kombiniert Web + DB-Cross-Lookups

### Tools-Module (für optionalen Tool-Agent)
- `tool_query_falken_db(question)` — fact_sql-Wrapper
- `tool_lookup_player(name)` — direkter pg_trgm-Lookup
- `tool_search_falken_news(query)` — narrative_rag-Wrapper
- `tool_search_web(query)` — Tavily-Wrapper

## Daten-Modell (Kern-Tabellen, Schema `falken`)

```
seasons (48 rows)             — Saisons mit league, league_tier, is_focus_team_season
teams (130)                   — Alle Liga-Teams mit alt_names
players (194)                 — Falken-Spieler
coaches (34)                  — Falken-Trainer
games (8290)                  — Alle Spiele mit Score, OT/SO, game_type
team_seasons (330)            — Standings pro Team×Saison
player_seasons (320)          — Jersey-Number + Role pro Spieler×Saison
player_stats (320)            — Goals/Assists/Points (points = generated)
goalie_stats (8)              — GAA, Save%, etc. (8 Einträge, ausbaufähig)
coach_tenures (58)            — Trainer-Amtszeiten via Date-Range
playoff_series (45)           — Round + Wins-Verhältnis + Winner
articles (22)                 — News-Artikel mit pgvector(768)-Embedding
sync_log                      — Phase-2-Trigger für Neo4j-Replikation
```

## Code-Layout

```
falken-knowledge-base/
├── falken_kb/
│   ├── config.py             — Settings (env-vars + Streamlit-secrets)
│   ├── db.py                 — Supabase-Client + SQL-Sanitizer
│   ├── genai/
│   │   ├── orchestrator.py   — Smart Routing
│   │   ├── router.py         — LLM-Klassifikation
│   │   ├── dgx_client.py     — OpenAI-API-Wrapper für DGX
│   │   ├── web_search.py     — Tavily-Wrapper
│   │   ├── tools.py          — Tool-Registry (für Tool-Agent)
│   │   ├── tool_agent.py     — ReAct-Loop (experimental)
│   │   └── handlers/
│   │       ├── fact_sql.py
│   │       ├── narrative_rag.py
│   │       ├── trend_chart.py
│   │       └── hybrid_web.py
│   └── ingestion/
│       ├── hockeydata_client.py
│       ├── loaders.py
│       └── scrapers/         — RSS, EliteProspects, etc.
├── frontend/falken_ui.py     — Streamlit-UI
├── scripts/                  — Backfill-, Test- und Migrations-Skripte
├── supabase/migrations/      — 0001-0008 (Init, RPCs, Views, Date-Backfill)
├── tests/                    — YAMLs + Results-JSONs
├── docs/                     — Diese Übersicht + Reports
└── .streamlit/               — Streamlit-Config + Secrets-Template
```

## Migrations (Supabase)

| Migration | Inhalt |
|---|---|
| `0001_init.sql` | Basis-Tabellen + Foreign Keys |
| `0002_indexes.sql` | pgvector HNSW-Index, B-Trees, Views |
| `0003_rpcs.sql` | `exec_sql`, `search_articles`, `upsert_*` |
| `0004_public_rpcs.sql` | public-Wrapper für PostgREST-Zugriff |
| `0005_team_dedup.sql` | Team-Merge-Helpers |
| `0006_coach_rpcs.sql` | Coach-Tenure-Upserts |
| `0007_focus_season_flag.sql` | `is_focus_team_season` + View `falken_focus_seasons` |
| `0008_season_dates_backfill.sql` | Sep 1 → May 31 Default für alle Saisons |

## Performance-Charakteristik

| Aspekt | Wert |
|---|---|
| Schnitt-Antwortzeit (single user) | 45 s |
| DB-Single-Query Antwort | 30-40 s |
| Multi-Hop Web+DB | 60-75 s |
| LLM-Latenz pro Call (DGX) | 3-5 s |
| Embedding-Call (nomic-768d) | <1 s |
| Tavily-Call | 2-5 s |
| Supabase-SQL-Roundtrip | 0.2-0.5 s |
| **Bottleneck** | DGX bei parallelen Requests (Queue-Stau) |

## Sicherheit

- **Public-Repo**: keine hardcoded Secrets, alle via env-vars / Streamlit-Secrets
- **Supabase-Service-Role-Key**: hat DB-Vollzugriff, lebt nur in Streamlit-Cloud-Secrets
- **`exec_sql`-RPC**: hard-locked auf SELECT/WITH/EXPLAIN — kein DDL/DML möglich
- **App-Auth**: Shared-Password für Team-Zugriff
- **Streamlit Cloud Sandbox**: jeder User in isoliertem Container

## Test-Suite

- `tests/ground_truth.yaml` — 49 hand-verified
- `tests/ground_truth_auto.yaml` — 139 auto-generated
- `tests/genai_questions.yaml` — 211 Test-Fragen (9 Kategorien)
- `tests/ideas_60.yaml` — 60 Brainstorm-Fragen
- `scripts/test_tool_agent.py` — 20 diverse Stress-Tests (aktuell 100 % pass)

## CI/CD

- **Git**: `siller/falken-knowledge-base` (public)
- **Auto-Deploy**: Streamlit Cloud triggert bei jedem `git push` automatisch
- **Re-Deploy-Zeit**: 1-2 Min
