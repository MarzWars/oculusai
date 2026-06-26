import re
import json
from datetime import datetime
from flask import Blueprint, session, request, Response, jsonify, render_template

from config import Config
from backend.extensions import supabase
from backend.models import query_openrouter, query_openrouter_stream
from backend.auth import login_required, current_user_id, current_email
from backend.memory import (
    load_memory, save_memory, extract_memory_regex, 
    extract_memory_async, memory_to_context
)
from backend.prompts import SYSTEM_PROMPT
from backend.search import web_search, should_search

chat_bp = Blueprint("chat", __name__)

def load_history(user_id: str) -> list:
    try:
        res = supabase.table("oculus_chat").select("messages").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0].get("messages", [])
    except Exception as e:
        print("History load error:", e)
    return []

def save_history(user_id: str, messages: list):
    try:
        supabase.table("oculus_chat").upsert({
            "user_id":  user_id,
            "messages": messages
        }).execute()
    except Exception as e:
        print("History save error:", e)

def load_action_cards(workspace_id: str) -> list:
    """Load persisted action cards for a workspace from oculus_chat.action_cards."""
    try:
        res = supabase.table("oculus_chat").select("action_cards").eq("user_id", workspace_id).execute()
        if res.data:
            return res.data[0].get("action_cards") or []
    except Exception as e:
        print("Action cards load error:", e)
    return []

def save_action_card(workspace_id: str, card: dict):
    """
    Upsert a single action card into oculus_chat.action_cards for the workspace.
    card schema: {action_id, action_type, status, download_url, message_index, created_at}
    Deduplicates by action_id and keeps the most recent 50.
    """
    try:
        existing = load_action_cards(workspace_id)
        # Deduplicate: replace any existing card with same action_id
        existing = [c for c in existing if c.get("action_id") != card.get("action_id")]
        existing.append(card)
        # Cap at 50 cards
        if len(existing) > 50:
            existing = existing[-50:]
        supabase.table("oculus_chat").upsert({
            "user_id": workspace_id,
            "action_cards": existing,
        }).execute()
    except Exception as e:
        print("save_action_card error:", e)

def load_summary(user_id: str) -> str:
    try:
        res = supabase.table("oculus_chat").select("summary").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0].get("summary", "")
    except Exception as e:
        print("Summary load error:", e)
    return ""

def save_summary(user_id: str, s: str):
    try:
        supabase.table("oculus_chat").upsert({
            "user_id": user_id,
            "summary": s
        }).execute()
    except Exception as e:
        print("Summary save error:", e)

def maybe_summarise_history(user_id: str, history: list):
    if len(history) < Config.SUMMARISE_AFTER:
        return
    half      = len(history) // 2
    old_chunk = history[:half]
    lines     = []
    for msg in old_chunk:
        role = "User" if msg["role"] == "user" else "Oculus"
        lines.append(f"{role}: {msg['text'][:120]}")
    chunk_text = "\n".join(lines)
    summary_prompt = (
        "Summarise the following conversation in 3-5 sentences. "
        "Focus on: topics covered, decisions made, user facts revealed, ongoing work. "
        "Be concise. Plain text only.\n\n"
        f"{chunk_text}\n\nSummary:"
    )
    try:
        new_summary = query_openrouter(summary_prompt)
        if new_summary:
            existing = load_summary(user_id)
            combined = (existing + " " + new_summary).strip() if existing else new_summary
            if len(combined) > 700:
                combined = combined[-700:]
            save_summary(user_id, combined)
        history[:] = history[half:]
        save_history(user_id, history)
    except Exception:
        pass


