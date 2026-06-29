"""
backend/memory_items.py
=======================
Normalized per-row memory storage layer for Oculus AI.

This module sits alongside (and will eventually replace) the legacy
oculus_memory JSONB-blob approach. It provides three public functions:

  flatten_mem_to_rows(user_id, mem_dict) -> list[dict]
      Converts the in-memory dict into a list of row dicts, one per
      memory item, ready for upsert into oculus_memory_items.

  save_memory_items(user_id, mem_dict)
      Upserts those rows using INSERT ... ON CONFLICT DO UPDATE so
      individual-row writes are atomic (no lost-update races).

  load_memory_items(user_id) -> dict
      Reads all rows for a user and reconstructs the same dict shape
      that the rest of the codebase (chat.py, the memory API routes,
      memory_to_context, etc.) already expects, so no callers need to
      change during Phase 2.

Phase 2 — dual-write only:  save_memory() calls save_memory_items() in
addition to the existing JSONB upsert.  load_memory() still reads from
oculus_memory exclusively.

Phase 3 — cutover: load_memory() will be switched to call
load_memory_items() as its primary path, and save_memory() will stop
writing to oculus_memory.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from backend.extensions import supabase

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current UTC time as an ISO-8601 string with timezone."""
    return datetime.now(timezone.utc).isoformat()

def _profile_key(field: str) -> str:
    return f"profile.{field}"

def _list_key(category: str, value: str) -> str:
    """
    Derive a stable, short deduplication key from a category + value pair.
    Truncated to 200 chars to stay well within Postgres index limits.
    """
    raw = f"{category}::{value.strip().lower()}"
    return raw[:200]

def _metadata_key() -> str:
    return "meta::session_info"


# ---------------------------------------------------------------------------
# flatten_mem_to_rows
# ---------------------------------------------------------------------------

