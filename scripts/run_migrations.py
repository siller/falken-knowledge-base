"""DEPRECATED: Migrations werden über Supabase Studio SQL Editor ausgeführt.

Dieser Script-Stub bleibt nur als Erinnerung. Die Files in supabase/migrations/
müssen einmalig per Studio SQL Editor (https://studio.supabase.siller.io)
in Reihenfolge ausgeführt werden:

  1. supabase/migrations/0001_init.sql
  2. supabase/migrations/0002_indexes.sql
  3. supabase/migrations/0003_rpcs.sql

Grund: Direkter Postgres-Connect über den Cloudron-gehosteten Supavisor-Pooler
ist mit "Tenant or user not found" geblockt. Wir nutzen REST + RPCs.
"""
import sys
sys.exit(
    "Bitte Migrations manuell im Studio SQL Editor ausführen.\n"
    "Pfade siehe Docstring oben."
)
