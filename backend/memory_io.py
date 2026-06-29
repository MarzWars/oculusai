import json
import logging
import re
import math
import uuid
import os
import threading
from datetime import datetime, timezone
from collections import OrderedDict
from flask import jsonify, request, current_app

from config import Config
from backend.extensions import supabase
from backend.models import get_llm, query_openrouter, query_openrouter_stream
from backend.prompts import MEMORY_EXTRACTION_PROMPT, STYLE_INFERENCE_PROMPT
from backend.memory_items import load_memory_items, save_memory_items
from flask import Blueprint, jsonify, request, session

memory_bp = Blueprint("memory", __name__)

MEMORY_DEFAULT = {
    "profile": {
        "name": {"value": "", "confidence": 1.0, "reasoning": "Unspecified"},
        "role": {"value": "", "confidence": 1.0, "reasoning": "Unspecified"},
        "company": {"value": "", "confidence": 1.0, "reasoning": "Unspecified"},
        "location": {"value": "", "confidence": 1.0, "reasoning": "Unspecified"},
        "email": {"value": "", "confidence": 1.0, "reasoning": "Unspecified"},
        "phone": {"value": "", "confidence": 1.0, "reasoning": "Unspecified"}
    },
    "clients":         [],
    "projects":        [],
    "preferences":     [],
    "important_facts": [],
    "topics_discussed":[],
    "deadlines":       [],
    "ai_notes":        [],
    "conflicts":       [],
    "first_seen":      "",
    "last_seen":       "",
    "session_count":   0,
    "message_count":   0,
    "last_decay_run":  ""
}

def normalize_fact(item, default_confidence=0.85, default_reasoning="Legacy memory item"):
    """Convert legacy string facts or raw dicts to structured confidence objects."""
    now_date = datetime.now().strftime("%Y-%m-%d")
    if isinstance(item, str):
        return {
            "value": item,
            "confidence": default_confidence,
            "source_type": "conversation",
            "last_reinforced": now_date,
            "reasoning": default_reasoning,
            "added": now_date,
            "last_seen": now_date
        }
    elif isinstance(item, dict):
        val = item.get("value") or item.get("name") or item.get("item") or ""
        conf = item.get("confidence")
        if conf is None:
            conf = default_confidence
        else:
            try:
                conf = float(conf)
            except Exception:
                conf = default_confidence
        
        source = item.get("source_type")
        if not source:
            source = "user_explicit" if conf >= 1.0 else "conversation"

        res = {
            "value": val,
            "confidence": conf,
            "source_type": source,
            "last_reinforced": item.get("last_reinforced") or item.get("last_seen") or item.get("added") or now_date,
            "reasoning": item.get("reasoning") or default_reasoning,
            "added": item.get("added") or now_date,
            "last_seen": item.get("last_seen") or item.get("added") or now_date
        }
        
        # Keep deadlines and projects fields intact
        for k in ["date", "name", "item"]:
            if k in item:
                res[k] = item[k]
        return res
    return None

def apply_memory_decay(mem: dict) -> bool:
    """Decay logic: subtracts 0.05 per week of inactivity, floored at 0.1."""
    now_date = datetime.now()
    changed = False
    
    list_keys = ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes", "projects", "deadlines"]
    for key in list_keys:
        for item in mem.get(key, []):
            last_seen_str = item.get("last_seen") or item.get("added")
            if not last_seen_str:
                continue
            try:
                date_only = last_seen_str.split()[0]
                last_seen_date = datetime.strptime(date_only, "%Y-%m-%d")
                days_inactive = (now_date - last_seen_date).days
                if days_inactive >= 7:
                    weeks = days_inactive // 7
                    decay_amount = weeks * 0.05
                    old_conf = item.get("confidence", 0.85)
                    new_conf = max(0.1, round(old_conf - decay_amount, 3))
                    if new_conf != old_conf:
                        item["confidence"] = new_conf
                        item["reasoning"] = f"Decayed due to {days_inactive} days of inactivity."
                        changed = True
            except Exception as e:
                print(f"[Decay] Error parsing date for item {item}: {e}")
                
    return changed

