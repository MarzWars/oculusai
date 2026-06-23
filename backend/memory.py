import re
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from config import Config
from backend.extensions import supabase
from backend.utils import is_ad_content, _add_unique
from backend.models import query_openrouter_extraction
from backend.prompts import MEMORY_EXTRACTION_PROMPT_TEMPLATE, MEMORY_CONSOLIDATION_PROMPT_TEMPLATE
from backend.auth import login_required, current_user_id

memory_bp = Blueprint("memory", __name__)

MEMORY_DEFAULT = {
    "profile": {
        "name": "", "role": "", "company": "",
        "location": "", "email": "", "phone": ""
    },
    "clients":         [],
    "projects":        [],
    "preferences":     [],
    "important_facts": [],
    "topics_discussed":[],
    "deadlines":       [],
    "ai_notes":        [],
    "first_seen":      "",
    "last_seen":       "",
    "session_count":   0,
    "message_count":   0
}

def load_memory(user_id: str) -> dict:
    try:
        res = supabase.table("oculus_memory").select("memory").eq("user_id", user_id).execute()
        mem = res.data[0].get("memory", {}) if res.data else {}
    except Exception as e:
        print("Memory load error:", e)
        mem = {}
    merged = json.loads(json.dumps(MEMORY_DEFAULT))
    for key, val in mem.items():
        if key in merged:
            if isinstance(val, dict) and isinstance(merged[key], dict):
                merged[key].update(val)
            else:
                merged[key] = val
    return merged

