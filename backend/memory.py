import re
import json
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from config import Config
from backend.extensions import supabase
from backend.utils import is_ad_content, _add_unique
from backend.models import query_openrouter_extraction
from backend.prompts import MEMORY_CONSOLIDATION_PROMPT_TEMPLATE
from backend.auth import login_required, current_user_id

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


def extract_memory_regex(text: str, mem: dict) -> bool:
    if is_ad_content(text):
        return False
    changed = False
    t = text.strip()

    # Check for explicit style training inputs prefixed with style/behavior notes
    for prefix in ["style preference:", "style note:", "behavior note:"]:
        if t.lower().startswith(prefix):
            style_content = t[len(prefix):].strip()
            if style_content:
                category = "tone"
                lower_sc = style_content.lower()
                if "format" in lower_sc or "bullet" in lower_sc or "list" in lower_sc or "paragraph" in lower_sc or "spacing" in lower_sc:
                    category = "formatting"
                elif "avoid" in lower_sc or "don't" in lower_sc or "dont" in lower_sc or "never" in lower_sc or "stop" in lower_sc:
                    category = "forbidden"
                elif "word" in lower_sc or "spelling" in lower_sc or "phrase" in lower_sc or "term" in lower_sc:
                    category = "vocabulary"
                elif "client" in lower_sc or "for " in lower_sc:
                    category = "client_specific"
                
                duplicate = False
                for note in mem.setdefault("ai_notes", []):
                    note_val = note.get("value") if isinstance(note, dict) else note
                    if note_val and str(note_val).lower() == style_content.lower():
                        duplicate = True
                        break
                
                if not duplicate:
                    mem["ai_notes"].append({
                        "value": style_content,
                        "category": category,
                        "confidence": 1.0,
                        "source_type": "user_explicit",
                        "last_reinforced": datetime.now().strftime("%Y-%m-%d"),
                        "reasoning": "Explicit style training command prefix detected",
                        "added": datetime.now().strftime("%Y-%m-%d"),
                        "last_seen": datetime.now().strftime("%Y-%m-%d")
                    })
                    changed = True
            return changed

    # ------------------------------------------------------------------ #
    # Issue 3 fix: pattern-matched fields get confidence=0.55 / source   #
    # type='regex_heuristic' so the decay system and quality audit can    #
    # treat them with appropriate scepticism.  Email and phone are        #
    # high-precision patterns → 0.85.  Style-prefix commands             #
    # (handled above) keep 1.0 / 'user_explicit'.                        #
    # ------------------------------------------------------------------ #

    for pat in [
        r"(?:my name is|i(?:'m| am) called|call me|i go by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+here[,.]",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in {"the", "a", "an", "this", "that", "here"}:
                if add_profile_field_with_conflict_check(
                    mem, "name", candidate,
                    confidence=0.55, reasoning="Regex heuristic match.",
                    source_type="regex_heuristic"
                ):
                    changed = True
                break

    for pat in [
        r"(?:i(?:'m| am) from|my company is|i work (?:at|for)|our company is|we(?:'re| are) called|the business is called)\s+(.+?)(?:\.|,|\band\b|$)",
        r"(?:my agency is|our agency is)\s+(.+?)(?:\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            if add_profile_field_with_conflict_check(
                mem, "company", m.group(1).strip()[:80],
                confidence=0.55, reasoning="Regex heuristic match.",
                source_type="regex_heuristic"
            ):
                changed = True
            break

    for pat in [
        r"(?:i(?:'m| am) (?:a|an|the))\s+([\w\s]+?)(?:\s+at|\s+for|\.|,|$)",
        r"my (?:job|role|position|title) is\s+(.+?)(?:\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            role = m.group(1).strip()
            if len(role.split()) <= 6:
                if add_profile_field_with_conflict_check(
                    mem, "role", role,
                    confidence=0.55, reasoning="Regex heuristic match.",
                    source_type="regex_heuristic"
                ):
                    changed = True
                break

    m = re.search(
        r"(?:i(?:'m| am) (?:based in|from|in)|we(?:'re| are) based in|located in)\s+(.+?)(?:\.|,|$)",
        t, re.IGNORECASE
    )
    if m:
        if add_profile_field_with_conflict_check(
            mem, "location", m.group(1).strip()[:60],
            confidence=0.55, reasoning="Regex heuristic match.",
            source_type="regex_heuristic"
        ):
            changed = True

    # Email and phone: high-precision patterns → confidence 0.85
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", t)
    if m:
        if add_profile_field_with_conflict_check(
            mem, "email", m.group(0),
            confidence=0.85, reasoning="Email pattern match.",
            source_type="regex_heuristic"
        ):
            changed = True

    m = re.search(r"(?:\+27|0)[6-8]\d[\s\-]?\d{3}[\s\-]?\d{4}", t)
    if m:
        if add_profile_field_with_conflict_check(
            mem, "phone", m.group(0),
            confidence=0.85, reasoning="Phone pattern match.",
            source_type="regex_heuristic"
        ):
            changed = True

    for pat in [
        r"(?:my client is|our client is|working (?:with|for) a? ?client called|the client(?:'s name)? is)\s+(.+?)(?:\.|,|$)",
        r"(?:client:)\s*(.+?)(?:\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            if _add_unique(mem["clients"], m.group(1).strip()[:60], max_len=50):
                changed = True

    for pat in [
        r"(?:project called|project named|project:)\s+(.+?)(?:\.|,|$)",
        r"(?:working on|launching|building|creating|developing)\s+(?:a|an|the)?\s*(.+?)(?:\s+for|\s+next|\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if 1 < len(candidate.split()) <= 8:
                existing = [p.get("name", "").lower() for p in mem["projects"]]
                if candidate.lower() not in existing:
                    mem["projects"].append({
                        "name":  candidate[:80],
                        "value": candidate[:80],
                        "added": datetime.now().strftime("%Y-%m-%d"),
                        "last_seen": datetime.now().strftime("%Y-%m-%d"),
                        "confidence": 0.85,
                        "reasoning": "Inferred from regex"
                    })
                    _evict_by_score(mem["projects"], max_len=30, category="projects",
                                    val_key="name")
                    changed = True

    m = re.search(
        r"(?:deadline|due|needed by|launch(?:ing)? on|goes live)\s+(?:is|on|by)?\s+(.+?)(?:\.|,|$)",
        t, re.IGNORECASE
    )
    if m:
        dl = m.group(1).strip()
        if len(dl) < 60:
            mem["deadlines"].append({
                "item":  t[:80],
                "value": t[:80],
                "date":  dl,
                "added": datetime.now().strftime("%Y-%m-%d"),
                "last_seen": datetime.now().strftime("%Y-%m-%d"),
                "confidence": 0.85,
                "reasoning": "Inferred from regex"
            })
            _evict_by_score(mem["deadlines"], max_len=25, category="deadlines",
                            val_key="item")
            changed = True

    for pat in [
        r"(?:i (?:prefer|like|love|hate|dislike|always want|never want))\s+(.+?)(?:[.!?,]|$)",
        r"(?:always (?:use|write|format|include|avoid))\s+(.+?)(?:[.!?,]|$)",
        r"(?:keep (?:it|responses|copy|ads|the tone))\s+(.+?)(?:[.!?,]|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            pref = m.group(0).strip()
            if len(pref) <= 100:
                if _add_unique(mem["preferences"], pref, max_len=25):
                    changed = True

    m = re.search(
        r"(?:remember (?:that )?|please note(?: that)?|keep in mind (?:that )?|don't forget (?:that )?)(.+?)(?:[.!?]|$)",
        t, re.IGNORECASE
    )
    if m:
        note = m.group(1).strip()
        if 5 < len(note) <= 120:
            if _add_unique(mem["important_facts"], note, max_len=25):
                changed = True

    topic_map = {
        "Facebook ads":          ["facebook", "fb ad", "facebook ad", "meta ad"],
        "Instagram content":     ["instagram", "ig ", "reel", "story", "carousel"],
        "Google Ads / PPC":      ["google ad", "adwords", "ppc", "sem", "search ad"],
        "Red Rooms":             ["red rooms", "locanto", "phone entertainment", "operator ad"],
        "Web design":            ["website", "web design", "landing page", "ux", "ui", "wireframe", "mockup"],
        "CIPC / Business reg":   ["cipc", "register", "pty", "company registration", "pty ltd"],
        "Email marketing":       ["email campaign", "newsletter", "mailchimp", "klaviyo"],
        "Customer reply":        ["customer reply", "respond to", "client email", "complaint", "review reply"],
        "Branding":              ["brand", "logo", "identity", "colour palette", "brand guide"],
        "SEO":                   ["seo", "search engine", "ranking", "keyword", "organic"],
        "Social media strategy": ["social media", "content calendar", "posting schedule", "content plan"],
        "Copywriting":           ["copy", "headline", "tagline", "slogan", "body copy"],
        "TikTok":                ["tiktok", "tik tok", "short video", "for you page"],
        "WhatsApp marketing":    ["whatsapp", "whatsapp campaign", "broadcast"],
        "Python":                ["python", ".py", "django", "flask", "fastapi", "pandas", "numpy"],
        "JavaScript / Node":     ["javascript", "node.js", "nodejs", "npm", "express"],
        "React / Frontend":      ["react", "vue", "svelte", "next.js", "nextjs", "tailwind", "jsx", "tsx"],
        "HTML / CSS":            ["html", "css", "stylesheet", "flexbox", "grid layout"],
        "Databases / SQL":       ["sql", "mysql", "postgresql", "sqlite", "mongodb", "database query"],
        "APIs & Backend":        ["api", "rest api", "endpoint", "flask route", "fastapi", "webhook"],
        "DevOps / Deployment":   ["render", "docker", "deploy", "ci/cd", "github actions", "vps", "nginx"],
        "Debugging":             ["error", "traceback", "bug", "fix my code", "not working", "exception"],
        "Bash / CLI":            ["bash", "shell", "terminal", "command line", "linux", "chmod", "cron"],
        "TypeScript":            ["typescript", ".ts", "interface", "type definition"],
        "PHP":                   ["php", "laravel", "wordpress plugin"],
    }
    tl = t.lower()
    for topic, keywords in topic_map.items():
        if any(kw in tl for kw in keywords):
            if _add_unique(mem["topics_discussed"], topic, max_len=40):
                changed = True

    return changed

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

def extract_memory_llm(user_message: str, current_memory: dict, history: list = None, preferred_model: str = None) -> bool:
    """Uses a two-stage LLM pipeline to extract, validate, and score background memories with quality audit."""
    if is_ad_content(user_message):
        return False

    recent_turns = []
    if history:
        for msg in history[-6:]:
            role = "User" if msg.get("role") == "user" else "Oculus"
            text = msg.get("text") or msg.get("text_content") or ""
            if text:
                recent_turns.append(f"{role}: {text}")
    
    recent_history_str = "\n".join(recent_turns) if recent_turns else "No recent conversation history."
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        from backend.prompts import MEMORY_STAGE1_EXTRACTION_PROMPT, MEMORY_STAGE2_QUALITY_PROMPT
        
        # Stage 1: Raw Extraction
        prompt1 = MEMORY_STAGE1_EXTRACTION_PROMPT.format(
            current_memory_json=json.dumps(current_memory, indent=2),
            recent_history=recent_history_str,
            user_message=user_message
        )
        
        print("[Memory Extraction] Running Stage 1: Raw Extraction...")
        stage1_res = query_openrouter_extraction(prompt1, preferred_model=preferred_model)
        
        # Stage 2: Quality Review & Scoring
        prompt2 = MEMORY_STAGE2_QUALITY_PROMPT.format(
            current_memory_json=json.dumps(current_memory, indent=2),
            recent_history=recent_history_str,
            user_message=user_message,
            stage1_output=stage1_res,
            current_date=current_date
        )
        
        print("[Memory Extraction] Running Stage 2: Quality Review & Scoring...")
        stage2_res = query_openrouter_extraction(prompt2, preferred_model=preferred_model)
        
        cleaned = stage2_res.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()
        
        res_data = json.loads(cleaned)
        if isinstance(res_data, dict):
            updates = res_data.get("updates", {})
            conflicts = res_data.get("conflicts", [])
            
            changed = False
            if updates:
                changed = merge_memory_updates(current_memory, updates)
                
            if conflicts and isinstance(conflicts, list):
                existing_conflicts = current_memory.setdefault("conflicts", [])
                for conflict in conflicts:
                    new_item = conflict.get("new", {})
                    new_val = new_item.get("value") or new_item.get("name") or new_item.get("item")
                    key = conflict.get("key")
                    
                    dup = any(
                        (c.get("new", {}).get("value") or c.get("new", {}).get("name") or c.get("new", {}).get("item")) == new_val 
                        and c.get("key") == key 
                        for c in existing_conflicts
                    )
                    if not dup:
                        conflict["id"] = str(uuid.uuid4())[:8]
                        conflict["detected_at"] = current_date
                        existing_conflicts.append(conflict)
                        changed = True
            return changed
    except Exception as e:
        print(f"[Memory Extraction Error] Two-stage LLM extraction failed: {e}. Falling back to Regex extraction.")
        return extract_memory_regex(user_message, current_memory)
    return False

def consolidate_memory_llm(current_memory: dict, preferred_model: str = None) -> dict:
    """Uses LLM to clean up redundancies, resolve contradictions, and remove outdated items in memory.

    Issue 5 fix: validates the result before accepting it.  If any list category
    loses more than 20% of its items (and had >3 items before), the consolidation
    is rejected and the original is returned unchanged.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    list_cats = ["clients", "projects", "preferences", "important_facts",
                 "topics_discussed", "deadlines", "ai_notes"]

    # Snapshot counts before consolidation
    before_counts = {cat: len(current_memory.get(cat, [])) for cat in list_cats}

    prompt = MEMORY_CONSOLIDATION_PROMPT_TEMPLATE.format(
        current_date=current_date,
        current_memory_json=json.dumps(current_memory, indent=2)
    )

    try:
        raw_res = query_openrouter_extraction(prompt, preferred_model=preferred_model)
        cleaned = raw_res.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()

        consolidated = json.loads(cleaned)
        if not isinstance(consolidated, dict):
            return current_memory

        # Count items after consolidation
        after_counts = {cat: len(consolidated.get(cat, [])) for cat in list_cats}
        accepted = True
        rejection_reason = ""

        for cat in list_cats:
            before = before_counts[cat]
            after  = after_counts[cat]
            if before > 3 and after < before * 0.8:
                accepted = False
                rejection_reason = (
                    f"category '{cat}' dropped from {before} to {after} items "
                    f"({100*(before-after)//before}% loss)"
                )
                break

        print(
            f"[Consolidation] before={before_counts} | after={after_counts} | "
            f"accepted={accepted}" + (f" | REJECTED: {rejection_reason}" if not accepted else "")
        )

        if accepted:
            return consolidated

    except Exception as e:
        print(f"[Memory Consolidation Error] LLM consolidation failed: {e}")
    return current_memory

def run_style_inference(user_id: str, mem: dict, history: list, preferred_model: str = None) -> bool:
    if not history:
        return False
    
    # Analyze the last 12 turns of dialog
    recent_history = history[-12:]
    recent_turns = []
    for msg in recent_history:
        role = "User" if msg.get("role") == "user" else "Oculus"
        text = msg.get("text") or msg.get("text_content") or ""
        if text:
            recent_turns.append(f"{role}: {text}")
            
    history_text = "\n".join(recent_turns)
    current_ai_notes = mem.get("ai_notes", [])
    
    from backend.prompts import STYLE_INFERENCE_PROMPT_TEMPLATE
    prompt = STYLE_INFERENCE_PROMPT_TEMPLATE.format(
        history_text=history_text,
        current_ai_notes_json=json.dumps(current_ai_notes, indent=2)
    )
    
    try:
        # Use low-temperature extraction helper (Llama 3.3 70B primary cheap option)
        raw_res = query_openrouter_extraction(prompt, preferred_model=preferred_model)
        cleaned = raw_res.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()
        
        res_data = json.loads(cleaned)
        if isinstance(res_data, dict):
            inferred_notes = res_data.get("inferred_style_notes", [])
            if not isinstance(inferred_notes, list):
                return False
                
            changed = False
            now_date = datetime.now().strftime("%Y-%m-%d")
            
            for item in inferred_notes:
                val = item.get("value")
                if not val:
                    continue
                category = item.get("category", "tone")
                conf = float(item.get("confidence", 0.75))
                reasoning = item.get("reasoning", "Inferred from discussion")
                source_type = item.get("source_type", "conversation")
                
                existing_item = next((i for i in mem.setdefault("ai_notes", []) if str(i.get("value", "")).lower() == val.lower()), None)
                
                if existing_item:
                    # Protect user_explicit items from degradation/override
                    is_existing_explicit = existing_item.get("source_type") == "user_explicit"
                    is_proposed_explicit = source_type == "user_explicit"
                    if is_existing_explicit and not is_proposed_explicit:
                        continue
                        
                    old_conf = existing_item.get("confidence", 0.75)
                    new_conf = min(1.0, max(old_conf, conf) + 0.05)
                    existing_item["confidence"] = round(new_conf, 3)
                    existing_item["reasoning"] = f"Reinforced by style analyzer. {reasoning}"
                    existing_item["last_reinforced"] = now_date
                    existing_item["last_seen"] = now_date
                    existing_item["category"] = category
                    changed = True
                else:
                    mem["ai_notes"].append({
                        "value": val,
                        "category": category,
                        "confidence": conf,
                        "source_type": source_type,
                        "last_reinforced": now_date,
                        "reasoning": reasoning,
                        "added": now_date,
                        "last_seen": now_date
                    })
                    changed = True
                    
            return changed
    except Exception as e:
        print(f"[Async Style Inference Error] Periodic style analyzer failed: {e}")
        
    return False

def extract_memory_async(user_id: str, user_message: str, history: list = None, preferred_model: str = None, workspace_id: str = None):
    """Background task to run LLM memory extraction, deconfliction, and save to Supabase."""
    try:
        mem = load_memory(user_id)
        changed = extract_memory_llm(user_message, mem, history=history, preferred_model=preferred_model)
        
        # Periodic Style Inference: check configurable interval
        style_interval = 10
        if workspace_id:
            try:
                res = supabase.table("oculus_workspaces").select("settings").eq("id", workspace_id).execute()
                if res.data:
                    settings = res.data[0].get("settings") or {}
                    style_interval = int(settings.get("style_inference_interval", 10))
            except Exception as e:
                print(f"[Async Memory] Failed to fetch workspace settings for style inference: {e}")
        
        msg_count = mem.get("message_count", 0)
        if msg_count > 0 and msg_count % style_interval == 0:
            print(f"[Async Style Inference] Running periodic style analyzer (interval: {style_interval}) for user: {user_id}...")
            style_changed = run_style_inference(user_id, mem, history, preferred_model)
            if style_changed:
                changed = True
        
        should_consolidate = changed and (
            mem.get("message_count", 0) % 5 == 0 or
            len(mem.get("preferences", [])) > 10 or
            len(mem.get("important_facts", [])) > 12
        )
        
        if should_consolidate:
            print(f"[Async Memory] Running memory consolidation for user: {user_id}")
            consolidated = consolidate_memory_llm(mem, preferred_model=preferred_model)
            required_keys = {"profile", "clients", "projects", "preferences", "important_facts", "topics_discussed", "deadlines", "ai_notes"}
            if isinstance(consolidated, dict) and required_keys.issubset(consolidated.keys()):
                consolidated["session_count"] = mem.get("session_count", 0)
                consolidated["message_count"] = mem.get("message_count", 0)
                consolidated["first_seen"] = mem.get("first_seen", "")
                consolidated["last_seen"] = mem.get("last_seen", "")
                consolidated["conflicts"] = mem.get("conflicts", [])
                mem = consolidated
                changed = True
                
        if changed:
            save_memory(user_id, mem)
            print(f"[Async Memory] Successfully updated and saved memory for user: {user_id}")
    except Exception as e:
        print("[Async Memory Error] Failed to process memory asynchronously:", e)

import collections

_EMBEDDING_CACHE_MODE = "lru"
try:
    EMBEDDING_CACHE = collections.OrderedDict()
except Exception:
    EMBEDDING_CACHE = {}
    _EMBEDDING_CACHE_MODE = "fallback"
    print("[Warning] Failed to initialize OrderedDict for embeddings; using unbounded dict.")

def get_embedding_cache_stats() -> dict:
    return {
        "size": len(EMBEDDING_CACHE),
        "max": 2000,
        "mode": _EMBEDDING_CACHE_MODE
    }

def cosine_similarity(v1, v2) -> float:
    if not v1 or not v2:
        return 0.0
    import math
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = math.sqrt(sum(x * x for x in v1))
    norm_v2 = math.sqrt(sum(x * x for x in v2))
    if not norm_v1 or not norm_v2:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def get_embeddings_cached(texts: list) -> list:
    results = [None] * len(texts)
    missing_texts = []
    missing_indices = []
    
    global _EMBEDDING_CACHE_MODE
    
    for i, text in enumerate(texts):
        if text in EMBEDDING_CACHE:
            emb = EMBEDDING_CACHE[text]
            if _EMBEDDING_CACHE_MODE == "lru":
                try:
                    EMBEDDING_CACHE.move_to_end(text)
                except Exception:
                    pass
            results[i] = emb
        else:
            missing_texts.append(text)
            missing_indices.append(i)
            
    if missing_texts:
        try:
            from backend.rag import generate_embeddings
            embedded = generate_embeddings(missing_texts)
            for text, emb in zip(missing_texts, embedded):
                EMBEDDING_CACHE[text] = emb
                if _EMBEDDING_CACHE_MODE == "lru":
                    try:
                        if len(EMBEDDING_CACHE) > 2000:
                            EMBEDDING_CACHE.popitem(last=False)
                    except Exception as e:
                        print(f"[Warning] Cache eviction failed, falling back to dict mode: {e}")
                        _EMBEDDING_CACHE_MODE = "fallback"
            for idx, emb in zip(missing_indices, embedded):
                results[idx] = emb
        except Exception as e:
            print("[Embedding Cache Error] Failed to generate embeddings:", e)
            
    return results

def rank_memory_items(user_message: str, items: list, max_results: int = 5, key_field: str = None, return_details: bool = False) -> list:
    if not items:
        return []

    # Prepare text representation for each item to embed
    item_texts = []
    for item in items:
        if isinstance(item, dict):
            if key_field and key_field in item:
                val = item[key_field]
            else:
                val = item.get("value") or item.get("name") or item.get("item") or ""
            item_texts.append(str(val))
        else:
            item_texts.append(str(item))

    # Fetch embeddings
    query_emb = None
    if user_message:
        query_embs = get_embeddings_cached([user_message])
        if query_embs:
            query_emb = query_embs[0]

    item_embs = get_embeddings_cached(item_texts)

    scored_items = []
    now = datetime.now()

    for idx, item in enumerate(items):
        # 1. Relevance: cosine similarity of embeddings (or 0.5 if query is empty)
        relevance = 0.5
        if user_message and query_emb and idx < len(item_embs) and item_embs[idx]:
            relevance = cosine_similarity(query_emb, item_embs[idx])
            relevance = max(0.0, relevance)

        # 2. Confidence: between 0.0 and 1.0
        confidence = 0.85
        if isinstance(item, dict) and "confidence" in item:
            try:
                confidence = float(item["confidence"])
            except Exception:
                pass

        # 3. Recency: parsed date diff
        recency = 0.5
        if isinstance(item, dict):
            date_str = item.get("last_reinforced") or item.get("last_seen") or item.get("added")
            if date_str:
                try:
                    added_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    days_since = (now - added_date).days
                    recency = 1.0 / (max(0, days_since) + 1.0)
                except Exception:
                    pass

        # 4. Importance: 1.0 if pinned or explicit, 0.0 otherwise
        importance = 0.0
        is_pinned = isinstance(item, dict) and (item.get("pinned") is True or item.get("is_pinned") is True)
        is_explicit = isinstance(item, dict) and item.get("source_type") == "user_explicit"
        if is_pinned or is_explicit:
            importance = 1.0

        # Weighted score: (relevance * 0.45) + (confidence * 0.25) + (recency * 0.20) + (importance * 0.10)
        final_score = (relevance * 0.45) + (confidence * 0.25) + (recency * 0.20) + (importance * 0.10)

        # Boost user_explicit and pinned items even more aggressively
        if is_pinned:
            final_score += 0.3  # Pinned items get massive boost
        elif is_explicit:
            final_score += 0.15 # Explicit items get substantial boost

        # Store details for debugging/breakdown if needed
        scored_items.append({
            "item": item,
            "text": item_texts[idx],
            "score": final_score,
            "relevance": relevance,
            "confidence": confidence,
            "recency": recency,
            "importance": importance
        })

    # Sort descending
    scored_items.sort(key=lambda x: x["score"], reverse=True)

    if return_details:
        return scored_items
    else:
        return [x["item"] for x in scored_items[:max_results]]

# Per-user ranking debug dict — keyed by user_id, max 100 entries (oldest evicted first).
# This replaces the previous single shared global that leaked one user's debug data to others.
_RANKING_DEBUG_BY_USER: dict = {}
_RANKING_DEBUG_MAX_USERS = 100

def _set_ranking_debug(user_id: str, data: dict):
    """Store per-user ranking debug data, evicting the oldest entry when the limit is reached."""
    if user_id in _RANKING_DEBUG_BY_USER:
        # Remove first so re-insertion places it at the end (preserves insertion-order for eviction)
        del _RANKING_DEBUG_BY_USER[user_id]
    elif len(_RANKING_DEBUG_BY_USER) >= _RANKING_DEBUG_MAX_USERS:
        # Evict the oldest entry (first key in insertion order)
        oldest_key = next(iter(_RANKING_DEBUG_BY_USER))
        del _RANKING_DEBUG_BY_USER[oldest_key]
    _RANKING_DEBUG_BY_USER[user_id] = data

def memory_to_context(mem: dict, user_message: str = "", memory_budget: int = 1500, preferred_model: str = None, user_id: str = None) -> str:

    def get_val(item):
        if isinstance(item, dict):
            return item.get("value") or item.get("name") or item.get("item") or ""
        return str(item)

    def filter_high_confidence(lst):
        res = []
        for item in lst:
            if isinstance(item, dict):
                if item.get("confidence", 1.0) >= 0.65:
                    res.append(item)
            else:
                res.append(item)
        return res

    def filter_low_confidence(lst):
        res = []
        for item in lst:
            if isinstance(item, dict):
                if item.get("confidence", 1.0) < 0.65:
                    res.append(item)
        return res

    # 1. Protected Section
    # - Profile fields with confidence >= 0.65
    # - AI Notes / Style rules with confidence >= 0.8 or pinned == True
    profile_lines = []
    p = mem.get("profile", {})
    for field in ["name", "role", "company", "location", "email", "phone"]:
        f_obj = p.get(field)
        if f_obj:
            val = f_obj.get("value") if isinstance(f_obj, dict) else f_obj
            conf = f_obj.get("confidence", 1.0) if isinstance(f_obj, dict) else 1.0
            if val and conf >= 0.65:
                profile_lines.append(f"- {field.capitalize()}: {val}")

    protected_notes = []
    other_notes = []
    for note in mem.get("ai_notes", []):
        if isinstance(note, dict):
            conf = note.get("confidence", 1.0)
            pinned = note.get("pinned", False) or note.get("is_pinned", False)
            if pinned or conf >= 0.8:
                protected_notes.append(note)
            elif conf >= 0.65:
                other_notes.append(note)
        else:
            other_notes.append(note)

    # Rank protected notes to display the most relevant ones first, but keep all of them
    protected_notes_details = rank_memory_items(user_message, protected_notes, max_results=len(protected_notes), return_details=True)
    ranked_protected_notes = [x["item"] for x in protected_notes_details]

    # Gather category lists
    categories = {
        "clients": (mem.get("clients", []), None),
        "projects": (mem.get("projects", []), "name"),
        "deadlines": (mem.get("deadlines", []), "item"),
        "preferences": (mem.get("preferences", []), None),
        "important_facts": (mem.get("important_facts", []), None),
        "ai_notes_other": (other_notes, None)
    }

    # Rank each category and collect details
    ranked_categories_details = {}
    for cat_name, (lst, key_f) in categories.items():
        high = filter_high_confidence(lst)
        # Use return_details=True to get scores and matching info
        details = rank_memory_items(user_message, high, max_results=len(high), key_field=key_f, return_details=True)
        ranked_categories_details[cat_name] = details

    # Low Priority items collection
    low_priority_fact_strings = []
    # Collect items from list categories that are not in the top limit (default 5 items per category) or are low confidence
    for cat_name, (lst, key_f) in categories.items():
        details = ranked_categories_details[cat_name]
        top_items = [d["item"] for d in details[:5]]
        rest_items = [d["item"] for d in details[5:]]
        low_conf = filter_low_confidence(lst)
        
        # Add rest and low_conf to low priority
        prefix = cat_name[:-6] if cat_name.endswith("_other") else cat_name
        # Singularize prefix for readability
        if prefix.endswith("s"):
            prefix = prefix[:-1]
        
        for item in (rest_items + low_conf):
            val_str = get_val(item)
            if val_str:
                if prefix == "deadline" and isinstance(item, dict) and "date" in item:
                    low_priority_fact_strings.append(f"Deadline: {val_str} (Due: {item['date']})")
                else:
                    low_priority_fact_strings.append(f"{prefix.capitalize()}: {val_str}")

    # Generate or retrieve low-priority summary paragraph
    summary_text = ""
    summary_used = False
    if low_priority_fact_strings:
        import hashlib
        low_priority_fact_strings.sort()
        joined_facts = "||".join(low_priority_fact_strings)
        current_hash = hashlib.md5(joined_facts.encode("utf-8")).hexdigest()
        
        if mem.get("low_priority_hash") == current_hash and mem.get("low_priority_summary"):
            summary_text = mem.get("low_priority_summary")
            summary_used = True
        else:
            print(f"[Memory Budget] Regenerating summary for {len(low_priority_fact_strings)} facts...")
            facts_bullet_list = "\n".join(f"- {f}" for f in low_priority_fact_strings)
            prompt = (
                "Summarize the following old or low-priority user facts, preferences, deadlines, and style rules "
                "into a single, short, dense 'Memory Summary' paragraph. Do not include duplicates. Keep it extremely "
                "concise (ideally under 300 characters, at most a couple of short sentences). Plain text only.\n\n"
                f"Facts to summarize:\n{facts_bullet_list}\n\nSummary:"
            )
            try:
                from backend.models import query_openrouter
                summary_text = query_openrouter(prompt, preferred_model=preferred_model)
                summary_text = summary_text.replace("\n", " ").strip()
                
                # Cache it in memory dict
                mem["low_priority_hash"] = current_hash
                mem["low_priority_summary"] = summary_text
                summary_used = True
                if user_id:
                    save_memory(user_id, mem)
            except Exception as e:
                print("[Memory Budget Error] Failed to generate low-priority summary:", e)
                summary_text = ""

    # Helper function to assemble and count tokens
    def assemble(limit):
        lines = []
        # Protected profile
        lines.extend(profile_lines)
        
        # Protected notes
        if ranked_protected_notes:
            lines.append("- Behavioral & Style rules to follow (High Priority):")
            for note in ranked_protected_notes:
                lines.append(f"  • {get_val(note)}")
                
        # Dynamic categories with limit
        cl = [d["item"] for d in ranked_categories_details["clients"][:limit]]
        if cl:
            lines.append(f"- Known clients: {', '.join([get_val(c) for c in cl])}")
            
        pr = [d["item"] for d in ranked_categories_details["projects"][:limit]]
        if pr:
            lines.append(f"- Active/recent projects: {', '.join([get_val(p) for p in pr])}")
            
        dl = [d["item"] for d in ranked_categories_details["deadlines"][:limit]]
        if dl:
            parts = [f"{d.get('date','?')} ({d.get('item','')[:40]})" for d in dl]
            lines.append(f"- Deadlines: {' | '.join(parts)}")
            
        pf = [d["item"] for d in ranked_categories_details["preferences"][:limit]]
        if pf:
            lines.append("- User preferences:")
            for pref in pf:
                lines.append(f"  • {get_val(pref)}")
                
        ft = [d["item"] for d in ranked_categories_details["important_facts"][:limit]]
        if ft:
            lines.append("- Important facts to remember:")
            for fact in ft:
                lines.append(f"  • {get_val(fact)}")
                
        nt = [d["item"] for d in ranked_categories_details["ai_notes_other"][:limit]]
        if nt:
            lines.append("- Behavioral & Style rules (Medium Priority):")
            for note in nt:
                lines.append(f"  • {get_val(note)}")
                
        if summary_text:
            lines.append(f"- Memory Summary (Older/Low-Priority facts): {summary_text}")
            
        # Metadata
        sessions = mem.get("session_count", 0)
        messages = mem.get("message_count", 0)
        if messages:
            lines.append(f"- Sessions: {sessions}  |  Messages sent: {messages}")
        if mem.get("first_seen") and mem.get("last_seen"):
            lines.append(f"- First seen: {mem['first_seen']}  |  Last seen: {mem['last_seen']}")
            
        return "\n".join(lines) if lines else "No user facts stored yet."

    # Progressive pruning logic if token budget exceeded
    final_limit = 5
    pruned = False
    context_str = assemble(final_limit)
    
    # Prune from 5 down to 1 if estimated tokens exceed budget
    for limit in range(5, 0, -1):
        estimated_tokens = len(context_str) // 4
        if estimated_tokens <= memory_budget:
            final_limit = limit
            break
        context_str = assemble(limit)
        final_limit = limit
        pruned = True

    # If still too large, try formatting without dynamic items at all (only protected + summary)
    estimated_tokens = len(context_str) // 4
    if estimated_tokens > memory_budget:
        context_str = assemble(0) # 0 limit means no dynamic items
        estimated_tokens = len(context_str) // 4
        pruned = True

    # Populate Debug dictionary
    debug_ranked = {}
    
    # 1. Protected items
    debug_protected = profile_lines.copy()
    for note in ranked_protected_notes:
        debug_protected.append(f"AI Note (High Priority): {get_val(note)}")
        
    # 2. Category rankings details
    for cat_name, details in ranked_categories_details.items():
        debug_ranked[cat_name] = []
        for d in details:
            injected = False
            if final_limit > 0:
                injected = (d["item"] in [x["item"] for x in details[:final_limit]])
            debug_ranked[cat_name].append({
                "text": d["text"],
                "score": d["score"],
                "injected": injected,
                "details": {
                    "relevance": d["relevance"],
                    "confidence": d["confidence"],
                    "recency": d["recency"],
                    "importance": d["importance"]
                }
            })
            
    debug_payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": user_message,
        "memory_budget": memory_budget,
        "estimated_tokens": estimated_tokens,
        "pruned": pruned,
        "summary_used": summary_used and bool(summary_text),
        "protected_items": debug_protected,
        "ranked_items": debug_ranked,
        "injected_context": context_str
    }
    # Store debug data scoped to this user only — never in a shared global
    if user_id:
        _set_ranking_debug(user_id, debug_payload)

    return context_str

@memory_bp.route("/api/memory", methods=["GET"])
@login_required
def get_memory_api():
    uid = current_user_id()
    mem = load_memory(uid)
    return jsonify(mem)

@memory_bp.route("/api/memory/debug", methods=["GET"])
@login_required
def get_ranking_debug_api():
    # Returns only this user's own debug data — never another user's.
    # Returns an empty dict if no ranking has been computed for this user yet.
    uid = current_user_id()
    return jsonify(_RANKING_DEBUG_BY_USER.get(uid, {}))

@memory_bp.route("/api/memory/pin", methods=["POST"])
@login_required
def pin_memory_api():
    uid = current_user_id()
    data = request.get_json() or {}
    key = data.get("key")
    val = data.get("value")
    pin = data.get("pin", True)
    
    mem = load_memory(uid)
    changed = False
    
    if key in ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]:
        for item in mem.get(key, []):
            if isinstance(item, dict) and item.get("value") == val:
                item["pinned"] = pin
                if pin:
                    item["confidence"] = 1.0
                changed = True
                break
    elif key == "projects":
        for item in mem.get("projects", []):
            if isinstance(item, dict) and item.get("name") == val:
                item["pinned"] = pin
                if pin:
                    item["confidence"] = 1.0
                changed = True
                break
    elif key == "deadlines":
        for item in mem.get("deadlines", []):
            if isinstance(item, dict) and item.get("item") == val:
                item["pinned"] = pin
                if pin:
                    item["confidence"] = 1.0
                changed = True
                break
                
    if changed:
        save_memory(uid, mem)
        return jsonify({"status": "ok", "memory": mem})
    return jsonify({"status": "no_change", "error": "Item not found"}), 404

def classify_memory_command(user_message: str, preferred_model: str = None) -> dict:
    keywords = {"forget", "stop using", "delete note", "remove preference", "unpin", "clear preference", "don't remember", "pin", "emphasize"}
    msg_lower = user_message.lower()
    if not any(kw in msg_lower for kw in keywords):
        return {"is_command": False}
        
    prompt = (
        "You are an intent classifier for a personal memory assistant.\n"
        "The user is issuing a command to delete or pin memory items.\n"
        "Analyze this user message and determine if it is an explicit command to modify their memory.\n"
        "Example commands:\n"
        "- 'forget everything about Vue' -> {\"is_command\": true, \"action\": \"forget\", \"target_query\": \"Vue\"}\n"
        "- 'stop using formal tone' -> {\"is_command\": true, \"action\": \"forget\", \"target_query\": \"formal tone\"}\n"
        "- 'Forget all old design preferences' -> {\"is_command\": true, \"action\": \"batch_forget\", \"target_query\": \"old design preferences\"}\n"
        "- 'remove preference for Lex Digitals' -> {\"is_command\": true, \"action\": \"forget\", \"target_query\": \"Lex Digitals\"}\n"
        "- 'unpin note about Lex' -> {\"is_command\": true, \"action\": \"unpin\", \"target_query\": \"Lex\"}\n"
        "- 'pin my preference for React' -> {\"is_command\": true, \"action\": \"pin\", \"target_query\": \"preference for React\"}\n"
        "\n"
        "Return a JSON object in this exact format (do not output any other text, markdown blocks, or styling):\n"
        "{\n"
        "  \"is_command\": true or false,\n"
        "  \"action\": \"forget\" | \"batch_forget\" | \"unpin\" | \"pin\",\n"
        "  \"target_query\": \"extracted topic or query or preference\"\n"
        "}\n\n"
        f"User message: {user_message}\n\n"
        "Response:"
    )
    
    try:
        from backend.models import query_openrouter
        resp = query_openrouter(prompt, preferred_model=preferred_model)
        cleaned = resp.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned.strip())
        return data
    except Exception as e:
        print("[Command Interceptor Error] Failed to classify command:", e)
        return {"is_command": False}

def execute_memory_command(uid: str, mem: dict, command_data: dict) -> str:
    action = command_data.get("action")
    target_query = command_data.get("target_query", "").strip()
    if not target_query:
        return "I'm not sure what you want me to do. Could you be more specific?"
        
    changed = False
    deleted_items = []
    
    list_keys = ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes", "projects", "deadlines"]
    
    def get_item_text(item):
        if isinstance(item, dict):
            return item.get("value") or item.get("name") or item.get("item") or ""
        return str(item)
        
    if action in ["forget", "batch_forget"]:
        candidates = []
        for key in list_keys:
            for idx, item in enumerate(mem.get(key, [])):
                text = get_item_text(item)
                if text:
                    candidates.append((key, idx, item, text))
                    
        if not candidates:
            return "I couldn't find anything matching that in my memory."
            
        target_emb = None
        target_embs = get_embeddings_cached([target_query])
        if target_embs:
            target_emb = target_embs[0]
            
        item_texts = [c[3] for c in candidates]
        item_embs = get_embeddings_cached(item_texts)
        
        to_delete = []
        for idx, (key, item_idx, item, text) in enumerate(candidates):
            keyword_match = target_query.lower() in text.lower()
            semantic_match = False
            if target_emb and idx < len(item_embs) and item_embs[idx]:
                sim = cosine_similarity(target_emb, item_embs[idx])
                if sim >= 0.55:
                    semantic_match = True
                    
            if keyword_match or semantic_match:
                to_delete.append((key, item))
                deleted_items.append(text)
                
        if to_delete:
            for key, item in to_delete:
                mem[key] = [x for x in mem[key] if x != item]
            changed = True
            
            bullets = "\n".join(f"• {item}" for item in deleted_items[:5])
            if len(deleted_items) > 5:
                bullets += f"\n• ... and {len(deleted_items) - 5} more items."
            
            if changed and uid:
                save_memory(uid, mem)
            return f"✓ I've forgotten the following from your memory:\n{bullets}"
        else:
            return f"I couldn't find any facts or preferences related to '{target_query}' in my memory."
            
    elif action in ["pin", "unpin"]:
        pin_val = (action == "pin")
        candidates = []
        for key in list_keys:
            for idx, item in enumerate(mem.get(key, [])):
                text = get_item_text(item)
                if text:
                    candidates.append((key, idx, item, text))
                    
        target_emb = None
        target_embs = get_embeddings_cached([target_query])
        if target_embs:
            target_emb = target_embs[0]
            
        best_match = None
        best_sim = -1.0
        
        item_texts = [c[3] for c in candidates]
        item_embs = get_embeddings_cached(item_texts)
        
        for idx, (key, item_idx, item, text) in enumerate(candidates):
            sim = 0.0
            if target_query.lower() in text.lower():
                sim = 1.0
            elif target_emb and idx < len(item_embs) and item_embs[idx]:
                sim = cosine_similarity(target_emb, item_embs[idx])
                
            if sim > best_sim:
                best_sim = sim
                best_match = (key, item, text)
                
        if best_match and best_sim >= 0.5:
            key, item, text = best_match
            if isinstance(item, dict):
                item["pinned"] = pin_val
                if pin_val:
                    item["confidence"] = 1.0
                changed = True
                action_str = "pinned" if pin_val else "unpinned"
                if changed and uid:
                    save_memory(uid, mem)
                return f"✓ I've {action_str} this item: '{text}'"
        
        return f"I couldn't find a matching fact or preference to pin/unpin for '{target_query}'."

    return "Memory command executed."

@memory_bp.route("/api/memory/update", methods=["POST"])
@login_required
def update_memory_api():
    uid = current_user_id()
    data = request.get_json() or {}
    update_type = data.get("type")
    
    mem = load_memory(uid)
    changed = False
    
    if update_type == "profile":
        field = data.get("field")
        value = (data.get("value") or "").strip()
        if field in mem["profile"]:
            mem["profile"][field] = {
                "value": value,
                "confidence": 1.0,
                "reasoning": "Manually set by user"
            }
            changed = True
            
    elif update_type == "list":
        key = data.get("key")
        value = (data.get("value") or "").strip()
        if key in ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]:
            existing = any((item.get("value") if isinstance(item, dict) else item) == value for item in mem[key])
            if not existing:
                mem[key].append({
                    "value": value,
                    "confidence": 1.0,
                    "reasoning": "Manually added by user",
                    "added": datetime.now().strftime("%Y-%m-%d"),
                    "last_seen": datetime.now().strftime("%Y-%m-%d")
                })
                changed = True
                
    elif update_type == "project":
        name = (data.get("name") or "").strip()
        if name:
            existing = any((p.get("name") if isinstance(p, dict) else p).lower() == name.lower() for p in mem["projects"])
            if not existing:
                mem["projects"].append({
                    "name": name,
                    "value": name,
                    "confidence": 1.0,
                    "reasoning": "Manually added by user",
                    "added": datetime.now().strftime("%Y-%m-%d"),
                    "last_seen": datetime.now().strftime("%Y-%m-%d")
                })
                changed = True
                
    elif update_type == "deadline":
        item = (data.get("item") or "").strip()
        date_val = (data.get("date") or "").strip()
        if item and date_val:
            mem["deadlines"].append({
                "item": item,
                "value": item,
                "date": date_val,
                "confidence": 1.0,
                "reasoning": "Manually added by user",
                "added": datetime.now().strftime("%Y-%m-%d"),
                "last_seen": datetime.now().strftime("%Y-%m-%d")
            })
            changed = True
            
    if changed:
        save_memory(uid, mem)
        return jsonify({"status": "ok", "memory": mem})
    return jsonify({"status": "no_change", "error": "Invalid request parameters or duplicate item"}), 400

@memory_bp.route("/api/memory/delete", methods=["POST"])
@login_required
def delete_memory_api():
    uid = current_user_id()
    data = request.get_json() or {}
    key = data.get("key")
    
    mem = load_memory(uid)
    changed = False
    
    if key in ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]:
        val = data.get("value")
        initial_len = len(mem[key])
        mem[key] = [item for item in mem[key] if (item.get("value") if isinstance(item, dict) else item) != val]
        if len(mem[key]) < initial_len:
            changed = True
            
    elif key == "projects":
        name = data.get("name")
        initial_len = len(mem["projects"])
        mem["projects"] = [p for p in mem["projects"] if (p.get("name") if isinstance(p, dict) else p) != name]
        if len(mem["projects"]) < initial_len:
            changed = True
            
    elif key == "deadlines":
        item = data.get("item")
        initial_len = len(mem["deadlines"])
        mem["deadlines"] = [d for d in mem["deadlines"] if (d.get("item") if isinstance(d, dict) else d) != item]
        if len(mem["deadlines"]) < initial_len:
            changed = True
            
    if changed:
        save_memory(uid, mem)
        return jsonify({"status": "ok", "memory": mem})
    return jsonify({"status": "no_change", "error": "Item not found"}), 404

@memory_bp.route("/api/memory/override_confidence", methods=["POST"])
@login_required
def override_confidence_api():
    uid = current_user_id()
    data = request.get_json() or {}
    key = data.get("key")
    val = data.get("value")
    confidence = float(data.get("confidence", 1.0))
    
    mem = load_memory(uid)
    changed = False
    
    if key == "profile":
        field = data.get("field")
        if field in mem["profile"]:
            mem["profile"][field]["confidence"] = confidence
            mem["profile"][field]["reasoning"] = "Manually overridden by user"
            changed = True
    elif key in ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes", "projects", "deadlines"]:
        for item in mem[key]:
            item_val = item.get("value") or item.get("name") or item.get("item")
            if item_val == val:
                item["confidence"] = confidence
                item["reasoning"] = "Manually overridden by user"
                item["last_seen"] = datetime.now().strftime("%Y-%m-%d")
                changed = True
                break
                
    if changed:
        save_memory(uid, mem)
        return jsonify({"status": "ok", "memory": mem})
    return jsonify({"status": "error", "error": "Item not found"}), 404

@memory_bp.route("/api/memory/resolve_conflict", methods=["POST"])
@login_required
def resolve_conflict_api():
    uid = current_user_id()
    data = request.get_json() or {}
    cid = data.get("conflict_id")
    action = data.get("action")
    
    mem = load_memory(uid)
    conflicts = mem.get("conflicts", [])
    conflict = next((c for c in conflicts if c.get("id") == cid), None)
    if not conflict:
        return jsonify({"status": "error", "error": "Conflict not found"}), 404
        
    key = conflict["key"]
    existing = conflict["existing"]
    new_item = conflict["new"]
    
    if key.startswith("profile."):
        field = key.split(".")[1]
        if action == "use_new":
            mem["profile"][field] = new_item
    else:
        if action == "use_new":
            target_val = existing.get("value") or existing.get("name") or existing.get("item")
            for idx, item in enumerate(mem[key]):
                item_val = item.get("value") or item.get("name") or item.get("item")
                if item_val == target_val:
                    mem[key][idx] = new_item
                    break
        elif action == "keep_both":
            mem[key].append(new_item)

    mem["conflicts"] = [c for c in conflicts if c.get("id") != cid]
    save_memory(uid, mem)
    return jsonify({"status": "ok", "memory": mem})

@memory_bp.route("/api/memory/run_decay", methods=["POST"])
@login_required
def run_decay_api():
    uid = current_user_id()
    mem = load_memory(uid)
    apply_memory_decay(mem)
    mem["last_decay_run"] = datetime.now().strftime("%Y-%m-%d")
    save_memory(uid, mem)
    return jsonify({"status": "ok", "memory": mem})

@memory_bp.route("/api/memory/style_feedback", methods=["POST"])
@login_required
def style_feedback_api():
    uid = current_user_id()
    data = request.get_json() or {}
    feedback = data.get("feedback")  # "positive" or "negative"
    correction = data.get("correction", "").strip()
    
    mem = load_memory(uid)
    changed = False
    now_date = datetime.now().strftime("%Y-%m-%d")
    
    if feedback == "positive":
        # Reinforce all style notes: positive feedback boosts notes by +0.05
        for note in mem.setdefault("ai_notes", []):
            old_conf = note.get("confidence", 0.75)
            note["confidence"] = round(min(1.0, old_conf + 0.05), 3)
            note["last_reinforced"] = now_date
            note["reasoning"] = f"Reinforced by positive user style feedback. {note.get('reasoning', '')}".split(". ")[-1]
            changed = True
    elif feedback == "negative" and correction:
        # Lower confidence of current inferred style notes by -0.1 (except user_explicit notes)
        for note in mem.setdefault("ai_notes", []):
            if note.get("source_type") != "user_explicit" or note.get("confidence", 1.0) < 1.0:
                old_conf = note.get("confidence", 0.75)
                note["confidence"] = round(max(0.1, old_conf - 0.1), 3)
                note["reasoning"] = f"Adjusted due to negative style feedback. {note.get('reasoning', '')}".split(". ")[-1]
                changed = True
        
        # Determine correction category (simple keyword detection or generic tone)
        category = "tone"
        lower_corr = correction.lower()
        if "format" in lower_corr or "bullet" in lower_corr or "list" in lower_corr or "paragraph" in lower_corr or "spacing" in lower_corr:
            category = "formatting"
        elif "avoid" in lower_corr or "don't" in lower_corr or "dont" in lower_corr or "never" in lower_corr or "stop" in lower_corr:
            category = "forbidden"
        elif "word" in lower_corr or "spelling" in lower_corr or "phrase" in lower_corr or "term" in lower_corr:
            category = "vocabulary"
        elif "client" in lower_corr or "for " in lower_corr:
            category = "client_specific"
            
        # Add correction note as a new high-confidence (0.9), user_explicit note
        mem["ai_notes"].append({
            "value": f"Style correction: {correction}",
            "category": category,
            "confidence": 0.9,
            "source_type": "user_explicit",
            "last_reinforced": now_date,
            "reasoning": "Explicit style correction from user feedback",
            "added": now_date,
            "last_seen": now_date
        })
        changed = True
        
    if changed:
        if len(mem["ai_notes"]) > 15:
            mem["ai_notes"] = mem["ai_notes"][-15:]
        save_memory(uid, mem)
        return jsonify({"status": "ok", "memory": mem})
        
    return jsonify({"status": "no_change", "memory": mem})