def load_memory(user_id: str) -> dict:
    """
    Phase 3 cutover: reads primarily from oculus_memory_items (normalized rows).
    Falls back to the legacy oculus_memory JSONB blob if the new table returns
    no data (belt-and-suspenders safety net during the transition).
    Shadow-comparison logging runs on every load so divergences are visible.
    """
    now_date = datetime.now().strftime("%Y-%m-%d")

    # --- Primary read: normalized oculus_memory_items ---
    try:
        from backend.memory_items import load_memory_items, _diff_mem_dicts
        new_mem = load_memory_items(user_id)
        new_has_data = bool(
            any(v for v in new_mem.get("profile", {}).values() if isinstance(v, dict) and v.get("value"))
            or any(new_mem.get(cat) for cat in ["clients", "projects", "deadlines", "preferences",
                                                "important_facts", "ai_notes", "topics_discussed"])
            or new_mem.get("message_count", 0) > 0
        )
    except Exception as e:
        print(f"[Phase3] load_memory_items failed for {user_id[:8]}: {e} — falling back to blob")
        new_mem = None
        new_has_data = False

    # --- Fallback / shadow read: legacy JSONB blob ---
    try:
        res = supabase.table("oculus_memory").select("memory").eq("user_id", user_id).execute()
        old_raw = res.data[0].get("memory", {}) if res.data else {}
    except Exception as e:
        print("[Phase3] Legacy blob read error:", e)
        old_raw = {}

    old_merged = json.loads(json.dumps(MEMORY_DEFAULT))
    for key, val in old_raw.items():
        if key in old_merged:
            old_merged[key] = val

    # Normalize the old blob's profile fields (same logic as before)
    profile = old_merged.setdefault("profile", {})
    for field in ["name", "role", "company", "location", "email", "phone"]:
        val = profile.get(field)
        if val is None:
            profile[field] = {"value": "", "confidence": 1.0, "source_type": "manual",
                              "last_reinforced": now_date, "reasoning": "Unspecified"}
        elif isinstance(val, str):
            profile[field] = {"value": val, "confidence": 1.0, "source_type": "manual",
                              "last_reinforced": now_date, "reasoning": "Legacy profile item"}
        elif isinstance(val, dict):
            conf = val.get("confidence") if val.get("confidence") is not None else 1.0
            source = val.get("source_type") or ("user_explicit" if conf >= 1.0 else "conversation")
            profile[field] = {
                "value": val.get("value") or "",
                "confidence": conf,
                "source_type": source,
                "last_reinforced": val.get("last_reinforced") or val.get("last_seen") or now_date,
                "reasoning": val.get("reasoning") or "Saved profile item"
            }

    # Normalize list-based fields in old blob
    for key in ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]:
        normalized = [normalize_fact(item, default_confidence=0.85, default_reasoning="Legacy memory item")
                      for item in old_merged.get(key, [])]
        old_merged[key] = [n for n in normalized if n]

    # Normalize projects in old blob
    normalized_projects = []
    for item in old_merged.get("projects", []):
        if isinstance(item, str):
            normalized_projects.append({"name": item, "value": item, "confidence": 0.85,
                                        "reasoning": "Legacy project item", "added": now_date, "last_seen": now_date})
        elif isinstance(item, dict):
            name = item.get("name") or item.get("value") or ""
            normalized_projects.append({"name": name, "value": name,
                                        "confidence": item.get("confidence") if item.get("confidence") is not None else 0.85,
                                        "reasoning": item.get("reasoning") or "Saved project item",
                                        "added": item.get("added") or now_date,
                                        "last_seen": item.get("last_seen") or item.get("added") or now_date})
    old_merged["projects"] = normalized_projects

    # Normalize deadlines in old blob
    normalized_deadlines = []
    for item in old_merged.get("deadlines", []):
        if isinstance(item, str):
            normalized_deadlines.append({"item": item, "value": item, "date": "Not specified",
                                         "confidence": 0.85, "reasoning": "Legacy deadline item",
                                         "added": now_date, "last_seen": now_date})
        elif isinstance(item, dict):
            task_name = item.get("item") or item.get("value") or ""
            normalized_deadlines.append({"item": task_name, "value": task_name,
                                         "date": item.get("date") or "Not specified",
                                         "confidence": item.get("confidence") if item.get("confidence") is not None else 0.85,
                                         "reasoning": item.get("reasoning") or "Saved deadline item",
                                         "added": item.get("added") or now_date,
                                         "last_seen": item.get("last_seen") or item.get("added") or now_date})
    old_merged["deadlines"] = normalized_deadlines

    if "conflicts" not in old_merged or not isinstance(old_merged["conflicts"], list):
        old_merged["conflicts"] = []

    # --- Shadow comparison log (runs on every load) ---
    if new_has_data and new_mem is not None:
        try:
            diffs = _diff_mem_dicts(old_merged, new_mem)
            if diffs:
                print(f"[ShadowDiff] user={user_id[:8]} — {len(diffs)} diff(s):")
                for d in diffs:
                    print(d)
            else:
                print(f"[ShadowDiff] user={user_id[:8]} — CLEAN (no diffs)")
        except Exception as e:
            print(f"[ShadowDiff] comparison error for {user_id[:8]}: {e}")

    # --- Choose which result to return ---
    # Use new table if it has data; otherwise fall back to old blob.
    # In practice after a successful backfill new_has_data should always be True.
    merged = new_mem if new_has_data else old_merged

    # Carry conflicts from old blob if the new table has none yet
    # (conflicts added before cutover would not have been migrated by backfill)
    if not merged.get("conflicts") and old_merged.get("conflicts"):
        merged["conflicts"] = old_merged["conflicts"]

    # --- Bounded daily decay run (dual-write) ---
    today_str = datetime.now().strftime("%Y-%m-%d")
    if merged.get("last_decay_run") != today_str:
        apply_memory_decay(merged)
        merged["last_decay_run"] = today_str
        # Write decay back to old table (keeps it in sync as a warm backup)
        try:
            supabase.table("oculus_memory").upsert({
                "user_id": user_id,
                "memory":  merged
            }).execute()
        except Exception as e:
            print("Failed to save decayed memory to blob:", e)
        # Write decay to new table too
        try:
            from backend.memory_items import save_memory_items
            save_memory_items(user_id, merged)
        except Exception as e:
            print(f"[Phase3] Failed to save decayed memory to items table: {e}")

    return merged

