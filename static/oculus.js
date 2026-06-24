// ─────────────────────────────────────────
// OCULUS AI — oculus.js  (single clean file)
// ─────────────────────────────────────────

// ── Load Highlight.js from CDN ───────────
(function loadHighlightJs() {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css';
  document.head.appendChild(link);

  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js';
  script.onload = () => {
    document.querySelectorAll('.code-block pre code').forEach(el => hljs.highlightElement(el));
  };
  document.head.appendChild(script);
})();

function highlight(codeEl) {
  if (window.hljs) hljs.highlightElement(codeEl);
}

// ── Avatar HTML helper ────────────────────
const AI_AVATAR = `
  <div class="avatar ai-avatar">
    <img src="/static/oculus_avatar.svg" width="20" height="20" alt="Oculus">
  </div>`;


// ── Escape HTML ───────────────────────────
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}


// ── Staged Thinking Progress helper ────────
function getStageHtml(thoughtText, isClosed) {
  let stage = 1;
  const len = thoughtText ? thoughtText.trim().length : 0;
  if (isClosed) {
    stage = 4;
  } else if (len >= 350) {
    stage = 3;
  } else if (len >= 120) {
    stage = 2;
  }

  const stageLabels = [
    { icon: "🔍", text: "Researching" },
    { icon: "🧠", text: "Analyzing memory" },
    { icon: "📝", text: "Planning response" },
    { icon: "✨", text: "Writing final answer" }
  ];

  let currentStatus = stageLabels[stage - 1].text + (isClosed ? "" : "...");

  let stagesMarkup = `
    <div class="thinking-stages">
      ${stageLabels.map((sl, idx) => {
    const stepNum = idx + 1;
    let stateClass = "pending";
    if (stepNum < stage) stateClass = "done";
    else if (stepNum === stage) stateClass = "active";
    return `
          <div class="stage-item ${stateClass}">
            <span class="stage-dot"></span>
            <span>${sl.icon} ${sl.text}</span>
          </div>
        `;
  }).join('')}
    </div>
  `;
  return { markup: stagesMarkup, statusText: currentStatus, stage: stage };
}


