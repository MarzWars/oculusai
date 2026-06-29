import json
import threading
from datetime import datetime
from backend.extensions import supabase
from backend.models import query_openrouter_extraction
from backend.memory import load_memory, save_memory

CLASSIFIER_PROMPT = """You are a precise action classifier for Oculus AI.
Your job is to determine if the user's message is requesting one of the following actions:
1. `create_task`: Add/schedule a task or deadline (e.g. "add task to design logo by Friday", "schedule website launch").
2. `generate_proposal`: Generate a proposal, quote, or contract for a client (e.g. "create a proposal for Acme Corp", "generate a quote for logo design").
3. `send_email`: Draft or send an email to a client or contact (e.g. "email John requesting feedback", "send follow up email to client ABC").
4. `generate_document`: Generate a document in .docx, .pdf, or .txt format (e.g. "generate me a DOCX with my business goals", "export this summary as a PDF", "give me this in .txt format so I can download it", "create a word document containing...").

If an action is detected, you MUST extract the arguments and return a single valid JSON object.
Use the provided memory details to resolve ambiguous names or details:
- If an email is requested to a contact name (e.g. "John"), check if their email address is in the memory (facts/profile/notes). If not, extract the name.
- If a client name is mentioned, match it with the closest client in the memory list if possible.
- If a relative date is mentioned (e.g. "by Friday"), translate it or output a clear relative string based on the current date: {current_date}.

JSON output format:
For `create_task`:
{{
  "action_type": "create_task",
  "arguments": {{
    "title": "Title of the task",
    "due_date": "Due date (resolved or relative)"
  }}
}}

For `generate_proposal`:
{{
  "action_type": "generate_proposal",
  "arguments": {{
    "client_name": "Name of the client",
    "proposal_title": "Title/Subject of proposal",
    "amount": "Estimated price/budget (if mentioned, otherwise blank)",
    "details": "Detailed scope of work"
  }}
}}

For `send_email`:
{{
  "action_type": "send_email",
  "arguments": {{
    "to": "Recipient email address or contact name",
    "subject": "Subject of the email",
    "body": "Body of the email"
  }}
}}

For `generate_document`:
{{
  "action_type": "generate_document",
  "arguments": {{
    "filename": "Filename with correct extension (e.g., goals.docx, notes.txt, report.pdf)",
    "format": "docx or pdf or txt",
    "title": "A title for the document",
    "content": "The full text or content to write in the document"
  }}
}}

If no action is requested, return exactly: {{}}

Return ONLY the raw JSON string. Do not wrap it in markdown code blocks or write any explanation.

Current Date: {current_date}
Memory Context:
{memory_json}

User Message: "{user_message}"
JSON Response:"""


def classify_and_extract_action(user_message: str, user_id: str, workspace_id: str) -> dict:
    """Analyze the user message for potential actions, referencing user memory."""
    try:
        memory = load_memory(user_id)
        # Remove massive list entries for quick context inclusion
        clean_mem = {
            "profile": memory.get("profile", {}),
            "clients": memory.get("clients", []),
            "projects": [p.get("name") if isinstance(p, dict) else p for p in memory.get("projects", [])],
            "deadlines": memory.get("deadlines", []),
            "important_facts": memory.get("important_facts", []),
            "preferences": memory.get("preferences", [])
        }
        
        now = datetime.now()
        current_date_str = now.strftime('%A, %d %B %Y %H:%M')
        
        prompt = CLASSIFIER_PROMPT.format(
            current_date=current_date_str,
            memory_json=json.dumps(clean_mem, indent=2),
            user_message=user_message
        )
        
        res = query_openrouter_extraction(prompt)
        res_clean = res.strip()
        if res_clean.startswith("```"):
            # Strip block formatting if output by model
            res_clean = res_clean.replace("```json", "").replace("```", "").strip()
            
        if not res_clean or res_clean == "{}":
            return {}
            
        data = json.loads(res_clean)
        if "action_type" in data and "arguments" in data:
            return data
    except Exception as e:
        print("[Actions Engine] Classification error:", e)
    return {}

