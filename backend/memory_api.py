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
from supabase import create_client, Client
from dotenv import load_dotenv

import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from backend.models import get_llm
from backend.prompts import MEMORY_EXTRACTION_PROMPT, STYLE_INFERENCE_PROMPT
from backend.memory_items import load_memory_items, save_memory_items

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
from .memory_io import *
from .memory_ranking import *
from .memory_llm import *
from backend.chat import chat_bp
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