function renderMarkdown(text) {
  // ── Stopgap: catch raw-JSON-only responses from backend action system ──
  // If the entire response is bare JSON (no user-facing text), render a
  // readable action card instead of showing nothing or raw braces.
  const trimmed = text.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}') && trimmed.length > 2) {
    try {
      const obj = JSON.parse(trimmed);
      const actionType = obj.action_type || obj.type || null;
      if (actionType) {
        const args = JSON.stringify(obj.arguments || obj.params || {}, null, 2);
        return `<div class="action-card"><span class="action-card-icon">⚡</span><div class="action-card-body"><div class="action-card-title">${escapeHtml(actionType.replace(/_/g, ' '))}</div><pre class="action-card-args">${escapeHtml(args)}</pre></div></div>`;
      }
      if (Object.keys(obj).length === 0) {
        // Empty {} — model returned no action and no text. Show nothing graceful.
        return '<p class="text-faint" style="font-style:italic;color:var(--text-faint)">_(No response — try rephrasing your message.)_</p>';
      }
    } catch (e) { /* not valid JSON, fall through to normal markdown */ }
  }

  let html = text;
  let actionProposalData = null;
  const proposalIdx = html.indexOf('[[ACTION_PROPOSAL]]:');
  if (proposalIdx !== -1) {
    const rawProposal = html.substring(proposalIdx + 20).trim();
    html = html.substring(0, proposalIdx);
    try {
      actionProposalData = JSON.parse(rawProposal);
    } catch (e) {
      console.error("Failed to parse action proposal in renderMarkdown:", e);
    }
  }

  // 1. Protect fenced code blocks first
  const codeBlocks = [];
  html = html.replace(/```(\w+)?\n?([\s\S]*?)```/g, (_, lang, code) => {
    const language = (lang || '').trim();
    const label = language || 'code';
    const escaped = escapeHtml(code.trimEnd());
    const idx = codeBlocks.length;

    // Code block line numbers wrapping
    const lines = escaped.split('\n');
    const numberedCode = lines.map((line, lineIdx) => {
      return `<span class="code-line"><span class="line-num" data-num="${lineIdx + 1}"></span>${line || ' '}</span>`;
    }).join('\n');

    const isPreviewable = ['html', 'css', 'javascript', 'js', 'svg', 'xml'].includes(language.toLowerCase());
    const previewBtn = isPreviewable ? `
      <button class="preview-btn" onclick="openSandboxFromCodeBlock(this)" title="Preview in Sandbox" style="display:flex; align-items:center; gap:5px; background:transparent; border:1px solid var(--border); color:var(--text-muted); font-family:var(--font-sans); font-size:11.5px; padding:3px 9px; border-radius:5px; cursor:pointer; transition:all .15s;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px; height:12px; flex-shrink:0;">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
          <span class="preview-label">Preview</span>
      </button>` : '';

    codeBlocks.push(`
<div class="code-block">
  <div class="code-header">
    <span class="code-lang">${label}</span>
    <div style="display:flex; gap:6px;">
      ${previewBtn}
      <button class="copy-btn" onclick="copyCode(this)" title="Copy code">
        <svg class="icon-copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2"/>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
        <svg class="icon-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="display:none">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span class="copy-label">Copy</span>
      </button>
    </div>
  </div>
  <pre><code class="language-${language}">${numberedCode}</code></pre>
</div>`);
    return `%%CODE_BLOCK_${idx}%%`;
  });

  // Handle <think> and <thinking> blocks (different models use different tags)
  // Build a combined tag pattern: think|thinking
  const thinkTagPattern = 'think(?:ing)?';

  // 1. Closed thinking blocks — <think>…</think> or <thinking>…</thinking>
  html = html.replace(new RegExp(`<(?:${thinkTagPattern})>([\\s\\S]*?)</(?:${thinkTagPattern})>`, 'gi'), (_, thought) => {
    const { markup, statusText } = getStageHtml(thought, true);
    return `
<details class="thinking-block">
  <summary class="thinking-header">
    <span class="thinking-icon">🧠</span>
    <span class="thinking-title">Thought Process: ${statusText}</span>
  </summary>
  ${markup}
  <div class="thinking-content">${thought}</div>
</details>`;
  });

  // 2. Open/streaming thinking blocks — tag opened but not yet closed
  html = html.replace(new RegExp(`<(?:${thinkTagPattern})>([\\s\\S]*)$`, 'gi'), (_, thought) => {
    const { markup, statusText } = getStageHtml(thought, false);
    return `
<details class="thinking-block" open>
  <summary class="thinking-header">
    <span class="thinking-icon">🧠</span>
    <span class="thinking-title">Thought Process: ${statusText}</span>
  </summary>
  ${markup}
  <div class="thinking-content">${thought}</div>
</details>`;
  });

  // 1b. Protect details blocks
  const thinkingBlocks = [];

  // Protect completed details blocks
  html = html.replace(/<details class="thinking-block"([\s\S]*?)<\/details>/gi, (match) => {
    const idx = thinkingBlocks.length;
    thinkingBlocks.push(match);
    return `%%THINKING_BLOCK_${idx}%%`;
  });

  // Protect open/streaming details blocks
  html = html.replace(/<details class="thinking-block"([\s\S]*)$/gi, (match) => {
    const idx = thinkingBlocks.length;
    thinkingBlocks.push(match);
    return `%%THINKING_BLOCK_${idx}%%`;
  });

  // 2. Inline code
  html = html.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  // 3. Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // 4. Italic
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

  // 5. Links — [text](url) and bare https:// URLs
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+|\/[^\s\)]+)\)/g, (match, text, url) => {
    if (url.includes('/api/sandbox/download')) {
      const ext = url.split('.').pop().toLowerCase();
      let btnLabel = "Download File";
      if (ext.startsWith('docx')) btnLabel = "Download DOCX";
      else if (ext.startsWith('html')) btnLabel = "Preview HTML";

      return `<a href="${url}" class="sandbox-download-btn" target="_blank" rel="noopener noreferrer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13" style="margin-right:5px; flex-shrink:0; display:inline-block; vertical-align:middle;">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>${btnLabel}</span>
      </a>`;
    }
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`;
  });
  html = html.replace(/(?<!["\(])(https?:\/\/[^\s<>")\]]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

  // 5b. Images — ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\((https?:\/\/[^\)]+)\)/g,
    '<img src="$2" alt="$1" class="md-image" loading="lazy">');

  // 6. Headings
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // 7. Horizontal rule
  html = html.replace(/^---+$/gm, '<hr class="md-hr">');

  // 8. Tables
  html = renderTables(html);

  // 9. Bullet lists
  html = renderLists(html);

  // 10. Paragraphs
  html = renderParagraphs(html);

  // 11. Restore thinking blocks
  thinkingBlocks.forEach((block, idx) => {
    html = html.replace(`%%THINKING_BLOCK_${idx}%%`, () => block);
  });

  // 12. Restore code blocks
  codeBlocks.forEach((block, idx) => {
    html = html.replace(`%%CODE_BLOCK_${idx}%%`, () => block);
  });

  // Append Action Proposal Card if present
  if (actionProposalData) {
    html += renderActionCard(actionProposalData);
    setTimeout(() => {
      updateActionCardStatusFromServer(actionProposalData.action_id);
    }, 50);
  }

  return html;
}


function renderLists(html) {
  return html.replace(/((?:^- .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n').map(line =>
      `<li>${line.replace(/^- /, '').trim()}</li>`
    ).join('');
    return `<ul class="md-list">${items}</ul>`;
  });
}

function renderTables(html) {
  return html.replace(/((?:^\|.+\|\n?)+)/gm, (block) => {
    const rows = block.trim().split('\n').filter(r => r.trim());
    if (rows.length < 2) return block;
    let out = '<div class="md-table-wrap"><table class="md-table">';
    rows.forEach((row, i) => {
      if (/^\|[-| :]+\|$/.test(row.trim())) return;
      const cells = row.split('|').filter((_, j, a) => j > 0 && j < a.length - 1);
      const tag = i === 0 ? 'th' : 'td';
      out += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
    });
    return out + '</table></div>';
  });
}

function renderParagraphs(html) {
  return html.split(/\n{2,}/).map(block => {
    block = block.trim();
    if (!block) return '';
    if (/^<(div|ul|ol|h[1-6]|pre|table|hr|blockquote|details)/i.test(block) || /^%%THINKING_BLOCK_\d+%%/.test(block)) return block;
    return `<p>${block.replace(/\n/g, '<br>')}</p>`;
  }).join('');
}


// ── Copy button ───────────────────────────
function copyCode(btn) {
  const text = btn.closest('.code-block').querySelector('pre code').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const iconCopy = btn.querySelector('.icon-copy');
    const iconCheck = btn.querySelector('.icon-check');
    const label = btn.querySelector('.copy-label');
    iconCopy.style.display = 'none';
    iconCheck.style.display = 'block';
    label.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      iconCopy.style.display = 'block';
      iconCheck.style.display = 'none';
      label.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2000);
  });
}


// ── DOM helpers ───────────────────────────
function scrollToBottom() {
  const feed = document.getElementById('chatFeed');
  if (feed) feed.scrollTop = feed.scrollHeight;
}

function removeEmptyState() {
  const empty = document.querySelector('.empty-state');
  if (empty) empty.remove();
  if (!document.querySelector('.date-divider')) {
    const feed = document.getElementById('chatFeed');
    const div = document.createElement('div');
    div.className = 'date-divider';
    div.textContent = 'Today';
    feed.insertBefore(div, feed.firstChild);
  }
}

function appendUserBubble(text) {
  const feed = document.getElementById('chatFeed');
  const row = document.createElement('div');
  row.className = 'bubble-row user-row';
  row.innerHTML = `
    <div class="bubble user-bubble"><p>${escapeHtml(text)}</p></div>
    <div class="avatar user-avatar">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="8" r="4" fill="currentColor"/>
        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </div>`;
  feed.insertBefore(row, document.getElementById('typingIndicator'));
  scrollToBottom();
}

function showTyping() {
  const t = document.getElementById('typingIndicator');
  if (t) t.style.display = 'flex';
  scrollToBottom();
}

function hideTyping() {
  const t = document.getElementById('typingIndicator');
  if (t) t.style.display = 'none';
}

function insertAiBubble(rawText) {
  const feed = document.getElementById('chatFeed');
  const row = document.createElement('div');
  row.className = 'bubble-row ai-row';
  row.innerHTML = `
    ${AI_AVATAR}
    <div class="bubble ai-bubble rendered">${renderMarkdown(rawText)}</div>`;
  feed.insertBefore(row, document.getElementById('typingIndicator'));
  row.querySelectorAll('.code-block pre code').forEach(el => highlight(el));
  scrollToBottom();
}


// ── Live streaming renderer ───────────────
// Used DURING a stream: lightweight, no heavy markdown parsing.
// Splits text into thinking blocks + response, adds a blinking cursor.
function renderStreamingHtml(text) {
  let html = '';
  let remaining = text;

  const actionIdx = remaining.indexOf('[[ACTION_PROPOSAL]]:');
  if (actionIdx !== -1) {
    remaining = remaining.substring(0, actionIdx);
  }


  // Match both <think>...</think> and <thinking>...</thinking>
  const closedRe = /<(?:think|thinking)>([\s\S]*?)<\/(?:think|thinking)>/gi;
  const openRe = /<(?:think|thinking)>([\s\S]*)$/i;

  // 1. Closed (complete) thinking blocks
  const closedBlocks = [];
  remaining = remaining.replace(closedRe, (_, thought) => {
    closedBlocks.push(thought);
    return '';
  });
  for (const thought of closedBlocks) {
    const { markup, statusText } = getStageHtml(thought, true);
    html += `
<div class="thinking-block-streaming">
  ${markup}
  <details class="thinking-block">
    <summary class="thinking-header">
      <span class="thinking-icon">🧠</span>
      <span class="thinking-title">Raw Thoughts: ${statusText}</span>
    </summary>
    <div class="thinking-content">${escapeHtml(thought)}</div>
  </details>
</div>`;
  }

  // 2. Open (still streaming) thinking block
  const openMatch = remaining.match(openRe);
  if (openMatch) {
    const thought = openMatch[1];
    remaining = remaining.replace(openRe, '');
    const { markup, statusText } = getStageHtml(thought, false);
    html += `
<div class="thinking-block-streaming">
  ${markup}
  <details class="thinking-block" open>
    <summary class="thinking-header">
      <span class="thinking-icon">🧠</span>
      <span class="thinking-title">Raw Thoughts: ${statusText}</span>
    </summary>
    <div class="thinking-content">${escapeHtml(thought)}<span class="stream-cursor"></span></div>
  </details>
</div>`;
  }

  // 3. Main response text (everything outside thinking tags)
  const responseText = remaining
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  if (responseText || (!openMatch && !closedBlocks.length)) {
    html += `<span class="stream-response">${responseText}<span class="stream-cursor"></span></span>`;
  }

  return html;
}


// ── Send message ──────────────────────────
async function sendMessage() {
  const input = document.getElementById('msgInput');
  const sendBtn = document.querySelector('.send-btn');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';
  input.disabled = true;
  sendBtn.disabled = true;

  // Clear uploaded file chips from UI since they are sent with this message
  clearUploadedChipsUI();

  removeEmptyState();
  appendUserBubble(text);
  showTyping();

  // Create stream bubble placeholder
  const feed = document.getElementById('chatFeed');
  const row = document.createElement('div');
  row.className = 'bubble-row ai-row';
  row.style.display = 'none'; // hide until first chunk arrives
  row.innerHTML = `
    ${AI_AVATAR}
    <div class="bubble ai-bubble rendered"></div>`;
  feed.insertBefore(row, document.getElementById('typingIndicator'));
  const bubble = row.querySelector('.ai-bubble');

  try {
    const resp = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let accumulated = "";
    let hasShown = false;

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      if (value) {
        const chunk = decoder.decode(value, { stream: !done });
        accumulated += chunk;

        if (!hasShown && accumulated.trim()) {
          // Hide typing indicator, show the streaming bubble
          hideTyping();
          row.style.display = 'flex';
          hasShown = true;
        }

        // Live streaming render — lightweight, shows text as it arrives
        bubble.innerHTML = renderStreamingHtml(accumulated);
        scrollToBottom();
      }
    }

    // Stream finished
    if (!hasShown) {
      hideTyping();
      row.remove();
      insertAiBubble('_No response received from the model. Please try again._');
    } else {
      // Final pass: full markdown rendering now that we have the complete text
      bubble.innerHTML = renderMarkdown(accumulated);
      bubble.querySelectorAll('.code-block pre code').forEach(el => highlight(el));
      scrollToBottom();
    }

  } catch (err) {
    hideTyping();
    // Remove the unused streaming row if it wasn't shown
    if (!hasShown) {
      row.remove();
    }
    insertAiBubble(`**Error:** ${err.message}`);
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  }
}


// ── Left Sidebar ─────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('leftSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (!sidebar) return;

  const isOpen = sidebar.classList.contains('open');
  if (isOpen) {
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
  } else {
    sidebar.classList.add('open');
    overlay.classList.add('open');
    // Load brain when sidebar opens (if not already loaded)
    const brainContent = document.getElementById('brainDrawerContent');
    if (brainContent && brainContent.querySelector('.brain-loading')) {
      loadBrainIntoSidebar();
    }
  }
}

async function loadBrainIntoSidebar() {
  const content = document.getElementById('brainDrawerContent');
  if (!content) return;
  content.innerHTML = '<div class="brain-loading">Loading brain state…</div>';
  try {
    const resp = await fetch('/api/memory');
    if (!resp.ok) throw new Error('Failed to fetch memory');
    currentBrainMemory = await resp.json();
    renderBrainIntoEl(content, currentBrainMemory);
  } catch (err) {
    content.innerHTML = `<div class="brain-loading" style="color:var(--red)">Error: ${err.message}</div>`;
  }
}

// ── Model switcher (card-based) ───────────
async function setModel(modelId) {
  const pill = document.getElementById('activeModelPill');
  const nameEl = document.getElementById('activeModelName');

  // Optimistic UI — mark the card active immediately
  document.querySelectorAll('.model-card').forEach(c => {
    c.classList.toggle('active', c.dataset.modelId === modelId);
  });
  if (nameEl) nameEl.textContent = '…';

  try {
    const resp = await fetch('/set_model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: modelId }),
    });
    const data = await resp.json();
    if (data.status === 'ok') {
      if (nameEl) nameEl.textContent = data.name;
    } else {
      if (nameEl) nameEl.textContent = 'Error';
    }
  } catch (err) {
    if (nameEl) nameEl.textContent = 'Error';
  }
}


// ── Keyboard / chips / clear ──────────────
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function fillMsg(el) {
  const input = document.getElementById('msgInput');
  input.value = el.textContent.trim();
  input.focus();
}

async function clearChat() {
  try {
    await fetch('/clear', { method: 'POST' });
  } catch (e) { /* ignore */ }
  // Force a full network reload, bypassing any service worker cache
  location.href = location.pathname + '?_=' + Date.now();
}


// ── Init ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Fix any history bubbles loaded from server that still have the text O avatar
  document.querySelectorAll('.ai-avatar').forEach(avatar => {
    if (avatar.textContent.trim() === 'O') {
      avatar.innerHTML = '<img src="/static/oculus_avatar.svg" width="20" height="20" alt="Oculus">';
    }
  });

  // Re-render any history bubbles that came as plain text from server
  document.querySelectorAll('.ai-bubble:not(.rendered)').forEach(bubble => {
    bubble.innerHTML = renderMarkdown(bubble.innerText);
    bubble.classList.add('rendered');
    bubble.querySelectorAll('.code-block pre code').forEach(el => highlight(el));
  });

  const streamRow = document.getElementById('streamRow');
  if (streamRow) streamRow.style.display = 'none';

  scrollToBottom();
  const input = document.getElementById('msgInput');
  if (input) input.focus();

  // Load user workspaces
  loadWorkspaces();

  // Load workspace documents for the active workspace
  loadWorkspaceDocuments();

  // Initialize AI Action Engine hooks
  activateHistoricalProposals();
  loadActionHistoryLog();

  // Initialize drag & drop for documents panel upload zone
  const docUploadArea = document.getElementById('docUploadArea');
  if (docUploadArea) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      docUploadArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      docUploadArea.addEventListener(eventName, () => docUploadArea.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      docUploadArea.addEventListener(eventName, () => docUploadArea.classList.remove('dragover'), false);
    });

    docUploadArea.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        const docFiles = Array.from(files).filter(f => {
          const ext = f.name.split('.').pop().toLowerCase();
          return ext === 'pdf' || ext === 'docx';
        });
        if (docFiles.length > 0) {
          uploadDocFiles(docFiles);
        } else {
          alert("Only PDF and DOCX files are allowed in this document workspace.");
        }
      }
    }, false);
  }
});

// ── Auto-grow textarea ────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('msgInput');
  if (input) {
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = input.scrollHeight + 'px';
    });
  }
});


// ─────────────────────────────────────────
// 🧠 OCULUS BRAIN (MEMORY DASHBOARD) CONTROLLER
// ─────────────────────────────────────────
let currentBrainMemory = null;

// toggleBrain now opens the sidebar (backward compat)
async function toggleBrain() { toggleSidebar(); }

async function loadBrainMemory() { await loadBrainIntoSidebar(); }

function renderBrain(mem) {
  const content = document.getElementById('brainDrawerContent') || document.querySelector('.brain-drawer-content');
  if (!content) return;
  renderBrainIntoEl(content, mem);
}

function renderBrainIntoEl(content, mem) {

  const profile = mem.profile || {};
  const clients = mem.clients || [];
  const projects = mem.projects || [];
  const preferences = mem.preferences || [];
  const importantFacts = mem.important_facts || [];
  const deadlines = mem.deadlines || [];

  content.innerHTML = `
    <!-- PROFILE SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">User Profile</div>
      <div class="brain-profile-grid">
        <div class="brain-profile-field">
          <label>Name</label>
          <input type="text" id="bp-name" value="${escapeHtml(profile.name || '')}">
        </div>
        <div class="brain-profile-field">
          <label>Role</label>
          <input type="text" id="bp-role" value="${escapeHtml(profile.role || '')}">
        </div>
        <div class="brain-profile-field">
          <label>Company</label>
          <input type="text" id="bp-company" value="${escapeHtml(profile.company || '')}">
        </div>
        <div class="brain-profile-field">
          <label>Location</label>
          <input type="text" id="bp-location" value="${escapeHtml(profile.location || '')}">
        </div>
        <div class="brain-profile-field">
          <label>Email</label>
          <input type="email" id="bp-email" value="${escapeHtml(profile.email || '')}">
        </div>
        <div class="brain-profile-field">
          <label>Phone</label>
          <input type="text" id="bp-phone" value="${escapeHtml(profile.phone || '')}">
        </div>
        <button class="brain-save-btn" onclick="saveBrainProfile()">Save Profile</button>
      </div>
    </div>

    <!-- PREFERENCES SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">Preferences</div>
      <div class="brain-list" id="brain-prefs-list">
        ${renderBrainListItems("preferences", preferences)}
      </div>
      <div class="brain-add-form">
        <input type="text" class="brain-add-input" id="brain-pref-add-input" placeholder="Add preference...">
        <button class="brain-add-btn" onclick="addBrainListItem('preferences', 'brain-pref-add-input')">Add</button>
      </div>
    </div>

    <!-- IMPORTANT FACTS SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">Important Facts</div>
      <div class="brain-list" id="brain-facts-list">
        ${renderBrainListItems("important_facts", importantFacts)}
      </div>
      <div class="brain-add-form">
        <input type="text" class="brain-add-input" id="brain-fact-add-input" placeholder="Add fact...">
        <button class="brain-add-btn" onclick="addBrainListItem('important_facts', 'brain-fact-add-input')">Add</button>
      </div>
    </div>

    <!-- ACTIVE PROJECTS SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">Active Projects</div>
      <div class="brain-list" id="brain-projects-list">
        ${renderBrainProjectItems(projects)}
      </div>
      <div class="brain-add-form">
        <input type="text" class="brain-add-input" id="brain-project-add-input" placeholder="Add project name...">
        <button class="brain-add-btn" onclick="addBrainProject()">Add</button>
      </div>
    </div>

    <!-- DEADLINES SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">Upcoming Deadlines</div>
      <div class="brain-list" id="brain-deadlines-list">
        ${renderBrainDeadlineItems(deadlines)}
      </div>
      <div class="brain-add-form" style="flex-direction:column; gap:6px;">
        <div style="display:flex; gap:6px;">
          <input type="text" style="flex:2;" class="brain-add-input" id="brain-deadline-add-item" placeholder="Task name...">
          <input type="text" style="flex:1;" class="brain-add-input" id="brain-deadline-add-date" placeholder="Date (e.g. Friday)...">
        </div>
        <button class="brain-add-btn" style="width:100%" onclick="addBrainDeadline()">Add Deadline</button>
      </div>
    </div>

    <!-- CLIENTS SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">Known Clients</div>
      <div class="brain-list" id="brain-clients-list">
        ${renderBrainListItems("clients", clients)}
      </div>
      <div class="brain-add-form">
        <input type="text" class="brain-add-input" id="brain-client-add-input" placeholder="Add client name...">
        <button class="brain-add-btn" onclick="addBrainListItem('clients', 'brain-client-add-input')">Add</button>
      </div>
    </div>

    <!-- AI BEHAVIORAL INFERENCES SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">🧠 Style & Behavior Notes</div>
      <div class="brain-list" id="brain-notes-list">
        ${renderBrainNotesItems(mem.ai_notes || [])}
      </div>
      <div class="brain-add-form">
        <input type="text" class="brain-add-input" id="brain-note-add-input" placeholder="Add custom behavior note...">
        <button class="brain-add-btn" onclick="addBrainListItem('ai_notes', 'brain-note-add-input')">Add</button>
      </div>
    </div>
  `;
}

function renderBrainListItems(key, lst) {
  if (!lst || lst.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return lst.map(item => `
    <div class="brain-list-item">
      <span class="brain-list-text">${escapeHtml(item)}</span>
      <button class="brain-delete-btn" onclick="deleteBrainListItem('${key}', \`${escapeHtml(item).replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete item">×</button>
    </div>
  `).join('');
}

function renderBrainNotesItems(lst) {
  if (!lst || lst.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return lst.map(item => `
    <div class="brain-notes-card">
      <span class="brain-list-text">${escapeHtml(item)}</span>
      <button class="brain-delete-btn" onclick="deleteBrainListItem('ai_notes', \`${escapeHtml(item).replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete behavioral note">×</button>
    </div>
  `).join('');
}

function renderBrainProjectItems(projects) {
  if (!projects || projects.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return projects.map(proj => `
    <div class="brain-list-item">
      <div class="brain-deadline-info">
        <span class="brain-list-text" style="color:var(--text); font-weight:500;">${escapeHtml(proj.name || '')}</span>
        <span>Added: ${escapeHtml(proj.added || '')}</span>
      </div>
      <button class="brain-delete-btn" onclick="deleteBrainProject(\`${escapeHtml(proj.name).replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete project">×</button>
    </div>
  `).join('');
}

function renderBrainDeadlineItems(deadlines) {
  if (!deadlines || deadlines.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return deadlines.map(dl => `
    <div class="brain-list-item">
      <div class="brain-deadline-info">
        <span class="brain-list-text" style="color:var(--text); font-weight:500;">${escapeHtml(dl.item || '')}</span>
        <span style="color:var(--purple); font-weight:500;">Due: ${escapeHtml(dl.date || '')}</span>
      </div>
      <button class="brain-delete-btn" onclick="deleteBrainDeadline(\`${escapeHtml(dl.item).replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete deadline">×</button>
    </div>
  `).join('');
}

async function saveBrainProfile() {
  const fields = ["name", "role", "company", "location", "email", "phone"];
  let updatedCount = 0;

  for (const field of fields) {
    const el = document.getElementById(`bp-${field}`);
    if (!el) continue;

    const newVal = el.value.trim();
    const oldVal = (currentBrainMemory.profile || {})[field] || "";

    if (newVal !== oldVal) {
      try {
        const resp = await fetch('/api/memory/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: "profile",
            field: field,
            value: newVal
          })
        });
        if (resp.ok) updatedCount++;
      } catch (err) {
        console.error(`Failed to update field ${field}:`, err);
      }
    }
  }

  if (updatedCount > 0) {
    alert("Profile saved successfully!");
    await loadBrainMemory();
  }
}

async function addBrainListItem(key, inputId) {
  const el = document.getElementById(inputId);
  if (!el) return;
  const val = el.value.trim();
  if (!val) return;

  try {
    const resp = await fetch('/api/memory/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: "list",
        key: key,
        value: val
      })
    });
    if (resp.ok) {
      el.value = '';
      await loadBrainMemory();
    } else {
      const errData = await resp.json();
      alert(errData.error || "Failed to add item.");
    }
  } catch (err) {
    alert("Error updating memory: " + err.message);
  }
}

async function deleteBrainListItem(key, value) {
  try {
    const resp = await fetch('/api/memory/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        key: key,
        value: value
      })
    });
    if (resp.ok) {
      await loadBrainMemory();
    }
  } catch (err) {
    console.error("Failed to delete memory item:", err);
  }
}

async function addBrainProject() {
  const el = document.getElementById('brain-project-add-input');
  if (!el) return;
  const val = el.value.trim();
  if (!val) return;

  try {
    const resp = await fetch('/api/memory/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: "project",
        name: val
      })
    });
    if (resp.ok) {
      el.value = '';
      await loadBrainMemory();
    }
  } catch (err) {
    console.error("Failed to add project:", err);
  }
}

async function deleteBrainProject(name) {
  try {
    const resp = await fetch('/api/memory/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        key: "projects",
        name: name
      })
    });
    if (resp.ok) {
      await loadBrainMemory();
    }
  } catch (err) {
    console.error("Failed to delete project:", err);
  }
}

async function addBrainDeadline() {
  const elItem = document.getElementById('brain-deadline-add-item');
  const elDate = document.getElementById('brain-deadline-add-date');
  if (!elItem || !elDate) return;
  const item = elItem.value.trim();
  const date = elDate.value.trim();
  if (!item || !date) return;

  try {
    const resp = await fetch('/api/memory/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: "deadline",
        item: item,
        date: date
      })
    });
    if (resp.ok) {
      elItem.value = '';
      elDate.value = '';
      await loadBrainMemory();
    }
  } catch (err) {
    console.error("Failed to add deadline:", err);
  }
}

async function deleteBrainDeadline(item) {
  try {
    const resp = await fetch('/api/memory/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        key: "deadlines",
        item: item
      })
    });
    if (resp.ok) {
      await loadBrainMemory();
    }
  } catch (err) {
    console.error("Failed to delete deadline:", err);
  }
}

// ─────────────────────────────────────────
// FILE ATTACHMENTS & DRAG-AND-DROP UPLOAD
// ─────────────────────────────────────────

function triggerFileSelect() {
  const input = document.getElementById('fileInput');
  if (input) input.click();
}

function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length) {
    uploadFiles(files);
  }
}

async function uploadFiles(files) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  try {
    const resp = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await resp.json();
    if (resp.ok || data.status === 'partial') {
      renderUploadedChips(data.files);
      
      let msg = "";
      if (data.rag_ingested && data.rag_ingested.length) {
        msg += "Successfully ingested to Workspace Knowledge:\n" + data.rag_ingested.join("\n") + "\n\n";
      }
      if (data.errors && data.errors.length) {
        msg += "Upload warning:\n" + data.errors.join("\n");
      }
      if (msg) {
        alert(msg);
      }
    } else {
      alert("Upload failed: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    console.error("Error uploading files:", err);
    alert("Upload failed: Network or connection error.");
  }
}

function renderUploadedChips(files) {
  const container = document.getElementById('uploadChipsContainer');
  if (!container) return;

  if (!files || files.length === 0) {
    container.innerHTML = '';
    container.style.display = 'none';
    return;
  }

  container.innerHTML = files.map(file => {
    // Label warning for files larger than 500KB (512,000 bytes)
    const isLarge = file.size > 512000;
    const warningClass = isLarge ? 'warning' : '';
    const displaySize = (file.size / 1024).toFixed(1) + ' KB';
    const warningTitle = isLarge ? 'title="Large file - may consume substantial context limit"' : '';

    return `
      <div class="upload-chip ${warningClass}" ${warningTitle}>
        <span class="chip-icon">📄</span>
        <span class="chip-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
        <span class="chip-size">(${displaySize})</span>
        <span class="chip-delete" onclick="deleteUploadedFile('${escapeHtml(file.name)}')">×</span>
      </div>
    `;
  }).join('');

  container.style.display = 'flex';
}

async function deleteUploadedFile(filename) {
  try {
    const resp = await fetch('/api/upload/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: filename })
    });
    const data = await resp.json();
    if (resp.ok) {
      renderUploadedChips(data.files);
    }
  } catch (err) {
    console.error("Error deleting file:", err);
  }
}

function clearUploadedChipsUI() {
  const container = document.getElementById('uploadChipsContainer');
  if (container) {
    container.innerHTML = '';
    container.style.display = 'none';
  }
  const fileInput = document.getElementById('fileInput');
  if (fileInput) fileInput.value = '';
}

// Window drag-and-drop listener setup
window.addEventListener('dragenter', (e) => {
  e.preventDefault();
  const overlay = document.getElementById('dragOverlay');
  if (overlay) overlay.classList.add('active');
});

window.addEventListener('dragover', (e) => {
  e.preventDefault();
});

window.addEventListener('dragleave', (e) => {
  // Only deactivate if dragged out of browser viewport bounds
  if (e.clientX === 0 && e.clientY === 0) {
    const overlay = document.getElementById('dragOverlay');
    if (overlay) overlay.classList.remove('active');
  }
});

window.addEventListener('drop', (e) => {
  e.preventDefault();
  const overlay = document.getElementById('dragOverlay');
  if (overlay) overlay.classList.remove('active');

  if (e.dataTransfer && e.dataTransfer.files.length) {
    uploadFiles(e.dataTransfer.files);
  }
});

// ── Interactive Sandbox Controllers ───────

function openSandboxFromCodeBlock(btn) {
  const codeBlock = btn.closest('.code-block');
  const codeElement = codeBlock.querySelector('pre code');
  const rawCode = codeElement.textContent;

  const langClass = Array.from(codeElement.classList).find(c => c.startsWith('language-'));
  const lang = langClass ? langClass.replace('language-', '') : 'html';

  openSandbox(rawCode, lang);
}

function openSandbox(code, language) {
  const overlay = document.getElementById('sandboxOverlay');
  const editor = document.getElementById('sandboxEditor');
  const badge = document.getElementById('sandboxLangBadge');
  const pathInput = document.getElementById('sandboxSavePath');

  if (!overlay || !editor) return;

  badge.textContent = language;
  editor.value = code;

  let ext = 'html';
  const l = language.toLowerCase();
  if (l === 'javascript' || l === 'js') ext = 'js';
  else if (l === 'css') ext = 'css';
  else if (l === 'svg') ext = 'svg';
  else if (l === 'xml') ext = 'xml';
  pathInput.value = `sandbox_file.${ext}`;

  overlay.classList.add('open');
  syncSandboxLineNumbers();
  runSandbox();
}

function closeSandbox() {
  const overlay = document.getElementById('sandboxOverlay');
  if (overlay) overlay.classList.remove('open');
}

function runSandbox() {
  const editor = document.getElementById('sandboxEditor');
  const badge = document.getElementById('sandboxLangBadge');
  const iframe = document.getElementById('sandboxPreview');
  if (!editor || !iframe) return;

  const code = editor.value;
  const lang = badge.textContent.toLowerCase();

  let src = "";
  if (lang === 'html') {
    if (!code.includes('<html') && !code.includes('<body')) {
      src = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; padding: 20px; color: #111; background: #fff; }
  </style>
</head>
<body>
  ${code}
</body>
</html>`;
    } else {
      let htmlCode = code;
      if (!htmlCode.includes('tailwindcss.com')) {
        if (htmlCode.includes('</head>')) {
          htmlCode = htmlCode.replace('</head>', '<script src="https://cdn.tailwindcss.com"></script></head>');
        } else {
          htmlCode = '<script src="https://cdn.tailwindcss.com"></script>' + htmlCode;
        }
      }
      src = htmlCode;
    }
  } else if (lang === 'svg' || lang === 'xml') {
    src = `<!DOCTYPE html>
<html>
<head>
  <style>
    body { display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f0f0f3; }
    svg { max-width: 90vw; max-height: 90vh; }
  </style>
</head>
<body>
  ${code}
</body>
</html>`;
  } else if (lang === 'css') {
    src = `<!DOCTYPE html>
<html>
<head>
  <style>${code}</style>
</head>
<body>
  <div style="padding: 20px; font-family:system-ui, sans-serif;">
    <h1>CSS Preview Pane</h1>
    <p>Your styles have been injected and applied successfully.</p>
    <hr style="border:none; border-top:1px solid #ccc; margin:16px 0;">
    <button style="padding: 8px 12px; border-radius: 4px; border: 1px solid #ccc; background: #f9f9f9; cursor:pointer;">Sample Button</button>
  </div>
</body>
</html>`;
  } else if (lang === 'javascript' || lang === 'js') {
    src = `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: monospace; padding: 20px; background: #121214; color: #a9b7c6; }
    #console { white-space: pre-wrap; font-size: 13px; line-height: 1.5; }
  </style>
  <script>
    window.console = {
      log: function(...args) {
        const div = document.getElementById('console');
        if (div) {
          div.textContent += args.map(a => typeof a === 'object' ? JSON.stringify(a, null, 2) : a).join(' ') + '\\n';
        }
      },
      error: function(...args) {
        const div = document.getElementById('console');
        if (div) {
          div.innerHTML += '<span style="color:#f38ba8;">Error: ' + args.join(' ') + '</span>\\n';
        }
      }
    };
  </script>
</head>
<body>
  <h3 style="margin-top:0; color:#7c6af7;">JavaScript Execution Output:</h3>
  <div id="console"></div>
  <script>
    try {
      ${code}
    } catch(err) {
      console.error(err.message);
    }
  </script>
</body>
</html>`;
  } else {
    src = `<!DOCTYPE html><html><body><pre>${escapeHtml(code)}</pre></body></html>`;
  }

  iframe.srcdoc = src;
}