def flatten_mem_to_rows(user_id: str, mem_dict: dict) -> list:
    """
    Convert a memory dict (the shape produced by load_memory / save_memory)
    into a flat list of row dicts, one per memory item.

    Each row dict matches the oculus_memory_items schema:
      id               — omitted (Postgres generates it on INSERT)
      user_id          — set from argument
      workspace_id     — NULL for now (profile-level / global facts)
      item_type        — e.g. "profile_field", "client", "project", etc.
      key              — stable dedupe key for the UNIQUE index
      value            — JSONB: the full item dict
      confidence       — float, pulled from item where present
      source_type      — string, pulled from item where present
      importance       — float, 1.0 if pinned or user_explicit, else 0.0
      pinned           — bool
      last_reinforced  — ISO timestamp string
      reasoning        — text
      created_at       — omitted (Postgres generates it on INSERT)
      updated_at       — set to now on every upsert
    """
    rows = []
    now = _now_iso()
    today = datetime.now().strftime("%Y-%m-%d")

    # ---- Profile fields --------------------------------------------------
    profile = mem_dict.get("profile", {})
    for field in ["name", "role", "company", "location", "email", "phone"]:
        obj = profile.get(field)
        if not obj:
            continue
        if isinstance(obj, str):
            val_str = obj
            conf = 1.0
            src = "manual"
            reasoning = "Legacy profile string"
            reinforced = today
        elif isinstance(obj, dict):
            val_str = obj.get("value", "")
            conf = float(obj.get("confidence", 1.0))
            src = obj.get("source_type", "manual")
            reasoning = obj.get("reasoning", "")
            reinforced = obj.get("last_reinforced") or today
        else:
            continue

        if not val_str:
            continue

        rows.append({
            "user_id": user_id,
            "workspace_id": None,
            "item_type": "profile_field",
            "key": _profile_key(field),
            "value": {"field": field, "value": val_str},
            "confidence": conf,
            "source_type": src,
            "importance": 1.0 if src == "user_explicit" else 0.5,
            "pinned": False,
            "last_reinforced": reinforced,
            "reasoning": reasoning,
            "updated_at": now,
        })

    # ---- Generic list categories -----------------------------------------
    list_categories = {
        "clients":         "client",
        "preferences":     "preference",
        "important_facts": "important_fact",
        "topics_discussed":"topic",
        "ai_notes":        "ai_note",
    }

    for mem_key, item_type in list_categories.items():
        for item in mem_dict.get(mem_key, []):
            if isinstance(item, str):
                val_str = item.strip()
                conf = 0.85
                src = "conversation"
                reasoning = "Legacy string item"
                reinforced = today
                pinned = False
                importance = 0.0
                full_value = {"value": val_str}
            elif isinstance(item, dict):
                val_str = (item.get("value") or item.get("name") or item.get("item") or "").strip()
                conf = float(item.get("confidence", 0.85))
                src = item.get("source_type", "conversation")
                reasoning = item.get("reasoning", "")
                reinforced = item.get("last_reinforced") or item.get("last_seen") or today
                pinned = bool(item.get("pinned") or item.get("is_pinned"))
                importance = 1.0 if (pinned or src == "user_explicit") else 0.0
                full_value = item
            else:
                continue

            if not val_str:
                continue

            rows.append({
                "user_id": user_id,
                "workspace_id": None,
                "item_type": item_type,
                "key": _list_key(item_type, val_str),
                "value": full_value,
                "confidence": conf,
                "source_type": src,
                "importance": importance,
                "pinned": pinned,
                "last_reinforced": reinforced,
                "reasoning": reasoning,
                "updated_at": now,
            })

    # ---- Projects --------------------------------------------------------
    for item in mem_dict.get("projects", []):
        if isinstance(item, str):
            name = item.strip()
            conf = 0.85
            src = "conversation"
            reasoning = "Legacy string project"
            reinforced = today
            pinned = False
            importance = 0.0
            full_value = {"name": name, "value": name}
        elif isinstance(item, dict):
            name = (item.get("name") or item.get("value") or "").strip()
            conf = float(item.get("confidence", 0.85))
            src = item.get("source_type", "conversation")
            reasoning = item.get("reasoning", "")
            reinforced = item.get("last_reinforced") or item.get("last_seen") or today
            pinned = bool(item.get("pinned") or item.get("is_pinned"))
            importance = 1.0 if (pinned or src == "user_explicit") else 0.0
            full_value = item
        else:
            continue

        if not name:
            continue

        rows.append({
            "user_id": user_id,
            "workspace_id": None,
            "item_type": "project",
            "key": _list_key("project", name),
            "value": full_value,
            "confidence": conf,
            "source_type": src,
            "importance": importance,
            "pinned": pinned,
            "last_reinforced": reinforced,
            "reasoning": reasoning,
            "updated_at": now,
        })

    # ---- Deadlines -------------------------------------------------------
    for item in mem_dict.get("deadlines", []):
        if isinstance(item, str):
            task_name = item.strip()
            conf = 0.85
            src = "conversation"
            reasoning = "Legacy string deadline"
            reinforced = today
            pinned = False
            importance = 0.0
            full_value = {"item": task_name, "value": task_name, "date": "Not specified"}
        elif isinstance(item, dict):
            task_name = (item.get("item") or item.get("value") or "").strip()
            conf = float(item.get("confidence", 0.85))
            src = item.get("source_type", "conversation")
            reasoning = item.get("reasoning", "")
            reinforced = item.get("last_reinforced") or item.get("last_seen") or today
            pinned = bool(item.get("pinned") or item.get("is_pinned"))
            importance = 1.0 if (pinned or src == "user_explicit") else 0.0
            full_value = item
        else:
            continue

        if not task_name:
            continue

        rows.append({
            "user_id": user_id,
            "workspace_id": None,
            "item_type": "deadline",
            "key": _list_key("deadline", task_name),
            "value": full_value,
            "confidence": conf,
            "source_type": src,
            "importance": importance,
            "pinned": pinned,
            "last_reinforced": reinforced,
            "reasoning": reasoning,
            "updated_at": now,
        })

    # ---- Metadata (session / message counts, timestamps) -----------------
    meta_value = {
        "first_seen":     mem_dict.get("first_seen", ""),
        "last_seen":      mem_dict.get("last_seen", ""),
        "session_count":  mem_dict.get("session_count", 0),
        "message_count":  mem_dict.get("message_count", 0),
        "last_decay_run": mem_dict.get("last_decay_run", ""),
        # low-priority summary cache
        "low_priority_hash":    mem_dict.get("low_priority_hash", ""),
        "low_priority_summary": mem_dict.get("low_priority_summary", ""),
    }
    rows.append({
        "user_id": user_id,
        "workspace_id": None,
        "item_type": "metadata",
        "key": _metadata_key(),
        "value": meta_value,
        "confidence": 1.0,
        "source_type": "system",
        "importance": 0.0,
        "pinned": False,
        "last_reinforced": now,
        "reasoning": "Session metadata",
        "updated_at": now,
    })

    return rows


# ---------------------------------------------------------------------------
# save_memory_items
# ---------------------------------------------------------------------------

