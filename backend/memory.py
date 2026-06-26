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
    now_date = datetime.now().strftime("%Y-%m-%d")
    try:
        res = supabase.table("oculus_memory").select("memory").eq("user_id", user_id).execute()
        mem = res.data[0].get("memory", {}) if res.data else {}
    except Exception as e:
        print("Memory load error:", e)
        mem = {}
        
    merged = json.loads(json.dumps(MEMORY_DEFAULT))
    for key, val in mem.items():
        if key in merged:
            merged[key] = val
            
    # Normalize profile fields
    profile = merged.setdefault("profile", {})
    for field in ["name", "role", "company", "location", "email", "phone"]:
        val = profile.get(field)
        if val is None:
            profile[field] = {"value": "", "confidence": 1.0, "source_type": "manual", "last_reinforced": now_date, "reasoning": "Unspecified"}
        elif isinstance(val, str):
            profile[field] = {"value": val, "confidence": 1.0, "source_type": "manual", "last_reinforced": now_date, "reasoning": "Legacy profile item"}
        elif isinstance(val, dict):
            conf = val.get("confidence") if val.get("confidence") is not None else 1.0
            source = val.get("source_type")
            if not source:
                source = "user_explicit" if conf >= 1.0 else "conversation"
            profile[field] = {
                "value": val.get("value") or "",
                "confidence": conf,
                "source_type": source,
                "last_reinforced": val.get("last_reinforced") or val.get("last_seen") or now_date,
                "reasoning": val.get("reasoning") or "Saved profile item"
            }

    # Normalize list-based fields
    list_keys = ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]
    for key in list_keys:
        normalized = []
        for item in merged.get(key, []):
            norm = normalize_fact(item, default_confidence=0.85, default_reasoning="Legacy memory item")
            if norm:
                normalized.append(norm)
        merged[key] = normalized

    # Normalize projects
    now_date = datetime.now().strftime("%Y-%m-%d")
    normalized_projects = []
    for item in merged.get("projects", []):
        if isinstance(item, str):
            normalized_projects.append({
                "name": item,
                "value": item,
                "confidence": 0.85,
                "reasoning": "Legacy project item",
                "added": now_date,
                "last_seen": now_date
            })
        elif isinstance(item, dict):
            name = item.get("name") or item.get("value") or ""
            normalized_projects.append({
                "name": name,
                "value": name,
                "confidence": item.get("confidence") if item.get("confidence") is not None else 0.85,
                "reasoning": item.get("reasoning") or "Saved project item",
                "added": item.get("added") or now_date,
                "last_seen": item.get("last_seen") or item.get("added") or now_date
            })
    merged["projects"] = normalized_projects

    # Normalize deadlines
    normalized_deadlines = []
    for item in merged.get("deadlines", []):
        if isinstance(item, str):
            normalized_deadlines.append({
                "item": item,
                "value": item,
                "date": "Not specified",
                "confidence": 0.85,
                "reasoning": "Legacy deadline item",
                "added": now_date,
                "last_seen": now_date
            })
        elif isinstance(item, dict):
            task_name = item.get("item") or item.get("value") or ""
            normalized_deadlines.append({
                "item": task_name,
                "value": task_name,
                "date": item.get("date") or "Not specified",
                "confidence": item.get("confidence") if item.get("confidence") is not None else 0.85,
                "reasoning": item.get("reasoning") or "Saved deadline item",
                "added": item.get("added") or now_date,
                "last_seen": item.get("last_seen") or item.get("added") or now_date
            })
    merged["deadlines"] = normalized_deadlines

    # Ensure conflicts list exists
    if "conflicts" not in merged or not isinstance(merged["conflicts"], list):
        merged["conflicts"] = []

    # Bounded daily decay run
    today_str = datetime.now().strftime("%Y-%m-%d")
    if merged.get("last_decay_run") != today_str:
        decay_changed = apply_memory_decay(merged)
        merged["last_decay_run"] = today_str
        try:
            supabase.table("oculus_memory").upsert({
                "user_id": user_id,
                "memory":  merged
            }).execute()
        except Exception as e:
            print("Failed to save decayed memory:", e)

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

    try:
        supabase.table("oculus_memory").upsert({
            "user_id": user_id,
            "memory":  mem
        }).execute()
    except Exception as e:
        print("Memory save error:", e)

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

