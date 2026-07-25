# Falken Knowledge Base

GenAI-basierte Wissensdatenbank über die Heilbronner Falken (Eishockey).

**Status:** Phase 1 MVP — Code-Skelett komplett, lauffähig sobald Supabase-Credentials vorliegen.

---

## Aktueller Stand (Was funktioniert / Was fehlt)

### ✅ Komplett lauffähig + befüllt
- **hockeydata-API-Client** mit DEB-Key + Referer `deb-online.live`, Rate-Limit 1 Req / 2-3 Sek + Jitter, alle 11 Endpoints
- **DGX-Client** für Gemma-4-31B + nomic-embed-text — Chat, Structured-Output, Embeddings 768d
- **DB-Schema** (graph-ready für Phase 2): 6 Knoten + 7 Kanten + `sync_log` mit >12k Mutations-Einträgen
- **GenAI-Orchestrator** mit Klassifikation (fact/narrative/trend) + 3 Handlern + Streamlit-UI
- **5 Backfill-Loader** komplett durchgelaufen:
  - **EliteProspects:** 10 Saisons × ~25 Spieler = 259 Player-Saisons + Stats
  - **eishockey-statistiken.de:** 43 Saisons (zurück bis 1980/81) + 58 Coach-Tenures
  - **del-2.org:** alle 83 Rounds → tausende DEL2-Spiele 2007-2026 (Hauptrunden + Playoffs + Playdowns + Testspiele + Cups)
  - **Wikipedia:** 10 DEL2-Saison-Artikel mit Embeddings (RAG-fähig)
  - **Playoff-Loader:** 45 Playoff-/Playdown-Serien + 180 historische Playoff-Einzelspiele
- **Cross-Source-Dedup:** 16 Team-Konsolidierungen (319 Spiele zusammengeführt)

### 🚀 Phase 2 (bereits eingeplant)
- **Neo4j-Layer** als reines Add-on: ein Worker polled `sync_log` und repliziert nach Neo4j. Mapping ist dokumentiert in `docs/graph-model.md`. Kein Phase-1-Code wird angefasst.

---

## Architektur in 30 Sekunden

```
┌──────────────┐   ┌────────────────┐   ┌──────────────┐
│ Streamlit UI │──▶│ GenAI Orches.  │──▶│ DGX (Gemma)  │
└──────────────┘   │                │   └──────────────┘
                   │ ┌────────────┐ │           │
                   │ │ Router     │ │           │
                   │ ├────────────┤ │           │
                   │ │ fact_sql   │ │   ┌──────────────┐
                   │ │ narrative  │─┼──▶│ Supabase     │
                   │ │ trend_chart│ │   │ (Postgres +  │
                   │ └────────────┘ │   │  pgvector)   │
                   └────────────────┘   └──────────────┘
                                                ▲
                   ┌────────────────┐           │
                   │ Ingestion      │           │
                   │ ┌────────────┐ │           │
                   │ │ hockeydata │─┼───────────┘
                   │ │ scrapers   │ │
                   │ │ news RSS   │ │
                   │ └────────────┘ │
                   └────────────────┘
```

---

## Setup

### 1. `.env` (Supabase + DGX-Keys sind bereits eingetragen)

Standardmäßig liegt `.env` mit allen Werten schon im Repo. Nur falls Du
Werte änderst: `.env.example` als Referenz.

### 2. Python-Deps

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Migrations im Studio SQL Editor ausführen (einmalig)

Direkter Postgres-Connect zu supabase.siller.io ist über den Supavisor-Pooler
geblockt (Tenant-Config), wir nutzen daher den Studio SQL Editor:

1. Öffne `https://studio.supabase.siller.io` → SQL Editor → **New query**
2. Inhalt von `supabase/migrations/0001_init.sql` reinkopieren → **Run**
3. Inhalt von `supabase/migrations/0002_indexes.sql` reinkopieren → **Run**
4. Inhalt von `supabase/migrations/0003_rpcs.sql` reinkopieren → **Run**

Erzeugt:
- Schema `falken` mit allen Tabellen, Indizes, Triggern (sync_log für Phase 2)
- pgvector HNSW-Index für Articles
- RPCs `exec_sql`, `search_articles`, `upsert_season/team/team_season/game`
- Public-Schema-Views (damit PostgREST sie sieht)

### 4. Aktuelle Saison laden

```bash
# täglicher Sync: News + Spiele + Tabelle (läuft auch als GitHub Action)
python3 scripts/sync_daily.py

# einmal pro Saison: neue divisionId ermitteln und in sync_daily.py eintragen
python3 scripts/load_season.py --discover 2027/28
python3 scripts/load_season.py --season 2027/28 --league "Oberliga Süd" --division <ID>
```

Lädt über die hockeydata-API → Supabase (REST + RPCs), mit den Keys aus `.env`,
kein DB-Passwort nötig. `scripts/bootstrap_current_season.py` ist der alte,
fest auf 2025/26 verdrahtete Vorgänger.

### 5. Streamlit starten

```bash
streamlit run frontend/streamlit_app.py
```

Browser öffnet sich auf `http://localhost:8501`.

---

## Smoke-Tests (laufen ohne DB)

```bash
# hockeydata-API verifizieren
python3 -m falken_kb.ingestion.smoke_test

# DGX-Endpunkt verifizieren
python3 -m falken_kb.genai.smoke_test

# Division-Discovery für aktuelle Saison
python3 -m falken_kb.ingestion.division_finder
```

## Validierung & Datenqualität

