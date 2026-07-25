# HORST — Technische Übersicht

## Architektur (3-Tier + GenAI-Layer)

```
┌────────────── PRESENTATION ──────────────┐
│ Streamlit UI (falkenapp.streamlit.app), │
│ passwort-geschützt,                     │
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
│ DGX    │ Supabase   │ Exa/Tavily    │
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
| **Web-Search** | Exa (primär, ~$0,007/Suche) mit Tavily als Gratis-Fallback |
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
- Web-Search über Exa bzw. Tavily (5 Snippets)
- LLM extrahiert Personen → parallele `lookup_player`-Calls (ThreadPool)
- Synthesis kombiniert Web + DB-Cross-Lookups

### Tools-Module (für optionalen Tool-Agent)
- `tool_query_falken_db(question)` — fact_sql-Wrapper
- `tool_lookup_player(name)` — direkter pg_trgm-Lookup
- `tool_search_falken_news(query)` — narrative_rag-Wrapper
- `tool_search_web(query)` — Web-Search-Wrapper

## Daten-Modell (Kern-Tabellen, Schema `falken`, Stand 25.07.2026)

```
seasons (49 rows)             — Saisons mit league, league_tier, is_focus_team_season
teams (135)                   — Alle Liga-Teams mit alt_names
players (244)                 — Falken-Spieler
coaches (36)                  — Falken-Trainer
games (8867)                  — Alle Spiele mit Score, OT/SO, game_type
                                (Score NULL = angesetzt, noch nicht gespielt)
team_seasons (344)            — Standings pro Team×Saison
player_seasons (379)          — Jersey-Number + Role pro Spieler×Saison
player_stats (349)            — Goals/Assists/Points (points = generated)
goalie_stats (6)              — GAA, Save%, Shutouts; hockeydata liefert das nur
                                für die Oberliga-Jahre ab 2023/24
coach_tenures (61)            — Trainer-Amtszeiten via Date-Range
playoff_series (68)           — Round + Wins-Verhältnis + Winner
articles (131)                — News aus 10 Quellen, pgvector(768)-Embedding
sync_log                      — Phase-2-Trigger für Neo4j-Replikation
```

### Fallstricke der hockeydata-Rohdaten

Drei Muster, die stillschweigend falsche Daten erzeugen — alle im Loader abgefangen,
Reparatur-Skript: `scripts/fix_phantom_results.py`:

| Symptom | Ursache | Behandlung |
|---|---|---|
| Ganze Spielpläne als 0:0-Ergebnisse | `homeTeamScore=0` statt `null` bei angesetzten Spielen | nur übernehmen, wenn `gameStatus != 0` |
| Halbe Liga auf "Platz 1" | Tabelle vor dem 1. Spieltag: jedes Team Rang 1, 0 Spiele | `final_rank` erst ab `gamesPlayed > 0` |
| Fremde Spieler in der Falken-Historie | Team-Filter über Kürzel — "HEC" ist *Höchstadt*, die Falken sind "HNF_" | Filter über `teamId` (47011, ab 26/27 70543) |

Dazu: der Klub tritt ab 2026/27 als "Heilbronner EC Falken" mit neuer teamId an.
`scripts/merge_known_duplicates.py` führt die Schreibweisen zusammen, sonst zerfällt
die Vereinshistorie in zwei Teams; der tägliche Sync ruft das automatisch auf.

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
│   │   ├── web_search.py     — Exa + Tavily, mit Anbieterwahl
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
| Web-Such-Call | Exa ~1 s, Tavily 2-5 s |
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

## Datenaktualität

Bis Juli 2026 lief jeder Load von Hand — mit dem Ergebnis, dass die DB ab März
unbemerkt einfror, während die App weiter selbstbewusst antwortete. Seitdem:

| Baustein | Zweck |
|---|---|
| `.github/workflows/sync.yml` | täglich 05:00 UTC, ruft den Sync auf und pingt die App |
| `scripts/sync_daily.py` | News-RSS + Web-Harvest + Spiele/Tabelle + Aktualitäts-Report |
| `scripts/load_season.py --discover 2027/28` | einmal pro Saison: neue divisionId ermitteln |
| `falken_kb/ingestion/scrapers/web_news.py` | Lokalpresse über Web-Suche, weil deren RSS-Feeds tot sind |
| `falken_kb/ingestion/scrapers/falken_preseason.py` | Testspiele von der Vereinsseite — hockeydata führt nur den Ligabetrieb |

**Einmal pro Saison von Hand**: `--discover` laufen lassen und die gefundene
divisionId in `scripts/sync_daily.py` (`CURRENT_SEASON_DIVISION_ID`) eintragen.