def extract_memory_regex(text: str, mem: dict) -> bool:
    if is_ad_content(text):
        return False
    changed = False
    t = text.strip()

    for pat in [
        r"(?:my name is|i(?:'m| am) called|call me|i go by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+here[,.]",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in {"the", "a", "an", "this", "that", "here"}:
                if add_profile_field_with_conflict_check(mem, "name", candidate, 1.0, "Direct statement."):
                    changed = True
                break

    for pat in [
        r"(?:i(?:'m| am) from|my company is|i work (?:at|for)|our company is|we(?:'re| are) called|the business is called)\s+(.+?)(?:\.|,|\band\b|$)",
        r"(?:my agency is|our agency is)\s+(.+?)(?:\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            if add_profile_field_with_conflict_check(mem, "company", m.group(1).strip()[:80], 1.0, "Direct statement."):
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
                if add_profile_field_with_conflict_check(mem, "role", role, 1.0, "Direct statement."):
                    changed = True
                break

    m = re.search(
        r"(?:i(?:'m| am) (?:based in|from|in)|we(?:'re| are) based in|located in)\s+(.+?)(?:\.|,|$)",
        t, re.IGNORECASE
    )
    if m:
        if add_profile_field_with_conflict_check(mem, "location", m.group(1).strip()[:60], 1.0, "Direct statement."):
            changed = True

    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", t)
    if m:
        if add_profile_field_with_conflict_check(mem, "email", m.group(0), 1.0, "Explicit statement."):
            changed = True

    m = re.search(r"(?:\+27|0)[6-8]\d[\s\-]?\d{3}[\s\-]?\d{4}", t)
    if m:
        if add_profile_field_with_conflict_check(mem, "phone", m.group(0), 1.0, "Explicit statement."):
            changed = True

    for pat in [
        r"(?:my client is|our client is|working (?:with|for) a? ?client called|the client(?:'s name)? is)\s+(.+?)(?:\.|,|$)",
        r"(?:client:)\s*(.+?)(?:\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            if _add_unique(mem["clients"], m.group(1).strip()[:60], max_len=20):
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
                    if len(mem["projects"]) > 15:
                        mem["projects"] = mem["projects"][-15:]
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
            if len(mem["deadlines"]) > 10:
                mem["deadlines"] = mem["deadlines"][-10:]
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
                if _add_unique(mem["preferences"], pref, max_len=15):
                    changed = True

    m = re.search(
        r"(?:remember (?:that )?|please note(?: that)?|keep in mind (?:that )?|don't forget (?:that )?)(.+?)(?:[.!?]|$)",
        t, re.IGNORECASE
    )
    if m:
        note = m.group(1).strip()
        if 5 < len(note) <= 120:
            if _add_unique(mem["important_facts"], note, max_len=20):
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
            if _add_unique(mem["topics_discussed"], topic, max_len=30):
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

    # Helper for standard lists: preferences, clients, important_facts, ai_notes, topics_discussed
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
                    current_memory[key] = current_memory[key][-max_len:]
                changed = True

    merge_list_field("preferences", 15)
    merge_list_field("clients", 20)
    merge_list_field("important_facts", 20)
    merge_list_field("topics_discussed", 30)
    merge_list_field("ai_notes", 15)

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
                if len(current_memory["projects"]) > 15:
                    current_memory["projects"] = current_memory["projects"][-15:]
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
                if len(current_memory["deadlines"]) > 10:
                    current_memory["deadlines"] = current_memory["deadlines"][-10:]
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
    """Uses LLM to clean up redundancies, resolve contradictions, and remove outdated items in memory."""
    current_date = datetime.now().strftime("%Y-%m-%d")
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
        if isinstance(consolidated, dict):
            return consolidated
    except Exception as e:
        print(f"[Memory Consolidation Error] LLM consolidation failed: {e}")
    return current_memory

def extract_memory_async(user_id: str, user_message: str, history: list = None, preferred_model: str = None):
    """Background task to run LLM memory extraction, deconfliction, and save to Supabase."""
    try:
        mem = load_memory(user_id)
        changed = extract_memory_llm(user_message, mem, history=history, preferred_model=preferred_model)
        
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

def rank_memory_items(user_message: str, items: list, max_results: int = 5, key_field: str = None) -> list:
    if not items:
        return []
    if not user_message:
        # Sort by confidence * recency descending
        scored_items = []
        for item in items:
            conf = 1.0
            if isinstance(item, dict) and "confidence" in item:
                conf = float(item["confidence"])
            
            recency = 0.5
            if isinstance(item, dict):
                date_str = item.get("last_seen") or item.get("added")
                if date_str:
                    try:
                        added_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                        days_since = (datetime.now() - added_date).days
                        recency = 1.0 / (max(0, days_since) + 1.0)
                    except Exception:
                        pass
            scored_items.append((conf * recency, item))
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_items[:max_results]]

    stop_words = {
        "the", "a", "an", "is", "for", "to", "and", "of", "in", "on", 
        "at", "with", "it", "that", "this", "i", "you", "my", "your", 
        "we", "us", "they", "them", "he", "she", "his", "her", "me", "our"
    }
    user_words = re.findall(r"\b\w+\b", user_message.lower())
    search_tokens = {w for w in user_words if w not in stop_words}

    scored_items = []
    for idx, item in enumerate(items):
        text_content = ""
        if isinstance(item, dict):
            text_content = str(item.get("value") or item.get("name") or item.get("item") or "")
        else:
            text_content = str(item)

        # 1. Relevance: token matches
        item_words = set(re.findall(r"\b\w+\b", text_content.lower()))
        overlap = search_tokens.intersection(item_words)
        relevance = 1.0 + len(overlap) * 2.0

        # 2. Recency: index position or parsed date diff
        recency = 0.5
        if isinstance(item, dict):
            date_str = item.get("last_seen") or item.get("added")
            if date_str:
                try:
                    added_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    days_since = (datetime.now() - added_date).days
                    recency = 1.0 / (max(0, days_since) + 1.0)
                except Exception:
                    pass

        # 3. Confidence
        confidence = 1.0
        if isinstance(item, dict) and "confidence" in item:
            confidence = float(item["confidence"])
        
        score = confidence * recency * relevance
        scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_items[:max_results]]

def memory_to_context(mem: dict, user_message: str = "", max_results: int = 5) -> str:
    lines = []
    
    def get_val(item):
        if isinstance(item, dict):
            return item.get("value") or item.get("name") or item.get("item") or ""
        return str(item)

    # Only inject facts with confidence >= 0.65
    def filter_high_confidence(lst):
        res = []
        for item in lst:
            if isinstance(item, dict):
                if item.get("confidence", 1.0) >= 0.65:
                    res.append(item)
            else:
                res.append(item)
        return res

    p = mem.get("profile", {})
    for field in ["name", "role", "company", "location", "email", "phone"]:
        f_obj = p.get(field)
        if f_obj:
            val = f_obj.get("value") if isinstance(f_obj, dict) else f_obj
            conf = f_obj.get("confidence", 1.0) if isinstance(f_obj, dict) else 1.0
            if val and conf >= 0.65:
                lines.append(f"- {field.capitalize()}: {val}")
    
    clients = rank_memory_items(user_message, filter_high_confidence(mem.get("clients", [])), max_results=max_results)
    if clients:
        lines.append(f"- Known clients: {', '.join([get_val(c) for c in clients])}")
        
    projects = rank_memory_items(user_message, filter_high_confidence(mem.get("projects", [])), max_results=max_results, key_field="name")
    if projects:
        names = [proj.get("name", "") for proj in projects]
        lines.append(f"- Active/recent projects: {', '.join(names)}")
        
    deadlines = rank_memory_items(user_message, filter_high_confidence(mem.get("deadlines", [])), max_results=max(1, max_results - 1), key_field="item")
    if deadlines:
        parts = [f"{d.get('date','?')} ({d.get('item','')[:40]})" for d in deadlines]
        lines.append(f"- Deadlines: {' | '.join(parts)}")
        
    preferences = rank_memory_items(user_message, filter_high_confidence(mem.get("preferences", [])), max_results=max_results)
    if preferences:
        lines.append("- User preferences:")
        for pref in preferences:
            lines.append(f"  • {get_val(pref)}")
            
    facts = rank_memory_items(user_message, filter_high_confidence(mem.get("important_facts", [])), max_results=max_results)
    if facts:
        lines.append("- Important facts to remember:")
        for fact in facts:
            lines.append(f"  • {get_val(fact)}")
            
    notes = rank_memory_items(user_message, filter_high_confidence(mem.get("ai_notes", [])), max_results=max_results)
    if notes:
        lines.append("- Inferred behavioral observations (ai_notes):")
        for note in notes:
            lines.append(f"  • {get_val(note)}")
            
    topics = rank_memory_items(user_message, filter_high_confidence(mem.get("topics_discussed", [])), max_results=max_results + 1)
    if topics:
        lines.append(f"- Topics worked on previously: {', '.join([get_val(t) for t in topics])}")
        
    sessions = mem.get("session_count", 0)
    messages = mem.get("message_count", 0)
    if messages:
        lines.append(f"- Sessions: {sessions}  |  Messages sent: {messages}")
    if mem.get("first_seen") and mem.get("last_seen"):
        lines.append(f"- First seen: {mem['first_seen']}  |  Last seen: {mem['last_seen']}")
    return "\n".join(lines) if lines else "No user facts stored yet."

@memory_bp.route("/api/memory", methods=["GET"])
@login_required
def get_memory_api():
    uid = current_user_id()
    mem = load_memory(uid)
    return jsonify(mem)

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