```bash
# Volles Audit-Suite: Consistency-Checks + Coverage-Report + Ground-Truth-Vergleich
python3 -m falken_kb.validation

# Player-Duplikate prüfen
python3 -m falken_kb.ingestion.dedup
python3 -m falken_kb.ingestion.dedup teams

# Cross-Source-Diff (re-fetcht Quellen live und vergleicht mit DB-Werten)
python3 scripts/cross_source_diff.py
```

Die Ground-Truth-Datei liegt in `tests/ground_truth.yaml` — JEDE Behauptung
muss aus min. 2 unabhängigen Quellen verifiziert sein. Aktuell sind 24+
manuell verifizierte Fakten drin (Falken-Endplatzierungen, Topscorer pro Saison,
Trainer-Historie, Playoff-Ausgänge, bekannte Extremwerte).

---

## Wichtige Erkenntnisse aus der API-Verprobung

- **API-Key:** Der DEB-Key (`3c5a99…`) ist referer-gelockt auf `deb-online.live` — funktioniert mit dem korrekten Referer-Header
- **Pfad-Konvention:** Alle Daten-Endpoints unter `/data/ih/…`, Discovery unter `/data/api/…`
- **Status-Codes:** `1=Ok`, `-1=Guid not found`, `3/4=ApiKey invalid` (Referer), `-8=Not calculated` (Saison-Wrapper-ID statt echter Wettbewerb)
- **Response-Format:** Daten kommen unter `data.rows` (nicht `data.teams` wie ursprünglich vermutet)
- **`lang=en`** ist Pflicht-Param — sonst liefern manche Endpoints leeres `data`
- **Saison-Wrapper-IDs** (aus GetSeasons) sind NICHT die Division-IDs für Standings/Schedule. Die echten IDs werden per Scrape aus deb-online.live geholt (siehe `division_finder.py`).
- **Historie:** DEL2 nur 2021/22–24/25 via API, DEB-Oberliga 2018/19–25/26. Ältere Falken-Saisons (2015/16–2020/21) brauchen Scraper.

### Supabase-Setup-Notizen

- **supabase.siller.io ist Cloudron-hosted und Multi-App** (z.B. parkhaus-Tabelle ist schon da). Wir nutzen daher ein eigenes Schema `falken.*` und legen für PostgREST-Sichtbarkeit `public.falken_*`-Views an.
- **Direkter Postgres-Connect ist über Supavisor-Pooler geblockt** ("Tenant or user not found"), Single-Tenant-Config in Cloudron-Setup. Wir nutzen ausschließlich REST + RPCs mit dem Service-Role-Key.
- **Gemma-generiertes SQL** läuft über die RPC `exec_sql` mit Hard-Cap auf SELECT/WITH/EXPLAIN (kein DDL/DML möglich). Plus Pattern-Match auf gefährliche Keywords (INSERT, UPDATE, DELETE, DROP, ...).

---

## Struktur

```
falken-knowledge-base/
├── supabase/migrations/    # SQL-Schema
├── falken_kb/
│   ├── config.py           # pydantic-settings (alle Env-Werte)
│   ├── db.py               # psycopg connection helpers
│   ├── ingestion/
│   │   ├── hockeydata_client.py   # async API-Client
│   │   ├── division_finder.py     # scrape deb-online.live für divisionIds
│   │   ├── loaders.py             # API-Response → DB upserts
│   │   └── smoke_test.py
│   └── genai/
│       ├── dgx_client.py          # OpenAI-kompatibler Gemma-Client
│       ├── router.py              # Klassifikation fact/narrative/trend
│       ├── orchestrator.py        # Top-Level-Routing
│       └── handlers/
│           ├── fact_sql.py        # SQL-Generation + Synthesis
│           ├── narrative_rag.py   # pgvector + Synthesis
│           └── trend_chart.py     # SQL + Vega-Lite-Spec
├── frontend/streamlit_app.py
├── scripts/
│   ├── run_migrations.py
│   └── bootstrap_current_season.py
├── docs/
│   └── graph-model.md     # Postgres ↔ Neo4j Mapping für Phase 2
├── cache/                  # Disk-Cache für Scraper + Division-Finder
└── .env / .env.example
```

---

## Wichtige Designentscheidungen

1. **UUIDs überall** statt sequentieller IDs — für Phase-2-Graph-Replikation und Cross-Source-Merges.
2. **`source_ids` JSONB** auf jeder Entity → hält externe IDs (hockeydata, EliteProspects, Wikipedia) für Dedup.
3. **`sync_log` Trigger auf allen Mutationen** → Phase 2 (Neo4j) kann polled, nichts in Phase 1 muss angefasst werden.
4. **Conventions für Naming** (Kanten-Tabellen heißen wie ihre künftige Neo4j-Relationship) — siehe `docs/graph-model.md`.
5. **Gemma ohne Tool-Use** → Structured-Output via `json_schema` (mit `json_object`-Fallback, weil LiteLLM nicht durchreicht).
6. **Polite Scraping** — Rate-Limit + Caching auch bei zukünftigen Scraper-Erweiterungen verpflichtend.

---

## Phase-2-Vorbereitung im Phase-1-Code

- Schema ist graph-ready (siehe `docs/graph-model.md`)
- `sync_log` läuft ab Tag 1 mit
- Naming-Konvention dokumentiert
- Phase-2-Worker-Pseudocode in `docs/graph-model.md` enthalten

Mein Plan ist, Phase 2 in einer separaten Session in 2–3 Tagen umzusetzen — keine Eingriffe in Phase-1-Code nötig.
