# How to Use Oculus AI

**Complete Field Manual & User Guide**

This is the detailed guide for using Oculus!

# 📖 Oculus AI — User Guides & Prompt Testing Manual

Welcome to the Oculus AI User Guides and Prompt Testing Manual. This document provides step-by-step guides, example workflows, and prompt scenarios to help you test and utilize every capability of Oculus.

For technical documentation, including the project architecture, stack, deployment instructions, and database schemas, please refer to [README.md](file:///c:/Oculusai/oculusai/README.md).

---

## 📌 Table of Contents
1. [🎯 Prompt Testing Guide](#-prompt-testing-guide)
   - [1. Verification of Confidence & Quality Control](#1-verification-of-confidence--quality-control)
   - [2. Verification of Behavioral & Style Notes](#2-verification-of-behavioral--style-notes)
   - [3. Verification of Context Ranking & Memory Commands](#3-verification-of-context-ranking---memory-commands)
2. [📖 How to Use Oculus — Complete Guide](#-how-to-use-oculus--complete-guide)
   - [Feature 1: Long-Term Memory (Oculus Brain)](#-feature-1-long-term-memory-oculus-brain)
   - [Feature 2: Client Workspaces](#-feature-2-client-workspaces)
   - [Feature 3: AI Actions Engine](#-feature-3-ai-actions-engine)
     - [3a. Scheduling Tasks & Deadlines](#3a-scheduling-tasks--deadlines)
     - [3b. Proposals & Quotes](#3b-proposals--quotes)
     - [3c. Email Drafting & Previews](#3c-email-drafting--previews)
     - [3d. Document Generation & Export (On-Demand)](#3d-document-generation--export-on-demand)
   - [Feature 4: Interactive Live Code Sandbox](#-feature-4-interactive-live-code-sandbox)
   - [Feature 5: Document Intelligence & RAG](#-feature-5-document-intelligence--rag)
   - [Feature 6: Live Web Search](#-feature-6-live-web-search)
   - [Feature 7: Model Selection & Thinking Mode](#-feature-7-model-selection--thinking-mode)
   - [Feature 8: File Uploads (Code & Text Files)](#-feature-8-file-uploads-code--text-files)
   - [Feature 9: Action Log Sidebar](#-feature-9-action-log-sidebar)
3. [💡 Power User Tips](#-power-user-tips)

---

## 🎯 Prompt Testing Guide

Use the following prompts to verify that the core intelligence, memory, and style adaptation features are working correctly.

> [!NOTE]
> Ensure you have the **Oculus Brain** and **Style & Behavior Notes** drawers open (via the left dock) when running these tests to observe memory state updates in real-time.

### 1. Verification of Confidence & Quality Control
* **Save a Fact**:
  > *"I have a pet dog named Buster who is a Golden Retriever."*
  * **Verify**: Open the **Oculus Brain** panel. Confirm the fact appears under *Important Facts* with a confidence score badge. Hover over the badge to inspect the reasoning tooltip.
* **Trigger a Conflict**:
  > *"Actually, Buster is a Black Labrador, not a Golden Retriever."*
  * **Verify**: Open the **Oculus Brain** panel. A red card at the top will alert you to a conflict between the existing fact and the new fact. Click **Use New** or **Keep Both** to resolve it.

### 2. Verification of Behavioral & Style Notes
* **Explicit Style Training**:
  > *"Style preference: When writing copy for Lex Digitals, always use a professional, clear tone and never use exclamation marks."*
  * **Verify**: Open the **Style & Behavior Notes** panel. Check that the rule has been saved with **High** confidence, source `user_explicit`, and category `tone`.
* **Interactive Style Feedback Widget**:
  * Send 4 conversation messages (e.g. *"hello"*, *"how are you?"*, etc.).
  * **Verify**: On the 4th response, a widget will appear at the bottom of the chat bubble asking *"Did this response match your style?"*.
  * Click **No**, input *"write responses in lowercase only"* and click **Submit**. Check the notes panel to confirm a new `user_explicit` style rule has been committed.

### 3. Verification of Context Ranking & Memory Commands
* **Semantic Delete Command**:
  > *"Forget everything about my dog."*
  * **Verify**: Oculus will immediately reply with: `✓ I've forgotten...` listing the Buster facts. Check the Brain UI to verify they have been deleted.
* **Pinning Facts**:
  * Add a fact or preference to your brain.
  * Click the 📌 icon next to it. Confirm that it turns peach colored.
  * Send a message: *"Who are you?"*
  * Expand the **Toggle Context Ranking Debug Info** console at the bottom of the Brain panel. Confirm that the pinned item shows an importance of `1.0` and a score boost.
* **Adjusting Token Budget**:
  * Open the **Workspace Settings** panel.
  * Change the **Memory Token Budget** to `1000`. Switch workspaces and switch back to confirm the value is persisted.

---

## 📖 How to Use Oculus — Complete Guide

This section covers every major feature in detail. Think of this as a field manual — read it once and you will know exactly how to get full value out of the system.

---

### 🧠 Feature 1: Long-Term Memory (Oculus Brain)

Oculus remembers things so you do not have to repeat yourself. Every conversation is passively scanned in the background and key facts — names, preferences, clients, deadlines — are extracted and stored in your **Brain**. This Brain is injected into every future request, so Oculus always knows the full picture.

**Opening the Brain Panel:**  
Click the **Oculus Brain** button in the vertical Sidebar Dock on the left. The panel will slide out from the left showing your live memory card. You can edit profile fields directly, delete individual facts, and manage project/client entries in real time.

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

> [!TIP]
> You never need to explicitly say "remember this." Just mention information naturally in conversation and Oculus will pick it up. Close the chat, come back tomorrow, and Oculus will still know who you are and what you are working on.

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

#### 3d. Document Generation & Export (On-Demand)

Oculus can generate arbitrary documents in `.docx`, `.pdf`, or `.txt` formats on-demand. When you ask Oculus to generate or export a document, it extracts the content and creates a document generation action card.

**Example prompts:**

> *"Generate a DOCX containing our notes from today's meeting."*

> *"Export this strategy summary as a PDF file."*

> *"Give me the final copy of this ad block in .txt format so I can download it."*

> *"Save this project outline as a file I can download."*

**What happens:**
1. An action card appears in the chat with editable fields: **Filename**, **Format (DOCX, PDF, or TXT)**, **Document Title**, and **Document Content**.
2. Select the format or edit the title/content directly on the card.
3. Click **✅ Confirm & Execute** — Oculus generates the file:
   - **DOCX:** Generates a styled Microsoft Word document.
   - **TXT:** Saves a plain text file.
   - **PDF:** Generates a crimson-accented PDF document (utilizes `docx2pdf` on Windows if Word is installed, falling back gracefully to pure Python `reportlab` PDF rendering for cross-platform Linux support).
4. Click the download link generated on the card to download it.
5. All generated documents can be undone/removed via the **↩️ Undo Action** button or the settings Action Log.

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
Click the **Models** button in the vertical Sidebar Dock on the left → select from the model switcher list.

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
Click the **Action Log** button in the vertical Sidebar Dock on the left. The panel will slide out from the left showing all logged actions grouped by status: `PENDING`, `EXECUTED`, `CANCELLED`, `UNDONE`.

**What you can do in the Action Log:**
- **Confirm a pending action** that you missed in chat by clicking the **✅ checkmark** button next to it.
- **Reject a pending action** by clicking the **✗ cross** button.
- **Delete any action** permanently with the **🗑️ trash** icon.
- **Download compiled files** (proposals, email drafts) directly from the log entry.

> [!TIP]
> If you navigate away from the chat mid-conversation before confirming an action, it will remain in the Action Log as `PENDING`. You can always come back and execute it from the sidebar without losing any extracted parameters.

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
