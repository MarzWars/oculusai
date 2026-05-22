<div align="center">

# 🧠 Oculus AI

**A custom-built intelligence system for real work.**  
Code. Copy. Strategy. Memory. All in one.

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=flat-square&logo=flask&logoColor=white)
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

Oculus is a custom AI assistant built on top of [Xoltron](https://huggingface.co/spaces/darkc0de/chat) with a full memory system, live web search, multi-user authentication, and a clean dark UI. It handles both **developer work** and **marketing work** without switching tools.

It remembers who you are. It searches the web when it needs to. It writes real, working code. It generates ads, copy, and strategy. And it does all of it without filler.

---

## ⚙️ Core Capabilities

| Capability | Description |
|---|---|
| 🔐 **Multi-User Auth** | Register, login, and logout — each user's data is fully isolated |
| 🧠 **Long-Term Memory** | Stores your profile, projects, clients, preferences and facts across sessions via Supabase |
| 🌐 **Live Web Search** | Pulls real-time information using DuckDuckGo when the question needs it |
| 💻 **Developer Assistant** | Writes full working code, debugs errors, explains logic — Python, JS, SQL, React, Bash and more |
| 📣 **Marketing Engine** | Ad copy, branding, SEO, social strategy, customer replies, CIPC basics |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns |
| 🔍 **Syntax Highlighting** | Code blocks rendered with Highlight.js — copy button included |

---

## 🏗️ Architecture

```
Oculus AI
│
├── Flask              → Web server + routing + session-based auth
├── Gradio Client      → Xoltron AI (darkc0de/chat) — language model backend
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory + chat history per user
├── DuckDuckGo DDGS    → Live web search when needed
└── Prompt Engine      → Injects memory, search results, date/time into every request
```

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

### Install dependencies

```bash
pip install flask gradio_client supabase duckduckgo_search
```

### Environment variables

Set these in your Render dashboard under **Environment**:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_secret_key
SECRET_KEY=your_flask_session_secret
```

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
├── static/
│   ├── oculus.js       # Frontend — send/receive, markdown render, code blocks
│   └── style.css       # Dark UI theme
├── requirements.txt
└── README.md
```

---

## ⚡ Design Philosophy

- **Clarity over fluff** — responses are direct and useful, never padded
- **Function over theory** — it does the work, not just talks about it
- **Memory that actually works** — context survives across sessions and deploys
- **Code that runs** — no pseudocode, no placeholders, no "add your logic here"
- **Private by design** — every user's data is fully isolated, no crossover

---

## 💀 Final Note

Oculus is not a wrapper around a chatbot. It is a system built around a specific use case — running a digital agency — with memory, tooling, and personality designed for that context.

**Built to think. Built to execute. Built for real work.**

---

<div align="center">

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