function copySandboxCode() {
  const editor = document.getElementById('sandboxEditor');
  if (!editor) return;
  navigator.clipboard.writeText(editor.value).then(() => {
    alert("Code copied to clipboard!");
  });
}

async function saveSandboxToProject() {
  const editor = document.getElementById('sandboxEditor');
  const pathInput = document.getElementById('sandboxSavePath');
  if (!editor || !pathInput) return;

  const content = editor.value;
  const filename = pathInput.value.trim();
  if (!filename) {
    alert("Filename is required.");
    return;
  }

  try {
    const resp = await fetch('/api/sandbox/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, content })
    });
    const data = await resp.json();
    if (resp.ok) {
      alert(`File successfully saved to workspace: ${data.path}`);
    } else {
      alert(`Error saving file: ${data.error}`);
    }
  } catch (err) {
    alert(`Failed to save file: ${err.message}`);
  }
}

function handleSandboxKeys(event) {
  const textarea = event.target;
  if (event.key === 'Tab') {
    event.preventDefault();
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    textarea.value = textarea.value.substring(0, start) + "  " + textarea.value.substring(end);
    textarea.selectionStart = textarea.selectionEnd = start + 2;
    syncSandboxLineNumbers();
  } else if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    runSandbox();
  }
}

function syncSandboxLineNumbers() {
  const textarea = document.getElementById('sandboxEditor');
  const lineNumbers = document.getElementById('sandboxEditorLines');
  if (!textarea || !lineNumbers) return;

  const lines = textarea.value.split('\n');
  const lineCount = lines.length;

  let markup = '';
  for (let i = 1; i <= lineCount; i++) {
    markup += `<div>${i}</div>`;
  }
  lineNumbers.innerHTML = markup;
  lineNumbers.scrollTop = textarea.scrollTop;
}

