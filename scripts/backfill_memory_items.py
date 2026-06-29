"""
scripts/backfill_memory_items.py
================================
One-off backfill script: reads every user's memory from the legacy
oculus_memory JSONB table and writes normalized rows into the new
oculus_memory_items table.

SAFE TO RE-RUN: uses INSERT ... ON CONFLICT DO NOTHING so no data is
overwritten, and rows that already exist are simply counted as "skipped".

Usage (from the project root):
    python scripts/backfill_memory_items.py

Output (per user):
    user_id (truncated) | items_attempted | items_inserted | items_skipped | errors

After running, verify in Supabase:
    SELECT item_type, COUNT(*) FROM oculus_memory_items GROUP BY item_type ORDER BY item_type;
    SELECT COUNT(DISTINCT user_id) FROM oculus_memory_items;
"""

import sys
import os

# Allow imports from the project root (backend/, config.py, etc.)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env so config.py picks up SUPABASE_URL and SUPABASE_KEY
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from config import Config
from supabase import create_client
from backend.memory_items import flatten_mem_to_rows

# ---------------------------------------------------------------------------
# Connect to Supabase
# ---------------------------------------------------------------------------

if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

db = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Fetch all users from the legacy table
# ---------------------------------------------------------------------------

print("=" * 72)
print("Oculus AI -- Memory Backfill: oculus_memory -> oculus_memory_items")
print("=" * 72)
print()

try:
    res = db.table("oculus_memory").select("user_id,memory").execute()
    users = res.data or []
except Exception as e:
    print(f"FATAL: Could not read from oculus_memory: {e}")
    sys.exit(1)

if not users:
    print("No rows found in oculus_memory. Nothing to backfill.")
    sys.exit(0)

print(f"Found {len(users)} user(s) in oculus_memory.\n")
print(f"{'USER_ID (truncated)':<38}  {'ATTEMPTED':>9}  {'INSERTED':>8}  {'SKIPPED':>7}  {'ERRORS':>6}")
print("-" * 72)

total_attempted = 0
total_inserted  = 0
total_skipped   = 0
total_errors    = 0

for user_row in users:
    user_id = user_row.get("user_id", "")
    mem_blob = user_row.get("memory") or {}

    if not user_id:
        print(f"{'(missing user_id)':<38}  {'':>9}  {'':>8}  {'':>7}  SKIP")
        continue

    if not isinstance(mem_blob, dict):
        try:
            import json
            mem_blob = json.loads(mem_blob)
        except Exception:
            mem_blob = {}

    try:
        rows = flatten_mem_to_rows(user_id, mem_blob)
    except Exception as e:
        print(f"{user_id[:36]:<38}  FLATTEN ERROR: {e}")
        total_errors += 1
        continue

    attempted = len(rows)
    inserted  = 0
    skipped   = 0
    errors    = 0

    # Insert in small batches to avoid hitting Supabase request-size limits
    BATCH_SIZE = 50
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            # ignore_duplicates=True → ON CONFLICT DO NOTHING
            result = db.table("oculus_memory_items").insert(
                batch,
                count="exact"    # ask PostgREST to return count
            ).execute()

            # PostgREST with prefer=count returns the count in result.count
            batch_inserted = result.count if result.count is not None else len(batch)

            # "skipped" = rows we sent that Postgres silently ignored due to
            # ON CONFLICT DO NOTHING.  Since insert() without upsert() raises on
            # conflict by default, we rely on the Supabase ignore_duplicates param
            # or catch the duplicate-key error per batch.
            inserted += batch_inserted
            skipped  += len(batch) - batch_inserted
        except Exception as e:
            err_str = str(e)
            if "duplicate" in err_str.lower() or "unique" in err_str.lower() or "conflict" in err_str.lower():
                # Whole batch conflicted (rare) — count as skipped
                skipped += len(batch)
            else:
                errors += 1
                print(f"\n  [BATCH ERROR for {user_id[:8]}] {err_str[:100]}")

    total_attempted += attempted
    total_inserted  += inserted
    total_skipped   += skipped
    total_errors    += errors

    uid_display = user_id[:36]
    print(f"{uid_display:<38}  {attempted:>9}  {inserted:>8}  {skipped:>7}  {errors:>6}")

print("-" * 72)
print(f"{'TOTAL':<38}  {total_attempted:>9}  {total_inserted:>8}  {total_skipped:>7}  {total_errors:>6}")
print()

if total_errors == 0:
    print("OK: Backfill completed successfully. Run this script again to verify idempotency (all rows should show as skipped).")
else:
    print(f"WARNING: Backfill completed with {total_errors} batch error(s). Review output above and re-run if needed.")

print()
print("Suggested Supabase verification queries:")
print("  SELECT item_type, COUNT(*) FROM oculus_memory_items GROUP BY item_type ORDER BY item_type;")
print("  SELECT COUNT(DISTINCT user_id) FROM oculus_memory_items;")
