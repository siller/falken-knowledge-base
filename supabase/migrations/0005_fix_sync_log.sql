-- ============================================================================
-- Fix: sync_log-Trigger braucht Schema-Prefix, sonst schlägt INSERT via public-Views fehl
-- ============================================================================

CREATE OR REPLACE FUNCTION falken.log_sync_event() RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = falken, public
AS $$
DECLARE
    pk_value UUID;
    composite JSONB;
BEGIN
    IF TG_OP = 'DELETE' THEN
        BEGIN pk_value := OLD.id; EXCEPTION WHEN OTHERS THEN pk_value := NULL; END;
        IF pk_value IS NULL THEN composite := to_jsonb(OLD); END IF;
        INSERT INTO falken.sync_log(table_name, row_id, composite_key, op, payload)
        VALUES (TG_TABLE_NAME, pk_value, composite, 'D', to_jsonb(OLD));
        RETURN OLD;
    ELSE
        BEGIN pk_value := NEW.id; EXCEPTION WHEN OTHERS THEN pk_value := NULL; END;
        IF pk_value IS NULL THEN composite := to_jsonb(NEW); END IF;
        INSERT INTO falken.sync_log(table_name, row_id, composite_key, op, payload)
        VALUES (TG_TABLE_NAME, pk_value, composite,
                CASE WHEN TG_OP = 'INSERT' THEN 'I' ELSE 'U' END,
                to_jsonb(NEW));
        RETURN NEW;
    END IF;
END;
$$;

-- Dito für touch_updated_at (sicherheitshalber)
CREATE OR REPLACE FUNCTION falken.touch_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = falken, public
AS $$ BEGIN NEW.updated_at := NOW(); RETURN NEW; END; $$;

-- Auch dem alten public.log_sync_event (falls noch da von initialer Migration) den Schema-Fix
CREATE OR REPLACE FUNCTION public.log_sync_event() RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = falken, public
AS $$
DECLARE
    pk_value UUID;
    composite JSONB;
BEGIN
    IF TG_OP = 'DELETE' THEN
        BEGIN pk_value := OLD.id; EXCEPTION WHEN OTHERS THEN pk_value := NULL; END;
        IF pk_value IS NULL THEN composite := to_jsonb(OLD); END IF;
        INSERT INTO falken.sync_log(table_name, row_id, composite_key, op, payload)
        VALUES (TG_TABLE_NAME, pk_value, composite, 'D', to_jsonb(OLD));
        RETURN OLD;
    ELSE
        BEGIN pk_value := NEW.id; EXCEPTION WHEN OTHERS THEN pk_value := NULL; END;
        IF pk_value IS NULL THEN composite := to_jsonb(NEW); END IF;
        INSERT INTO falken.sync_log(table_name, row_id, composite_key, op, payload)
        VALUES (TG_TABLE_NAME, pk_value, composite,
                CASE WHEN TG_OP = 'INSERT' THEN 'I' ELSE 'U' END,
                to_jsonb(NEW));
        RETURN NEW;
    END IF;
END;
$$;

NOTIFY pgrst, 'reload schema';
