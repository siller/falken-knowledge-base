-- ============================================================================
-- is_focus_team_season Flag + Filter-View
--
-- Lösung für die "scheinbaren Dubletten": DEL2 + Oberliga Süd laufen parallel
-- in derselben Saison. Die Falken sind in JEWEILS EINER der beiden — die
-- jeweils andere ist eine "Hintergrund-Saison" mit fremden Teams.
--
-- Mit dieser Spalte können wir klar zwischen "Falken-Saison" und
-- "Hintergrund-Saison" unterscheiden, ohne Daten zu verlieren.
-- ============================================================================

ALTER TABLE falken.seasons
    ADD COLUMN IF NOT EXISTS is_focus_team_season BOOLEAN DEFAULT FALSE;

-- Initialer Backfill: jede Saison mit Falken-team_season-Eintrag wird als
-- focus_team_season markiert.
UPDATE falken.seasons s
SET is_focus_team_season = TRUE
WHERE EXISTS (
    SELECT 1 FROM falken.team_seasons ts
    JOIN falken.teams t ON t.id = ts.team_id
    WHERE ts.season_id = s.id AND t.name = 'Heilbronner Falken'
);

-- Trigger: bei jedem Insert/Update auf team_seasons mit Falken → setze Flag
CREATE OR REPLACE FUNCTION falken.update_focus_season_flag() RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = falken, public
AS $$
DECLARE
    is_falken BOOLEAN;
BEGIN
    SELECT TRUE INTO is_falken
    FROM falken.teams
    WHERE id = NEW.team_id AND name = 'Heilbronner Falken';

    IF is_falken THEN
        UPDATE falken.seasons SET is_focus_team_season = TRUE
        WHERE id = NEW.season_id AND is_focus_team_season = FALSE;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS team_seasons_focus_flag_trigger ON falken.team_seasons;
CREATE TRIGGER team_seasons_focus_flag_trigger
    AFTER INSERT OR UPDATE OF team_id ON falken.team_seasons
    FOR EACH ROW EXECUTE FUNCTION falken.update_focus_season_flag();

-- Re-create View ohne neue Spalte zu vergessen
CREATE OR REPLACE VIEW public.falken_seasons AS SELECT * FROM falken.seasons;

-- Neue Convenience-View nur für Falken-Saisons (keine Hintergrund-DEL2-23-25)
CREATE OR REPLACE VIEW public.falken_focus_seasons AS
SELECT * FROM falken.seasons WHERE is_focus_team_season = TRUE
ORDER BY label DESC;

GRANT SELECT ON public.falken_seasons, public.falken_focus_seasons
    TO anon, authenticated, service_role;

-- Update season_standings View — neue Spalte `is_focus_team_season` muss
-- ans ENDE: CREATE OR REPLACE VIEW erlaubt nur das Anhängen von Spalten,
-- kein Einfügen in der Mitte (sonst 42P16 "cannot change name of view column").
-- Bestehende Spalten-Reihenfolge MUSS exakt erhalten bleiben (1-14):
-- season, league, final_rank, team, games_played, wins, losses,
-- ot_wins, ot_losses, points, goals_for, goals_against, goal_diff, playoff_result
-- Neue Spalten (league_tier, is_focus_team_season) NUR ans Ende anhängen.
CREATE OR REPLACE VIEW falken.season_standings AS
SELECT
    s.label AS season,
    s.league,
    ts.final_rank,
    t.name AS team,
    ts.games_played,
    ts.wins,
    ts.losses,
    ts.ot_wins,
    ts.ot_losses,
    ts.points,
    ts.goals_for,
    ts.goals_against,
    (ts.goals_for - ts.goals_against) AS goal_diff,
    ts.playoff_result,
    s.league_tier,
    s.is_focus_team_season
FROM falken.team_seasons ts
JOIN falken.teams t ON t.id = ts.team_id
JOIN falken.seasons s ON s.id = ts.season_id
ORDER BY s.start_date DESC NULLS LAST, s.label DESC, ts.final_rank ASC;

NOTIFY pgrst, 'reload schema';