def build_prompt(workspace_id: str, user_message: str, mem: dict, history: list) -> str:
    # Format uploaded files context
    from backend.files import UPLOADED_FILES_CACHE
    uploaded_files = UPLOADED_FILES_CACHE.get(workspace_id, [])
    file_context = ""
    if uploaded_files:
        blocks = []
        for uf in uploaded_files:
            name = uf.get("name", "unknown")
            if uf.get("is_long"):
                size_kb = round(uf.get("size", 0) / 1024, 1)
                summary = uf.get("summary", "")
                blocks.append(f"[File: {name} (Size: {size_kb}KB, Summary: {summary})]\n(Note: This file is large and has been summarized to save context window.)")
            else:
                content = uf.get("content", "")
                blocks.append(f"[File: {name}]\n[Content]:\n{content}\n[End of File: {name}]")
        file_context = "══════════ UPLOADED FILE CONTEXT ══════════\nUse the following user-attached files to answer their query:\n\n" + "\n\n".join(blocks)

    rr_patterns = [
        r"\bred rooms?\b", r"\blocanto\b", r"\bphone entertain",
        r"\boperator ad\b", r"\bad for.*operator\b"
    ]
    is_rr = any(re.search(p, user_message, re.IGNORECASE) for p in rr_patterns)

    now     = datetime.now()
    live_dt = (
        f"{now.strftime('%A, %d %B %Y')}  |  "
        f"Time: {now.strftime('%H:%M')} SAST (UTC+2)"
    )

    # Load active workspace name
    workspace_name = "Default Workspace"
    try:
        res = supabase.table("oculus_workspaces").select("name").eq("id", workspace_id).execute()
        if res.data:
            workspace_name = res.data[0].get("name", "Default Workspace")
    except Exception as e:
        print("[Prompt Engine] Error loading workspace name:", e)

    web_raw_context = web_search(user_message) if should_search(user_message) else ""

    # Query workspace documents RAG context
    from backend.rag import query_workspace_rag_hybrid
    rag_chunks = query_workspace_rag_hybrid(workspace_id, user_message, match_count=5)

    # Fetch overview list of all documents in this workspace (helps with cross-document reasoning)
    doc_metadata_context = ""
    try:
        res_docs = supabase.table("oculus_documents")\
            .select("filename", "document_type", "summary")\
            .eq("workspace_id", workspace_id)\
            .execute()
        if res_docs.data:
            doc_lines = []
            for d in res_docs.data:
                fname = d.get("filename", "document")
                dtype = d.get("document_type", "other")
                dsummary = d.get("summary") or "No summary available."
                doc_lines.append(f"- {fname} (Category: {dtype}): {dsummary}")
            doc_metadata_context = (
                "Workspace Documents Overview:\n"
                + "\n".join(doc_lines)
                + "\n\n"
            )
    except Exception as e:
        print("[Prompt Engine] Error loading doc metadata for context:", e)

    # Start with default budget variables
    verbatim_turns = Config.VERBATIM_TURNS
    memory_max_results = 5
    web_length_limit = len(web_raw_context)
    rag_max_results = len(rag_chunks) if rag_chunks else 0

    while True:
        # 1. Compile Memory Context
        mem_context = memory_to_context(mem, user_message, max_results=memory_max_results)
        
        # 2. Compile Web Context
        web_context = web_raw_context[:web_length_limit] if web_raw_context else ""

        # 3. Compile RAG Context
        rag_context = ""
        if (rag_chunks and rag_max_results > 0) or doc_metadata_context:
            blocks = []
            if rag_chunks and rag_max_results > 0:
                for c in rag_chunks[:rag_max_results]:
                    filename = c.get("filename", "document")
                    page = c.get("page_number") or 1
                    section = c.get("section_title") or f"Page {page}"
                    text = c.get("chunk_text", "")
                    blocks.append(f"[Source Chunk: {filename} | {section}]\n{text}\n[End of chunk]")
            
            rag_context = (
                "══════════ WORKSPACE DOCUMENT CONTEXT ══════════\n"
                "You have access to the following documents in this workspace:\n"
                f"{doc_metadata_context}"
                "Here are relevant chunks matching the user's query. If you use this information, "
                "you MUST cite the source precisely in your answer (e.g. 'According to [filename] (Page X)...' "
                "or 'Source: [filename], Section: [title]'):\n\n"
                + "\n\n".join(blocks)
            )

        # 4. Assemble parts
        parts = [SYSTEM_PROMPT, ""]
        parts += [
            "══════════ LIVE SYSTEM INFO ══════════",
            f"- Current date and time: {live_dt}",
            "  Use this as the authoritative date/time. Never guess the date.",
            f"- Active Workspace: {workspace_name}",
            f"  You are currently assisting the user in the workspace '{workspace_name}'. All file uploads, project code saving, and chat history are isolated within this context. Focus on topics, clients, and files relative to this workspace.",
            "",
            "══════════ PERSISTENT USER MEMORY ══════════",
            mem_context,
        ]

        if file_context:
            parts += [
                "",
                file_context,
            ]

        if rag_context:
            parts += [
                "",
                rag_context,
            ]

        if web_context:
            parts += [
                "",
                "══════════ LIVE WEB SEARCH RESULTS ══════════",
                "Use these to inform your answer. Weave naturally — do not paste them raw.",
                web_context,
            ]

        if is_rr:
            parts += [
                "",
                "══════════ RED ROOMS AD — MANDATORY CHECKLIST ══════════",
                "You MUST perform your checklist verification and character counting inside `<think>...</think>` tags first.",
                "1. Title is EXACTLY 60 characters — count every character including spaces",
                "2. Description is 750–850 characters — rich, full, complete",
                "3. Written entirely in first person (I / me / my)",
                "4. Words 'red rooms', 'alex', 'oculus', 'lex digitals' do NOT appear anywhere",
                "5. Tone is bold, adult, direct",
                "",
                "Output format:",
                "<think>",
                "[Perform your character counting, checks, and planning here]",
                "</think>",
                "**Title:** [exactly 60 chars]",
                "**Description:** [750–850 chars]",
            ]

        parts += [
            "",
            "Follow formatting rules exactly. Blank lines between paragraphs. '- ' for bullets.",
            "Code always in fenced code blocks with language specified. Never truncate code output.",
            "Be concise unless depth is needed. Never start a response with the word 'I'.",
            "When answering, if you reference content from any user-attached files, cite them clearly in the format: 'According to [filename]...'",
            "",
            "══════════ CONVERSATION HISTORY ══════════",
        ]

        stored_summary = load_summary(workspace_id)
        if stored_summary:
            parts.append(f"[Earlier summary]: {stored_summary}")
            parts.append("")

        prior = history[:-1]
        for msg in prior[-verbatim_turns:]:
            role    = "User" if msg["role"] == "user" else "Oculus"
            content = msg.get("text", "").strip()
            if content:
                parts.append(f"{role}: {content}")

        parts += [
            "",
            "══════════ CURRENT MESSAGE ══════════",
            f"User: {user_message}",
            "",
            "Oculus:",
        ]

        prompt_str = "\n".join(parts)
        approx_tokens = len(prompt_str) // 4
        
        # Check budget
        if approx_tokens <= 6000:
            print(f"[Token Budget] Prompt assembled: {approx_tokens} tokens (approx). Limit: 6000.")
            return prompt_str
            
        # Pruning sequence:
        if verbatim_turns > 1:
            verbatim_turns -= 1
            print(f"[Token Budget Warning] Prompt size {approx_tokens} exceeds 6000. Reducing conversation history turns to {verbatim_turns}...")
        elif rag_max_results > 0:
            rag_max_results -= 1
            print(f"[Token Budget Warning] Prompt size {approx_tokens} exceeds 6000. Reducing RAG document chunks to {rag_max_results}...")
        elif memory_max_results > 1:
            memory_max_results -= 1
            print(f"[Token Budget Warning] Prompt size {approx_tokens} exceeds 6000. Reducing memory max_results to {memory_max_results}...")
        elif web_length_limit > 0:
            web_length_limit = max(0, web_length_limit - 1000)
            print(f"[Token Budget Warning] Prompt size {approx_tokens} exceeds 6000. Truncating web search context to {web_length_limit} chars...")
        else:
            print(f"[Token Budget Danger] Prompt size {approx_tokens} exceeds 6000 and cannot be pruned further. Returning best effort.")
            return prompt_str