def save_memory(user_id: str, mem: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mem["last_seen"] = now
    if not mem.get("first_seen"):
        mem["first_seen"] = now
    mem.pop("conversation_count", None)
    try:
        supabase.table("oculus_memory").upsert({
            "user_id": user_id,
            "memory":  mem
        }).execute()
    except Exception as e:
        print("Memory save error:", e)

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
                mem["profile"]["name"] = candidate
                changed = True
                break

    for pat in [
        r"(?:i(?:'m| am) from|my company is|i work (?:at|for)|our company is|we(?:'re| are) called|the business is called)\s+(.+?)(?:\.|,|\band\b|$)",
        r"(?:my agency is|our agency is)\s+(.+?)(?:\.|,|$)",
    ]:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            mem["profile"]["company"] = m.group(1).strip()[:80]
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
                mem["profile"]["role"] = role
                changed = True
                break

    m = re.search(
        r"(?:i(?:'m| am) (?:based in|from|in)|we(?:'re| are) based in|located in)\s+(.+?)(?:\.|,|$)",
        t, re.IGNORECASE
    )
    if m:
        mem["profile"]["location"] = m.group(1).strip()[:60]
        changed = True

    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", t)
    if m:
        mem["profile"]["email"] = m.group(0)
        changed = True

    m = re.search(r"(?:\+27|0)[6-8]\d[\s\-]?\d{3}[\s\-]?\d{4}", t)
    if m:
        mem["profile"]["phone"] = m.group(0)
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
                        "added": datetime.now().strftime("%Y-%m-%d")
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
                "date":  dl,
                "added": datetime.now().strftime("%Y-%m-%d")
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
    """Safely merges LLM updates dictionary into current_memory."""
    changed = False

    # 1. Profile
    profile_updates = updates.get("profile", {})
    if isinstance(profile_updates, dict):
        for field in ["name", "role", "company", "location", "email", "phone"]:
            new_val = (profile_updates.get(field) or "").strip()
            if new_val and current_memory["profile"].get(field) != new_val:
                current_memory["profile"][field] = new_val
                changed = True

    # 2. Clients
    client_updates = updates.get("clients", [])
    if isinstance(client_updates, list):
        for client in client_updates:
            if isinstance(client, str):
                if _add_unique(current_memory["clients"], client, max_len=20):
                    changed = True

    # 3. Projects
    project_updates = updates.get("projects", [])
    if isinstance(project_updates, list):
        for project in project_updates:
            proj_name = ""
            if isinstance(project, dict) and "name" in project:
                proj_name = project["name"].strip()
            elif isinstance(project, str):
                proj_name = project.strip()
                
            if proj_name:
                existing = [p.get("name", "").lower() for p in current_memory["projects"]]
                if proj_name.lower() not in existing:
                    current_memory["projects"].append({
                        "name": proj_name[:80],
                        "added": datetime.now().strftime("%Y-%m-%d")
                    })
                    if len(current_memory["projects"]) > 15:
                        current_memory["projects"] = current_memory["projects"][-15:]
                    changed = True

    # 4. Preferences
    pref_updates = updates.get("preferences", [])
    if isinstance(pref_updates, list):
        for pref in pref_updates:
            if isinstance(pref, str):
                if _add_unique(current_memory["preferences"], pref, max_len=15):
                    changed = True

    # 5. Important Facts
    fact_updates = updates.get("important_facts", [])
    if isinstance(fact_updates, list):
        for fact in fact_updates:
            if isinstance(fact, str):
                if _add_unique(current_memory["important_facts"], fact, max_len=20):
                    changed = True

    # 6. Deadlines
    deadline_updates = updates.get("deadlines", [])
    if isinstance(deadline_updates, list):
        for dl in deadline_updates:
            item_name = ""
            date_val = ""
            if isinstance(dl, dict) and "item" in dl and "date" in dl:
                item_name = dl["item"].strip()
                date_val = dl["date"].strip()
            elif isinstance(dl, str):
                item_name = dl.strip()
                date_val = "Not specified"
                
            if item_name:
                current_memory["deadlines"].append({
                    "item": item_name[:80],
                    "date": date_val[:60],
                    "added": datetime.now().strftime("%Y-%m-%d")
                })
                if len(current_memory["deadlines"]) > 10:
                    current_memory["deadlines"] = current_memory["deadlines"][-10:]
                changed = True

    # 7. Topics
    topic_updates = updates.get("topics_discussed", [])
    if isinstance(topic_updates, list):
        for topic in topic_updates:
            if isinstance(topic, str):
                if _add_unique(current_memory["topics_discussed"], topic, max_len=30):
                    changed = True

    # 8. AI Inferences (ai_notes)
    ai_notes_updates = updates.get("ai_notes", [])
    if isinstance(ai_notes_updates, list):
        for note in ai_notes_updates:
            if isinstance(note, str):
                if _add_unique(current_memory["ai_notes"], note, max_len=15):
                    changed = True

    return changed


def extract_memory_llm(user_message: str, current_memory: dict, preferred_model: str = None) -> bool:
    """Uses LLM to extract structured memory from the user's message, falling back to regex on failure."""
    if is_ad_content(user_message):
        return False

    prompt = MEMORY_EXTRACTION_PROMPT_TEMPLATE.format(
        current_memory_json=json.dumps(current_memory, indent=2),
        user_message=user_message
    )

    try:
        raw_res = query_openrouter_extraction(prompt, preferred_model=preferred_model)
        cleaned = raw_res.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()
        
        updates = json.loads(cleaned)
        if isinstance(updates, dict) and updates:
            return merge_memory_updates(current_memory, updates)
    except Exception as e:
        print(f"[Memory Extraction Error] LLM extraction failed: {e}. Falling back to Regex extraction.")
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


def extract_memory_async(user_id: str, user_message: str, preferred_model: str = None):
    """Background task to run LLM memory extraction, deconfliction, and save to Supabase."""
    try:
        mem = load_memory(user_id)
        changed = extract_memory_llm(user_message, mem, preferred_model=preferred_model)
        
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
                mem = consolidated
                changed = True
                
        if changed:
            save_memory(user_id, mem)
            print(f"[Async Memory] Successfully updated and saved memory for user: {user_id}")
    except Exception as e:
        print("[Async Memory Error] Failed to process memory asynchronously:", e)


def memory_to_context(mem: dict) -> str:
    lines = []
    p = mem.get("profile", {})
    if p.get("name"):     lines.append(f"- Name: {p['name']}")
    if p.get("role"):     lines.append(f"- Role: {p['role']}")
    if p.get("company"):  lines.append(f"- Company: {p['company']}")
    if p.get("location"): lines.append(f"- Location: {p['location']}")
    if p.get("email"):    lines.append(f"- Email: {p['email']}")
    if p.get("phone"):    lines.append(f"- Phone: {p['phone']}")
    if mem.get("clients"):
        lines.append(f"- Known clients: {', '.join(mem['clients'][-8:])}")
    if mem.get("projects"):
        names = [proj.get("name", "") for proj in mem["projects"][-5:]]
        lines.append(f"- Active/recent projects: {', '.join(names)}")
    if mem.get("deadlines"):
        parts = [f"{d.get('date','?')} ({d.get('item','')[:40]})" for d in mem["deadlines"][-3:]]
        lines.append(f"- Deadlines: {' | '.join(parts)}")
    if mem.get("preferences"):
        lines.append("- User preferences:")
        for pref in mem["preferences"][-8:]:
            lines.append(f"  • {pref}")
    if mem.get("important_facts"):
        lines.append("- Important facts to remember:")
        for fact in mem["important_facts"][-10:]:
            lines.append(f"  • {fact}")
    if mem.get("ai_notes"):
        lines.append("- Inferred behavioral observations (ai_notes):")
        for note in mem["ai_notes"][-10:]:
            lines.append(f"  • {note}")
    if mem.get("topics_discussed"):
        lines.append(f"- Topics worked on previously: {', '.join(mem['topics_discussed'][-12:])}")
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
            mem["profile"][field] = value
            changed = True
            
    elif update_type == "list":
        key = data.get("key")
        value = (data.get("value") or "").strip()
        if key in ["preferences", "important_facts", "clients", "topics_discussed", "ai_notes"]:
            if _add_unique(mem[key], value):
                changed = True
                
    elif update_type == "project":
        name = (data.get("name") or "").strip()
        if name:
            existing = [p.get("name", "").lower() for p in mem["projects"]]
            if name.lower() not in existing:
                mem["projects"].append({
                    "name": name[:80],
                    "added": datetime.now().strftime("%Y-%m-%d")
                })
                changed = True
                
    elif update_type == "deadline":
        item = (data.get("item") or "").strip()
        date_val = (data.get("date") or "").strip()
        if item and date_val:
            mem["deadlines"].append({
                "item": item[:80],
                "date": date_val[:60],
                "added": datetime.now().strftime("%Y-%m-%d")
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
        if val in mem[key]:
            mem[key].remove(val)
            changed = True
            
    elif key == "projects":
        name = data.get("name")
        initial_len = len(mem["projects"])
        mem["projects"] = [p for p in mem["projects"] if p.get("name") != name]
        if len(mem["projects"]) < initial_len:
            changed = True
            
    elif key == "deadlines":
        item = data.get("item")
        initial_len = len(mem["deadlines"])
        mem["deadlines"] = [d for d in mem["deadlines"] if d.get("item") != item]
        if len(mem["deadlines"]) < initial_len:
            changed = True
            
    if changed:
        save_memory(uid, mem)
        return jsonify({"status": "ok", "memory": mem})
    return jsonify({"status": "no_change", "error": "Item not found"}), 404