// ── Service worker registration & Scroll Sync ──────────
document.addEventListener('DOMContentLoaded', () => {
  const textarea = document.getElementById('sandboxEditor');
  const lineNumbers = document.getElementById('sandboxEditorLines');
  if (textarea && lineNumbers) {
    textarea.addEventListener('scroll', () => {
      lineNumbers.scrollTop = textarea.scrollTop;
    });
  }

  // Load Workspaces
  loadWorkspaces();

  // Register service worker for PWA caching support
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(reg => {
      console.log('ServiceWorker registration successful');
    }).catch(err => {
      console.warn('ServiceWorker registration failed: ', err);
    });
  }
});

// ── Global Keyboard Shortcuts ─────────────
window.addEventListener('keydown', (e) => {
  // Ctrl + B toggles brain
  if (e.key === 'b' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    toggleBrain();
  }
  // Esc closes sandbox or brain drawer
  if (e.key === 'Escape') {
    closeSandbox();
    const drawer = document.getElementById('brainDrawer');
    if (drawer && drawer.classList.contains('open')) {
      toggleBrain();
    }
  }
});

// ─────────────────────────────────────────
// 🏢 CLIENT WORKSPACES CONTROLLER
// ─────────────────────────────────────────
let userWorkspaces = [];
let activeWorkspaceId = null;

