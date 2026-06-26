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
| 🔐 **Multi-User Auth & Security** | Register, login, and logout — each user's data is fully isolated in Supabase. Enforces strict backend workspace and action ownership checks to prevent cross-user data leakage. |
| 🧠 **Long-Term Memory** | Stores your profile, projects, clients, preferences, and key facts across sessions. A background LLM pipeline extracts, consolidates, and deconflicts information automatically. |
| 🧠 **Oculus Brain UI** | Dynamic sliding drawer panel with live view of your memory — edit profiles, add facts, manage projects, clients, and deadlines in real time, accessed from the vertical left dock. |
| ⚡ **AI Actions Engine** | Generates proposals, exports documents (DOCX, PDF, TXT), sends emails, schedules tasks, and logs workflow history. Uses low-temperature function extraction with OpenRouter to produce active proposals. Includes confirmation, cancellation, and deletion controls. |
| 📄 **Advanced RAG & Doc Intel** | Semantic search over PDFs and DOCX files. Ingests, chunks, embeds (via OpenRouter), and indexes documents in Supabase. Classifies documents, auto-summarizes them using OpenRouter, and supports hybrid (vector + full-text search) retrieval with RRF ranking and citations. |
| 🔄 **Real-Time Streaming** | Token-by-token streaming so responses appear word-by-word as the model generates. |
| 🔬 **Deep Self-Reflection** | A 2-pass metacognitive review pass checks drafts against memory, facts, and the Oculus persona. This thinking trace is buffered and completely hidden on the backend for a polished user experience. |
| 🌐 **Live Web Search** | Automatically pulls real-time information via Tavily Search when the query requires current data. |
| 💻 **Interactive Code Sandbox** | HTML, CSS, JavaScript, and SVG snippets open in a live split-screen iframe sandbox directly in the chat — edit, run, and preview without leaving the app. |
| 🗂️ **File Upload & Parsing** | Drag-and-drop or select plaintext and code files (.py, .js, .json, .css, etc.). Content is injected into the prompt automatically and cleared after each submit. |
| 🗺️ **Left Dock Layout** | Vertical navigation bar on the left providing instant access to Model selection, Workspace Settings, Oculus Brain, Style & Behavior Notes, Action Log, and Generated Documents. |
| ⚙️ **Manual Model Selection** | Pin any supported model via the Models dock panel (e.g. Nemotron 3 Super 120B, Llama 3.3 70B, Hermes 3 405B, Dolphin Mistral 24B). |
| 🔄 **Model Fallback Chain** | If the pinned model is rate-limited, returns an error, or times out, the system automatically tries the next model in the chain — no failed requests. |
| 🗂️ **Conversation History** | Keeps recent context in memory and auto-summarises older turns to stay within model context windows. |

---

## 🧠 Major Memory & Intelligence Upgrades (26 June 2026)

Oculus's core intelligence, long-term memory capabilities, and user style adaptation have been heavily upgraded. The memory system is now divided into three major architectural pillars implemented throughout June 2026:

### 1. Confidence Scoring & Quality Control (Phase 1)
* **Metadata-Rich Memory Schema**: Every memorized item (preferences, important facts, projects, deadlines, clients) now contains metadata attributes: `confidence` score (0.0 to 1.0), `source_type` (`conversation` or `user_explicit`), `last_reinforced` date, and extraction `reasoning` justification.
* **Badges & Tooltips**: The Oculus Brain UI renders confidence score badges (High, Medium, Low) for all items. Hovering over a badge reveals a tooltip explaining why Oculus extracted that fact, its source type, and the date it was reinforced.
* **Self-Conflict Resolution UI**: When you tell Oculus something that contradicts an existing memory item, a red **Resolve Memory Conflict** card appears at the top of the Brain drawer, allowing you to choose whether to keep the existing fact, use the new fact, or keep both.
* **Automatic Decay Auditing**: An active memory decay audit system reduces confidence by `-0.05` per week of inactivity, floored at `0.1`, forcing outdated facts to decay naturally unless reinforced.

### 2. Style & Behavior Notes (Phase 2)
* **AI Style Inference**: A background style analyzer reads your recent conversation logs every few turns (default 10, configurable) to infer formatting guidelines, tone preferences, vocabulary directives, and forbidden styles.
* **Categorized AI Notes**: Inferred observations are saved in the **Style & Behavior Notes** drawer, split into `"tone"`, `"formatting"`, `"vocabulary"`, `"client_specific"`, and `"forbidden"` rules.
* **Interactive Cooldown Widget**: After every 4 assistant responses, an interactive feedback widget ("Did this response match your style? (Yes/No)") renders at the bottom of the chat bubble.
  - Clicking **Yes** reinforces the notes (confidence $+0.05$).
  - Clicking **No** allows you to input an explicit correction, creating a high-confidence (`0.9`) `user_explicit` style rule.
* **Prefix Directives**: Prefixing prompts with `"Style preference:"` or `"style note:"` bypasses normal conversation flow and writes style rules directly to memory.