@chat_bp.route("/")
@login_required
def home():
    uid          = current_user_id()
    email        = current_email()
    
    # Ensure default workspace exists and load user workspaces
    from backend.workspaces import get_workspaces_for_user
    workspaces = get_workspaces_for_user(uid)
    
    current_wid = session.get("current_workspace_id")
    valid_ids = {w["id"] for w in workspaces}
    if not current_wid or current_wid not in valid_ids:
        current_wid = uid
        session["current_workspace_id"] = current_wid

    chat_history = load_history(current_wid)
    memory       = load_memory(uid)
    mem_name     = memory.get("profile", {}).get("name", "")
    display_name = mem_name or email.split("@")[0]
    greeting     = f"Welcome back, {display_name}." if chat_history else "What are we building today?"
    active_model = session.get("selected_model", Config.DEFAULT_MODEL)
    active_name  = next((m["name"] for m in Config.MODEL_OPTIONS if m["id"] == active_model), active_model)

    return render_template(
        "index.html",
        email=email,
        chat_history=chat_history,
        greeting=greeting,
        active_model=active_model,
        active_name=active_name,
        model_options=Config.MODEL_OPTIONS
    )


@chat_bp.route("/set_model", methods=["POST"])
@login_required
def set_model():
    data  = request.get_json()
    model = (data.get("model") or "").strip()
    valid_ids = {m["id"] for m in Config.MODEL_OPTIONS}
    if model not in valid_ids:
        return jsonify({"error": "Invalid model"}), 400
    session["selected_model"] = model
    name = next((m["name"] for m in Config.MODEL_OPTIONS if m["id"] == model), model)
    return jsonify({"status": "ok", "model": model, "name": name})


@chat_bp.route("/clear", methods=["POST"])
@login_required
def clear():
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    try:
        supabase.table("oculus_chat").upsert({
            "user_id":  wid,
            "messages": [],
            "summary":  ""
        }).execute()
    except Exception as e:
        print("Clear error:", e)
    return jsonify({"status": "cleared"})