// Toggle workspace dropdown menu
function toggleWorkspaceDropdown(event) {
  if (event) event.stopPropagation();
  const dropdown = document.getElementById('workspaceDropdown');
  if (!dropdown) return;
  dropdown.classList.toggle('open');
}

// Close dropdown on clicking outside
document.addEventListener('click', (e) => {
  const dropdown = document.getElementById('workspaceDropdown');
  const trigger = document.getElementById('workspaceTrigger');
  if (dropdown && dropdown.classList.contains('open')) {
    if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
      dropdown.classList.remove('open');
    }
  }
});

// Load workspaces from backend
async function loadWorkspaces() {
  try {
    const resp = await fetch('/api/workspaces');
    if (!resp.ok) throw new Error('Failed to fetch workspaces');
    const data = await resp.json();
    userWorkspaces = data.workspaces;
    activeWorkspaceId = data.current_workspace_id;

    // Update the trigger label
    const activeWs = userWorkspaces.find(w => w.id === activeWorkspaceId);
    const nameEl = document.getElementById('currentWorkspaceName');
    if (nameEl && activeWs) {
      nameEl.textContent = activeWs.name;
    }

    // Render the dropdown list
    renderWorkspacesList();
  } catch (err) {
    console.error('[Workspaces] Error loading:', err);
  }
}

