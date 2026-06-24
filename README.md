<div align="center">

<img src="static/oculus_logo.svg" alt="Oculus AI Logo" width="300"/>

<br><br>

**A custom-built artificial intelligence system for real work.**  
Workspaces. Action Engine. Code. Copy. Memory. All in one.

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

Oculus is a custom AI assistant built for running a digital agency — not a generic chatbot wrapper. It is powered by **OpenRouter** (a gateway to multiple top LLMs) and layered with a unified cross-workspace memory system, isolated client workspaces, live web search, interactive sandbox code execution, and a newly implemented **AI Actions Engine** for workflow automation.

---

## ⚡ Key Upgrades

### 🏢 Client Workspaces
Switch between isolated client environments. Isolates:
* **Chat Logs:** Independent histories per workspace.
* **Sandbox Files:** Code saves write to `workspaces/<workspace_id>/`.
* **Uploaded Files:** Temporary attachments stay inside the selected context.
* **Memory Sync:** User profiles, preferences, client facts, style guides, and deadlines sync globally across all workspaces for the logged-in user, but Oculus targets facts and queries contextually.

### ⚙️ AI Actions Engine (v1)
An automated workflow runner that intercepts user intents, parses arguments using memory, and displays interactive **Action Cards** inside the chat feed. Every action must be verified and confirmed by the user before running, with full support to edit fields inline or trigger an **Undo** event.

* **Task Scheduling:** Saves deadlines directly into persistent user memory, updating the sidebar dashboard instantly.
* **Document Compilation (.docx):** Generates styled proposal templates containing summaries, deliverables scope, and tables. Documents are written to the workspace's sandbox folder with a secure download route.
* **Email Simulation:** Drafts responsive HTML emails with headers and body text, saving a preview file locally in the workspace (SMTP code is built and ready for activation).
* **Collapsible Action Log:** Collapsible audit trail in the settings sidebar detailing active, completed, cancelled, and undone operations.

---

## 📖 Feature Usage Guide

Here is how to use the core capabilities of Oculus AI using natural language prompts:

### 1. Unified Long-Term Memory
Oculus listens and extracts facts about your projects, preferences, and clients automatically during normal conversation.
* **Trigger Memory Extraction:** 
  > *"My name is Alex, I'm a developer at Lex Digitals and I prefer writing Python code with Flask."*
* **Add Clients:**
  > *"I work with Client Acme Digital Agency. They do real estate branding."*
* **Manage In Brain UI:** Open the settings panel (hamburger menu in the top left) to manually edit your profile, add styling preferences, facts, or deadlines.

### 2. Isolated Workspaces
Keep client boundaries distinct.
* **Switching Workspaces:** Click the dropdown in the header next to "Oculus AI" to swap between projects.
* **Creating a Workspace:** Click "Create Workspace" from the selector, name it, and Oculus will instantly create a clean context with empty chat history.
* **Deleting a Workspace:** Click the trash icon next to a workspace. This cascades and deletes the workspace entry, isolated chats, cached attachments, and sandbox files on the server.

### 3. Scheduling Tasks
Oculus extracts dates and titles to schedule deadlines.
* **Trigger Prompt:** 
  > *"Add a task to review client mockups by Friday"*
* **Interactive Confirmation:** A glassmorphic card will slide into view showing `Task Title` and `Due Date` fields. You can edit the text inside the inputs.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ the card shows a completion log and the deadline appears immediately in your sidebar brain panel.
* **Undo:** Click **Undo Action** to remove the task from memory instantly.

### 4. Compiling Proposals & Quotes
Generate professional documents directly in the workspace sandbox.
* **Trigger Prompt:** 
  > *"Generate a proposal for Acme Corp for a website rebrand costing R 45,000. Deliverables include UI mockups, contact forms, and SEO setup."*
* **Interactive Confirmation:** Edit fields like client name, budget amount, and details scope directly on the card.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ Oculus compiles a formal `.docx` layout (using `python-docx`) and saves it to the sandbox.
* **Download:** A download link is generated (`[proposals/proposal_Acme_Corp_timestamp.docx]`). Click to download the file directly to your system.

### 5. Email Drafting & Previews
Simulate email transmissions securely.
* **Trigger Prompt:** 
  > *"Draft a check-in email to john@example.com about project deadlines"*
* **Interactive Confirmation:** A card displays the recipient, subject line, and a text area containing the full body text. Adjust the text as needed.
* **Confirm:** Click **Confirm & Execute** $\rightarrow$ Oculus writes a responsive, formatted HTML email container to the workspace sandbox directory. Click the generated link to preview the compiled email in your browser.
* **SMTP Mode:** If you set the environment variable `ENABLE_SMTP_DELIVERY=true` and configure the SMTP host settings, Oculus will actively send the MIME formatted email to the recipient.

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

---

## 🧠 Database Schema

Ensure these tables are active in your Supabase SQL editor:

```sql
-- Per-user memory (shared globally across workspaces)
CREATE TABLE oculus_memory (
  user_id UUID PRIMARY KEY,
  memory  JSONB DEFAULT '{}'
);

-- Per-workspace chat history and summaries (workspace-isolated)
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

---

## 🚀 Setup & Run Locally

1. **Install Dependencies:**
   ```bash
   pip install flask openai supabase tavily-python requests python-docx
   ```

2. **Configure Environment Variables:**
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_secret_key
   SECRET_KEY=your_flask_session_secret
   TAVILY_API_KEY=your_tavily_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   
   # Optional SMTP credentials for email sending
   ENABLE_SMTP_DELIVERY=false # Set to true to activate smtplib sending
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

3. **Start Server:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your web browser.

---

<div align="center">

<img src="static/oculus_avatar.svg" alt="Oculus Avatar" width="64"/>

### 🚀 [oculusai.onrender.com](https://oculusai.onrender.com/)

<sub>Built with 🖤 by Alex · Lex Digitals</sub>

</div>
