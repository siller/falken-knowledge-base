-- ============================================================================
-- Falken Knowledge Base — Initial Schema
-- ============================================================================
-- Graph-ready Schema: Knoten- und Kanten-Tabellen sind so benannt, dass
-- Phase 2 (Neo4j-Replikation) als reines Add-on über sync_log funktioniert.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Eigenes Schema, damit wir Supabase-Default-Tabellen nicht stören
CREATE SCHEMA IF NOT EXISTS falken;
SET search_path TO falken, public;

-- ============================================================================
-- KNOTEN-TABELLEN (= Neo4j-Labels in Phase 2)
-- ============================================================================

-- Saisons: 2015/16 bis 2025/26 (auch Oberliga-Süd nach Abstieg)
CREATE TABLE seasons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label           TEXT NOT NULL,                              -- "2022/23"
    league          TEXT NOT NULL,                              -- "DEL2" | "Oberliga Süd"
    league_tier     SMALLINT NOT NULL,                          -- 2=DEL2, 3=Oberliga
    start_date      DATE,
    end_date        DATE,
    source_ids      JSONB DEFAULT '{}'::jsonb,                  -- {"hockeydata": "season-id"}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (label, league)
);

CREATE TABLE teams (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,                       -- "Heilbronner Falken"
    short_name      TEXT,                                       -- "HEI"
    alt_names       TEXT[] DEFAULT '{}',                        -- ["Falken", "HEC", ...]
    city            TEXT,
    arena           TEXT,
    founded_year    SMALLINT,
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE players (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    first_name      TEXT,
    last_name       TEXT,
    position        TEXT,                                       -- "F" | "D" | "G"
    nation          TEXT,                                       -- "DE", "CA", ...
    birthdate       DATE,
    height_cm       SMALLINT,
    weight_kg       SMALLINT,
    shoots          CHAR(1),                                    -- 'L' | 'R'
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_players_name ON players USING gin (name gin_trgm_ops);  -- Fuzzy-Match (pg_trgm-Extension oben geladen)

CREATE TABLE coaches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    first_name      TEXT,
    last_name       TEXT,
    nation          TEXT,
    birthdate       DATE,
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE games (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id       UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    date            TIMESTAMPTZ NOT NULL,
    game_type       TEXT NOT NULL,                              -- "regular" | "playoff" | "playdown" | "friendly"
    round_label     TEXT,                                       -- "Halbfinale", "Hauptrunde", ...
    home_team_id    UUID NOT NULL REFERENCES teams(id),
    away_team_id    UUID NOT NULL REFERENCES teams(id),
    home_score      SMALLINT,
    away_score      SMALLINT,
    overtime        BOOLEAN DEFAULT FALSE,
    shootout        BOOLEAN DEFAULT FALSE,
    venue           TEXT,
    attendance      INT,
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_games_season ON games(season_id);
CREATE INDEX idx_games_date ON games(date);
CREATE INDEX idx_games_home_team ON games(home_team_id);
CREATE INDEX idx_games_away_team ON games(away_team_id);

CREATE TABLE articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source          TEXT NOT NULL,                              -- "heilbronner-falken.de" | "stimme.de" | "del-2.org"
    url             TEXT NOT NULL UNIQUE,
    published_at    TIMESTAMPTZ,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    summary         TEXT,                                       -- optional LLM-Zusammenfassung
    -- Bezüge zu Entitäten (optional, vom Extractor gefüllt)
    season_id       UUID REFERENCES seasons(id),
    game_id         UUID REFERENCES games(id),
    embedding       vector(768),                                -- nomic-embed-text
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_published ON articles(published_at);
-- HNSW-Index für Vector-Search (separate Migration weil parametrisiert)

-- ============================================================================
-- KANTEN-TABELLEN (= Neo4j-Relationships in Phase 2)
-- ============================================================================

-- team -[:PLAYED_IN]-> season (mit Abschluss-Stats)
CREATE TABLE team_seasons (
    team_id         UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    season_id       UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    final_rank      SMALLINT,                                   -- 1..N
    games_played    SMALLINT,
    wins            SMALLINT,
    losses          SMALLINT,
    ot_wins         SMALLINT,
    ot_losses       SMALLINT,
    points          SMALLINT,
    goals_for       SMALLINT,
    goals_against   SMALLINT,
    -- Playoff/Playdown-Ergebnis (Text-Beschreibung)
    playoff_result  TEXT,                                       -- "Halbfinale (1:4 gegen Hannover)"
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (team_id, season_id)
);

-- player -[:SKATED_FOR]-> team (in einer season)
CREATE TABLE player_seasons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id         UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    season_id       UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    jersey_number   SMALLINT,
    role            TEXT,                                       -- "Captain", "Assistant", null
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (player_id, team_id, season_id)
);

CREATE INDEX idx_player_seasons_player ON player_seasons(player_id);
CREATE INDEX idx_player_seasons_team_season ON player_seasons(team_id, season_id);

-- Stats für Feldspieler (1:1 zu player_seasons)
CREATE TABLE player_stats (
    player_season_id UUID PRIMARY KEY REFERENCES player_seasons(id) ON DELETE CASCADE,
    games_played    SMALLINT,
    goals           SMALLINT,
    assists         SMALLINT,
    points          SMALLINT GENERATED ALWAYS AS (COALESCE(goals,0) + COALESCE(assists,0)) STORED,
    pim             SMALLINT,
    plus_minus      SMALLINT,
    ppg             SMALLINT,                                   -- Powerplay-Tore
    shg             SMALLINT,                                   -- Shorthanded-Tore
    gwg             SMALLINT,                                   -- Game-Winning-Goals
    shots           SMALLINT,
    shooting_pct    NUMERIC(4,1),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Stats für Torhüter (1:1 zu player_seasons)
CREATE TABLE goalie_stats (
    player_season_id UUID PRIMARY KEY REFERENCES player_seasons(id) ON DELETE CASCADE,
    games_played    SMALLINT,
    wins            SMALLINT,
    losses          SMALLINT,
    ot_losses       SMALLINT,
    shutouts        SMALLINT,
    goals_against   SMALLINT,
    saves           SMALLINT,
    shots_against   SMALLINT,
    gaa             NUMERIC(4,2),                               -- Goals Against Average
    save_pct        NUMERIC(5,3),                               -- 0.912 etc.
    minutes_played  INT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- coach -[:COACHED]-> team (Zeitraum)
CREATE TABLE coach_tenures (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id        UUID NOT NULL REFERENCES coaches(id) ON DELETE CASCADE,
    team_id         UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,                              -- "Headcoach" | "Assistant"
    start_date      DATE NOT NULL,
    end_date        DATE,                                       -- NULL = aktuell
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_coach_tenures_team ON coach_tenures(team_id);
CREATE INDEX idx_coach_tenures_coach ON coach_tenures(coach_id);

-- game -[:GENERATED_EVENT]-> game_event (Tore, Strafen, etc.)
CREATE TABLE game_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id             UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    period              SMALLINT NOT NULL,                      -- 1, 2, 3, 4=OT, 5=Shootout
    time_in_period      INTERVAL,                               -- "12:34"
    type                TEXT NOT NULL,                          -- "goal" | "penalty" | "faceoff" | ...
    team_id             UUID REFERENCES teams(id),
    primary_player_id   UUID REFERENCES players(id),
    secondary_player_ids UUID[] DEFAULT '{}',                   -- Assists, etc.
    detail              JSONB,                                  -- type-specific data (Strafenart, Bullygewinner, ...)
    description         TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_game_events_game ON game_events(game_id);
CREATE INDEX idx_game_events_player ON game_events(primary_player_id);
CREATE INDEX idx_game_events_type ON game_events(type);

-- Playoff-Serien
CREATE TABLE playoff_series (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id       UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    round           TEXT NOT NULL,                              -- "Viertelfinale" | "Halbfinale" | "Finale" | "Playdown"
    team_a_id       UUID NOT NULL REFERENCES teams(id),
    team_b_id       UUID NOT NULL REFERENCES teams(id),
    wins_a          SMALLINT DEFAULT 0,
    wins_b          SMALLINT DEFAULT 0,
    winner_team_id  UUID REFERENCES teams(id),
    game_ids        UUID[] DEFAULT '{}',                        -- Referenz auf games
    source_ids      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_playoff_series_season ON playoff_series(season_id);

-- ============================================================================
-- SYNC LOG (für Phase 2 Neo4j-Replikation)
-- ============================================================================

CREATE TABLE sync_log (
    id              BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    row_id          UUID,                                       -- primary key der mutierten Row (NULL bei composite PKs)
    composite_key   JSONB,                                      -- für Tabellen mit composite PK (team_seasons etc.)
    op              CHAR(1) NOT NULL,                           -- 'I'nsert | 'U'pdate | 'D'elete
    payload         JSONB,                                      -- Snapshot der neuen Row (für UPDATE/INSERT)
    occurred_at     TIMESTAMPTZ DEFAULT NOW(),
    replicated_to   JSONB DEFAULT '{}'::jsonb                   -- {"neo4j": "2026-05-17T12:00:00Z"}
);

CREATE INDEX idx_sync_log_table ON sync_log(table_name);
CREATE INDEX idx_sync_log_occurred ON sync_log(occurred_at);
CREATE INDEX idx_sync_log_not_replicated ON sync_log(occurred_at) WHERE (replicated_to = '{}'::jsonb);

-- Generischer Trigger
CREATE OR REPLACE FUNCTION log_sync_event() RETURNS TRIGGER AS $$
DECLARE
    pk_value UUID;
    composite JSONB;
BEGIN
    IF TG_OP = 'DELETE' THEN
        BEGIN pk_value := OLD.id; EXCEPTION WHEN OTHERS THEN pk_value := NULL; END;
        IF pk_value IS NULL THEN composite := to_jsonb(OLD); END IF;
        INSERT INTO sync_log(table_name, row_id, composite_key, op, payload)
        VALUES (TG_TABLE_NAME, pk_value, composite, 'D', to_jsonb(OLD));
        RETURN OLD;
    ELSE
        BEGIN pk_value := NEW.id; EXCEPTION WHEN OTHERS THEN pk_value := NULL; END;
        IF pk_value IS NULL THEN composite := to_jsonb(NEW); END IF;
        INSERT INTO sync_log(table_name, row_id, composite_key, op, payload)
        VALUES (TG_TABLE_NAME, pk_value, composite,
                CASE WHEN TG_OP = 'INSERT' THEN 'I' ELSE 'U' END,
                to_jsonb(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger auf alle Knoten- und Kanten-Tabellen
DO $$
DECLARE
    t TEXT;
    target_tables TEXT[] := ARRAY[
        'seasons','teams','players','coaches','games','articles',
        'team_seasons','player_seasons','player_stats','goalie_stats',
        'coach_tenures','game_events','playoff_series'
    ];
BEGIN
    FOREACH t IN ARRAY target_tables LOOP
        EXECUTE format('CREATE TRIGGER %I_sync_trigger AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION log_sync_event();', t, t);
    END LOOP;
END $$;

-- ============================================================================
-- updated_at-Trigger (Hygiene)
-- ============================================================================

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at := NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE t TEXT;
BEGIN
    FOR t IN
        SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='falken' AND c.relkind='r'
          AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attname='updated_at')
    LOOP
        EXECUTE format('CREATE TRIGGER %I_touch_updated AFTER UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION touch_updated_at();', t, t);
    END LOOP;
END $$;
