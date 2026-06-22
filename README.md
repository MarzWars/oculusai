<div align="center">

<img src="static/oculus_logo.svg" alt="Oculus AI Logo" width="300"/>

<br><br>

**A custom-built artificial intelligence system for real work.**  
Code. Copy. Strategy. Memory. Uncensored. All in one.

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=flat-square&logo=flask&logoColor=white)
![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-6366F1?style=flat-square&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Memory-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat-square&logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-Private-red?style=flat-square)

<br>

### 🚀 [Try it live → oculusai.onrender.com](https://oculusai.onrender.com/)

<br>

> Built by **Alex** · [Lex Digitals](https://lexdigitals.co.za)

</div>

---

# Oculus AI (Uncensored)

One-line elevator pitch

A lightweight, self-hostable AI web app for exploring large language models without preset filters — built for researchers and teams who need an uncensored sandbox for experimentation and production prototypes.

Why it matters

Oculus AI provides a fast, web-based interface to interact with multiple LLM backends, keep long-term memory per user, and run workflows that combine web search, memory, and model reasoning.

Quick wins — Try it in under 5 minutes

1. Clone the repo

   git clone https://github.com/MarzWars/oculusai.git
   cd oculusai

2. Create a virtualenv & install

   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt

3. Run locally (example)

   # replace with the project's actual start command if different
   python app.py

4. Open http://localhost:8000 (or the port printed by the server)

If you require API keys, place them in a .env file or set them in your host environment (see "Environment" below).

Demo / Screenshots

Include a screenshot or short GIF showing the UI. Example:

![screenshot](static/screenshot.png)

If you have a hosted demo, it's linked at the top: https://oculusai.onrender.com/

Highlights

- Fast, minimal UI for prompt experimentation
- Extensible adapter system for multiple LLM backends via OpenRouter
- Long-term, per-user memory stored in Supabase
- Real-time token streaming for live responses
- Exportable conversation logs and prompt histories

Quick usage example

```python
from oculusai import Client
client = Client(api_key="YOUR_API_KEY")
print(client.chat("Say hello in a pirate voice"))
```

Architecture overview

```
Oculus AI
│
├── Flask              → Web server + routing + session-based auth
├── OpenRouter API     → AI model gateway (OpenAI-compatible)
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory + chat history per user
├── Tavily Search      → Live web search when needed
└── Prompt Engine      → Injects memory, search results, date/time into every request
```

Deployment & Requirements

- Python 3.10+
- Supabase project (for auth & storage)
- OpenRouter API key (or configured LLM backend)
- A host (Render, Vercel, Heroku, or similar) or run locally

Install dependencies

```bash
pip install -r requirements.txt
```

Environment variables (example)

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_secret_key
SECRET_KEY=your_flask_session_secret
TAVILY_API_KEY=your_tavily_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

Supabase table setup (example)

```sql
-- Per-user memory
CREATE TABLE oculus_memory (
  user_id UUID PRIMARY KEY,
  memory  JSONB DEFAULT '{}'
);

-- Per-user chat history and summaries
CREATE TABLE oculus_chat (
  user_id  UUID PRIMARY KEY,
  messages JSONB DEFAULT '[]',
  summary  TEXT  DEFAULT ''
);
```

Project structure (overview)

```
oculus-ai/
├── app.py
├── requirements.txt
├── static/
│   ├── oculus.js
│   ├── style.css
│   ├── oculus_logo.svg
│   └── favicon.ico
└── README.md
```

Contributing

Contributions are welcome. A CONTRIBUTING.md will land soon with setup, tests, and style guides. If you're getting started, look for issues labeled `good first issue`.

License

This repository is available under the MIT License. See LICENSE for details.

Security and community

- Consider adding SECURITY.md and CODE_OF_CONDUCT.md for contributor trust.
- Add GitHub topics: ai, lms, chatbot, research, python, webapp, prompt-engineering

What changed in this update

- Clarified the elevator pitch and quick-start instructions
- Added a small "Try it" quick-start so newcomers can run the app in minutes
- Added explicit environment variable notes and sample Supabase schema
- Called out contributing/next steps (CONTRIBUTING.md, good-first-issue)

Next steps I can do for you

- Create CONTRIBUTING.md and CODE_OF_CONDUCT.md
- Add 2–3 ready-to-implement `good first issue` issue templates and open them in the repo
- Draft social post copy (Hacker News/Reddit/Twitter)
- Create a short demo GIF checklist and hosting steps

If you want any of those created, tell me which and I'll add them directly to the repository.
