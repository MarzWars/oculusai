"""
backend/docs.py
Oculus AI — Generated Documents System
Handles: Supabase Storage upload, doc registration, listing, retrieval, and download.
All generated proposals, emails, and documents are persisted here with permanent URLs.
"""

import io
import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, request, session, redirect
from backend.auth import login_required, current_user_id
from backend.extensions import supabase

docs_bp = Blueprint("docs", __name__)

STORAGE_BUCKET = "Documents"  # Supabase Storage bucket name


# ─────────────────────────────────────────────────────────────────
# CORE STORAGE HELPERS
# ─────────────────────────────────────────────────────────────────

def _sanitize_storage_path(path: str) -> str:
    """Remove characters that Supabase Storage doesn't accept in paths."""
    return re.sub(r"[^a-zA-Z0-9_\-./]", "_", path)


def upload_to_storage(workspace_id: str, local_path: str, storage_path: str) -> str:
    """
    Upload a local file to Supabase Storage under:
      {workspace_id}/{storage_path}
    Returns a long-lived signed URL (1-year expiry), or '' on failure.
    Falls back gracefully — caller should handle empty string return.
    """
    full_storage_path = _sanitize_storage_path(f"{workspace_id}/{storage_path}")
    try:
        with open(local_path, "rb") as f:
            file_bytes = f.read()

        # Determine MIME type from extension
        ext = os.path.splitext(local_path)[1].lower()
        mime_map = {
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pdf":  "application/pdf",
            ".txt":  "text/plain",
            ".html": "text/html",
        }
        content_type = mime_map.get(ext, "application/octet-stream")

        # Upload (upsert: overwrite if already exists)
        supabase.storage.from_(STORAGE_BUCKET).upload(
            full_storage_path,
            file_bytes,
            {"content-type": content_type, "upsert": "true"},
        )
        print(f"[Docs Storage] Uploaded: {full_storage_path}")

        # Generate a signed URL valid for 1 year (3600 * 24 * 365 seconds)
        signed = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
            full_storage_path, 31536000
        )
        signed_url = signed.get("signedURL") or signed.get("signedUrl") or ""
        if signed_url:
            print(f"[Docs Storage] Signed URL generated for: {full_storage_path}")
            return signed_url

        print(f"[Docs Storage] Warning: could not extract signed URL from response: {signed}")
        return ""
    except Exception as e:
        print(f"[Docs Storage] Upload failed for {full_storage_path}: {e}")
        return ""


def register_generated_doc(
    user_id: str,
    workspace_id: str,
    action_id: str,
    doc_type: str,       # 'proposal' | 'document' | 'email' | 'quote'
    filename: str,
    title: str,
    description: str,
    fmt: str,            # 'docx' | 'pdf' | 'txt' | 'html'
    storage_path: str,
    download_url: str,
    file_size: int,
) -> str:
    """
    Insert a row into oculus_generated_docs.
    Returns the new doc id (str) or '' on failure.
    """
    try:
        res = supabase.table("oculus_generated_docs").insert({
            "user_id":      user_id,
            "workspace_id": workspace_id,
            "action_id":    action_id or None,
            "doc_type":     doc_type,
            "filename":     filename,
            "title":        title or filename,
            "description":  description or "",
            "format":       fmt,
            "storage_path": storage_path,
            "download_url": download_url,
            "file_size":    file_size,
            "version":      1,
        }).execute()

        if res.data:
            doc_id = res.data[0].get("id", "")
            print(f"[Docs Registry] Registered doc '{filename}' → id={doc_id}")
            return doc_id
    except Exception as e:
        print(f"[Docs Registry] Failed to register doc '{filename}': {e}")
    return ""


def update_memory_after_doc(user_id: str, doc_type: str, title: str, client_name: str = ""):
    """
    Asynchronously update the user's memory with a note about the generated document.
    Call in a background thread after generation.
    """
    try:
        from backend.memory import load_memory, save_memory
        from backend.utils import _add_unique
        mem = load_memory(user_id)
        date_str = datetime.now().strftime("%Y-%m-%d")
        if client_name:
            note = f"Created {doc_type} '{title}' for {client_name} on {date_str}"
        else:
            note = f"Generated {doc_type} '{title}' on {date_str}"
        if _add_unique(mem.setdefault("ai_notes", []), note, max_len=20):
            save_memory(user_id, mem)
            print(f"[Docs Memory] Updated memory with doc generation note.")
    except Exception as e:
        print(f"[Docs Memory] Failed to update memory after doc gen: {e}")


