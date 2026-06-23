<div align="center">

<img src="static/oculus_logo.svg" alt="Oculus AI Logo" width="300"/>

<br><br>

**A memory-powered AI workspace for developers, agencies, consultants, and business owners.**  
Persistent AI Memory • Multi-Model AI • Web Search • File Analysis • Code Assistant

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

Oculus is a memory-powered AI workspace built with **Flask**, **OpenRouter**, **Supabase**, and **Tavily Search**.

Unlike traditional AI chatbots, Oculus combines **persistent AI memory**, **long-term context retention**, **live web search**, **file analysis**, **code assistance**, **multi-model AI routing**, and **project awareness** into a single platform.

It is designed for developers, digital agencies, consultants, marketers, entrepreneurs, and business owners who need an AI assistant that remembers information across sessions and works directly with files, projects, clients, and ongoing conversations.

It remembers who you are. It searches the web in real time. It writes code that actually runs. It analyzes files. It generates ads, copy, and strategy without filler — and without guardrails blocking legitimate adult ad content.

Oculus is not designed to be another chatbot wrapper.

It is designed to become a persistent business assistant that understands your work, remembers important context, and helps execute real tasks.

---

## 🎯 Use Cases

### 👨‍💻 Developers

- Debug applications
- Analyze codebases
- Generate scripts
- Review source code
- Work with Python, JavaScript, SQL, React, HTML, CSS, and Bash

### 📣 Digital Agencies

- Store client context
- Generate proposals
- Create advertising copy
- Maintain project memory
- Track deadlines and deliverables

### 🏢 Consultants & Business Owners

- Retain long-term business knowledge
- Build reusable knowledge bases
- Conduct research with live web search
- Analyze files and documentation
- Manage ongoing projects and workflows

---

## ⚙️ Core Capabilities

| Capability | Description |
|---|---|
| 🔐 **Multi-User Auth** | Register, login, and logout — each user's data is fully isolated in Supabase |
| 🧠 **Long-Term Memory** | Stores your profile, projects, clients, preferences, and key facts across sessions. A background LLM pipeline extracts, consolidates, and deconflicts information automatically |
| 🧠 **Oculus Brain UI** | Sliding side panel with live view of your memory — edit profiles, add facts, manage projects, clients, and deadlines in real time |
| 🔄 **Real-Time Streaming** | Token-by-token streaming so responses appear word-by-word as the model generates |
| 🔬 **Collapsible Thinking** | Internal model reasoning streams live in a greyed-out block, then folds into a collapsible summary when the final response begins |
| 🌐 **Live Web Search** | Automatically pulls real-time information via Tavily Search when the query requires current data |
| 💻 **Interactive Code Sandbox** | HTML, CSS, JavaScript, and SVG snippets open in a live split-screen iframe sandbox directly in the chat — edit, run, and preview without leaving the app |
| 🗂️ **File Upload & Parsing** | Drag-and-drop or select plaintext and code files (.py, .js, .json, .css, etc.). Content is injected into the prompt automatically and cleared after each submit |
| ⚙️ **Manual Model Selection** | Pin any supported model via the sidebar panel (e.g. Nemotron 3 Super 120B, Llama 3.3 70B, Hermes 3 405B, Dolphin Mistral 24B) |
| 🔄 **Model Fallback Chain** | If the pinned model is rate-limited, returns an error, or times out, the system automatically tries the next model in the chain — no failed requests |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns to stay within model context windows |
| 📣 **Marketing Engine** | Ad copy, branding, social strategy, customer replies, and CIPC basics — built into the system prompt |
| 👨‍💻 **Developer Assistant** | Full working code, debugging, and explanations across Python, JavaScript, SQL, React, Bash, and more |

---

## 🏗️ Architecture

```
Oculus AI
│
├── Flask              → Web server, routing, session-based auth
├── OpenRouter API     → AI model gateway (OpenAI-compatible)
│   ├── Nemotron 3 Super 120B       → Primary (Default) — fast, cheap, unmoderated
│   ├── Llama 3.3 70B               → Fallback 1 — balanced, reliable
│   ├── Hermes 3 405B               → Fallback 2 — powerful, unmoderated
│   ├── Dolphin Mistral 24B         → Fallback 3 — uncensored, free tier
│   └── Free Fallbacks              → (Nemotron 3, Llama 3.3, Hermes 3 405B)
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory + chat history per user
├── Tavily Search      → Live web search injected into prompt context
└── Prompt Engine      → Injects memory, search results, and date/time into every request
```

### Model Selection & Fallback Chain

**Manual selection:** Users pin a preferred model from the sidebar panel. The selected model is persisted in the Flask session and used first on every request.

