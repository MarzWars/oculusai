"""
Oculus AI — Lex Digitals
Multi-user edition: register · login · logout
Memory, chat history, and summaries all stored per-user in Supabase
"""

import os
from flask import Flask
from config import Config
from backend import auth_bp, memory_bp, files_bp, chat_bp
from backend.utils import _esc, _render_links

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(memory_bp)
app.register_blueprint(files_bp)
app.register_blueprint(chat_bp)

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
    return _render_links(_esc(s)).replace('\n', '<br>')

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)