def log_proposed_action(user_id: str, workspace_id: str, action_type: str, arguments: dict) -> str:
    """Log a proposed action to the database as 'pending'."""
    try:
        res = supabase.table("oculus_actions").insert({
            "user_id": user_id,
            "workspace_id": workspace_id,
            "action_type": action_type,
            "arguments": arguments,
            "status": "pending"
        }).execute()
        if res.data:
            return res.data[0].get("id")
    except Exception as e:
        print("[Actions Engine] Database logging error:", e)
    return ""

def execute_action(action_id: str, user_id: str, workspace_id: str, overrides: dict = None) -> dict:
    """Execute a pending action using updated/overridden arguments."""
    try:
        # Load the action entry
        res = supabase.table("oculus_actions").select("*").eq("id", action_id).execute()
        if not res.data:
            return {"status": "error", "message": "Action proposal not found."}
            
        action = res.data[0]
        if action.get("user_id") != user_id:
            return {"status": "error", "message": "Access denied to this action."}
        if action["status"] != "pending":
            return {"status": "error", "message": f"Action is already {action['status']}."}
            
        action_type = action["action_type"]
        arguments = overrides if overrides is not None else action["arguments"]
        
        outcome = ""
        # 1. Route based on Action Type
        if action_type == "create_task":
            outcome = _execute_create_task(user_id, workspace_id, arguments)
        elif action_type == "generate_proposal":
            outcome = _execute_generate_proposal(user_id, workspace_id, arguments)
        elif action_type == "send_email":
            outcome = _execute_send_email(user_id, workspace_id, arguments)
        elif action_type == "generate_document":
            outcome = _execute_generate_document(user_id, workspace_id, arguments)
        else:
            return {"status": "error", "message": f"Unknown action type: {action_type}"}

            
        # Update log
        supabase.table("oculus_actions").update({
            "arguments": arguments,
            "status": "executed",
            "outcome": outcome,
            "executed_at": datetime.utcnow().isoformat() + "Z"
        }).eq("id", action_id).execute()
        
        return {"status": "success", "outcome": outcome}
    except Exception as e:
        print("[Actions Engine] Execution error:", e)
        return {"status": "error", "message": str(e)}

def cancel_action(action_id: str) -> dict:
    """Mark an action as cancelled."""
    try:
        supabase.table("oculus_actions").update({
            "status": "cancelled"
        }).eq("id", action_id).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def undo_action(action_id: str, user_id: str, workspace_id: str) -> dict:
    """Undo an executed action if supported."""
    try:
        res = supabase.table("oculus_actions").select("*").eq("id", action_id).execute()
        if not res.data:
            return {"status": "error", "message": "Action not found."}
            
        action = res.data[0]
        if action.get("user_id") != user_id:
            return {"status": "error", "message": "Access denied to this action."}
        if action["status"] != "executed":
            return {"status": "error", "message": f"Cannot undo action with status: {action['status']}"}
            
        action_type = action["action_type"]
        arguments = action["arguments"]
        
        outcome = ""
        if action_type == "create_task":
            # Revert task in memory
            outcome = _undo_create_task(user_id, workspace_id, arguments)
        elif action_type in ("generate_proposal", "send_email", "generate_document"):
            # Deletes generated files/emails/documents from sandbox
            outcome = _undo_file_action(user_id, workspace_id, action_type, arguments)
        else:
            return {"status": "error", "message": f"Undo not supported for: {action_type}"}
            
        # Update log status
        supabase.table("oculus_actions").update({
            "status": "undone",
            "outcome": f"Undone: {outcome}"
        }).eq("id", action_id).execute()
        
        return {"status": "success", "outcome": outcome}
    except Exception as e:
        print("[Actions Engine] Undo error:", e)
        return {"status": "error", "message": str(e)}

# ----------------- Private Execution Helpers -----------------

