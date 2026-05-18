-- ============================================================================
-- Coach- + Tenure-Upsert-RPCs + Wrapper-Views
-- ============================================================================

CREATE OR REPLACE VIEW public.falken_coaches AS SELECT * FROM falken.coaches;
CREATE OR REPLACE VIEW public.falken_coach_tenures AS SELECT * FROM falken.coach_tenures;
CREATE OR REPLACE VIEW public.falken_playoff_series AS SELECT * FROM falken.playoff_series;
CREATE OR REPLACE VIEW public.falken_game_events AS SELECT * FROM falken.game_events;

GRANT SELECT ON public.falken_coaches, public.falken_coach_tenures, public.falken_playoff_series, public.falken_game_events
  TO anon, authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON public.falken_coaches, public.falken_coach_tenures, public.falken_playoff_series, public.falken_game_events
  TO service_role;


CREATE OR REPLACE FUNCTION falken.upsert_coach(p_name text)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
    SELECT id INTO v_id FROM falken.coaches WHERE name = p_name LIMIT 1;
    IF v_id IS NOT NULL THEN RETURN v_id; END IF;
    INSERT INTO falken.coaches (name, source_ids)
    VALUES (p_name, jsonb_build_object('eishockey_statistiken', true))
    RETURNING id INTO v_id;
    RETURN v_id;
END $$;

CREATE OR REPLACE FUNCTION public.upsert_coach(p_name text)
RETURNS uuid LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_coach(p_name); $$;

GRANT EXECUTE ON FUNCTION public.upsert_coach(text) TO service_role;


CREATE OR REPLACE FUNCTION falken.upsert_coach_tenure(
    p_coach_id uuid, p_team_id uuid, p_role text, p_start date, p_end date, p_source text
)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
    SELECT id INTO v_id FROM falken.coach_tenures
        WHERE coach_id = p_coach_id AND team_id = p_team_id AND start_date = p_start LIMIT 1;
    IF v_id IS NOT NULL THEN RETURN v_id; END IF;
    INSERT INTO falken.coach_tenures (coach_id, team_id, role, start_date, end_date, source_ids)
    VALUES (p_coach_id, p_team_id, p_role, p_start, p_end, jsonb_build_object('source', p_source))
    RETURNING id INTO v_id;
    RETURN v_id;
END $$;

CREATE OR REPLACE FUNCTION public.upsert_coach_tenure(
    p_coach_id uuid, p_team_id uuid, p_role text, p_start date, p_end date, p_source text
)
RETURNS uuid LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_coach_tenure(p_coach_id, p_team_id, p_role, p_start, p_end, p_source); $$;

GRANT EXECUTE ON FUNCTION public.upsert_coach_tenure(uuid, uuid, text, date, date, text) TO service_role;


-- Variante von upsert_team_season die auch playoff_result mitnimmt
CREATE OR REPLACE FUNCTION falken.upsert_team_season_full(
    p_team_id uuid, p_season_id uuid, p_rank int, p_gp int, p_wins int, p_losses int,
    p_ot_wins int, p_ot_losses int, p_points int, p_gf int, p_ga int,
    p_playoff_result text, p_source text
) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO falken.team_seasons (team_id, season_id, final_rank, games_played,
        wins, losses, ot_wins, ot_losses, points, goals_for, goals_against, playoff_result, source_ids)
    VALUES (p_team_id, p_season_id, p_rank, p_gp, p_wins, p_losses,
            p_ot_wins, p_ot_losses, p_points, p_gf, p_ga, p_playoff_result,
            jsonb_build_object('source', p_source))
    ON CONFLICT (team_id, season_id) DO UPDATE SET
        final_rank=COALESCE(EXCLUDED.final_rank, falken.team_seasons.final_rank),
        games_played=COALESCE(EXCLUDED.games_played, falken.team_seasons.games_played),
        wins=COALESCE(EXCLUDED.wins, falken.team_seasons.wins),
        losses=COALESCE(EXCLUDED.losses, falken.team_seasons.losses),
        ot_wins=COALESCE(EXCLUDED.ot_wins, falken.team_seasons.ot_wins),
        ot_losses=COALESCE(EXCLUDED.ot_losses, falken.team_seasons.ot_losses),
        points=COALESCE(EXCLUDED.points, falken.team_seasons.points),
        goals_for=COALESCE(EXCLUDED.goals_for, falken.team_seasons.goals_for),
        goals_against=COALESCE(EXCLUDED.goals_against, falken.team_seasons.goals_against),
        playoff_result=COALESCE(EXCLUDED.playoff_result, falken.team_seasons.playoff_result),
        source_ids=falken.team_seasons.source_ids || EXCLUDED.source_ids;
END $$;

CREATE OR REPLACE FUNCTION public.upsert_team_season_full(
    p_team_id uuid, p_season_id uuid, p_rank int, p_gp int, p_wins int, p_losses int,
    p_ot_wins int, p_ot_losses int, p_points int, p_gf int, p_ga int,
    p_playoff_result text, p_source text
) RETURNS void LANGUAGE sql SECURITY DEFINER
SET search_path = falken, public
AS $$ SELECT falken.upsert_team_season_full(p_team_id, p_season_id, p_rank, p_gp, p_wins, p_losses,
        p_ot_wins, p_ot_losses, p_points, p_gf, p_ga, p_playoff_result, p_source); $$;

GRANT EXECUTE ON FUNCTION public.upsert_team_season_full(uuid, uuid, int, int, int, int, int, int, int, int, int, text, text) TO service_role;

NOTIFY pgrst, 'reload schema';
