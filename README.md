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

Oculus is a custom AI assistant powered by **OpenRouter** — a gateway to multiple large language models — with a full persistent memory system, live web search, multi-user authentication, and a clean dark UI. It handles both **developer work** and **marketing work** without switching tools.

It remembers who you are. It searches the web when it needs to. It writes real, working code. It generates ads, copy, and strategy. And it does all of it without filler — and without guardrails blocking legitimate adult ad content.

---

## ⚙️ Core Capabilities

| Capability | Description |
|---|---|
| 🔐 **Multi-User Auth** | Register, login, and logout — each user's data is fully isolated |
| 🧠 **Long-Term Memory** | Stores your profile, projects, clients, preferences and facts across sessions via Supabase |
| 🌐 **Live Web Search** | Pulls real-time information using Tavily Search when the question needs it |
| 💻 **Developer Assistant** | Writes full working code, debugs errors, explains logic — Python, JS, SQL, React, Bash and more |
| 📣 **Marketing Engine** | Ad copy, branding, SEO, social strategy, customer replies, CIPC basics |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns |
| 🔄 **Model Fallback Chain** | If the primary AI model is busy, the system automatically tries the next one — no manual intervention needed |

---

## 🏗️ Architecture

```
Oculus AI
│
├── Flask              → Web server + routing + session-based auth
├── OpenRouter API     → AI model gateway (OpenAI-compatible)
│   ├── Dolphin Mistral 24B Venice  → Primary — uncensored, adult-content tuned
│   ├── Llama 3.3 70B               → Fallback 1 — fast, unmoderated
│   ├── Nex N2 Pro                  → Fallback 2 — fast MoE, unmoderated
│   ├── Nemotron Super 120B         → Fallback 3 — large, unmoderated
│   ├── Hermes 3 Llama 405B         → Fallback 4 — very large, unmoderated
│   └── Nemotron Ultra 550B         → Fallback 5 — last resort
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory + chat history per user
├── Tavily Search      → Live web search when needed
└── Prompt Engine      → Injects memory, search results, date/time into every request
```

### How the Fallback Chain Works

Each request tries the models in order. If a model is **rate-limited (429)**, returns an **invalid ID (400)**, or **times out (45 seconds)**, it is skipped and the next model is tried automatically. The response always comes from whichever model picks it up first.

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
├── app.py              # Flask backend — all logic lives here
├── requirements.txt    # Dependencies (flask, openai, supabase, tavily-python)
├── static/
│   ├── oculus.js       # Frontend — send/receive, markdown render, code blocks
│   ├── style.css       # Dark UI theme
│   ├── oculus_logo.svg # Full logo with wordmark
│   ├── oculus_avatar.svg # Avatar / chat icon
│   └── favicon.ico     # Browser tab icon
└── README.md
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

---

## 💀 Final Note

Oculus is not a wrapper around a chatbot. It is a system built around a specific use case — running a digital agency — with memory, tooling, and personality designed for that context. The AI backend is chosen specifically to handle adult content without refusals, making it a practical tool for legitimate businesses like Red Rooms.

**Built to think. Built to execute. Built for real work.**

---

## 🚀 Coming Soon

| Capability | Description |
|---|---|
| 🧠 **AI-Powered Memory Extraction** | Upgrade the regex-based `extract_memory` system to use a dedicated AI post-turn pipeline for cleaner, more accurate long-term memory. |
| 🔬 **Advanced Multi-Stage Reasoning** | Introduce a reasoning pre-pass for complex prompts so Oculus structures its thinking before generating a final response. |
| ✨ **Rich Markdown + HTML Rendering** | Full markdown-to-HTML formatter for the `render_bubble` pipeline — tables, links, code blocks all rendered cleanly. |
| 🧬 **AI Inference Memory** | An `ai_notes` memory layer generated by the model itself — retaining inferred context, patterns, and observations beyond literal user statements. |
| 🔄 **Streaming Responses** | Token-by-token streaming so replies appear word-by-word instead of all at once after a delay. |

---

<div align="center">

<img src="static/oculus_avatar.svg" alt="Oculus Avatar" width="64"/>

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