def save_memory(user_id: str, mem: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    now_date = datetime.now().strftime("%Y-%m-%d")
    mem["last_seen"] = now
    if not mem.get("first_seen"):
        mem["first_seen"] = now
    mem.pop("conversation_count", None)

    # Normalize profile fields
    profile = mem.setdefault("profile", {})
    for field in ["name", "role", "company", "location", "email", "phone"]:
        val = profile.get(field)
        if isinstance(val, str):
            profile[field] = {"value": val, "confidence": 1.0, "source_type": "manual", "last_reinforced": now_date, "reasoning": "Saved profile item"}
        elif isinstance(val, dict):
            if "value" not in val:
                profile[field] = {"value": "", "confidence": 1.0, "source_type": "manual", "last_reinforced": now_date, "reasoning": "Unspecified"}
            else:
                val.setdefault("source_type", "user_explicit" if val.get("confidence", 1.0) >= 1.0 else "conversation")
                val.setdefault("last_reinforced", now_date)

    # Normalize list fields
    list_keys = ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]
    for key in list_keys:
        if key in mem:
            mem[key] = [normalize_fact(item) for item in mem[key] if normalize_fact(item) is not None]

    # --- Primary write: existing JSONB blob (unchanged) ---
    try:
        supabase.table("oculus_memory").upsert({
            "user_id": user_id,
            "memory":  mem
        }).execute()
    except Exception as e:
        print("Memory save error:", e)

    # --- Dual-write: normalized oculus_memory_items table (Phase 2) ---
    # Errors here are caught and logged separately — they must never interrupt
    # the primary JSONB write above.  This block will be removed in Phase 3
    # once reads are fully switched over to the new table.
    try:
        from backend.memory_items import save_memory_items
        save_memory_items(user_id, mem)
    except Exception as e:
        print(f"[DualWrite] save_memory_items failed for user {user_id[:8]}...: {e}")

