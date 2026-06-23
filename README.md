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

## What is Oculus?

Oculus is a custom AI assistant powered by **OpenRouter** — a gateway to multiple large language models — with a full persistent memory system, automated live web search, multi-user authentication, and a clean dark UI. It handles both **developer work** and **marketing work** without switching tools.

It remembers who you are. It searches the web when it needs to. It writes real, working code. It generates ads, copy, and strategy. And it does all of it without filler — and without guardrails blocking legitimate adult ad content.

---

## ⚙️ Core Capabilities

| Capability | Description |
|---|---|
| 🔐 **Multi-User Auth** | Register, login, and logout — each user's data is fully isolated |
| 🧠 **Long-Term Memory** | Stores profile, projects, clients, preferences, and facts via Supabase. Uses a background LLM pipeline to extract, consolidate, and deconflict information dynamically |
| 🧠 **Oculus Brain UI** | Premium sliding glassmorphic dashboard drawer. View, edit, add, or delete memory facts in real-time |
| 🗂️ **File Upload & Parsing** | Drag and drop or select plaintext/code files (.py, .js, .json, .css, etc.). Injects content into prompt context automatically, clearing instantly on submit |
| 🔄 **Real-Time Streaming** | Token-by-token streaming so responses appear word-by-word in real time |
| 🔬 **Collapsible Thinking** | Shows the AI's internal reasoning live in greyed-out font, folding it into a collapsible block when the final response starts |
| 🌐 **Live Web Search** | Pulls real-time information using Tavily Search automatically when the query demands it |
| 💻 **Developer Assistant** | Writes full working code, debugs errors, explains logic — Python, JS, SQL, React, Bash and more |
| 📣 **Marketing Engine** | Ad copy, branding, social strategy, customer replies, CIPC basics |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns |
| ⚙️ **Manual Model Selection** | Pin a specific model (e.g., Hermes 3 70B, Llama 3.3 70B, Dolphin Mistral 24B) via the header dropdown |
| 🔄 **Model Fallback Chain** | If the preferred/pinned model is busy, the system automatically falls back to the next available model in the chain |


---

## 🏗️ Architecture

```
Oculus AI
│
├── Flask              → Web server + routing + session-based auth
├── OpenRouter API     → AI model gateway (OpenAI-compatible)
│   ├── Hermes 3 70B                → Primary (Default) — fast, unmoderated
│   ├── Nemotron 3 Super 120B       → Fallback 1 — fast, moderated
│   ├── Llama 3.3 70B               → Fallback 2 — balanced, moderated
│   ├── Hermes 3 405B               → Fallback 3 — powerful, unmoderated
│   ├── Dolphin Mistral 24B         → Fallback 4 — uncensored, free
│   └── Free Fallbacks              → (Nemotron 3, Llama 3.3, Hermes 3 405B)
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory + chat history per user
├── Tavily Search      → Live web search when needed
└── Prompt Engine      → Injects memory, search results, date/time into every request
```

### Model Selection & Fallback Chain

* **Manual Selection:** Users can choose a preferred model via the dropdown selector in the header (e.g., Hermes 3 70B, Llama 3.3 70B, Dolphin Mistral 24B, etc.).
* **Automatic Fallback:** Each request tries the preferred model first. If a model is **rate-limited (429)**, returns an **invalid ID (400)**, or **times out (45 seconds)**, it is skipped and the next model in the chain is tried automatically to guarantee a response.


---

## 🧠 Memory Schema

Oculus stores everything it learns about you in Supabase — isolated per user. The memory record looks like this:

```json
{
  "profile": {
    "name": "",
    "role": "",
    "company": "",
    "location": "",
    "email": "",
    "phone": ""
  },
  "clients": [],
  "projects": [],
  "preferences": [],
  "important_facts": [],
  "topics_discussed": [],
  "deadlines": [],
  "session_count": 0,
  "message_count": 0,
  "first_seen": "",
  "last_seen": ""
}
```

Memory is extracted automatically from natural conversation — no forms, no setup. Just talk.

---

## 🚀 Deployment

### Requirements