// Render the list of workspaces inside the dropdown
function renderWorkspacesList() {
  const listEl = document.getElementById('workspaceList');
  if (!listEl) return;

  if (userWorkspaces.length === 0) {
    listEl.innerHTML = '<div class="workspace-empty">No workspaces found</div>';
    return;
  }

  listEl.innerHTML = userWorkspaces.map(ws => {
    const isActive = ws.id === activeWorkspaceId;
    const activeClass = isActive ? 'active' : '';
    // Backwards compatibility check: default workspace (id == user_id) cannot be deleted.
    const isDefault = ws.id === ws.user_id;
    const deleteBtn = isDefault ? '' : `
      <button class="ws-delete-btn" onclick="confirmDeleteWorkspace(event, '${ws.id}', \`${escapeHtml(ws.name).replace(/'/g, "\\'")}\`)" title="Delete workspace">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    `;

    return `
      <div class="workspace-item ${activeClass}" onclick="switchWorkspace('${ws.id}')">
        <div class="workspace-item-content">
          <span class="workspace-item-dot"></span>
          <span class="workspace-item-name" title="${escapeHtml(ws.name)}">${escapeHtml(ws.name)}</span>
        </div>
        ${deleteBtn}
      </div>
    `;
  }).join('');
}

// Switch active workspace
async function switchWorkspace(workspaceId) {
  if (workspaceId === activeWorkspaceId) return;

  try {
    const resp = await fetch('/api/workspaces/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId })
    });
    if (resp.ok) {
      // Force a full reload to reload memory, chat history, elements, etc.
      location.href = location.pathname + '?_ws=' + Date.now();
    } else {
      const err = await resp.json();
      alert(err.error || 'Failed to switch workspace.');
    }
  } catch (err) {
    alert('Error switching workspace: ' + err.message);
  }
}

// Show Create Workspace Modal
function showCreateWorkspaceModal(event) {
  if (event) event.stopPropagation();
  // Close dropdown first
  const dropdown = document.getElementById('workspaceDropdown');
  if (dropdown) dropdown.classList.remove('open');

  const modal = document.getElementById('workspaceModalOverlay');
  const input = document.getElementById('newWorkspaceName');
  if (modal) {
    modal.classList.add('open');
    if (input) {
      input.value = '';
      setTimeout(() => input.focus(), 150);
    }
  }
}

// Hide Create Workspace Modal
function hideCreateWorkspaceModal() {
  const modal = document.getElementById('workspaceModalOverlay');
  if (modal) modal.classList.remove('open');
}

// Create Workspace Call
async function createWorkspace() {
  const input = document.getElementById('newWorkspaceName');
  if (!input) return;
  const name = input.value.trim();
  if (!name) {
    alert('Workspace name is required.');
    return;
  }

  try {
    const resp = await fetch('/api/workspaces/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const data = await resp.json();
    if (resp.ok) {
      hideCreateWorkspaceModal();
      // Reload page to enter new workspace
      location.href = location.pathname + '?_ws=' + Date.now();
    } else {
      alert(data.error || 'Failed to create workspace.');
    }
  } catch (err) {
    alert('Error creating workspace: ' + err.message);
  }
}

// Confirm delete workspace
function confirmDeleteWorkspace(event, id, name) {
  if (event) event.stopPropagation();

  const modal = document.getElementById('deleteWorkspaceModalOverlay');
  const nameSpan = document.getElementById('deleteWorkspaceNameSpan');
  const idInput = document.getElementById('deleteWorkspaceIdInput');

  if (modal) {
    if (nameSpan) nameSpan.textContent = name;
    if (idInput) idInput.value = id;
    modal.classList.add('open');
  }
}

// Hide Delete Workspace Modal
function hideDeleteWorkspaceModal() {
  const modal = document.getElementById('deleteWorkspaceModalOverlay');
  if (modal) modal.classList.remove('open');
}

// Delete Workspace Call
async function deleteWorkspace() {
  const idInput = document.getElementById('deleteWorkspaceIdInput');
  if (!idInput) return;
  const workspaceId = idInput.value;

  try {
    const resp = await fetch('/api/workspaces/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId })
    });
    const data = await resp.json();
    if (resp.ok) {
      hideDeleteWorkspaceModal();
      // Reload page (will switch to default workspace or new active one)
      location.href = location.pathname + '?_ws=' + Date.now();
    } else {
      alert(data.error || 'Failed to delete workspace.');
    }
  } catch (err) {
    alert('Error deleting workspace: ' + err.message);
  }
}

// ─────────────────────────────────────────
// ⚡ AI ACTIONS ENGINE CLIENT CONTROLLERS
// ─────────────────────────────────────────

// Render Glassmorphic Action Proposal Card
function renderActionCard(data) {
  const actionId = data.action_id;
  const type = data.action_type;
  const args = data.arguments || {};

  let icon = "⚡";
  let title = "Proposed Action";
  let accentClass = "action-card-generic";
  let formFields = "";

  if (type === "create_task") {
    icon = "📅";
    title = "Create Task / Deadline";
    accentClass = "action-card-task";
    formFields = `
      <div class="action-field">
        <label>Task Title</label>
        <input type="text" data-key="title" value="${escapeHtml(args.title || '')}">
      </div>
      <div class="action-field">
        <label>Due Date</label>
        <input type="text" data-key="due_date" value="${escapeHtml(args.due_date || '')}">
      </div>
    `;
  } else if (type === "generate_proposal") {
    icon = "📝";
    title = "Generate Proposal / Quote";
    accentClass = "action-card-proposal";
    formFields = `
      <div class="action-field">
        <label>Client Name</label>
        <input type="text" data-key="client_name" value="${escapeHtml(args.client_name || '')}">
      </div>
      <div class="action-field">
        <label>Proposal Title</label>
        <input type="text" data-key="proposal_title" value="${escapeHtml(args.proposal_title || '')}">
      </div>
      <div class="action-field">
        <label>Estimated Amount</label>
        <input type="text" data-key="amount" value="${escapeHtml(args.amount || '')}">
      </div>
      <div class="action-field">
        <label>Scope of Work Details</label>
        <textarea data-key="details" rows="3">${escapeHtml(args.details || '')}</textarea>
      </div>
    `;
  } else if (type === "send_email") {
    icon = "✉️";
    title = "Draft & Send Email";
    accentClass = "action-card-email";
    formFields = `
      <div class="action-field">
        <label>Recipient (Email or Name)</label>
        <input type="text" data-key="to" value="${escapeHtml(args.to || '')}">
      </div>
      <div class="action-field">
        <label>Subject</label>
        <input type="text" data-key="subject" value="${escapeHtml(args.subject || '')}">
      </div>
      <div class="action-field">
        <label>Email Body</label>
        <textarea data-key="body" rows="4">${escapeHtml(args.body || '')}</textarea>
      </div>
    `;
  }

  return `
    <div class="action-proposal-card ${accentClass}" id="action-card-${actionId}" data-action-id="${actionId}" data-action-type="${type}">
      <div class="action-card-header">
        <span class="action-card-icon">${icon}</span>
        <strong>${title}</strong>
      </div>
      <div class="action-card-body">
        ${formFields}
      </div>
      <div class="action-card-status" id="action-status-${actionId}"></div>
      <div class="action-card-actions" id="action-btns-${actionId}">
        <button class="action-card-btn reject-btn" onclick="cancelProposedAction('${actionId}')">Reject</button>
        <button class="action-card-btn execute-btn" onclick="executeProposedAction('${actionId}')">Confirm &amp; Execute</button>
      </div>
    </div>
  `;
}

// Scans message bubbles for backend placeholders and replaces them with active HTML cards
function activateHistoricalProposals() {
  document.querySelectorAll('.action-proposal-placeholder').forEach(el => {
    try {
      const dataRaw = el.getAttribute('data-proposal');
      if (dataRaw) {
        const data = JSON.parse(dataRaw);
        el.outerHTML = renderActionCard(data);
        updateActionCardStatusFromServer(data.action_id);
      }
    } catch (e) {
      console.error("Error activating proposal:", e);
    }
  });
}

// Queries action status from the database to update cards loaded in chat history
async function updateActionCardStatusFromServer(actionId) {
  const card = document.getElementById(`action-card-${actionId}`);
  if (!card) return;
  const statusEl = document.getElementById(`action-status-${actionId}`);
  const btnEl = document.getElementById(`action-btns-${actionId}`);

  try {
    const resp = await fetch(`/api/actions/status/${actionId}`);
    if (!resp.ok) return;
    const result = await resp.json();
    if (result.status === 'success' && result.action) {
      const action = result.action;
      const state = action.status;

      if (state === 'executed') {
        statusEl.className = "action-card-status success";
        statusEl.innerHTML = `✨ <strong>Completed:</strong> ${renderMarkdown(action.outcome || '')}`;
        btnEl.style.display = 'flex';
        btnEl.innerHTML = `<button class="action-card-btn undo-btn" onclick="undoExecutedAction('${actionId}')">Undo Action</button>`;
        // Disable fields
        card.querySelectorAll('.action-card-body input, .action-card-body textarea').forEach(el => el.disabled = true);
      } else if (state === 'cancelled') {
        statusEl.className = "action-card-status cancelled";
        statusEl.textContent = "🚫 Action Rejected / Cancelled";
        btnEl.style.display = 'none';
        card.querySelectorAll('.action-card-body input, .action-card-body textarea').forEach(el => el.disabled = true);
      } else if (state === 'undone') {
        statusEl.className = "action-card-status undone";
        statusEl.textContent = "↩️ Action Reverted / Undone";
        btnEl.style.display = 'none';
        card.querySelectorAll('.action-card-body input, .action-card-body textarea').forEach(el => el.disabled = true);
      } else {
        // Pending
        statusEl.className = "action-card-status pending";
        statusEl.textContent = "";
        btnEl.style.display = 'flex';
      }
    }
  } catch (err) {
    console.error("Error updating action card status:", err);
  }
}

