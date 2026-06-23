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


def summarize_long_file(filename: str, content: str) -> str:
    from backend.models import query_openrouter
    sample = content[:15000]
    prompt = (
        "You are a file summarization assistant. Summarise the following file. "
        "Provide a concise 2-sentence overview of its purpose, and list up to 5 key config parameters, settings, or quotes. "
        "Output plain text only, no formatting wrappers.\n\n"
        f"Filename: {filename}\n"
        f"Content:\n{sample}\n\n"
        "Summary:"
    )
    try:
        summary = query_openrouter(prompt)
        return summary.strip()
    except Exception as e:
        print(f"[File Summarization Error] Failed to summarize {filename}: {e}")
        return "Could not summarize file content automatically."


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
                
            is_long = len(content) > 3000
            summary_content = ""
            if is_long:
                print(f"[Files] {filename} length is {len(content)} chars. Running LLM summarizer...")
                summary_content = summarize_long_file(filename, content)

            # Check if file with same name already uploaded, replace it
            cache = [f for f in cache if f["name"] != filename]
            cache.append({
                "name": filename,
                "content": content,
                "size": len(content_bytes),
                "summary": summary_content,
                "is_long": is_long
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


@files_bp.route("/api/sandbox/save", methods=["POST"])
@login_required
def save_sandbox_file_api():
    data = request.get_json() or {}
    filename = data.get("filename", "").strip()
    content = data.get("content", "")
    
    if not filename:
        return jsonify({"error": "Filename is required"}), 400
        
    # Prevent empty or absolute path traversal escape
    # The workspace root is c:\Oculusai\oculusai
    workspace_root = os.path.abspath(os.getcwd())
    
    # Normalize path and check directory bounds
    target_path = os.path.abspath(os.path.join(workspace_root, filename))
    if not target_path.startswith(workspace_root):
        return jsonify({"error": "Access denied: cannot write outside workspace"}), 403
        
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"status": "ok", "path": filename})
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