- Python 3.10+
- A [Supabase](https://supabase.com) account
- A [Render](https://render.com) account (or any Python host)
- An [OpenRouter](https://openrouter.ai) account (free tier works; credits recommended for speed)

### Install dependencies

```bash
pip install flask openai supabase tavily-python requests
```

### Environment variables

Set these in your Render dashboard under **Environment**:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_secret_key
SECRET_KEY=your_flask_session_secret
TAVILY_API_KEY=your_tavily_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

> **Get your OpenRouter key:** Sign up at [openrouter.ai](https://openrouter.ai) → Settings → API Keys

### Supabase table setup

Run this in your Supabase SQL editor:

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

Also go to **Supabase → Authentication → Settings** and disable **"Enable email confirmations"** so users can log in immediately after registering.

### Run locally

```bash
python app.py
```

---

## 📁 Project Structure

```
oculus-ai/
├── app.py              # Main entry point - instantiates Flask, registers blueprints, and runs.
├── config.py           # Configuration settings (environment variables, models, timeouts)
├── requirements.txt    # Dependencies (flask, openai, supabase, tavily-python)
├── backend/
│   ├── __init__.py     # Exposes all Blueprints from the backend package
│   ├── extensions.py   # Initializes shared API clients (Supabase, Tavily)
│   ├── auth.py         # Authentication logic, routes, and @login_required decorator
│   ├── memory.py       # Memory persistence DB calls, regex profiles, and LLM updates
│   ├── chat.py         # Main home chat layout, clearing chat, and submission endpoints
│   ├── files.py        # Allowed types, upload caches, and deletion route controllers
│   ├── search.py       # Tavily search query refinement and trigger checks
│   ├── models.py       # OpenRouter gateway stream connections and model fallback chains
│   └── prompts.py      # Core instructions, memory extractions, and search prompts
├── templates/
│   ├── index.html      # Main chat interface template (Jinja2)
│   ├── login.html      # Authentication login interface template (Jinja2)
│   └── register.html   # Authentication registration interface template (Jinja2)
└── static/
    ├── oculus.js       # Frontend — send/receive, markdown render, code blocks
    ├── style.css       # Dark UI theme
    ├── oculus_logo.svg # Full logo with wordmark
    ├── oculus_avatar.svg # Avatar / chat icon
    └── favicon.ico     # Browser tab icon
```

---

## 💸 OpenRouter Costs & Speed

| Setup | Response Time | Models Available | Rate Limits |
|---|---|---|---|
| **Free tier** | 30 sec — 2+ min | Shared pool | Shared with all users |
| **With credits ($5–$10)** | **5 – 15 seconds** | Dolphin 24B (primary) | Your own quota |

At approximately **$0.20 per million tokens**, a typical message (system prompt + request + response ≈ 2,500 tokens) costs roughly **0.05 US cents**. A $5 top-up covers around **1,500+ messages**.

Add credits at: [openrouter.ai → Settings → Credits](https://openrouter.ai/settings/credits)

---

## ⚡ Design Philosophy

- **Clarity over fluff** — responses are direct and useful, never padded
- **Function over theory** — it does the work, not just talks about it
- **Memory that actually works** — context survives across sessions and deploys
- **Code that runs** — no pseudocode, no placeholders, no "add your logic here"
- **Private by design** — every user's data is fully isolated, no crossover
- **Uncensored by design** — models chosen specifically for minimal guardrails on adult/creative content
- **Premium User Experience** — real-time word-by-word streaming combined with dynamic styling and custom animated reasoning blocks

---

## 💀 Final Note

Oculus is not a wrapper around a chatbot. It is a system built around a specific use case — running a digital agency — with memory, tooling, and personality designed for that context. The AI backend is chosen specifically to handle adult content without refusals, making it a practical tool for legitimate businesses like Red Rooms.

**Built to think. Built to execute. Built for real work.**

---

## 🚀 Coming Soon

| Capability | Description |
|---|---|
| 💻 **Interactive Code Preview Sandbox** | Render HTML, CSS, Javascript, and SVG code snippets in a live, interactive split-screen iframe sandbox directly in the UI |
| 🌐 **Smart Contextual Search Classifier** | LLM-based classifier to dynamically route queries for web search and structure optimized query strings rather than simple keyword matches |
| 🔬 **Advanced Multi-Stage Reasoning** | Introduce a reasoning pre-pass for complex prompts so Oculus structures its thinking before generating a final response |


---

<div align="center">

<img src="static/oculus_avatar.svg" alt="Oculus Avatar" width="64"/>

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