def save_memory_items(user_id: str, mem_dict: dict) -> None:
    """
    Upsert all memory items for a user into oculus_memory_items.

    Each row is identified by (user_id, item_type, key) — matched by the
    unique partial index in Postgres.  Rows without a key (key IS NULL) are
    always inserted, not deduped — but all our generated rows have a key, so
    this branch doesn't apply here.

    Errors are logged and suppressed so a failure here never breaks the
    existing JSONB write path during Phase 2 dual-write.
    """
    try:
        rows = flatten_mem_to_rows(user_id, mem_dict)
        if not rows:
            return

        # Supabase Python SDK upsert with on_conflict handles the
        # INSERT ... ON CONFLICT (user_id, item_type, key) DO UPDATE
        # The unique index is: idx_omi_user_type_key (user_id, item_type, key) WHERE key IS NOT NULL
        supabase.table("oculus_memory_items").upsert(
            rows,
            on_conflict="user_id,item_type,key"
        ).execute()
        print(f"[MemoryItems] Saved {len(rows)} rows for user {user_id[:8]}...")
    except Exception as e:
        print(f"[MemoryItems] save_memory_items failed for user {user_id[:8]}...: {e}")


# ---------------------------------------------------------------------------
# load_memory_items
# ---------------------------------------------------------------------------

def load_memory_items(user_id: str) -> dict:
    """
    Load all memory items for a user from oculus_memory_items and reconstruct
    the same dict shape that load_memory() returns.

    Returns a dict with the same top-level keys as MEMORY_DEFAULT:
      profile, clients, projects, preferences, important_facts,
      topics_discussed, deadlines, ai_notes, conflicts,
      first_seen, last_seen, session_count, message_count, last_decay_run

    Used in Phase 3 to switch load_memory() off the old blob.
    Also used in the Phase 2 shadow-comparison log.
    """
    # Import here to avoid circular import at module level
    from backend.memory import MEMORY_DEFAULT
    import json as _json

    # Start with the default shape
    mem = _json.loads(_json.dumps(MEMORY_DEFAULT))

    try:
        res = supabase.table("oculus_memory_items") \
            .select("item_type,key,value,confidence,source_type,importance,pinned,last_reinforced,reasoning") \
            .eq("user_id", user_id) \
            .execute()

        rows = res.data or []
    except Exception as e:
        print(f"[MemoryItems] load_memory_items failed for user {user_id[:8]}...: {e}")
        return mem

    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Map item_type -> mem key for list categories
    type_to_key = {
        "client":         "clients",
        "preference":     "preferences",
        "important_fact": "important_facts",
        "topic":          "topics_discussed",
        "ai_note":        "ai_notes",
        "project":        "projects",
        "deadline":       "deadlines",
    }

    for row in rows:
        item_type = row.get("item_type", "")
        value = row.get("value") or {}

        # Enrich value with the top-level metadata columns so the rest of the
        # codebase sees a unified dict (same shape as what came from the blob)
        if isinstance(value, dict):
            if "confidence" not in value and row.get("confidence") is not None:
                value["confidence"] = row["confidence"]
            if "source_type" not in value and row.get("source_type"):
                value["source_type"] = row["source_type"]
            if "pinned" not in value and row.get("pinned") is not None:
                value["pinned"] = row["pinned"]
            if "last_reinforced" not in value and row.get("last_reinforced"):
                # last_reinforced in the DB is a timestamptz; strip to date string
                lr = str(row["last_reinforced"])
                value["last_reinforced"] = lr[:10] if len(lr) >= 10 else lr
            if "reasoning" not in value and row.get("reasoning"):
                value["reasoning"] = row["reasoning"]

        if item_type == "profile_field":
            field = value.get("field")
            if field and field in mem["profile"]:
                mem["profile"][field] = {
                    "value": value.get("value", ""),
                    "confidence": row.get("confidence", 1.0),
                    "source_type": row.get("source_type", "manual"),
                    "last_reinforced": str(row.get("last_reinforced", today))[:10],
                    "reasoning": row.get("reasoning", ""),
                }

        elif item_type in type_to_key:
            mem_key = type_to_key[item_type]
            mem[mem_key].append(value)

        elif item_type == "metadata":
            mem["first_seen"]     = value.get("first_seen", "")
            mem["last_seen"]      = value.get("last_seen", "")
            mem["session_count"]  = value.get("session_count", 0)
            mem["message_count"]  = value.get("message_count", 0)
            mem["last_decay_run"] = value.get("last_decay_run", "")
            if value.get("low_priority_hash"):
                mem["low_priority_hash"]    = value["low_priority_hash"]
            if value.get("low_priority_summary"):
                mem["low_priority_summary"] = value["low_priority_summary"]

        # conflicts are not stored in oculus_memory_items (they live in the
        # JSONB blob and will be migrated in a later sub-task if needed)

    return mem