// Sends user-edited inputs to endpoint for verification and action execution
async function executeProposedAction(actionId) {
  const card = document.getElementById(`action-card-${actionId}`);
  if (!card) return;

  const overrides = {};
  card.querySelectorAll('.action-card-body input, .action-card-body textarea').forEach(el => {
    overrides[el.dataset.key] = el.value;
  });

  const statusEl = document.getElementById(`action-status-${actionId}`);
  const btnEl = document.getElementById(`action-btns-${actionId}`);

  statusEl.className = "action-card-status running";
  statusEl.innerHTML = '<span style="display:inline-block; animation: spin 1s infinite linear; margin-right:5px;">⏳</span> Executing action...';
  btnEl.style.display = 'none';

  try {
    const resp = await fetch('/api/actions/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId, overrides: overrides })
    });
    const result = await resp.json();
    if (resp.ok && result.status === 'success') {
      statusEl.className = "action-card-status success";
      statusEl.innerHTML = `✨ <strong>Completed:</strong> ${renderMarkdown(result.outcome)}`;
      btnEl.style.display = 'flex';
      btnEl.innerHTML = `<button class="action-card-btn undo-btn" onclick="undoExecutedAction('${actionId}')">Undo Action</button>`;

      // Disable inputs
      card.querySelectorAll('.action-card-body input, .action-card-body textarea').forEach(el => el.disabled = true);

      // Sync UI components
      loadBrainIntoSidebar();
      loadActionHistoryLog();
    } else {
      statusEl.className = "action-card-status failed";
      statusEl.textContent = `❌ Failed: ${result.error || result.message || 'Execution error'}`;
      btnEl.style.display = 'flex';
    }
  } catch (err) {
    statusEl.className = "action-card-status failed";
    statusEl.textContent = `❌ Error: ${err.message}`;
    btnEl.style.display = 'flex';
  }
}

// Rejects and cancels a proposed action card
async function cancelProposedAction(actionId) {
  const card = document.getElementById(`action-card-${actionId}`);
  if (!card) return;
  const statusEl = document.getElementById(`action-status-${actionId}`);
  const btnEl = document.getElementById(`action-btns-${actionId}`);

  try {
    const resp = await fetch('/api/actions/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId })
    });
    if (resp.ok) {
      statusEl.className = "action-card-status cancelled";
      statusEl.textContent = "🚫 Action Rejected / Cancelled";
      btnEl.style.display = 'none';
      card.querySelectorAll('.action-card-body input, .action-card-body textarea').forEach(el => el.disabled = true);
      loadActionHistoryLog();
    }
  } catch (err) {
    console.error("Cancel action error:", err);
  }
}

// Reverts an executed action (e.g. removes tasks or files)
async function undoExecutedAction(actionId) {
  const card = document.getElementById(`action-card-${actionId}`);
  if (!card) return;
  const statusEl = document.getElementById(`action-status-${actionId}`);
  const btnEl = document.getElementById(`action-btns-${actionId}`);

  statusEl.className = "action-card-status running";
  statusEl.innerHTML = '<span style="display:inline-block; animation: spin 1s infinite linear; margin-right:5px;">⏳</span> Reverting action...';
  btnEl.style.display = 'none';

  try {
    const resp = await fetch('/api/actions/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId })
    });
    const result = await resp.json();
    if (resp.ok && result.status === 'success') {
      statusEl.className = "action-card-status undone";
      statusEl.textContent = "↩️ Action Reverted / Undone";
      btnEl.style.display = 'none';

      loadBrainIntoSidebar();
      loadActionHistoryLog();
    } else {
      statusEl.className = "action-card-status failed";
      statusEl.textContent = `❌ Undo failed: ${result.message}`;
      btnEl.style.display = 'flex';
    }
  } catch (err) {
    statusEl.className = "action-card-status failed";
    statusEl.textContent = `❌ Error: ${err.message}`;
    btnEl.style.display = 'flex';
  }
}

// Loads action history and populates settings sidebar Action Log
async function loadActionHistoryLog() {
  const container = document.getElementById('actionsLogContent');
  if (!container) return;

  try {
    const resp = await fetch('/api/actions/history');
    if (!resp.ok) throw new Error("Failed to load actions history");
    const data = await resp.json();

    if (data.status === 'success' && data.history && data.history.length > 0) {
      let html = '<div class="actions-history-list">';
      data.history.forEach(act => {
        let icon = "⚡";
        let label = "Action";
        if (act.action_type === 'create_task') { icon = "📅"; label = "Task Details"; }
        else if (act.action_type === 'generate_proposal') { icon = "📝"; label = "Proposal Draft"; }
        else if (act.action_type === 'send_email') { icon = "✉️"; label = "Email Sent"; }

        let statusBadge = `<span class="act-badge status-${act.status}">${act.status.toUpperCase()}</span>`;

        let actionBtns = "";
        if (act.status === 'executed') {
          let btnTitle = "Undo Action";
          if (act.action_type === 'create_task') btnTitle = "Delete Task";
          else if (act.action_type === 'generate_proposal') btnTitle = "Delete Proposal File";
          else if (act.action_type === 'send_email') btnTitle = "Delete Email File";

          actionBtns = `
            <button class="act-log-action-btn act-log-delete-btn" onclick="deleteActionFromLog('${act.id}', event)" title="${btnTitle}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="11" height="11">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          `;
        } else if (act.status === 'pending') {
          actionBtns = `
            <button class="act-log-action-btn act-log-confirm-btn" onclick="executeActionFromLog('${act.id}', event)" title="Confirm &amp; Execute">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="11" height="11">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </button>
            <button class="act-log-action-btn act-log-cancel-btn" onclick="cancelActionFromLog('${act.id}', event)" title="Reject &amp; Cancel">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="11" height="11">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          `;
        }

        let timeStr = new Date(act.created_at).toLocaleDateString() + ' ' + new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Summarize args
        let summaryText = "";
        const args = act.arguments || {};
        if (act.action_type === 'create_task') summaryText = args.title || "New Task";
        else if (act.action_type === 'generate_proposal') summaryText = `Client: ${args.client_name || 'Unknown'}`;
        else if (act.action_type === 'send_email') summaryText = `To: ${args.to || 'Unknown'}`;

        html += `
          <div class="actions-log-item" data-action-id="${act.id}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span style="font-size:11.5px; color:var(--text-muted); font-weight:500;">${icon} ${label}</span>
              <div style="display:flex; align-items:center; gap:6px;">
                ${statusBadge}
                ${actionBtns}
              </div>
            </div>
            <div style="font-size:12.5px; color:var(--text); font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-bottom:2px;">
              ${escapeHtml(summaryText)}
            </div>
            <div style="font-size:10.5px; color:var(--text-faint);">${timeStr}</div>
          </div>
        `;
      });
      html += '</div>';
      container.innerHTML = html;
    } else {
      container.innerHTML = '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">No actions recorded yet.</div>';
    }
  } catch (err) {
    container.innerHTML = `<div style="font-size:12px; color:var(--red); padding: 4px;">Error: ${err.message}</div>`;
  }
}

// Reverts and deletes an action directly from the Action Log history panel
async function deleteActionFromLog(actionId, event) {
  if (event) event.stopPropagation();

  if (!confirm("Are you sure you want to delete/revert this action?")) {
    return;
  }

  const itemEl = document.querySelector(`.actions-log-item[data-action-id="${actionId}"]`);
  let originalHtml = "";
  if (itemEl) {
    originalHtml = itemEl.innerHTML;
    itemEl.innerHTML = `
      <div style="font-size:11.5px; color:var(--text-muted); padding: 4px; display:flex; align-items:center; gap:5px;">
        <span style="display:inline-block; animation: spin 1s infinite linear;">⏳</span> Reverting...
      </div>
    `;
  }

  try {
    const resp = await fetch('/api/actions/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId })
    });
    const result = await resp.json();
    if (resp.ok && result.status === 'success') {
      loadBrainIntoSidebar();
      loadActionHistoryLog();
      
      // Also update the chat screen action card status if it's currently loaded
      updateActionCardStatusFromServer(actionId);
    } else {
      alert(result.message || "Failed to revert action");
      if (itemEl) itemEl.innerHTML = originalHtml;
    }
  } catch (err) {
    alert("Error reverting action: " + err.message);
    if (itemEl) itemEl.innerHTML = originalHtml;
  }
}

