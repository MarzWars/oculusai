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
from .memory_io import *
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
