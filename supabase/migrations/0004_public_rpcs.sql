-- ============================================================================
-- Public-Schema-Wrapper für alle RPCs
-- PostgREST sucht standardmäßig nur im public Schema — daher Wrapper.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.exec_sql(query_text text)
RETURNS jsonb LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.exec_sql(query_text); $$;

GRANT EXECUTE ON FUNCTION public.exec_sql(text) TO authenticated, service_role;


CREATE OR REPLACE FUNCTION public.search_articles(query_embedding vector, match_count int DEFAULT 6)
RETURNS TABLE(id uuid, title text, source text, published_at timestamptz, excerpt text, similarity real)
LANGUAGE sql STABLE
SET search_path = falken, public
AS $$ SELECT * FROM falken.search_articles(query_embedding, match_count); $$;

GRANT EXECUTE ON FUNCTION public.search_articles(vector, int) TO authenticated, service_role;


CREATE OR REPLACE FUNCTION public.upsert_season(
    p_label text, p_league text, p_league_tier smallint, p_hockeydata_id text
) RETURNS uuid LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_season(p_label, p_league, p_league_tier, p_hockeydata_id); $$;

GRANT EXECUTE ON FUNCTION public.upsert_season(text, text, smallint, text) TO service_role;


CREATE OR REPLACE FUNCTION public.upsert_team(
    p_name text, p_short_name text, p_hockeydata_id text
) RETURNS uuid LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_team(p_name, p_short_name, p_hockeydata_id); $$;

GRANT EXECUTE ON FUNCTION public.upsert_team(text, text, text) TO service_role;


CREATE OR REPLACE FUNCTION public.upsert_team_season(
    p_team_id uuid, p_season_id uuid, p_rank int, p_gp int, p_wins int, p_losses int,
    p_ot_wins int, p_ot_losses int, p_points int, p_gf int, p_ga int, p_hd_id text
) RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_team_season(p_team_id, p_season_id, p_rank, p_gp, p_wins, p_losses,
        p_ot_wins, p_ot_losses, p_points, p_gf, p_ga, p_hd_id); $$;

GRANT EXECUTE ON FUNCTION public.upsert_team_season(uuid, uuid, int, int, int, int, int, int, int, int, int, text) TO service_role;


CREATE OR REPLACE FUNCTION public.upsert_game(
    p_season_id uuid, p_date timestamptz, p_game_type text,
    p_home_team_id uuid, p_away_team_id uuid,
    p_home_score smallint, p_away_score smallint,
    p_overtime bool, p_shootout bool, p_hd_id text
) RETURNS boolean LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_game(p_season_id, p_date, p_game_type, p_home_team_id, p_away_team_id,
        p_home_score, p_away_score, p_overtime, p_shootout, p_hd_id); $$;

GRANT EXECUTE ON FUNCTION public.upsert_game(uuid, timestamptz, text, uuid, uuid, smallint, smallint, bool, bool, text) TO service_role;


-- Schema-Cache-Reload
NOTIFY pgrst, 'reload schema';
