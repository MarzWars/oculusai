<div align="center">

<img src="static/oculus_logo.svg" alt="Oculus AI Logo" width="300"/>

<br><br>

**A custom-built artificial intelligence system for real work.**  
Code. Copy. Strategy. Memory. Workspaces. Actions Engine. All in one.

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

Oculus is an AI workspace that remembers clients, generates proposals, drafts emails, manages tasks, and executes workflows built for running a digital agency — not a generic chatbot wrapper. It's powered by **OpenRouter**, a gateway to multiple large language models, and layered with a persistent memory system, isolated client workspaces, live web search, a custom-built code sandbox, and an interactive **AI Actions Engine** for automations.

It remembers who you are. It searches the web in real time. It writes code that actually runs. It generates proposals, drafts emails, schedules tasks, and coordinates workflows without guardrails blocking creative or adult ad campaigns.

---

## ⚙️ Core Capabilities

| Capability | Description |
|---|---|
| 🏢 **Client Workspaces** | Switch between isolated workspaces. Isolates chat histories, sandbox code files, and active attachments, while maintaining a unified long-term memory across workspaces. |
| 🔐 **Multi-User Auth** | Register, login, and logout — each user's data is fully isolated in Supabase. |
| 🧠 **Long-Term Memory** | Stores your profile, projects, clients, preferences, and key facts across sessions. A background LLM pipeline extracts, consolidates, and deconflicts information automatically. |
| 🧠 **Oculus Brain UI** | Sliding side panel with live view of your memory — edit profiles, add facts, manage projects, clients, and deadlines in real time. |
| ⚡ **AI Actions Engine** | Generates proposals, sends emails, schedules tasks, and logs workflow history. Uses low-temperature function extraction with OpenRouter to produce active proposals. Includes interactive sidebar confirmation, cancellation, and deletion controls. |
| 🔄 **Real-Time Streaming** | Token-by-token streaming so responses appear word-by-word as the model generates. |
| 🔬 **Collapsible Thinking** | Internal model reasoning streams live in a greyed-out block, then folds into a collapsible summary when the final response begins. |
| 🌐 **Live Web Search** | Automatically pulls real-time information via Tavily Search when the query requires current data. |
| 💻 **Interactive Code Sandbox** | HTML, CSS, JavaScript, and SVG snippets open in a live split-screen iframe sandbox directly in the chat — edit, run, and preview without leaving the app. |
| 🗂️ **File Upload & Parsing** | Drag-and-drop or select plaintext and code files (.py, .js, .json, .css, etc.). Content is injected into the prompt automatically and cleared after each submit. |
| ⚙️ **Manual Model Selection** | Pin any supported model via the sidebar panel (e.g. Nemotron 3 Super 120B, Llama 3.3 70B, Hermes 3 405B, Dolphin Mistral 24B). |
| 🔄 **Model Fallback Chain** | If the pinned model is rate-limited, returns an error, or times out, the system automatically tries the next model in the chain — no failed requests. |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns to stay within model context windows. |
| 📣 **Marketing Engine** | Ad copy, branding, social strategy, customer replies, and CIPC basics — built into the system prompt. |
| 👨‍💻 **Developer Assistant** | Full working code, debugging, and explanations across Python, JavaScript, SQL, React, Bash, and more. |

---

## 📖 Feature Usage Guide

Here is a quick reference guide on how to trigger the newly added workspace and action automation features:

### 1. Unified Long-Term Memory
Oculus automatically listens and extracts facts about your projects, preferences, and clients during normal conversation.
* **Extraction Trigger:** 
  > *"My name is Alex, I'm a developer at Lex Digitals and I prefer writing Python code with Flask."*
* **Add Clients:**
  > *"I work with Client Acme Digital Agency. They do real estate branding."*
* **Manage In Brain UI:** Open the settings sidebar panel (hamburger menu in the top left) to edit your profile, add styling preferences, facts, or deadlines manually.

### 2. Isolated Workspaces
Swap between client or project boundaries.
* **Switching:** Click the dropdown selector in the header next to "Oculus AI" to swap between projects.
* **Creating a Workspace:** Click "Create Workspace" from the selector, name it, and Oculus will create a clean context with empty chat history.
* **Deleting a Workspace:** Click the trash icon next to a workspace. This cascades and deletes the workspace entry, isolated chats, cached attachments, and sandbox files on the server.

### 3. Scheduling Tasks
Oculus extracts dates and titles to schedule deadlines.
* **Trigger Prompt:** 
  > *"Add a task to review client mockups by Friday"*
* **Interactive Confirmation:** A glassmorphic card will slide into view showing `Task Title` and `Due Date` fields. You can edit the text inside the inputs.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ the card shows a completion log and the deadline appears immediately in your sidebar brain panel.
* **Undo/Delete**: Click **Undo Action** on the card to remove the task from memory instantly. Alternatively, click the trash can icon next to the task in your sidebar **Action Log** to delete it manually at any time.

### 4. Compiling Proposals & Quotes
Generate professional documents directly in the workspace sandbox.
* **Trigger Prompt:** 
  > *"Generate a proposal for Acme Corp for a website rebrand costing R 45,000. Deliverables include UI mockups, contact forms, and SEO setup."*
* **Interactive Confirmation:** Edit fields like client name, budget amount, and details scope directly on the card.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ Oculus compiles a formal `.docx` layout (using `python-docx`) and saves it to the sandbox.
* **Download:** A download link is generated as an elegant inline **Download DOCX** button inside the card. Click it to download the file directly to your system. You can also view/delete this action later from the sidebar **Action Log**.

### 5. Email Drafting & Previews
Draft emails and review them securely.
* **Trigger Prompt:** 
  > *"Draft a check-in email to john@example.com about project deadlines"*