**Automatic fallback:** If a model returns a rate-limit error (429), invalid ID (400), empty response, or times out after 45 seconds, it is skipped and the next model in the chain is tried automatically — guaranteeing a response even when individual models are unavailable.

---

## 🧠 Memory Schema

Memory is stored in Supabase and fully isolated per user. It's extracted automatically from natural conversation — no forms, no manual setup.

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

---

## 🚀 Deployment

### Requirements

- Python 3.10+
- A [Supabase](https://supabase.com) account
- A [Render](https://render.com) account (or any Python host)
- An [OpenRouter](https://openrouter.ai) account (free tier works; credits recommended)
- A [Tavily](https://tavily.com) account (free tier available)

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

> **Get your OpenRouter key:** [openrouter.ai](https://openrouter.ai) → Settings → API Keys

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

Then go to **Supabase → Authentication → Settings** and disable **"Enable email confirmations"** so users can log in immediately after registering.

### Run locally

```bash
python app.py
```

---

## 📁 Project Structure

```
oculus-ai/
├── app.py                  # Entry point — instantiates Flask, registers blueprints, runs server
├── config.py               # Environment variables, model list, timeout settings
├── requirements.txt        # Python dependencies
├── backend/
│   ├── __init__.py         # Exposes all Blueprints from the backend package
│   ├── extensions.py       # Initialises shared API clients (Supabase, Tavily)
│   ├── auth.py             # Auth routes, login/register/logout, @login_required decorator
│   ├── memory.py           # Memory DB read/write, LLM-based extraction and consolidation
│   ├── chat.py             # Home route, chat submission, clear, model switching
│   ├── files.py            # File upload handling, allowed types, prompt injection
│   ├── search.py           # Tavily query refinement and search trigger logic
│   ├── models.py           # OpenRouter streaming gateway and model fallback chain
│   └── prompts.py          # System prompt construction, memory injection, search formatting
├── templates/
│   ├── index.html          # Main chat interface (Jinja2)
│   ├── login.html          # Login page
│   └── register.html       # Registration page
└── static/
    ├── oculus.js           # Frontend — streaming, markdown render, code sandbox, brain UI
    ├── style.css           # Dark terminal theme
    ├── oculus_logo.svg     # Full logo with wordmark
    ├── oculus_avatar.svg   # Avatar / chat bubble icon
    ├── manifest.json       # PWA manifest
    ├── sw.js               # Service worker — static asset caching
    └── favicon.ico         # Browser tab icon
```

---

## 💸 OpenRouter Costs & Speed

| Setup | Response Time | Rate Limits |
|---|---|---|
| **Free tier** | 30 sec – 2+ min | Shared pool across all users |
| **With credits ($5–$10)** | **5 – 15 seconds** | Your own dedicated quota |

At roughly **$0.20 per million tokens**, a typical message (system prompt + request + response ≈ 2,500 tokens) costs around **0.05 US cents**. A $5 top-up covers approximately **1,500+ messages**.

Add credits at: [openrouter.ai → Settings → Credits](https://openrouter.ai/settings/credits)

---

## ⚡ Design Philosophy

- **Clarity over fluff** — responses are direct and useful, never padded
- **Function over theory** — it does the work, not just talks about it
- **Memory that actually works** — context survives across sessions and deploys
- **Code that runs** — no pseudocode, no placeholders, no "add your logic here"
- **Private by design** — every user's data is fully isolated, no crossover
- **Uncensored by design** — models chosen specifically for minimal guardrails on adult and creative content
- **Premium UX** — real-time word-by-word streaming, animated reasoning blocks, live code sandbox

---

## 🚀 Coming Soon

| Capability                          | Description |
|-------------------------------------|-----------|
| 🌐 **Smart Search Classifier**      | LLM decides when and how to search the web, generating optimised queries |
| 🔬 **Multi-Stage Reasoning**        | Structured reasoning pass before final response for better complex task handling |
| 🖼️ **Image Understanding**         | Upload and analyze screenshots, mockups, and designs |
| 🏢 **Client Workspaces**            | Fully isolated per-client environments with dedicated memory, files, and projects |
| 📋 **Project & Deadline Management**| Automatic task/deadline extraction and tracking |
| 📄 **Advanced RAG & Document Intelligence** | Semantic search over PDFs, DOCX, and other documents with citations |
| 🔧 **AI Actions Engine**            | Generate proposals, send emails, create tasks, and automate workflows |
| 📱 **Enhanced Mobile Experience**   | Full PWA support and optimised Brain UI on mobile |

---

<div align="center">

<img src="static/oculus_avatar.svg" alt="Oculus Avatar" width="64"/>

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