// Executes a pending action directly from the Action Log history panel
async function executeActionFromLog(actionId, event) {
  if (event) event.stopPropagation();

  const itemEl = document.querySelector(`.actions-log-item[data-action-id="${actionId}"]`);
  let originalHtml = "";
  if (itemEl) {
    originalHtml = itemEl.innerHTML;
    itemEl.innerHTML = `
      <div style="font-size:11.5px; color:var(--text-muted); padding: 4px; display:flex; align-items:center; gap:5px;">
        <span style="display:inline-block; animation: spin 1s infinite linear;">⏳</span> Executing...
      </div>
    `;
  }

  try {
    const resp = await fetch('/api/actions/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId })
    });
    const result = await resp.json();
    if (resp.ok && result.status === 'success') {
      loadBrainIntoSidebar();
      loadActionHistoryLog();
      
      // Also update chat card if on screen
      updateActionCardStatusFromServer(actionId);
    } else {
      alert(result.message || "Failed to execute action");
      if (itemEl) itemEl.innerHTML = originalHtml;
    }
  } catch (err) {
    alert("Error executing action: " + err.message);
    if (itemEl) itemEl.innerHTML = originalHtml;
  }
}

// Cancels a pending action directly from the Action Log history panel
async function cancelActionFromLog(actionId, event) {
  if (event) event.stopPropagation();

  if (!confirm("Are you sure you want to reject and cancel this action?")) {
    return;
  }

  const itemEl = document.querySelector(`.actions-log-item[data-action-id="${actionId}"]`);
  let originalHtml = "";
  if (itemEl) {
    originalHtml = itemEl.innerHTML;
    itemEl.innerHTML = `
      <div style="font-size:11.5px; color:var(--text-muted); padding: 4px; display:flex; align-items:center; gap:5px;">
        <span style="display:inline-block; animation: spin 1s infinite linear;">⏳</span> Cancelling...
      </div>
    `;
  }

  try {
    const resp = await fetch('/api/actions/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId })
    });
    const result = await resp.json();
    if (resp.ok && result.status === 'success') {
      loadActionHistoryLog();
      
      // Also update chat card if on screen
      updateActionCardStatusFromServer(actionId);
    } else {
      alert(result.message || "Failed to cancel action");
      if (itemEl) itemEl.innerHTML = originalHtml;
    }
  } catch (err) {
    alert("Error cancelling action: " + err.message);
    if (itemEl) itemEl.innerHTML = originalHtml;
  }
}

// ─────────────────────────────────────────
// 📂 WORKSPACE DOCUMENTS CONTROLLER
// ─────────────────────────────────────────

// Toggle Right Sidebar (Workspace Documents Browser)
function toggleRightSidebar() {
  const sidebar = document.getElementById('rightSidebar');
  const overlay = document.getElementById('rightSidebarOverlay');
  if (!sidebar) return;

  const isOpen = sidebar.classList.contains('open');
  if (isOpen) {
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
  } else {
    sidebar.classList.add('open');
    overlay.classList.add('open');
    // Load documents when sidebar opens
    loadWorkspaceDocuments();
  }
}

// Load workspace documents from backend
async function loadWorkspaceDocuments() {
  const container = document.getElementById('documentsListContent');
  if (!container) return;

  container.innerHTML = '<div class="docs-loading" style="font-size:12.5px; color:var(--text-muted); padding: 4px;">Loading workspace documents…</div>';

  try {
    const resp = await fetch('/api/documents');
    if (!resp.ok) throw new Error('Failed to fetch documents');
    const data = await resp.json();

    if (data.status === 'success' && data.documents && data.documents.length > 0) {
      container.innerHTML = data.documents.map(doc => {
        // Human readable file size
        const sizeKB = (doc.file_size / 1024).toFixed(1);
        const uploadedDate = new Date(doc.uploaded_at).toLocaleDateString() + ' ' + 
          new Date(doc.uploaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          
        let summaryHtml = '';
        if (doc.summary) {
          summaryHtml = `<div class="doc-summary">${escapeHtml(doc.summary)}</div>`;
        } else {
          summaryHtml = `<div class="doc-summary" style="border-left-color: var(--border); color: var(--text-faint); font-style: italic;">No summary available.</div>`;
        }

        const ext = doc.filename.split('.').pop().toLowerCase();
        let docIcon = "📄";
        if (ext === 'pdf') docIcon = "📕";
        else if (ext === 'docx') docIcon = "📘";

        let typeBadge = '';
        if (doc.document_type && doc.document_type !== 'other' && doc.document_type !== 'document') {
          typeBadge = `<span class="doc-type-badge type-${doc.document_type}">${escapeHtml(doc.document_type.replace('_', ' '))}</span>`;
        }

        return `
          <div class="doc-item" data-doc-id="${doc.id}">
            <div class="doc-header-row">
              <div class="doc-name-wrap">
                <span class="doc-icon">${docIcon}</span>
                <span class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</span>
                ${typeBadge}
              </div>
              <button class="doc-delete-btn" onclick="deleteWorkspaceDocument('${doc.id}', event)" title="Delete document">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="11" height="11">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
            <div class="doc-meta">
              <span class="doc-size">${sizeKB} KB</span>
              <span class="doc-date">${uploadedDate}</span>
            </div>
            ${summaryHtml}
          </div>
        `;
      }).join('');
    } else {
      container.innerHTML = `
        <div style="font-size:12.5px; color:var(--text-faint); padding: 20px 0; text-align: center;">
          No documents uploaded yet.
        </div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="docs-loading" style="color:var(--red); padding: 4px;">Error: ${err.message}</div>`;
  }
}

// Trigger file input click for document ingestion
function triggerDocSelect() {
  const fileInput = document.getElementById('docFileInput');
  if (fileInput) fileInput.click();
}

// Handle file selection from input
function handleDocSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    uploadDocFiles(files);
  }
  // Clear the input so selecting the same file again triggers change
  event.target.value = '';
}

// Upload documents to backend
async function uploadDocFiles(files) {
  const uploadArea = document.getElementById('docUploadArea');
  const uploadText = uploadArea ? uploadArea.querySelector('.doc-upload-text') : null;
  const originalText = uploadText ? uploadText.textContent : 'Click or drag PDF/DOCX here to ingest';

  if (uploadText) {
    uploadText.innerHTML = '<span style="display:inline-block; animation: spin 1s infinite linear; margin-right:5px;">⏳</span> Ingesting...';
  }
  if (uploadArea) {
    uploadArea.style.pointerEvents = 'none';
    uploadArea.style.opacity = '0.7';
  }

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  try {
    const resp = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    if (!resp.ok) throw new Error(`Upload failed: ${resp.status}`);
    
    const result = await resp.json();
    
    // Check results
    if (result.status === 'ok' || result.status === 'partial') {
      if (result.errors && result.errors.length > 0) {
        alert("Some uploads failed:\n" + result.errors.join("\n"));
      }
    } else {
      alert("Ingestion failed: " + (result.error || result.errors.join("\n")));
    }
  } catch (err) {
    alert("Upload error: " + err.message);
  } finally {
    if (uploadText) {
      uploadText.textContent = originalText;
    }
    if (uploadArea) {
      uploadArea.style.pointerEvents = 'auto';
      uploadArea.style.opacity = '1';
    }
    // Refresh document list
    loadWorkspaceDocuments();
  }
}

// Delete document call
async function deleteWorkspaceDocument(docId, event) {
  if (event) event.stopPropagation();

  if (!confirm("Are you sure you want to permanently delete this document and all its embedded text chunks? This cannot be undone.")) {
    return;
  }

  const itemEl = document.querySelector(`.doc-item[data-doc-id="${docId}"]`);
  let originalHtml = "";
  if (itemEl) {
    originalHtml = itemEl.innerHTML;
    itemEl.innerHTML = `
      <div style="font-size:11.5px; color:var(--text-muted); padding: 4px; display:flex; align-items:center; gap:5px;">
        <span style="display:inline-block; animation: spin 1s infinite linear;">⏳</span> Deleting...
      </div>
    `;
  }

  try {
    const resp = await fetch('/api/documents/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: docId })
    });
    const result = await resp.json();
    if (resp.ok && result.status === 'success') {
      // Refresh list
      loadWorkspaceDocuments();
    } else {
      alert(result.error || "Failed to delete document");
      if (itemEl) itemEl.innerHTML = originalHtml;
    }
  } catch (err) {
    alert("Error deleting document: " + err.message);
    if (itemEl) itemEl.innerHTML = originalHtml;
  }
}