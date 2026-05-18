-- ============================================================================
-- RPCs — werden aus dem Python-Code via Supabase REST aufgerufen
-- (vermeidet direkte Postgres-Verbindung, läuft mit service_role-Key)
-- ============================================================================
SET search_path TO falken, public;

-- ---------------------------------------------------------------------------
-- exec_sql: führt ein vom LLM generiertes SELECT aus, gibt Result als JSON.
-- Sicherheit: SECURITY DEFINER + Hard-Cap auf SELECT-only (kein DDL/DML).
-- Wird nur vom Backend mit service_role-Key aufgerufen, nie vom Frontend.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION falken.exec_sql(query_text text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = falken, public
AS $$
DECLARE
    trimmed text := regexp_replace(query_text, '^\s+', '');
    first_word text;
    result jsonb;
BEGIN
    first_word := upper(split_part(trimmed, ' ', 1));
    IF first_word NOT IN ('SELECT', 'WITH', 'EXPLAIN') THEN
        RAISE EXCEPTION 'Only SELECT/WITH/EXPLAIN allowed, got: %', first_word;
    END IF;
    -- Verbiete riskante Pattern hart
    IF trimmed ~* '\m(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|COPY)\M' THEN
        RAISE EXCEPTION 'DDL/DML keywords detected — not allowed';
    END IF;
    EXECUTE format('SELECT COALESCE(jsonb_agg(t), ''[]''::jsonb) FROM (%s) t', trimmed) INTO result;
    RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION falken.exec_sql(text) TO authenticated, service_role;

-- ---------------------------------------------------------------------------
-- search_articles: pgvector-Top-K mit gegebenem Query-Embedding
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION falken.search_articles(
    query_embedding vector,
    match_count int DEFAULT 6
)
RETURNS TABLE(
    id uuid,
    title text,
    source text,
    published_at timestamptz,
    excerpt text,
    similarity real
)
LANGUAGE sql STABLE
AS $$
    SELECT
        a.id,
        a.title,
        a.source,
        a.published_at,
        LEFT(a.body, 800) AS excerpt,
        (1 - (a.embedding <=> query_embedding))::real AS similarity
    FROM falken.articles a
    WHERE a.embedding IS NOT NULL
    ORDER BY a.embedding <=> query_embedding
    LIMIT match_count;
$$;

GRANT EXECUTE ON FUNCTION falken.search_articles(vector, int) TO authenticated, service_role;

-- ---------------------------------------------------------------------------
-- Schema-Beschreibung als View für Gemma's SQL-Prompt
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW falken.schema_info AS
SELECT
    c.relname AS table_name,
    a.attname AS column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
    a.attnotnull AS not_null
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'falken'
  AND c.relkind IN ('r','v')
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;

-- ---------------------------------------------------------------------------
-- Falken-Schema im PostgREST-API verfügbar machen
-- (REST würde sonst nur public Schema sehen)
-- ---------------------------------------------------------------------------
-- Dies muss eigentlich in der Supabase-Config (db.schemas / pgrst.db_schemas) stehen,
-- aber als Workaround: Wir legen Views/Tabellen-Aliase in `public` an, die auf `falken` zeigen.

-- Wrapper-Views in public, damit PostgREST sie sieht
CREATE OR REPLACE VIEW public.falken_seasons AS SELECT * FROM falken.seasons;
CREATE OR REPLACE VIEW public.falken_teams AS SELECT * FROM falken.teams;
CREATE OR REPLACE VIEW public.falken_players AS SELECT * FROM falken.players;
CREATE OR REPLACE VIEW public.falken_games AS SELECT * FROM falken.games;
CREATE OR REPLACE VIEW public.falken_team_seasons AS SELECT * FROM falken.team_seasons;
CREATE OR REPLACE VIEW public.falken_player_seasons AS SELECT * FROM falken.player_seasons;
CREATE OR REPLACE VIEW public.falken_player_stats AS SELECT * FROM falken.player_stats;
CREATE OR REPLACE VIEW public.falken_goalie_stats AS SELECT * FROM falken.goalie_stats;
CREATE OR REPLACE VIEW public.falken_articles AS SELECT * FROM falken.articles;
CREATE OR REPLACE VIEW public.falken_skater_stats_v AS SELECT * FROM falken.falken_skater_stats;
CREATE OR REPLACE VIEW public.falken_goalie_stats_v AS SELECT * FROM falken.falken_goalie_stats;
CREATE OR REPLACE VIEW public.season_standings_v AS SELECT * FROM falken.season_standings;

-- Insert-/Update-Funktionen für die wichtigsten Upserts (loaders verwenden diese via RPC)
CREATE OR REPLACE FUNCTION falken.upsert_season(
    p_label text, p_league text, p_league_tier smallint, p_hockeydata_id text
) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
    INSERT INTO falken.seasons (label, league, league_tier, source_ids)
    VALUES (p_label, p_league, p_league_tier, jsonb_build_object('hockeydata', p_hockeydata_id))
    ON CONFLICT (label, league) DO UPDATE
        SET source_ids = falken.seasons.source_ids || EXCLUDED.source_ids,
            league_tier = EXCLUDED.league_tier
    RETURNING id INTO v_id;
    RETURN v_id;
END $$;

CREATE OR REPLACE FUNCTION falken.upsert_team(
    p_name text, p_short_name text, p_hockeydata_id text
) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
    INSERT INTO falken.teams (name, short_name, source_ids)
    VALUES (p_name, p_short_name, jsonb_build_object('hockeydata', p_hockeydata_id))
    ON CONFLICT (name) DO UPDATE
        SET short_name = COALESCE(EXCLUDED.short_name, falken.teams.short_name),
            source_ids = falken.teams.source_ids || EXCLUDED.source_ids
    RETURNING id INTO v_id;
    RETURN v_id;
END $$;

CREATE OR REPLACE FUNCTION falken.upsert_team_season(
    p_team_id uuid, p_season_id uuid, p_rank int, p_gp int, p_wins int, p_losses int,
    p_ot_wins int, p_ot_losses int, p_points int, p_gf int, p_ga int, p_hd_id text
) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO falken.team_seasons (team_id, season_id, final_rank, games_played,
        wins, losses, ot_wins, ot_losses, points, goals_for, goals_against, source_ids)
    VALUES (p_team_id, p_season_id, p_rank, p_gp, p_wins, p_losses,
            p_ot_wins, p_ot_losses, p_points, p_gf, p_ga,
            jsonb_build_object('hockeydata', p_hd_id))
    ON CONFLICT (team_id, season_id) DO UPDATE SET
        final_rank=EXCLUDED.final_rank, games_played=EXCLUDED.games_played,
        wins=EXCLUDED.wins, losses=EXCLUDED.losses, ot_wins=EXCLUDED.ot_wins,
        ot_losses=EXCLUDED.ot_losses, points=EXCLUDED.points,
        goals_for=EXCLUDED.goals_for, goals_against=EXCLUDED.goals_against,
        source_ids=falken.team_seasons.source_ids || EXCLUDED.source_ids;
END $$;

CREATE OR REPLACE FUNCTION falken.upsert_game(
    p_season_id uuid, p_date timestamptz, p_game_type text,
    p_home_team_id uuid, p_away_team_id uuid,
    p_home_score smallint, p_away_score smallint,
    p_overtime bool, p_shootout bool, p_hd_id text
) RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE v_inserted boolean;
BEGIN
    INSERT INTO falken.games (season_id, date, game_type, home_team_id, away_team_id,
        home_score, away_score, overtime, shootout, source_ids)
    SELECT p_season_id, p_date, p_game_type, p_home_team_id, p_away_team_id,
           p_home_score, p_away_score, p_overtime, p_shootout,
           jsonb_build_object('hockeydata', p_hd_id)
    WHERE NOT EXISTS (
        SELECT 1 FROM falken.games WHERE (source_ids->>'hockeydata') = p_hd_id
    );
    GET DIAGNOSTICS v_inserted = ROW_COUNT;
    RETURN v_inserted;
END $$;

GRANT EXECUTE ON FUNCTION falken.upsert_season TO service_role;
GRANT EXECUTE ON FUNCTION falken.upsert_team TO service_role;
GRANT EXECUTE ON FUNCTION falken.upsert_team_season TO service_role;
GRANT EXECUTE ON FUNCTION falken.upsert_game TO service_role;