def _execute_create_task(user_id: str, workspace_id: str, args: dict) -> str:
    title = args.get("title", "New Task")
    due_date = args.get("due_date", "Upcoming")
    
    memory = load_memory(user_id)
    deadlines = memory.setdefault("deadlines", [])
    
    # Avoid duplicate tasks with same title
    if not any(d.get("item") == title for d in deadlines):
        deadlines.append({"item": title, "date": due_date})
        save_memory(user_id, memory)
        
    return f"Task created: '{title}' due {due_date}"

def _undo_create_task(user_id: str, workspace_id: str, args: dict) -> str:
    title = args.get("title")
    memory = load_memory(user_id)
    deadlines = memory.get("deadlines", [])
    
    original_len = len(deadlines)
    deadlines = [d for d in deadlines if d.get("item") != title]
    
    if len(deadlines) < original_len:
        memory["deadlines"] = deadlines
        save_memory(user_id, memory)
        return f"Task removed: '{title}'"
    return "Task was already removed or not found."

def _execute_send_email(user_id: str, workspace_id: str, args: dict) -> str:
    import os
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    to_contact = args.get("to", "Unknown")
    subject = args.get("subject", "No Subject")
    body = args.get("body", "")

    # Use the AI's full drafted email body if it's richer than the brief typed body
    ai_draft = (args.get("ai_draft") or "").strip()
    if len(ai_draft) > len(body) + 50:
        body = ai_draft

    smtp_enabled = os.environ.get("ENABLE_SMTP_DELIVERY", "false").lower() == "true"

    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: sans-serif; background: #0d0d0f; color: #e4e4e9; padding: 20px; }}
  .card {{ background: #16161a; border: 1px solid #2a2a35; border-radius: 8px; padding: 20px; }}
  .header-item {{ margin-bottom: 10px; font-size: 13px; color: #a0a0ab; }}
  .header-item strong {{ color: #ffffff; }}
  hr {{ border: 0; border-top: 1px solid #2a2a35; margin: 20px 0; }}
  .body-content {{ white-space: pre-wrap; font-size: 14px; line-height: 1.6; }}
</style>
</head>
<body>
<div class="card">
  <div class="header-item"><strong>To:</strong> {to_contact}</div>
  <div class="header-item"><strong>Subject:</strong> {subject}</div>
  <div class="header-item"><strong>Status:</strong> {"Sent via SMTP" if smtp_enabled else "Draft Saved (SMTP Inactive)"}</div>
  <hr>
  <div class="body-content">{body}</div>
</div>
</body>
</html>
"""

    if smtp_enabled:
        try:
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASSWORD", "")
            smtp_sender = os.environ.get("SMTP_SENDER_EMAIL", smtp_user)
            
            if not smtp_user or not smtp_pass:
                raise Exception("SMTP credentials missing from environment.")
                
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_sender
            msg["To"] = to_contact
            
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_sender, to_contact, msg.as_string())
                
            return f"Email sent successfully to {to_contact}."
        except Exception as e:
            print(f"[Actions Engine] SMTP failed, falling back to simulated output: {e}")
            
    # Simulated email delivery - save HTML draft in workspace
    sandbox_dir = os.path.join("workspaces", workspace_id, "emails")
    os.makedirs(sandbox_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"email_{timestamp}.html"
    file_path = os.path.join(sandbox_dir, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # Upload to Supabase Storage → permanent signed URL
    from backend.docs import upload_to_storage, register_generated_doc, update_memory_after_doc
    storage_sub = f"emails/{file_name}"
    download_url = upload_to_storage(workspace_id, file_path, storage_sub)

    if not download_url:
        download_url = f"/api/sandbox/download?path=emails/{file_name}"
        print(f"[Actions] Email Storage upload failed — using local fallback URL")

    full_storage_path = f"{workspace_id}/{storage_sub}"
    register_generated_doc(
        user_id=user_id,
        workspace_id=workspace_id,
        action_id="",
        doc_type="email",
        filename=file_name,
        title=f"Email to {to_contact}: {subject}",
        description=f"To: {to_contact} | Subject: {subject}",
        fmt="html",
        storage_path=full_storage_path,
        download_url=download_url,
        file_size=os.path.getsize(file_path),
    )

    # Update memory in background
    threading.Thread(
        target=update_memory_after_doc,
        args=(user_id, "email", subject, to_contact)
    ).start()

    status_label = "Email sent via SMTP ✅" if smtp_enabled else "Email draft saved"
    return f"{status_label} — [⬇ Preview Email Draft]({download_url})"


def _undo_file_action(user_id: str, workspace_id: str, action_type: str, args: dict) -> str:
    import os
    if action_type == "generate_proposal":
        sub_dir = "proposals"
    elif action_type == "send_email":
        sub_dir = "emails"
    else:
        sub_dir = "documents"
    target_dir = os.path.join("workspaces", workspace_id, sub_dir)
    if os.path.exists(target_dir):
        files = [os.path.join(target_dir, f) for f in os.listdir(target_dir)]
        if files:
            latest_file = max(files, key=os.path.getctime)
            os.remove(latest_file)
            return f"Removed generated file: {os.path.basename(latest_file)}"
    return "No file found to delete."

# ----------------- Flask Blueprint & Endpoints -----------------
from flask import Blueprint, request, jsonify, session
from backend.auth import login_required, current_user_id
from .document_builder import _execute_generate_proposal, _execute_generate_document

actions_bp = Blueprint("actions", __name__)

@actions_bp.route("/api/actions/execute", methods=["POST"])
@login_required
def api_execute_action():
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    from backend.workspaces import verify_workspace_ownership
    if not verify_workspace_ownership(uid, wid):
        wid = uid
        session["current_workspace_id"] = wid
    data = request.get_json() or {}
    action_id = data.get("action_id")
    overrides = data.get("overrides")
    
    if not action_id:
        return jsonify({"error": "action_id is required"}), 400
        
    result = execute_action(action_id, uid, wid, overrides=overrides)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)

@actions_bp.route("/api/actions/cancel", methods=["POST"])
@login_required
def api_cancel_action():
    uid = current_user_id()
    data = request.get_json() or {}
    action_id = data.get("action_id")
    if not action_id:
        return jsonify({"error": "action_id is required"}), 400
    
    # Verify action ownership before cancelling
    res = supabase.table("oculus_actions").select("user_id").eq("id", action_id).execute()
    if not res.data or res.data[0].get("user_id") != uid:
        return jsonify({"error": "Access denied"}), 403
        
    result = cancel_action(action_id)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)

@actions_bp.route("/api/actions/undo", methods=["POST"])
@login_required
def api_undo_action():
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    from backend.workspaces import verify_workspace_ownership
    if not verify_workspace_ownership(uid, wid):
        wid = uid
        session["current_workspace_id"] = wid
    data = request.get_json() or {}
    action_id = data.get("action_id")
    
    if not action_id:
        return jsonify({"error": "action_id is required"}), 400
        
    result = undo_action(action_id, uid, wid)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)

@actions_bp.route("/api/actions/history", methods=["GET"])
@login_required
def api_action_history():
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    from backend.workspaces import verify_workspace_ownership
    if not verify_workspace_ownership(uid, wid):
        wid = uid
        session["current_workspace_id"] = wid
    try:
        res = supabase.table("oculus_actions")\
            .select("*")\
            .eq("user_id", uid)\
            .eq("workspace_id", wid)\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        return jsonify({"status": "success", "history": res.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@actions_bp.route("/api/actions/status/<action_id>", methods=["GET"])
@login_required
def api_action_status(action_id):
    uid = current_user_id()
    try:
        res = supabase.table("oculus_actions").select("*").eq("id", action_id).execute()
        if res.data:
            if res.data[0].get("user_id") != uid:
                return jsonify({"error": "Access denied"}), 403
            return jsonify({"status": "success", "action": res.data[0]})
        return jsonify({"error": "Action not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


