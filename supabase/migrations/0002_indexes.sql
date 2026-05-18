-- ============================================================================
-- Falken Knowledge Base — Indexes & Helpers
-- Separate Migration weil HNSW-Index lange dauert (>1s) und pg_trgm separat lädt
-- ============================================================================
SET search_path TO falken, public;

-- pgvector HNSW-Index für Articles (Vector-Search)
-- m=16, ef_construction=64 sind für unsere Größenordnung (≤10k Artikel) gut
CREATE INDEX IF NOT EXISTS idx_articles_embedding ON articles
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Convenience-View: Falken-Spieler pro Saison mit allen Stats
CREATE OR REPLACE VIEW falken_skater_stats AS
SELECT
    s.label AS season,
    s.league,
    p.name AS player,
    p.position,
    p.nation,
    ps.jersey_number,
    pst.games_played,
    pst.goals,
    pst.assists,
    pst.points,
    pst.pim,
    pst.plus_minus
FROM player_seasons ps
JOIN players p ON p.id = ps.player_id
JOIN teams t ON t.id = ps.team_id
JOIN seasons s ON s.id = ps.season_id
LEFT JOIN player_stats pst ON pst.player_season_id = ps.id
WHERE t.name = 'Heilbronner Falken';

CREATE OR REPLACE VIEW falken_goalie_stats AS
SELECT
    s.label AS season,
    s.league,
    p.name AS goalie,
    ps.jersey_number,
    gst.games_played,
    gst.wins,
    gst.losses,
    gst.gaa,
    gst.save_pct,
    gst.shutouts
FROM player_seasons ps
JOIN players p ON p.id = ps.player_id
JOIN teams t ON t.id = ps.team_id
JOIN seasons s ON s.id = ps.season_id
JOIN goalie_stats gst ON gst.player_season_id = ps.id
WHERE t.name = 'Heilbronner Falken';

-- Convenience-View: Liga-Tabelle pro Saison
CREATE OR REPLACE VIEW season_standings AS
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
    ts.playoff_result
FROM team_seasons ts
JOIN teams t ON t.id = ts.team_id
JOIN seasons s ON s.id = ts.season_id
ORDER BY s.start_date DESC, ts.final_rank ASC;
