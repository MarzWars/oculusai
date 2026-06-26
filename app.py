"""
Oculus AI — Lex Digitals
Multi-user edition: register · login · logout
Memory, chat history, and summaries all stored per-user in Supabase
"""

import os
from flask import Flask
from config import Config
from backend import auth_bp, memory_bp, files_bp, chat_bp, workspaces_bp, actions_bp, rag_bp, docs_bp
from backend.utils import _esc, _render_links

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(memory_bp)
app.register_blueprint(files_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(workspaces_bp)
app.register_blueprint(actions_bp)
app.register_blueprint(rag_bp)
app.register_blueprint(docs_bp)



# Register Jinja2 template filters
@app.template_filter("esc")
def esc_filter(s):
    if not s:
        return ""
    return _esc(s)

@app.template_filter("format_ai_response")
def format_ai_response_filter(s):
    if not s:
        return ""
    import re
    import json
    # Match greedily to the end since the action JSON is always appended last
    proposal_match = re.search(r'\[\[ACTION_PROPOSAL\]\]:\s*(\{.*\})', s)
    placeholder = ""
    if proposal_match:
        raw_json = proposal_match.group(1)
        s = s.replace(proposal_match.group(0), "")
        try:
            data = json.loads(raw_json)
            # Safely embed JSON string in HTML data attribute
            placeholder = f'<div class="action-proposal-placeholder" data-proposal="{_esc(json.dumps(data))}"></div>'
        except Exception:
            pass

    escaped = _esc(s)
    rendered = _render_links(escaped).replace('\n', '<br>')
    return rendered + placeholder


@app.route("/sw.js")
def service_worker():
    response = app.send_static_file("sw.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response

@app.route("/manifest.json")
def manifest():
    response = app.send_static_file("manifest.json")
    response.headers["Content-Type"] = "application/json"
    return response

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)