def add_profile_field_with_conflict_check(mem: dict, field: str, new_val: str, confidence: float, reasoning: str, source_type: str = "conversation", last_reinforced: str = None) -> bool:
    """Safely updates a profile field or registers a conflict if it contradicts the existing value."""
    now_date = datetime.now().strftime("%Y-%m-%d")
    reinforced_date = last_reinforced or now_date
    old_obj = mem["profile"].get(field) or {}
    old_val = (old_obj.get("value") if isinstance(old_obj, dict) else old_obj) or ""
    
    if old_val and old_val.lower() != new_val.lower():
        conflict_obj = {
            "id": str(uuid.uuid4())[:8],
            "key": f"profile.{field}",
            "existing": {
                "value": old_val,
                "confidence": old_obj.get("confidence", 1.0) if isinstance(old_obj, dict) else 1.0,
                "source_type": old_obj.get("source_type", "manual") if isinstance(old_obj, dict) else "manual",
                "last_reinforced": old_obj.get("last_reinforced", now_date) if isinstance(old_obj, dict) else now_date,
                "reasoning": old_obj.get("reasoning", "Existing profile item") if isinstance(old_obj, dict) else "Existing profile item"
            },
            "new": {
                "value": new_val,
                "confidence": confidence,
                "source_type": source_type,
                "last_reinforced": reinforced_date,
                "reasoning": reasoning
            },
            "detected_at": now_date
        }
        existing_conflicts = mem.setdefault("conflicts", [])
        if not any(c.get("key") == f"profile.{field}" and c.get("new", {}).get("value").lower() == new_val.lower() for c in existing_conflicts):
            existing_conflicts.append(conflict_obj)
            return True
    elif old_val != new_val:
        mem["profile"][field] = {
            "value": new_val,
            "confidence": confidence,
            "source_type": source_type,
            "last_reinforced": reinforced_date,
            "reasoning": reasoning
        }
        return True
    return False

