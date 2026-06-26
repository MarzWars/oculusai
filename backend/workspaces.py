import os
from flask import Blueprint, jsonify, request, session
from backend.auth import login_required, current_user_id
from backend.extensions import supabase

workspaces_bp = Blueprint("workspaces", __name__)

def ensure_default_workspace(user_id: str):
    """Ensures a default workspace exists for the user.
    Uses user_id as workspace_id to preserve backwards compatibility with existing memory/chat logs.
    """
    try:
        res = supabase.table("oculus_workspaces").select("id").eq("user_id", user_id).execute()
        if not res.data:
            supabase.table("oculus_workspaces").insert({
                "id": user_id,
                "user_id": user_id,
                "name": "Personal Workspace"
            }).execute()
            print(f"[Workspaces] Created default workspace for user: {user_id}")
    except Exception as e:
        print("[Workspaces] Error ensuring default workspace:", e)

def get_workspaces_for_user(user_id: str) -> list:
    """Returns all workspaces for the given user, ensuring a default one exists first."""
    ensure_default_workspace(user_id)
    try:
        res = supabase.table("oculus_workspaces").select("*").eq("user_id", user_id).order("created_at").execute()
        return res.data or []
    except Exception as e:
        print("[Workspaces] Error loading workspaces:", e)
        return []

@workspaces_bp.route("/api/workspaces", methods=["GET"])
@login_required
def get_workspaces_api():
    uid = current_user_id()
    workspaces = get_workspaces_for_user(uid)
    current_wid = session.get("current_workspace_id", uid)
    
    # Verify current workspace is valid, fallback to user_id if not
    valid_ids = {w["id"] for w in workspaces}
    if current_wid not in valid_ids:
        current_wid = uid
        session["current_workspace_id"] = current_wid
        
    return jsonify({
        "workspaces": workspaces,
        "current_workspace_id": current_wid
    })

@workspaces_bp.route("/api/workspaces/create", methods=["POST"])
@login_required
def create_workspace_api():
    uid = current_user_id()
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Workspace name is required."}), 400
        
    try:
        res = supabase.table("oculus_workspaces").insert({
            "user_id": uid,
            "name": name
        }).execute()
        if res.data:
            new_ws = res.data[0]
            # Automatically switch to the newly created workspace
            session["current_workspace_id"] = new_ws["id"]
            return jsonify({"status": "ok", "workspace": new_ws})
        else:
            return jsonify({"error": "Failed to create workspace."}), 500
    except Exception as e:
        return jsonify({"error": f"Error creating workspace: {str(e)}"}), 500

@workspaces_bp.route("/api/workspaces/switch", methods=["POST"])
@login_required
def switch_workspace_api():
    uid = current_user_id()
    data = request.get_json() or {}
    wid = data.get("workspace_id")
    if not wid:
        return jsonify({"error": "Workspace ID is required."}), 400
        
    try:
        # Verify workspace belongs to current user
        res = supabase.table("oculus_workspaces").select("id").eq("user_id", uid).eq("id", wid).execute()
        if not res.data:
            return jsonify({"error": "Workspace not found or access denied."}), 404
            
        session["current_workspace_id"] = wid
        
        # Clear files cache for safety when switching
        from backend.files import UPLOADED_FILES_CACHE
        UPLOADED_FILES_CACHE.pop(wid, None)
        
        return jsonify({"status": "ok", "current_workspace_id": wid})
    except Exception as e:
        return jsonify({"error": f"Error switching workspace: {str(e)}"}), 500

@workspaces_bp.route("/api/workspaces/delete", methods=["POST"])
@login_required
def delete_workspace_api():
    uid = current_user_id()
    data = request.get_json() or {}
    wid = data.get("workspace_id")
    if not wid:
        return jsonify({"error": "Workspace ID is required."}), 400
        
    if wid == uid:
        return jsonify({"error": "Cannot delete the default workspace."}), 400
        
    try:
        # Verify workspace ownership
        res = supabase.table("oculus_workspaces").select("id").eq("user_id", uid).eq("id", wid).execute()
        if not res.data:
            return jsonify({"error": "Workspace not found or access denied."}), 404
            
        # Delete related database records: memory and chat logs
        # Note: both tables use workspace_id as primary key (named 'user_id' in DB schema)
        supabase.table("oculus_memory").delete().eq("user_id", wid).execute()
        supabase.table("oculus_chat").delete().eq("user_id", wid).execute()
        
        # Delete workspace entry
        supabase.table("oculus_workspaces").delete().eq("id", wid).execute()
        
        # Clear files cache
        from backend.files import UPLOADED_FILES_CACHE
        UPLOADED_FILES_CACHE.pop(wid, None)
        
        # Clean up local sandbox files directory
        import shutil
        workspace_dir = os.path.abspath(os.path.join(os.getcwd(), "workspaces", wid))
        if os.path.exists(workspace_dir):
            shutil.rmtree(workspace_dir, ignore_errors=True)
            
        # Fall back to default workspace if deleting the active workspace
        if session.get("current_workspace_id") == wid:
            session["current_workspace_id"] = uid
            
        return jsonify({"status": "ok", "current_workspace_id": session["current_workspace_id"]})
    except Exception as e:
        return jsonify({"error": f"Error deleting workspace: {str(e)}"}), 500


@workspaces_bp.route("/api/workspaces/<workspace_id>/settings", methods=["POST"])
@login_required
def update_workspace_settings_api(workspace_id):
    uid = current_user_id()
    try:
        res = supabase.table("oculus_workspaces").select("id, settings").eq("user_id", uid).eq("id", workspace_id).execute()
        if not res.data:
            return jsonify({"error": "Workspace not found or access denied."}), 404
            
        current_settings = res.data[0].get("settings") or {}
        if not isinstance(current_settings, dict):
            current_settings = {}
            
        data = request.get_json() or {}
        for k, v in data.items():
            current_settings[k] = v
            
        supabase.table("oculus_workspaces").update({"settings": current_settings}).eq("id", workspace_id).execute()
        return jsonify({"status": "ok", "settings": current_settings})
    except Exception as e:
        return jsonify({"error": f"Error updating settings: {str(e)}"}), 500
