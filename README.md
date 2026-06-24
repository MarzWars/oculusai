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

### 🚀 [Try it live → oculusai.onrender.com](https://oculusai.onrender.com/)

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
* **The Solution:** **Isolated Client Workspaces**. Oculus creates distinct digital sandboxes for every client project. Swapping a workspace switches the active chat history, file uploads, and directory files on the server, keeping Acme Corp's assets completely isolated from Lex Digitals' internals.

### 2. The "Forgetting" Problem
* **The Problem:** LLM chats have static context windows. If you tell an AI your styling rules, client emails, or task deadlines on Monday, it will forget them by Friday.
* **The Solution:** **Unified Long-Term Memory (Oculus Brain)**. A background pipeline reads conversations, extracts client profiles, preferences, and deadlines, and consolidates them in Supabase. This compiled "Brain" is injected into every chat request automatically, ensuring Oculus remembers everything that matters across sessions.

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

## 📖 Feature Usage Guide & Example Prompts

Here is a quick reference guide on how to trigger and use newly added workspace, document, and action automation features:

### 1. Unified Long-Term Memory (Oculus Brain)
Oculus automatically listens and extracts facts about your projects, preferences, and clients during normal conversation.
* **Extraction Trigger Prompt:** 
  > *"My name is Alex, I'm a developer at Lex Digitals and I prefer writing Python code with Flask."*
* **Client Context Prompt:**
  > *"Sarah is our main contact at Acme Digital Agency. Their website is acmedigital.com."*
* **Styling Preference Prompt:**
  > *"Always use Outfit fonts and a dark terminal aesthetic when writing CSS layouts."*
* **Manual Management:** Click the hamburger menu toggle button in the header to open the settings sidebar and scroll to **Oculus Brain**. Here you can edit your profile fields directly or manually delete preferences, deadlines, and clients.

### 2. Isolated Workspaces
Keep chats and sandbox directories segregated.
* **Switching:** Click the dropdown trigger label (e.g. *Personal Workspace*) in the header next to "Oculus AI". Select a workspace to switch to it.
* **Creating a Workspace:** Click "Create Workspace" from the selector, name it (e.g. *Acme Corp*), and Oculus will initialize a clean, isolated context.
* **Deleting a Workspace:** Click the trash icon next to a workspace. This cascades and deletes the workspace entry, isolated chats, cached attachments, and sandbox files on the server.

### 3. Scheduling Tasks & Deadlines
Schedule items in the DB by letting Oculus extract dates and names.
* **Trigger Prompt:** 
  > *"Add a task to review client mockups with Sarah by next Friday"*
* **Interactive Confirmation:** An action proposal card will render in the chat feed showing `Task Title` and `Due Date`. You can adjust these values inside the inputs.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ the task will be added to memory and display in your sidebar Brain panel.
* **Reversion / Deletion:** Click **Undo Action** on the confirmation card to revert. Alternatively, click the trash icon next to the task in your sidebar **Action Log** list to delete it at any time.

### 4. Compiling Proposals & Quotes
Compile formal document structures in the workspace sandbox.
* **Trigger Prompt:** 
  > *"Generate a proposal for Acme Corp for a website rebrand costing R 45,000. Under scope of work, list: UI wireframes, contact form script integration, and SEO setups."*
* **Interactive Confirmation:** Edit fields like client name, budget amount, and details scope directly on the card.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ Oculus compiles a formal `.docx` layout (using `python-docx`) and saves it to the sandbox.
* **Download:** A download link is generated as an elegant inline **Download DOCX** button inside the card. Click it to download the file directly to your system. You can also view/delete this action later from the sidebar **Action Log**.

### 5. Email Drafting & Previews
Draft emails and review them securely.
* **Trigger Prompt:** 
  > *"Draft a check-in email to sarah@acme.com about the rebrand scope approval"*
* **Interactive Confirmation:** A card displays the recipient, subject line, and a text area containing the full body text. Adjust the text as needed.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ Oculus writes a responsive, formatted HTML email container to the workspace sandbox directory. Click the generated inline **Preview HTML** button to open the compiled email in your browser.
* **SMTP Mode:** If you set the environment variable `ENABLE_SMTP_DELIVERY=true` and configure the SMTP host settings, Oculus will actively send the MIME formatted email to the recipient.
* **Action Log Sidebar Controls**: If you clear the chat before confirming or rejecting an action, it will appear in your sidebar **Action Log** as `PENDING`. You can click the checkmark button next to it to **Confirm & Execute** directly from the log, or click the cross button to **Reject & Cancel** it.

### 6. Interactive Live Code Sandbox
Design, test, and save website layouts directly.
* **Trigger Prompt:** 
  > *"Write a CSS/HTML landing page layout for our real estate client. Include a glassmorphic navbar and clean search fields."*
* **Previewing:** When the code block finishes rendering, a **Preview** button will appear in the header of the code block. Click it to open the Sandbox editor and live split-screen preview.
* **Editing & Saving:** Modify the code in the text editor and click **⚡ Run** (or press `Ctrl+Enter`) to refresh the preview. Type a filename in the path bar (e.g. `index.html`) and click **💾 Save to Project** to write the file directly to your workspace directory.

### 7. Advanced RAG & Document Intelligence
Upload documents for deep analysis, classification, and retrieval.
* **Opening Documents Sidebar:** Click the **Docs** button in the header. A right-aligned panel will slide into view.
* **Ingesting files:** Drag a `.pdf` or `.docx` file into the ingestion zone (`doc-upload-area`) or click to select files. The system parses, chunks, generates embeddings, and indexes the document in Supabase.
* **Document Metadata Card:** Ingested files display a colored semantic tag (e.g. `CONTRACT`, `INVOICE`, `RESUME`) based on automatic classification, alongside a 2-sentence summary and extracted keywords.
* **Retrieval & Citations Prompt:**
  > *"What are the retainer billing details mentioned in the Acme SLA contract?"*
  - Oculus retrieves matching chunks via hybrid search, formats citations in the response, and lists the source file.
* **Cross-Document Reasoning Prompt:**
  > *"Summarize all contracts and invoices we have in this workspace and list our active monthly retainer agreements."*
  - Oculus parses the overview metadata of all ingested documents to describe details, even if specific text chunks are not retrieved in search results.

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