@chat_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    uid          = current_user_id()
    wid          = session.get("current_workspace_id", uid)
    data         = request.get_json()
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return Response("No message provided.", mimetype="text/plain")

    history = load_history(wid)
    memory  = load_memory(uid)

    # 1. Run memory extraction and update message count
    extract_memory_regex(user_message, memory)
    memory["message_count"] = memory.get("message_count", 0) + 1
    save_memory(uid, memory)

    # 2. Add user message to history
    history.append({"role": "user", "text": user_message})
    save_history(wid, history)

    # 3. Classify message for potential AI Actions
    from backend.actions import classify_and_extract_action, log_proposed_action
    action_data = classify_and_extract_action(user_message, uid, wid)
    action_id = ""
    if action_data:
        action_id = log_proposed_action(uid, wid, action_data["action_type"], action_data["arguments"])

    prompt = build_prompt(wid, user_message, memory, history)
    # Clear uploaded files cache immediately
    from backend.files import UPLOADED_FILES_CACHE
    UPLOADED_FILES_CACHE.pop(wid, None)
    
    preferred_model = session.get("selected_model", Config.DEFAULT_MODEL)
    # Track how many messages exist before this exchange so we know the card's message_index
    msg_index_before = len(history) - 1  # the user message was just appended

    def generate():
        try:
            output_chunks = []
            for chunk in query_openrouter_stream(prompt, preferred_model=preferred_model):
                output_chunks.append(chunk)
                yield chunk
            
            full_text = "".join(output_chunks)

            # 4. Stream and append action proposal at the end if detected
            if action_data and action_id:
                proposal_block = f"\n\n[[ACTION_PROPOSAL]]: {json.dumps({'action_id': action_id, 'action_type': action_data['action_type'], 'arguments': action_data['arguments']})}"
                full_text += proposal_block
                yield proposal_block

            history.append({"role": "ai", "text": full_text.strip()})
            save_history(wid, history)

            # Persist action card to Supabase so it survives page refresh
            # Note: download_url will be updated when the action is *executed* — here we store the pending card
            if action_data and action_id:
                save_action_card(wid, {
                    "action_id":    action_id,
                    "action_type":  action_data["action_type"],
                    "status":       "pending",
                    "download_url": "",
                    "message_index": msg_index_before + 1,  # index of the AI reply
                    "created_at":   datetime.utcnow().isoformat() + "Z",
                })

                # Save the AI's full drafted content into the action's arguments
                # so document generators can use it as the body (not just the brief user input)
                try:
                    ai_draft_text = full_text  # full text before the [[ACTION_PROPOSAL]] block
                    # Strip the [[ACTION_PROPOSAL]] block if present
                    ap_idx = ai_draft_text.find("[[ACTION_PROPOSAL]]:")
                    if ap_idx != -1:
                        ai_draft_text = ai_draft_text[:ap_idx].strip()

                    merged_args = {**action_data.get("arguments", {}), "ai_draft": ai_draft_text}
                    supabase.table("oculus_actions").update({
                        "arguments": merged_args
                    }).eq("id", action_id).execute()
                except Exception as _e:
                    print(f"[Chat] Failed to save ai_draft to action {action_id}: {_e}")

            # Summarise in background after responding and saving
            import threading
            threading.Thread(
                target=maybe_summarise_history,
                args=(wid, history.copy())
            ).start()

            # Run deep LLM extraction in background
            threading.Thread(
                target=extract_memory_async,
                args=(uid, user_message, preferred_model)
            ).start()
        except Exception as e:
            error = f"\n[Error: {str(e)}]"
            print("[ASK ERROR]", error)
            yield error
            history.append({"role": "ai", "text": error})
            save_history(wid, history)

    return Response(generate(), mimetype="text/event-stream")


@chat_bp.route("/api/chat/state", methods=["GET"])
@login_required
def get_chat_state():
    """
    Returns the full chat state for the current workspace:
    - messages list (for rehydration)
    - action_cards list (so download links and card statuses survive refresh)
    Used by the frontend on DOMContentLoaded to rehydrate action cards with permanent URLs.
    """
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    messages     = load_history(wid)
    action_cards = load_action_cards(wid)

    # Enrich each action card with the latest status from oculus_actions
    enriched_cards = []
    for card in action_cards:
        aid = card.get("action_id")
        if aid:
            try:
                res = supabase.table("oculus_actions").select("status, outcome").eq("id", aid).execute()
                if res.data:
                    row = res.data[0]
                    card["status"] = row.get("status", card.get("status", "pending"))
                    # If executed, try to pull the download URL from outcome text
                    if row.get("status") == "executed" and not card.get("download_url"):
                        outcome = row.get("outcome", "")
                        # Extract URL from markdown link pattern in outcome string
                        import re
                        url_match = re.search(r'\((/api/[^\)]+|https?://[^\)]+)\)', outcome)
                        if url_match:
                            card["download_url"] = url_match.group(1)
            except Exception:
                pass
        enriched_cards.append(card)

    return jsonify({
        "status":       "success",
        "messages":     messages,
        "action_cards": enriched_cards,
    })

