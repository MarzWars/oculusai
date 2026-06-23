import os
from flask import Blueprint, jsonify, request
from backend.auth import login_required, current_user_id

files_bp = Blueprint("files", __name__)

# File upload cache and configuration
UPLOADED_FILES_CACHE = {}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html", 
    ".md", ".txt", ".csv", ".yml", ".yaml", ".ini", ".cfg", ".xml", 
    ".svg", ".sql", ".sh", ".bat", ".c", ".cpp", ".h", ".go", ".rs"
}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB per file


@files_bp.route("/api/upload", methods=["POST"])
@login_required
def upload_file_api():
    uid = current_user_id()
    if "files" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    uploaded_files = request.files.getlist("files")
    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ""):
        return jsonify({"error": "No files selected"}), 400
        
    if uid not in UPLOADED_FILES_CACHE:
        UPLOADED_FILES_CACHE[uid] = []
        
    cache = UPLOADED_FILES_CACHE[uid]
    errors = []
    successes = []
    
    for file in uploaded_files:
        filename = file.filename
        if not filename:
            continue
            
        _, ext = os.path.splitext(filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"{filename}: File extension not allowed")
            continue
            
        try:
            # Read content
            content_bytes = file.read()
            if len(content_bytes) > MAX_FILE_SIZE:
                errors.append(f"{filename}: Exceeds 2MB size limit")
                continue
                
            try:
                content = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = content_bytes.decode("latin-1")
                
            # Check if file with same name already uploaded, replace it
            cache = [f for f in cache if f["name"] != filename]
            cache.append({
                "name": filename,
                "content": content,
                "size": len(content_bytes)
            })
            UPLOADED_FILES_CACHE[uid] = cache
            successes.append(filename)
        except Exception as e:
            errors.append(f"{filename}: Error reading file ({type(e).__name__})")
            
    files_list = [{"name": f["name"], "size": f["size"]} for f in cache]
    
    return jsonify({
        "status": "ok" if not errors else "partial",
        "successes": successes,
        "errors": errors,
        "files": files_list
    })


@files_bp.route("/api/upload/delete", methods=["POST"])
@login_required
def delete_uploaded_file_api():
    uid = current_user_id()
    data = request.get_json() or {}
    filename = data.get("name")
    
    if not filename:
        return jsonify({"error": "Filename is required"}), 400
        
    if uid in UPLOADED_FILES_CACHE:
        UPLOADED_FILES_CACHE[uid] = [f for f in UPLOADED_FILES_CACHE[uid] if f["name"] != filename]
        
    cache = UPLOADED_FILES_CACHE.get(uid, [])
    files_list = [{"name": f["name"], "size": f["size"]} for f in cache]
    return jsonify({"status": "ok", "files": files_list})
