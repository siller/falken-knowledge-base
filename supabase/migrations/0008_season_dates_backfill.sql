-- ============================================================================
-- 0008_season_dates_backfill.sql
--
-- WARUM: Vor dieser Migration waren `falken.seasons.start_date` und
-- `end_date` in ALLEN 48 Saisons NULL — `upsert_season` setzt diese Felder
-- nicht. Das brach alle Coach-Tenure-Date-Range-Joins komplett (NULL-Compare
-- = false) und führte zu 0/22 Pass-Rate in der Trainer-Kategorie beim GenAI-
-- Eval. Konvention im deutschen Eishockey: Saison "YYYY/YY" läuft Sep 1 (YYYY)
-- bis May 31 (YY+1).
--
-- Diese Migration ist idempotent — sie aktualisiert nur Saisons, deren
-- Datum NULL ist, also kein Risiko handgepflegte Daten zu überschreiben.
-- ============================================================================
SET search_path TO falken, public;

UPDATE falken.seasons
SET start_date = make_date(
        CAST(split_part(label, '/', 1) AS int),
        9, 1
    ),
    end_date = make_date(
        -- "2022/23" → end_year=2023, "1999/00" → end_year=2000
        CASE
            WHEN length(split_part(label, '/', 2)) = 2 THEN
                (CAST(split_part(label, '/', 1) AS int) / 100) * 100
                + CAST(split_part(label, '/', 2) AS int)
                + CASE
                    WHEN CAST(split_part(label, '/', 2) AS int)
                       < (CAST(split_part(label, '/', 1) AS int) % 100)
                    THEN 100 ELSE 0
                  END
            ELSE CAST(split_part(label, '/', 1) AS int) + 1
        END,
        5, 31
    )
WHERE (start_date IS NULL OR end_date IS NULL)
  AND label ~ '^\d{4}(/\d{2}|/\d{4})?$';

-- Sanity-Check ins Log
DO $$
DECLARE
    cnt int;
BEGIN
    SELECT COUNT(*) INTO cnt FROM falken.seasons WHERE start_date IS NULL;
    RAISE NOTICE 'Seasons noch ohne start_date: %', cnt;
END $$;

-- Future-proof: upsert_season füllt Dates jetzt auch beim INSERT
CREATE OR REPLACE FUNCTION falken.upsert_season(
    p_label text, p_league text, p_league_tier smallint, p_hockeydata_id text
) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
    v_id uuid;
    v_start date;
    v_end date;
BEGIN
    -- Default-Dates aus Label ableiten (Sep 1 → May 31)
    IF p_label ~ '^\d{4}/\d{2}$' THEN
        v_start := make_date(CAST(split_part(p_label, '/', 1) AS int), 9, 1);
        v_end := make_date(
            (CAST(split_part(p_label, '/', 1) AS int) / 100) * 100
                + CAST(split_part(p_label, '/', 2) AS int)
                + CASE WHEN CAST(split_part(p_label, '/', 2) AS int)
                            < (CAST(split_part(p_label, '/', 1) AS int) % 100)
                       THEN 100 ELSE 0 END,
            5, 31);
    ELSIF p_label ~ '^\d{4}$' THEN
        v_start := make_date(CAST(p_label AS int), 9, 1);
        v_end := make_date(CAST(p_label AS int) + 1, 5, 31);
    END IF;

    INSERT INTO falken.seasons (label, league, league_tier, start_date, end_date, source_ids)
    VALUES (p_label, p_league, p_league_tier, v_start, v_end,
            jsonb_build_object('hockeydata', p_hockeydata_id))
    ON CONFLICT (label, league) DO UPDATE
        SET source_ids = falken.seasons.source_ids || EXCLUDED.source_ids,
            league_tier = EXCLUDED.league_tier,
            start_date = COALESCE(falken.seasons.start_date, EXCLUDED.start_date),
            end_date = COALESCE(falken.seasons.end_date, EXCLUDED.end_date)
    RETURNING id INTO v_id;
    RETURN v_id;
END $$;