### 3. Superior Context Ranking & Conversation Intelligence (Phase 3)
* **Weighted Scored Context Ranking Engine**: When you query Oculus, memory items are ranked by a weighted scoring formula:
  $$\text{final\_score} = (\text{relevance} \times 0.45) + (\text{confidence} \times 0.25) + (\text{recency} \times 0.20) + (\text{importance} \times 0.10)$$
  Relevance is calculated using OpenAI's `text-embedding-3-small` vector embeddings to measure semantic similarity.
* **Sub-Millisecond Embedding Cache**: High-performance in-memory caching mapping strings to embedding vectors ensures zero API latency when loading memory.
* **Token Budget & Hashed LLM Summary Compression**: Memory context injected into chat is limited to a strict token budget (default `1500` tokens, configurable in settings). Low-priority facts are compressed into a single dense summary paragraph using a hashed LLM call that only triggers when facts change.
* **Memory Control Commands**: You can issue explicit instructions like *"forget everything about Vue"*, *"stop using formal tone"*, or *"pin Acme mockup deadline"* in conversation. Oculus intercepts these semantically, updates your memory database, and reloads the Brain UI instantly.
* **UI Pinning**: Click 📌 on any list item in the Brain or Notes panel to pin it, giving it maximum importance boost (`importance = 1.0` plus `+0.3` score boost).
* **Developer Debug Panel**: A collapsible panel at the bottom of the Brain drawer showing timestamp, query, estimated tokens, pruning status, score breakdown details for each memory item, and the final prompt block.

---

## 📖 User Guides & Prompts

For user guides and step-by-step feature walkthroughs (Features 1–9, Power User Tips, and the Prompt Testing scenarios), see the new guide document:

### 🔗 [Oculus How-To Manual & Prompt Testing Guide](file:///c:/Oculusai/oculusai/How%20To.md)

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
pip install flask openai supabase tavily-python requests python-docx pypdf docx2pdf reportlab
```

### Environment variables

Set these in your environment (or a local `.env` file):

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

* [app.py](file:///c:/Oculusai/oculusai/app.py) — Entry point: instantiates Flask, registers blueprints, runs server
* [config.py](file:///c:/Oculusai/oculusai/config.py) — Environment variables, model list, timeout settings
* [requirements.txt](file:///c:/Oculusai/oculusai/requirements.txt) — Python dependencies
* **`backend/`** — Core python blueprints:
  * [backend/\_\_init\_\_.py](file:///c:/Oculusai/oculusai/backend/__init__.py) — Exposes all Blueprints from the backend package
  * [backend/extensions.py](file:///c:/Oculusai/oculusai/backend/extensions.py) — Initialises Supabase & Tavily API clients
  * [backend/auth.py](file:///c:/Oculusai/oculusai/backend/auth.py) — Auth routes, login/register/logout, @login_required decorator
  * [backend/workspaces.py](file:///c:/Oculusai/oculusai/backend/workspaces.py) — Workspaces API lifecycle (create, delete, list, switch)
  * [backend/memory.py](file:///c:/Oculusai/oculusai/backend/memory.py) — Memory DB read/write, LLM-based extraction and consolidation
  * [backend/chat.py](file:///c:/Oculusai/oculusai/backend/chat.py) — Home route, chat submission, clear, model switching
  * [backend/files.py](file:///c:/Oculusai/oculusai/backend/files.py) — File upload handling, allowed types, prompt injection, sandbox download
  * [backend/search.py](file:///c:/Oculusai/oculusai/backend/search.py) — Tavily query refinement and search trigger logic
  * [backend/models.py](file:///c:/Oculusai/oculusai/backend/models.py) — OpenRouter streaming gateway and model fallback chain
  * [backend/actions.py](file:///c:/Oculusai/oculusai/backend/actions.py) — AI Actions Engine, classification prompts, execution wrappers
  * [backend/rag.py](file:///c:/Oculusai/oculusai/backend/rag.py) — PDF/DOCX extractors, chunkers, embeds, hybrid rankers
* **`templates/`** — HTML files:
  * [templates/index.html](file:///c:/Oculusai/oculusai/templates/index.html) — Main chat interface (Jinja2)
  * [templates/login.html](file:///c:/Oculusai/oculusai/templates/login.html) — Login page
  * [templates/register.html](file:///c:/Oculusai/oculusai/templates/register.html) — Registration page
* **`static/`** — Static front-end assets:
  * [static/oculus.js](file:///c:/Oculusai/oculusai/static/oculus.js) — Frontend routing, streaming, markdown render, code sandbox, drawers, action cards
  * [static/style.css](file:///c:/Oculusai/oculusai/static/style.css) — Dark terminal theme styling, animations, UI responsive rules, layout grids
  * [static/oculus_logo.svg](file:///c:/Oculusai/oculusai/static/oculus_logo.svg) — SVG logo with wordmark
  * [static/oculus_avatar.svg](file:///c:/Oculusai/oculusai/static/oculus_avatar.svg) — Avatar icon for chat bubbles
  * [static/manifest.json](file:///c:/Oculusai/oculusai/static/manifest.json) — Progressive Web App manifest
  * [static/sw.js](file:///c:/Oculusai/oculusai/static/sw.js) — Service worker for offline asset caching
* **`workspaces/`** — Local sandbox folders isolated per workspace ID (git-ignored)

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

### 🚀 [oculusai.lexdigitals.co.za](https://oculusai.lexdigitals.co.za/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
