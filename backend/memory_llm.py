import json
import logging
import re
import math
import uuid
import os
import threading
import collections
from datetime import datetime, timezone
from collections import OrderedDict
from flask import jsonify, request, current_app

from config import Config
from backend.extensions import supabase
from backend.models import query_openrouter, query_openrouter_stream, query_openrouter_extraction
from backend.prompts import MEMORY_STAGE1_EXTRACTION_PROMPT, MEMORY_STAGE2_QUALITY_PROMPT, MEMORY_CONSOLIDATION_PROMPT_TEMPLATE, STYLE_INFERENCE_PROMPT_TEMPLATE
from backend.memory_items import load_memory_items, save_memory_items
from .memory_io import *
from .memory_ranking import *
from backend.utils import is_ad_content


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