# ─────────────────────────────────────────────────────────────────
# FLASK API ROUTES
# ─────────────────────────────────────────────────────────────────

@docs_bp.route("/api/generated-docs", methods=["GET"])
@login_required
def list_generated_docs():
    """
    List all generated documents for the current workspace.
    Query params:
      ?q=<search term>   — fuzzy filter on title/filename
      ?type=<doc_type>   — filter by doc_type (proposal, document, email)
      ?from=<YYYY-MM-DD> — only docs after this date
    """
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    from backend.workspaces import verify_workspace_ownership
    if not verify_workspace_ownership(uid, wid):
        wid = uid
        session["current_workspace_id"] = wid

    q       = (request.args.get("q") or "").strip().lower()
    dtype   = (request.args.get("type") or "").strip().lower()
    from_dt = (request.args.get("from") or "").strip()

    try:
        query = (
            supabase.table("oculus_generated_docs")
            .select("*")
            .eq("workspace_id", wid)
            .order("created_at", desc=True)
            .limit(50)
        )
        if dtype:
            query = query.eq("doc_type", dtype)
        if from_dt:
            query = query.gte("created_at", from_dt)

        res = query.execute()
        docs = res.data or []

        # Client-side fuzzy filter on title + filename
        if q:
            docs = [
                d for d in docs
                if q in (d.get("title") or "").lower()
                or q in (d.get("filename") or "").lower()
                or q in (d.get("description") or "").lower()
            ]

        return jsonify({"status": "success", "docs": docs})
    except Exception as e:
        print(f"[Docs API] list_generated_docs error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@docs_bp.route("/api/generated-docs/<doc_id>/download", methods=["GET"])
@login_required
def download_generated_doc(doc_id):
    """
    Redirect to the signed Supabase Storage URL for a generated doc.
    Enforces workspace ownership before redirecting.
    """
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    from backend.workspaces import verify_workspace_ownership
    if not verify_workspace_ownership(uid, wid):
        wid = uid
        session["current_workspace_id"] = wid

    try:
        res = supabase.table("oculus_generated_docs").select("*").eq("id", doc_id).execute()
        if not res.data:
            return jsonify({"error": "Document not found"}), 404

        doc = res.data[0]

        # Security: ensure the doc belongs to this user
        if doc.get("user_id") != uid:
            return jsonify({"error": "Access denied"}), 403

        download_url = doc.get("download_url", "")
        if not download_url:
            return jsonify({"error": "No download URL available for this document"}), 404

        return redirect(download_url)
    except Exception as e:
        print(f"[Docs API] download_generated_doc error: {e}")
        return jsonify({"error": str(e)}), 500


@docs_bp.route("/api/generated-docs/<doc_id>/refresh-url", methods=["POST"])
@login_required
def refresh_doc_url(doc_id):
    """
    Re-generate a fresh signed URL for an existing doc and update the DB.
    Useful when old signed URLs expire.
    """
    uid = current_user_id()
    wid = session.get("current_workspace_id", uid)
    from backend.workspaces import verify_workspace_ownership
    if not verify_workspace_ownership(uid, wid):
        wid = uid
        session["current_workspace_id"] = wid

    try:
        res = supabase.table("oculus_generated_docs").select("*").eq("id", doc_id).execute()
        if not res.data:
            return jsonify({"error": "Document not found"}), 404

        doc = res.data[0]
        if doc.get("user_id") != uid:
            return jsonify({"error": "Access denied"}), 403

        storage_path = doc.get("storage_path", "")
        if not storage_path:
            return jsonify({"error": "No storage path on record"}), 400

        signed = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
            storage_path, 31536000
        )
        new_url = signed.get("signedURL") or signed.get("signedUrl") or ""
        if not new_url:
            return jsonify({"error": "Failed to generate new signed URL"}), 500

        supabase.table("oculus_generated_docs").update({
            "download_url": new_url,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }).eq("id", doc_id).execute()

        return jsonify({"status": "success", "download_url": new_url})
    except Exception as e:
        print(f"[Docs API] refresh_doc_url error: {e}")
        return jsonify({"error": str(e)}), 500