* **Interactive Confirmation:** A card displays the recipient, subject line, and a text area containing the full body text. Adjust the text as needed.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ Oculus writes a responsive, formatted HTML email container to the workspace sandbox directory. Click the generated inline **Preview HTML** button to open the compiled email in your browser.
* **SMTP Mode:** If you set the environment variable `ENABLE_SMTP_DELIVERY=true` and configure the SMTP host settings, Oculus will actively send the MIME formatted email to the recipient.
* **Action Log Sidebar Controls**: If you clear the chat before confirming or rejecting an action, it will appear in your sidebar **Action Log** as `PENDING`. You can click the checkmark button next to it to **Confirm & Execute** directly from the log, or click the cross button to **Reject & Cancel** it.


---

## 🏗️ Architecture

```
Oculus AI
│
├── Flask              → Web server, routing, session-based auth, client workspaces
├── Actions Engine     → Intent classifier (Llama 3.3), execution wrapper, audit logs
├── OpenRouter API     → AI model gateway (OpenAI-compatible)
│   ├── Nemotron 3 Super 120B       → Primary (Default) — fast, cheap, unmoderated
│   ├── Llama 3.3 70B               → Fallback 1 — balanced, reliable
│   ├── Hermes 3 405B               → Fallback 2 — powerful, unmoderated
│   ├── Dolphin Mistral 24B         → Fallback 3 / Switcher — uncensored
│   └── Free Fallbacks              → (Nemotron 3, Llama 3.3, Hermes 3 405B)
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory (user-scoped), workspaces config, chat history (workspace-isolated), action log audit trail
├── Tavily Search      → Live web search injected into prompt context
└── Prompt Engine      → Injects memory, active workspace context, search results, and date/time into every request
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
  "ai_notes": [],
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
pip install flask openai supabase tavily-python requests python-docx
```

### Environment variables

Set these in your Render dashboard under **Environment**:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_secret_key
SECRET_KEY=your_flask_session_secret
TAVILY_API_KEY=your_tavily_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional SMTP settings for email delivery
ENABLE_SMTP_DELIVERY=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

> **Get your OpenRouter key:** [openrouter.ai](https://openrouter.ai) → Settings → API Keys

### Supabase table setup

Run this in your Supabase SQL editor:

```sql
-- Per-user memory (shared globally across workspaces)
CREATE TABLE oculus_memory (
  user_id UUID PRIMARY KEY,
  memory  JSONB DEFAULT '{}'
);

-- Per-workspace chat history and summaries (workspace-isolated)
-- Note: 'user_id' column stores the workspace_id for isolated context targeting
CREATE TABLE oculus_chat (
  user_id  UUID PRIMARY KEY,
  messages JSONB DEFAULT '[]',
  summary  TEXT  DEFAULT ''
);

-- Workspace lifecycle tracking
CREATE TABLE oculus_workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX idx_oculus_workspaces_user_id ON oculus_workspaces(user_id);

-- Action log history & audit trail
CREATE TABLE oculus_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID NOT NULL,
  action_type TEXT NOT NULL,
  arguments JSONB NOT NULL,
  status TEXT NOT NULL, -- 'pending', 'executed', 'cancelled', 'undone'
  outcome TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
  executed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_oculus_actions_user_id ON oculus_actions(user_id);
CREATE INDEX idx_oculus_actions_workspace_id ON oculus_actions(workspace_id);
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
│   ├── workspaces.py       # Workspaces API lifecycle (create, delete, list, switch)
│   ├── memory.py           # Memory DB read/write, LLM-based extraction and consolidation
│   ├── chat.py             # Home route, chat submission, clear, model switching
│   ├── files.py            # File upload handling, allowed types, prompt injection, sandbox download
│   ├── search.py           # Tavily query refinement and search trigger logic
│   ├── models.py           # OpenRouter streaming gateway and model fallback chain
│   ├── actions.py          # AI Actions Engine, classification prompts, execution wrappers
│   └── prompts.py          # System prompt construction, memory injection, search formatting
├── templates/
│   ├── index.html          # Main chat interface (Jinja2)
│   ├── login.html          # Login page
│   └── register.html       # Registration page
├── workspaces/             # Local sandbox folders isolated per workspace ID (git-ignored)
└── static/
    ├── oculus.js           # Frontend — streaming, markdown render, code sandbox, brain UI, action cards
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

- **Clarity over fluff** — responses are direct and useful, never padded.
- **Function over theory** — it does the work, not just talks about it.
- **Memory that actually works** — context survives across sessions and deploys.
- **Code that runs** — no pseudocode, no placeholders, no "add your logic here".
- **Private by design** — every user's data is fully isolated, no crossover.
- **Uncensored by design** — models chosen specifically for minimal guardrails on adult and creative content.
- **Premium UX** — real-time word-by-word streaming, animated reasoning blocks, live code sandbox.

---

## 🚀 Coming Soon

| Capability                          | Description |
|-------------------------------------|-----------|
| 🌐 **Smart Search Classifier**      | LLM decides when and how to search the web, generating optimised queries. |
| 🔬 **Multi-Stage Reasoning**        | Structured reasoning pass before final response for better complex task handling. |
| 🖼️ **Image Understanding**         | Upload and analyze screenshots, mockups, and designs. |
| 📄 **Advanced RAG & Document Intelligence** | Semantic search over PDFs, DOCX, and other documents with citations. |
| 🔗 **Advanced Multi-Action Workflows** | Chain actions together (e.g. Generate Proposal $\rightarrow$ Draft Email with PDF attached). |
| 📱 **Enhanced Mobile Experience**   | Full PWA support and optimised Brain UI on mobile. |

---

<div align="center">

<img src="static/oculus_avatar.svg" alt="Oculus Avatar" width="64"/>

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