def _evict_by_score(lst: list, max_len: int, category: str, val_key: str = "value") -> None:
    """
    Issue 4: Score-based eviction helper.  Keeps the highest-scoring items up
    to max_len.  Score = confidence * 0.5 + recency_score * 0.5, where
    recency_score decays 0.05 per week of inactivity (min 0.0).

    Modifies lst in-place.  Logs every item dropped.
    """
    if len(lst) <= max_len:
        return

    now = datetime.now()

    def _score(item: dict) -> float:
        conf = float(item.get("confidence", 0.85))
        last_str = item.get("last_seen") or item.get("last_reinforced") or item.get("added") or ""
        try:
            last_date = datetime.strptime(str(last_str).split()[0][:10], "%Y-%m-%d")
            weeks_inactive = max(0, (now - last_date).days // 7)
            recency = max(0.0, 1.0 - weeks_inactive * 0.05)
        except Exception:
            recency = 0.5
        return conf * 0.5 + recency * 0.5

    scored = sorted(lst, key=_score, reverse=True)
    kept = set(id(x) for x in scored[:max_len])
    evicted = [x for x in lst if id(x) not in kept]
    for item in evicted:
        label = item.get(val_key) or item.get("value") or item.get("name") or str(item)[:60]
        print(f"[MemEvict] category={category} dropped: {label!r} "
              f"(conf={item.get('confidence', '?')}, "
              f"last_seen={item.get('last_seen') or item.get('added', '?')})")
    lst[:] = scored[:max_len]


def merge_memory_updates(current_memory: dict, updates: dict) -> bool:
    """Safely merges LLM updates dictionary into current_memory with confidence tracking & conflict detection."""
    changed = False
    now_date = datetime.now().strftime("%Y-%m-%d")

    # 1. Profile
    profile_updates = updates.get("profile", {})
    if isinstance(profile_updates, dict):
        for field in ["name", "role", "company", "location", "email", "phone"]:
            new_obj = profile_updates.get(field)
            if not new_obj:
                continue
                
            new_val = (new_obj.get("value") if isinstance(new_obj, dict) else new_obj) or ""
            new_val = str(new_val).strip()
            if not new_val:
                continue
                
            confidence = new_obj.get("confidence") if isinstance(new_obj, dict) and new_obj.get("confidence") is not None else 0.85
            reasoning = new_obj.get("reasoning") if isinstance(new_obj, dict) else "Inferred from discussion"
            source_type = new_obj.get("source_type") if isinstance(new_obj, dict) else "conversation"
            last_reinforced = new_obj.get("last_reinforced") if isinstance(new_obj, dict) and new_obj.get("last_reinforced") else now_date
            
            if add_profile_field_with_conflict_check(current_memory, field, new_val, confidence, reasoning, source_type, last_reinforced):
                changed = True

    # Helper for standard lists: preferences, clients, important_facts, topics_discussed
    def merge_list_field(key, max_len):
        nonlocal changed
        updates_list = updates.get(key, [])
        if not isinstance(updates_list, list):
            return
            
        for item in updates_list:
            if not item:
                continue
            val = (item.get("value") if isinstance(item, dict) else item) or ""
            val = str(val).strip()
            if not val:
                continue
                
            existing_item = next((i for i in current_memory.get(key, []) if str(i.get("value", "")).lower() == val.lower()), None)
            proposed_conf = item.get("confidence") if isinstance(item, dict) and item.get("confidence") is not None else 0.85
            proposed_reasoning = item.get("reasoning") if isinstance(item, dict) else "Inferred from discussion"
            proposed_source = item.get("source_type") if isinstance(item, dict) else "conversation"
            proposed_reinforced = item.get("last_reinforced") if isinstance(item, dict) and item.get("last_reinforced") else now_date

            if existing_item:
                # Reinforce
                old_conf = existing_item.get("confidence", 0.85)
                new_conf = min(1.0, max(old_conf, proposed_conf) + 0.1)
                existing_item["confidence"] = round(new_conf, 3)
                existing_item["reasoning"] = f"Reinforced. {proposed_reasoning}"
                existing_item["source_type"] = proposed_source
                existing_item["last_reinforced"] = proposed_reinforced
                existing_item["last_seen"] = now_date
                changed = True
            else:
                current_memory[key].append({
                    "value": val,
                    "confidence": proposed_conf,
                    "source_type": proposed_source,
                    "last_reinforced": proposed_reinforced,
                    "reasoning": proposed_reasoning,
                    "added": now_date,
                    "last_seen": now_date
                })
                if len(current_memory[key]) > max_len:
                    _evict_by_score(current_memory[key], max_len=max_len, category=key)
                changed = True

    # Dedicated merging helper for ai_notes (with category and user_explicit protection support)
    def merge_ai_notes(max_len):
        nonlocal changed
        updates_list = updates.get("ai_notes", [])
        if not isinstance(updates_list, list):
            return

        for item in updates_list:
            if not item:
                continue
            val = (item.get("value") if isinstance(item, dict) else item) or ""
            val = str(val).strip()
            if not val:
                continue

            category = item.get("category", "tone") if isinstance(item, dict) else "tone"
            proposed_conf = item.get("confidence") if isinstance(item, dict) and item.get("confidence") is not None else 0.85
            proposed_reasoning = item.get("reasoning") if isinstance(item, dict) else "Inferred from discussion"
            proposed_source = item.get("source_type") if isinstance(item, dict) else "conversation"
            proposed_reinforced = item.get("last_reinforced") if isinstance(item, dict) and item.get("last_reinforced") else now_date

            existing_item = next((i for i in current_memory.get("ai_notes", []) if str(i.get("value", "")).lower() == val.lower()), None)

            if existing_item:
                # Merge logic with user_explicit protection
                is_existing_explicit = existing_item.get("source_type") == "user_explicit"
                is_proposed_explicit = proposed_source == "user_explicit"

                if is_existing_explicit and not is_proposed_explicit:
                    # Protect existing explicit notes from regular inferred updates
                    continue

                # Otherwise, reinforce or update confidence/reasoning
                old_conf = existing_item.get("confidence", 0.75)
                # Boost confidence slightly
                new_conf = min(1.0, max(old_conf, proposed_conf) + 0.05)
                existing_item["confidence"] = round(new_conf, 3)
                existing_item["reasoning"] = f"Reinforced. {proposed_reasoning}"
                existing_item["source_type"] = proposed_source
                existing_item["last_reinforced"] = proposed_reinforced
                existing_item["last_seen"] = now_date
                existing_item["category"] = category
                changed = True
            else:
                current_memory["ai_notes"].append({
                    "value": val,
                    "category": category,
                    "confidence": proposed_conf,
                    "source_type": proposed_source,
                    "last_reinforced": proposed_reinforced,
                    "reasoning": proposed_reasoning,
                    "added": now_date,
                    "last_seen": now_date
                })
                changed = True

        if len(current_memory["ai_notes"]) > max_len:
            _evict_by_score(current_memory["ai_notes"], max_len=max_len, category="ai_notes")

    merge_list_field("preferences", 25)
    merge_list_field("clients", 50)
    merge_list_field("important_facts", 25)
    merge_list_field("topics_discussed", 40)
    merge_ai_notes(20)

    # 3. Projects
    project_updates = updates.get("projects", [])
    if isinstance(project_updates, list):
        for proj in project_updates:
            name = (proj.get("name") or proj.get("value") if isinstance(proj, dict) else proj) or ""
            name = str(name).strip()
            if not name:
                continue
                
            existing = next((p for p in current_memory["projects"] if str(p.get("name", "")).lower() == name.lower()), None)
            proposed_conf = proj.get("confidence") if isinstance(proj, dict) and proj.get("confidence") is not None else 0.85
            proposed_reasoning = proj.get("reasoning") if isinstance(proj, dict) else "Inferred from discussion"
            proposed_source = proj.get("source_type") if isinstance(proj, dict) else "conversation"
            proposed_reinforced = proj.get("last_reinforced") if isinstance(proj, dict) and proj.get("last_reinforced") else now_date

            if existing:
                old_conf = existing.get("confidence", 0.85)
                new_conf = min(1.0, max(old_conf, proposed_conf) + 0.1)
                existing["confidence"] = round(new_conf, 3)
                existing["reasoning"] = f"Reinforced. {proposed_reasoning}"
                existing["source_type"] = proposed_source
                existing["last_reinforced"] = proposed_reinforced
                existing["last_seen"] = now_date
                changed = True
            else:
                current_memory["projects"].append({
                    "name": name,
                    "value": name,
                    "confidence": proposed_conf,
                    "source_type": proposed_source,
                    "last_reinforced": proposed_reinforced,
                    "reasoning": proposed_reasoning,
                    "added": now_date,
                    "last_seen": now_date
                })
                if len(current_memory["projects"]) > 30:
                    _evict_by_score(current_memory["projects"], max_len=30, category="projects",
                                    val_key="name")
                changed = True

    # 4. Deadlines
    deadline_updates = updates.get("deadlines", [])
    if isinstance(deadline_updates, list):
        for dl in deadline_updates:
            item_name = ""
            date_val = ""
            if isinstance(dl, dict):
                item_name = (dl.get("item") or dl.get("value") or "").strip()
                date_val = dl.get("date") or "Not specified"
            else:
                item_name = str(dl).strip()
                date_val = "Not specified"
                
            if not item_name:
                continue
                
            existing = next((d for d in current_memory["deadlines"] if str(d.get("item", "")).lower() == item_name.lower()), None)
            proposed_conf = dl.get("confidence") if isinstance(dl, dict) and dl.get("confidence") is not None else 0.85
            proposed_reasoning = dl.get("reasoning") if isinstance(dl, dict) else "Inferred from discussion"
            proposed_source = dl.get("source_type") if isinstance(dl, dict) else "conversation"
            proposed_reinforced = dl.get("last_reinforced") if isinstance(dl, dict) and dl.get("last_reinforced") else now_date

            if existing:
                if date_val != "Not specified" and existing.get("date") != date_val:
                    existing["date"] = date_val
                    existing["confidence"] = min(1.0, max(existing.get("confidence", 0.85), proposed_conf) + 0.1)
                    existing["reasoning"] = f"Deadline date updated. {proposed_reasoning}"
                    existing["source_type"] = proposed_source
                    existing["last_reinforced"] = proposed_reinforced
                    existing["last_seen"] = now_date
                    changed = True
                else:
                    old_conf = existing.get("confidence", 0.85)
                    new_conf = min(1.0, max(old_conf, proposed_conf) + 0.1)
                    existing["confidence"] = round(new_conf, 3)
                    existing["reasoning"] = f"Reinforced. {proposed_reasoning}"
                    existing["source_type"] = proposed_source
                    existing["last_reinforced"] = proposed_reinforced
                    existing["last_seen"] = now_date
                    changed = True
            else:
                current_memory["deadlines"].append({
                    "item": item_name,
                    "value": item_name,
                    "date": date_val,
                    "confidence": proposed_conf,
                    "source_type": proposed_source,
                    "last_reinforced": proposed_reinforced,
                    "reasoning": proposed_reasoning,
                    "added": now_date,
                    "last_seen": now_date
                })
                if len(current_memory["deadlines"]) > 25:
                    _evict_by_score(current_memory["deadlines"], max_len=25, category="deadlines",
                                    val_key="item")
                changed = True

    return changed

