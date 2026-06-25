<div align="center">

<img src="static/oculus_logo.svg" alt="Oculus AI Logo" width="300"/>

<br><br>

**A custom-built artificial intelligence operating system for real work.**  
Code. Copy. Strategy. Memory. Documents. Actions. All in one.

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=flat-square&logo=flask&logoColor=white)
![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-6366F1?style=flat-square&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Memory-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat-square&logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-Private-red?style=flat-square)

<br>

### 🚀 [Try it live → oculusai.lexdigitals.co.za](https://oculusai.lexdigitals.co.za/)

<br>

> Built by **Alex** · [Lex Digitals](https://lexdigitals.co.za)

</div>

---

## What is Oculus?

Oculus is an **AI Knowledge Workspace & Actions Engine** designed specifically for running a digital agency. Unlike generic chat wrappers that forget context, return empty placeholders, or block copy generation for diverse marketing campaigns, Oculus functions as an integrated **AI Operating System**. It layers LLM intelligence directly over client databases, documents, persistent memories, a live browser code sandbox, and an interactive confirmation engine to let you execute actual work.

---

## ⚡ The Problems Oculus Solves

### 1. The Context-Switching Tax
* **The Problem:** In a typical agency, you are constantly swapping between different clients. Chat logs get cluttered, attachment lists get mixed up, and sandbox files overwrite each other.
* **The Solution:** **Isolated Client Workspaces**. Oculus creates distinct digital sandboxes for every client project. Swapping a workspace switches the active chat history, file uploads, and directory files on the server, keeping Acme Corp assets completely isolated from Lex Digitals internals.

### 2. The "Forgetting" Problem
* **The Problem:** LLM chats have static context windows. If you tell an AI your styling rules, client emails, or task deadlines on Monday, it will forget them by Friday.
* **The Solution:** **Unified Long-Term Memory (Oculus Brain)**. A background pipeline reads conversations, extracts client profiles, preferences, and deadlines, and consolidates them in Supabase. This compiled Brain is injected into every chat request automatically, ensuring Oculus remembers everything that matters across sessions.

### 3. Passive Conversation vs. Active Execution
* **The Problem:** Chatbots only give advice. If you ask them to create a task, draft a proposal, or write an email, they just give you a block of markdown text that you have to copy, paste, and compile yourself.
* **The Solution:** **AI Actions Engine**. Oculus classifies intent and renders interactive **action proposal cards** directly in the chat feed. You can review parameters, edit content, and click **Confirm & Execute**. The system compiles standard `.docx` proposals, saves `.html` email draft previews to the sandbox, or writes task deadlines to the database.

### 4. Placeholder Code and "Pseudo-Logic"
* **The Problem:** AI models frequently write incomplete code, adding comments like `// TODO: Implement styling here` or leaving you to copy-paste scripts into local test files.
* **The Solution:** **Interactive Live Sandbox**. Oculus intercepts HTML, CSS, JavaScript, and SVG blocks and renders them in a split-screen live preview iframe. You can edit the code, run it, review rendering output in real time, and save the finalized code directly to your server workspace.

### 5. Corporate Censorship and Guardrail Blocks
* **The Problem:** Commercial AI interfaces (like ChatGPT) block copy generation for adult entertainment marketing, Locanto campaigns, or dating ads.
* **The Solution:** **OpenRouter Model Gateway**. Bypasses strict filters using unmoderated open models (like Llama 3.3 70B, Nemotron 3 120B, and Dolphin Mistral) to write copy for real clients in high-conversion campaigns (e.g. Red Rooms ads, operator recruitment copies) without blocking.

---

## ⚙️ Core Capabilities

| Capability | Description |
|---|---|
| 🏢 **Client Workspaces** | Switch between isolated workspaces. Isolates chat histories, sandbox code files, and active attachments, while maintaining a unified long-term memory across workspaces. |
| 🔐 **Multi-User Auth** | Register, login, and logout — each user's data is fully isolated in Supabase. |
| 🧠 **Long-Term Memory** | Stores your profile, projects, clients, preferences, and key facts across sessions. A background LLM pipeline extracts, consolidates, and deconflicts information automatically. |
| 🧠 **Oculus Brain UI** | Sliding sidebar drawer panel with live view of your memory — edit profiles, add facts, manage projects, clients, and deadlines in real time. |
| ⚡ **AI Actions Engine** | Generates proposals, sends emails, schedules tasks, and logs workflow history. Uses low-temperature function extraction with OpenRouter to produce active proposals. Includes interactive sidebar confirmation, cancellation, and deletion controls. |
| 📄 **Advanced RAG & Doc Intel** | Semantic search over PDFs and DOCX files. Ingests, chunks, embeds (via OpenRouter), and indexes documents in Supabase. Classifies documents, auto-summarizes them using OpenRouter, and supports hybrid (vector + full-text search) retrieval with RRF ranking and citations. |
| 🔄 **Real-Time Streaming** | Token-by-token streaming so responses appear word-by-word as the model generates. |
| 🔬 **Collapsible Thinking** | Internal model reasoning streams live in a greyed-out block, then folds into a collapsible summary when the final response begins. |
| 🌐 **Live Web Search** | Automatically pulls real-time information via Tavily Search when the query requires current data. |
| 💻 **Interactive Code Sandbox** | HTML, CSS, JavaScript, and SVG snippets open in a live split-screen iframe sandbox directly in the chat — edit, run, and preview without leaving the app. |
| 🗂️ **File Upload & Parsing** | Drag-and-drop or select plaintext and code files (.py, .js, .json, .css, etc.). Content is injected into the prompt automatically and cleared after each submit. |
| ⚙️ **Manual Model Selection** | Pin any supported model via the sidebar panel (e.g. Nemotron 3 Super 120B, Llama 3.3 70B, Hermes 3 405B, Dolphin Mistral 24B). |
| 🔄 **Model Fallback Chain** | If the pinned model is rate-limited, returns an error, or times out, the system automatically tries the next model in the chain — no failed requests. |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns to stay within model context windows. |

---

## 📖 How to Use Oculus — Complete Guide

This section covers every major feature in detail. Think of this as a field manual — read it once and you will know exactly how to get full value out of the system.

---

### 🧠 Feature 1: Long-Term Memory (Oculus Brain)

Oculus remembers things so you do not have to repeat yourself. Every conversation is passively scanned in the background and key facts — names, preferences, clients, deadlines — are extracted and stored in your **Brain**. This Brain is injected into every future request, so Oculus always knows the full picture.

**Opening the Brain Panel:**  
Click the **☰ menu icon** in the top-right header. The settings sidebar will slide out. Scroll down to see **Oculus Brain** — your live memory card. You can edit profile fields directly, delete individual facts, and manage project/client entries in real time.

**How memory is built — example prompts to teach Oculus about you:**

> *"My name is Alex. I run Lex Digitals, a digital marketing agency based in South Africa."*

> *"Our primary design style is dark-themed glassmorphism with subtle gradients. Use Outfit or Inter fonts in all UI work."*

> *"I always use Flask for Python web apps and prefer PostgreSQL over SQLite."*

> *"My client Sarah runs Acme Digital Agency. Their website is acmedigital.com and she prefers to be contacted via email."*

> *"Red Rooms is our adult entertainment platform client. Always use bold, direct copy for their campaigns."*

**Asking Oculus to recall memory:**

> *"What do you know about my design preferences?"*

> *"Remind me what clients we are currently working with."*

> *"What stack do I usually use for web apps?"*

**Tip:** You never need to explicitly say "remember this." Just mention information naturally in conversation and Oculus will pick it up. Close the chat, come back tomorrow, and Oculus will still know who you are and what you are working on.

---

### 🏢 Feature 2: Client Workspaces

Workspaces are isolated project environments. Each one has its own chat history, sandbox folder, and uploaded file context. Your Brain (memory) is shared globally across all workspaces.

**Creating a workspace:**
1. Click the workspace name dropdown in the header (e.g. *Personal Workspace*).
2. Click **+ Create Workspace**.
3. Name it after your client or project (e.g. `Acme Corp`, `Red Rooms`, `Lex Digitals Internal`).
4. Click **Create** — Oculus initialises a clean, isolated context instantly.

**Switching workspaces:**
- Click the workspace dropdown and select any workspace in the list.
- The chat history, sandbox files, and uploaded document context all switch immediately.

**Deleting a workspace:**
- Click the **🗑️ trash icon** next to a workspace name.
- This cascades and removes the workspace entry, chat history, sandbox files, and cached attachments from the server.

**Example workflow:**  
Create a `Acme Corp` workspace before every client meeting. Drop all their files, ask strategy questions, draft proposals — all isolated. Then switch back to `Lex Digitals Internal` for your own work with no crossover.

---

### ⚡ Feature 3: AI Actions Engine

The Actions Engine turns conversation into execution. When Oculus detects intent to schedule a task, compile a proposal, or draft an email, it generates an interactive **Action Proposal Card** directly in the chat. You review the extracted parameters, make adjustments, and confirm — Oculus does the rest.

#### 3a. Scheduling Tasks & Deadlines

Oculus detects scheduling intent and extracts a task title and due date. An interactive card appears with editable fields.

**Example prompts:**

> *"Add a task: review the Acme Corp homepage mockup with Sarah. Due next Friday."*

> *"Remind me to follow up with Red Rooms about the operator recruitment campaign — deadline end of month."*

> *"Schedule a task: send the revised quote to the client. Due tomorrow."*

> *"Create a deadline for the Lex Digitals SEO audit report — due 30 June."*

> *"Task: prepare the monthly performance report for all clients. Due this Sunday."*

**What happens:**
1. An action card appears in chat with a `Task Title` input and `Due Date` picker.
2. Edit either field directly on the card if needed.
3. Click **✅ Confirm & Execute** — the task is saved to your database and appears in the **Action Log** sidebar.
4. To undo, click **↩️ Undo Action** on the card, or click the **🗑️ trash icon** next to the entry in your Action Log.

---

#### 3b. Proposals & Quotes

Oculus compiles formal proposal documents and saves them as downloadable `.docx` files to your workspace sandbox.

**Example prompts:**

> *"Generate a proposal for Acme Corp for a full website rebrand. Budget: R45,000. Scope: UI wireframes, contact form integration, mobile responsiveness, SEO setup, and one round of revisions."*

> *"Write a quote for Red Rooms for a 3-month social media management retainer. Monthly fee: R8,500. Include content creation (12 posts/month), story scheduling, and monthly performance reporting."*

> *"Create a proposal for a new client who wants a custom e-commerce platform built in React. Budget R120,000. Scope of work: product catalogue, Stripe integration, admin dashboard, and 6 months of support."*

> *"Draft a retainer agreement proposal for Lex Digitals internal — monthly content calendar management at R5,000/month."*

> *"Write a website maintenance proposal for an existing client. Monthly fee R2,500. Covers: plugin updates, weekly backups, uptime monitoring, and one hour of change requests per month."*

**What happens:**
1. An action card appears with editable fields: **Client Name**, **Project Title**, **Budget**, and **Scope of Work**.
2. Edit any field before confirming.
3. Click **✅ Confirm & Execute** — Oculus uses `python-docx` to compile a formatted `.docx` proposal and saves it to your workspace sandbox.
4. A **📥 Download DOCX** button appears inline on the card. Click it to download directly.
5. The action is logged in your **Action Log** sidebar for future reference.

---

#### 3c. Email Drafting & Previews

Oculus drafts formal emails, shows you a preview, and can optionally deliver via SMTP.

**Example prompts:**

> *"Draft a follow-up email to sarah@acmedigital.com about the rebrand proposal I sent last week. Tone should be professional but friendly. Ask if she has had a chance to review."*

> *"Write a cold outreach email to info@realestateco.za introducing Lex Digitals and pitching our website package. Keep it under 200 words."*

> *"Draft an invoice reminder email to john@client.com. Invoice #1042, R12,000, due last Friday."*

> *"Write a project completion email to the Red Rooms team. Confirm the campaign went live, link to the results dashboard, and invite feedback."*

> *"Send a welcome onboarding email to a new client at hello@newclient.com. Explain the project kickoff process, introduce our team, and set the first milestone."*

**What happens:**
1. An action card appears with fields for **Recipient**, **Subject**, and a **Body** text area.
2. Edit anything on the card.
3. Click **✅ Confirm & Execute** — Oculus writes a responsive HTML email container to your workspace sandbox.
4. A **👁️ Preview HTML** button appears — click it to open the rendered email in your browser.
5. If `ENABLE_SMTP_DELIVERY=true` is set in your environment, Oculus will also send the email to the recipient directly via SMTP.

---

### 💻 Feature 4: Interactive Live Code Sandbox

When Oculus generates HTML, CSS, JavaScript, or SVG code, a **Preview** button appears on the code block. Click it to open a full split-screen editor and live preview — no copy-pasting required.

**Example prompts to generate sandbox-ready code:**

> *"Build a responsive HTML/CSS landing page for a real estate agency. Include a glassmorphic navbar, a hero section with a property search bar, and a 3-column services section."*

> *"Write a dark-themed pricing table in HTML and CSS with 3 tiers: Starter, Growth, and Enterprise. Highlight the Growth tier."*

> *"Create an animated SVG logo placeholder — use a glowing circle with a pulsing ring animation."*

> *"Build an interactive JavaScript quiz — 5 questions, multiple choice, score counter, and a results screen at the end."*

> *"Write the complete HTML/CSS/JS for a countdown timer widget that counts down to 1 January 2026."*

> *"Design a contact form with name, email, message fields, and a submit button. Style it with a dark glassmorphism card effect."*

> *"Create a JavaScript-powered image gallery with a lightbox popup when you click a thumbnail."*

**Using the Sandbox:**
1. When the code block finishes rendering, click the **⚡ Preview** button in the code block header.
2. The Sandbox panel opens — code editor on the left, live rendered output on the right.
3. Edit the code directly in the editor.
4. Press **⚡ Run** (or `Ctrl+Enter`) to refresh the live preview.
5. Type a filename in the path bar (e.g. `index.html` or `landing.css`) and click **💾 Save to Project** to write the file to your workspace server directory.
6. Previously saved files are listed below the editor — click any to load it back.

---

### 📄 Feature 5: Document Intelligence & RAG

Upload PDFs and DOCX files into a workspace. Oculus parses, chunks, embeds, and indexes them in Supabase. You can then ask questions and get answers with source citations pulled directly from document content.

**Opening the Documents Sidebar:**  
Click the **📄 Docs** button in the header. A right-aligned slide-in panel will appear.

**Uploading documents:**
- Drag and drop a `.pdf` or `.docx` file into the upload zone, or click the zone to browse.
- Oculus parses the file, splits it into chunks, generates embeddings, and indexes everything in Supabase.
- A document card appears showing: **auto-detected category badge** (e.g. `CONTRACT`, `INVOICE`, `PROPOSAL`, `RESUME`, `REPORT`), a **2-sentence AI summary**, and **extracted keywords**.

**Example documents to upload and queries for each:**

**SLA or Contract:**
> *"What are the payment terms in the Acme SLA contract?"*

> *"Does the contract include a termination clause? What are the notice requirements?"*

> *"List all deliverables and deadlines mentioned in the contract."*

> *"Is there a penalty clause if we miss a milestone?"*

**Invoice:**
> *"What is the outstanding balance on the Red Rooms invoice?"*

> *"What services are listed on invoice #1042?"*

> *"Is VAT included in this invoice? What is the VAT amount?"*

> *"What is the payment due date on this invoice?"*

**Proposal:**
> *"Summarise the scope of work in the submitted proposal."*

> *"What is the timeline breakdown in this proposal?"*

> *"What was the quoted price and what is included at that price?"*

**Resume or CV:**
> *"What is this candidate's most recent job title and employer?"*

> *"Does this CV show experience with React and TypeScript?"*

> *"Summarise this applicant's skills in two sentences."*

**Multi-document cross-reasoning:**
> *"Summarise all the documents in this workspace and tell me which clients have active contracts."*

> *"Compare the payment terms across all contracts uploaded. Which gives us the shortest payment window?"*

> *"List all outstanding invoice amounts across every uploaded invoice and give me the total."*

> *"Which proposals have been converted to contracts based on the documents uploaded?"*

> *"Do any of the uploaded contracts have exclusivity clauses that would stop us taking on competing clients?"*

**How retrieval works:**  
Oculus uses **hybrid search** — combining vector similarity (semantic meaning) with full-text keyword matching — and ranks results using Reciprocal Rank Fusion (RRF). When Oculus cites a source, it will clearly state: *"According to [filename] (Page X)..."* or *"Source: [filename], Section: [title]."*

---

### 🌐 Feature 6: Live Web Search

Oculus automatically detects when a query requires current information and triggers a live web search via Tavily. No setup required — it fires silently in the background.

**Queries that auto-trigger web search:**

> *"What is the current exchange rate from ZAR to USD?"*

> *"What are the latest trends in digital marketing for 2025?"*

> *"What is the going rate for social media management services in South Africa?"*

> *"Find me the latest news about Google's algorithm update."*

> *"What are the best Locanto posting strategies for adult classified ads this year?"*

> *"What is the current CPC for Facebook Ads in the South African market?"*

> *"Are there any new regulations around digital advertising in South Africa?"*

Oculus weaves the live search results naturally into the answer — it will not paste raw URLs or unformatted scrapes.

---

### 🔬 Feature 7: Model Selection & Thinking Mode

Oculus is not locked to one model. You can pin any model for specific tasks.

**Opening Model Settings:**  
Click the **☰ menu icon** in the header → scroll to **Model** in the sidebar panel → select from the dropdown.

**Model guide:**

| Model | Best for |
|---|---|
| **Nemotron 3 Super 120B** | Default. Fast, sharp, uncensored. Great all-rounder. |
| **Claude Sonnet 4.6 (Thinking)** | Deep reasoning tasks, complex analysis, multi-step logic. Shows live thinking stream. |
| **Llama 3.3 70B** | Reliable fallback. Fast, balanced. |
| **Hermes 3 405B** | Very powerful, uncensored. Best for creative or sensitive copy. |
| **Dolphin Mistral 24B** | Lightest, fastest. Good for quick tasks. |

**Example use cases by model:**

> Switch to **Claude Sonnet Thinking** then ask:  
> *"Analyse this contract clause and tell me if there are any legal risks or ambiguities."*

> Switch to **Claude Sonnet Thinking** then ask:  
> *"Plan out the full system architecture for a SaaS platform, including the database schema, API layers, and auth flow."*

> Switch to **Hermes 3 405B** then ask:  
> *"Write a high-converting Locanto ad for an adult entertainment service. Bold, direct, first-person."*

> Use **Nemotron 120B** (default) for:  
> *"Write the complete Python backend for a Flask REST API with JWT authentication."*

> Use **Dolphin Mistral 24B** for:  
> *"Quickly rewrite this paragraph to be more persuasive."*

**Thinking Mode:** When using Claude Sonnet Thinking, you will see a live **🔬 Thinking...** block stream above the response. Once the model produces its answer, the thinking block collapses into a small **▶ Show reasoning** toggle you can expand at any time.

---

### 🗂️ Feature 8: File Uploads (Code & Text Files)

Attach files to your prompt for Oculus to read, analyse, or modify.

**How to upload:**
- Click the **📎 paperclip icon** in the chat input area, or drag a file directly onto the input.
- Supported types: `.py`, `.js`, `.ts`, `.json`, `.css`, `.html`, `.txt`, `.md`, `.env.example`, `.csv`, and more.
- The file content is injected into the next prompt automatically and cleared after you submit.

**Example prompts after uploading a file:**

> *(After uploading `app.py`)*  
> *"Review this Flask app for security vulnerabilities. Focus on the auth routes."*

> *(After uploading `style.css`)*  
> *"Refactor this CSS file to use CSS custom properties for all colours and font sizes."*

> *(After uploading `data.json`)*  
> *"Parse this JSON and write a Python script that reads it and exports a formatted CSV."*

> *(After uploading `requirements.txt`)*  
> *"Are there any outdated or conflicting dependencies in this requirements file?"*

> *(After uploading `index.html`)*  
> *"Audit this HTML file for SEO issues — check title tags, meta descriptions, heading hierarchy, and alt text."*

> *(After uploading `campaign_results.csv`)*  
> *"Analyse this CSV and summarise the top 3 performing ad campaigns by click-through rate."*

---

### 📋 Feature 9: Action Log Sidebar

Every action Oculus proposes — whether confirmed, pending, or cancelled — is logged in the **Action Log**.

**Opening the Action Log:**  
Click the **⚡ Actions** button in the header. The left sidebar will slide out showing all logged actions grouped by status: `PENDING`, `EXECUTED`, `CANCELLED`, `UNDONE`.

**What you can do in the Action Log:**
- **Confirm a pending action** that you missed in chat by clicking the **✅ checkmark** button next to it.
- **Reject a pending action** by clicking the **✗ cross** button.
- **Delete any action** permanently with the **🗑️ trash** icon.
- **Download compiled files** (proposals, email drafts) directly from the log entry.

**Tip:** If you navigate away from the chat mid-conversation before confirming an action, it will remain in the Action Log as `PENDING`. You can always come back and execute it from the sidebar without losing any extracted parameters.

---

## 💡 Power User Tips

- **Natural Language Deadlines:** Say "by end of next week" or "before the client call on Thursday" — Oculus extracts the date automatically.
- **Chain Requests:** After generating a proposal, say *"Now draft the follow-up email to send it to them."* Oculus carries context forward within the same session.
- **Workspace Naming:** Name workspaces after clients (e.g. `Red Rooms`, `Acme Corp`) so sandbox files and histories are always easy to identify.
- **Document First:** Before a client call, upload their contract or brief to the workspace Docs panel. Oculus will automatically have it in context and cite it when relevant.
- **Model Switching Mid-Session:** Switch to Thinking mode for a single deep-reasoning question, then switch back to the default without losing your chat history.
- **Teach Preferences Once:** Tell Oculus your font preferences, code style, or tone requirements once. It will apply them in every future session without being reminded.
- **Sandbox as a Sketchpad:** Use the code sandbox as a rapid prototyping tool — generate layouts, iterate on them in the editor, and save the ones you like directly to the project without leaving the app.
- **Multi-Document Upload:** Upload multiple contracts, invoices, or reports at once. Oculus indexes them all and can reason across the entire set in a single query.

---

## 🏗️ Architecture

```
Oculus AI
│
├── Flask              → Web server, routing, session-based auth, client workspaces
├── Actions Engine     → Intent classifier (Llama 3.3), execution wrapper, audit logs
├── RAG Pipeline       → PDF/DOCX extractors, semantic chunker, vector embeddings (OpenRouter)
├── OpenRouter API     → AI model gateway (OpenAI-compatible)
│   ├── Nemotron 3 Super 120B       → Primary (Default) — fast, cheap, unmoderated
│   ├── Llama 3.3 70B               → Fallback 1 — balanced, reliable
│   ├── Hermes 3 405B               → Fallback 2 — powerful, unmoderated
│   ├── Dolphin Mistral 24B         → Fallback 3 / Switcher — uncensored
│   └── Free Fallbacks              → (Nemotron 3, Llama 3.3, Hermes 3 405B)
├── Supabase Auth      → User registration, login, logout
├── Supabase DB        → Persistent memory (user-scoped), workspaces config, chat history (workspace-isolated), action log audit trail, document RAG vectors
├── Tavily Search      → Live web search injected into prompt context
└── Prompt Engine      → Injects memory, active workspace context, search results, and date/time into every request
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
pip install flask openai supabase tavily-python requests python-docx pypdf
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

### Supabase table setup

Run this script in your Supabase SQL editor:

```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

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

-- Document Metadata Table (Phase 2 & 3 RAG)
CREATE TABLE oculus_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  workspace_id UUID NOT NULL,
  filename TEXT NOT NULL,
  file_size INT NOT NULL,
  document_type TEXT DEFAULT 'other', -- 'contract', 'invoice', 'proposal', etc.
  summary TEXT,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX idx_oculus_documents_workspace ON oculus_documents(workspace_id);

-- Document Chunks Table (Phase 2 & 3 RAG)
CREATE TABLE oculus_document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES oculus_documents(id) ON DELETE CASCADE,
  workspace_id UUID NOT NULL,
  page_number INT,
  section_title TEXT,
  chunk_text TEXT NOT NULL,
  embedding vector(1536), -- 1536 dimensions for text-embedding-3-small
  fts tsvector, -- Full-text search vector
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX idx_chunks_workspace ON oculus_document_chunks(workspace_id);
CREATE INDEX idx_chunks_embedding ON oculus_document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_fts ON oculus_document_chunks USING gin(fts);

-- Automatically update fts vectors on chunk insert/update
CREATE OR REPLACE FUNCTION oculus_chunks_fts_trigger() RETURNS trigger AS $$
BEGIN
  new.fts := to_tsvector('english', coalesce(new.chunk_text, ''));
  RETURN new;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chunks_fts_update
  BEFORE INSERT OR UPDATE ON oculus_document_chunks
  FOR EACH ROW EXECUTE FUNCTION oculus_chunks_fts_trigger();

-- Stored procedure for vector similarity matching
CREATE OR REPLACE FUNCTION match_document_chunks (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  filter_workspace_id uuid
)
RETURNS TABLE (
  chunk_id uuid,
  document_id uuid,
  filename text,
  page_number int,
  section_title text,
  chunk_text text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id AS chunk_id,
    c.document_id,
    d.filename,
    c.page_number,
    c.section_title,
    c.chunk_text,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM oculus_document_chunks c
  JOIN oculus_documents d ON c.document_id = d.id
  WHERE c.workspace_id = filter_workspace_id
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Stored procedure for full-text search matching
CREATE OR REPLACE FUNCTION search_document_chunks_fts (
  query_text text,
  match_count int,
  filter_workspace_id uuid
)
RETURNS TABLE (
  chunk_id uuid,
  document_id uuid,
  filename text,
  page_number int,
  section_title text,
  chunk_text text,
  fts_rank float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id AS chunk_id,
    c.document_id,
    d.filename,
    c.page_number,
    c.section_title,
    c.chunk_text,
    ts_rank_cd(c.fts, plainto_tsquery('english', query_text)) AS fts_rank
  FROM oculus_document_chunks c
  JOIN oculus_documents d ON c.document_id = d.id
  WHERE c.workspace_id = filter_workspace_id
    AND c.fts @@ plainto_tsquery('english', query_text)
  ORDER BY fts_rank DESC
  LIMIT match_count;
END;
$$;
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
│   ├── extensions.py       # Initialises Supabase & Tavily API clients
│   ├── auth.py             # Auth routes, login/register/logout, @login_required decorator
│   ├── workspaces.py       # Workspaces API lifecycle (create, delete, list, switch)
│   ├── memory.py           # Memory DB read/write, LLM-based extraction and consolidation
│   ├── chat.py             # Home route, chat submission, clear, model switching
│   ├── files.py            # File upload handling, allowed types, prompt injection, sandbox download
│   ├── search.py           # Tavily query refinement and search trigger logic
│   ├── models.py           # OpenRouter streaming gateway and model fallback chain
│   ├── actions.py          # AI Actions Engine, classification prompts, execution wrappers
│   └── rag.py              # PDF/DOCX extractors, chunkers, embeds, hybrid rankers
├── templates/
│   ├── index.html          # Main chat interface (Jinja2)
│   ├── login.html          # Login page
│   └── register.html       # Registration page
├── workspaces/             # Local sandbox folders isolated per workspace ID (git-ignored)
└── static/
    ├── oculus.js           # Frontend — streaming, markdown render, code sandbox, sidebars, action cards
    ├── style.css           # Dark terminal theme, animations, badge states
    ├── oculus_logo.svg     # Full logo with wordmark
    ├── oculus_avatar.svg   # Avatar / chat bubble icon
    ├── manifest.json       # PWA manifest
    ├── sw.js               # Service worker — static asset caching
    └── favicon.ico         # Browser tab icon
```

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

<div align="center">

<img src="static/oculus_avatar.svg" alt="Oculus Avatar" width="64"/>

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
