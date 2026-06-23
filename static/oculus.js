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


// ── Markdown renderer ─────────────────────
function renderMarkdown(text) {
  let html = text;

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
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
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

  // Match both <think>...</think> and <thinking>...</thinking>
  const closedRe = /<(?:think|thinking)>([\s\S]*?)<\/(?:think|thinking)>/gi;
  const openRe   = /<(?:think|thinking)>([\s\S]*)$/i;

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


// ── Model switcher ────────────────────────
async function setModel(modelId) {
  const select = document.getElementById('modelSelect');
  const status = document.getElementById('modelStatus');
  if (select) select.disabled = true;
  if (status) { status.textContent = 'Switching…'; status.classList.add('switching'); }

  try {
    const resp = await fetch('/set_model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: modelId }),
    });
    const data = await resp.json();
    if (data.status === 'ok') {
      if (status) { status.textContent = data.name; status.classList.remove('switching'); }
    } else {
      if (status) { status.textContent = 'Error'; status.classList.remove('switching'); }
      if (select) select.value = select.dataset.previous || select.value;
    }
  } catch (err) {
    if (status) { status.textContent = 'Error'; status.classList.remove('switching'); }
  } finally {
    if (select) select.disabled = false;
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
  await fetch('/clear', { method: 'POST' });
  location.reload();
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

async function toggleBrain() {
  const drawer = document.getElementById('brainDrawer');
  const overlay = document.getElementById('brainOverlay');
  if (!drawer || !overlay) return;

  const isOpen = drawer.classList.contains('open');
  if (isOpen) {
    drawer.classList.remove('open');
    overlay.classList.remove('open');
  } else {
    drawer.classList.add('open');
    overlay.classList.add('open');
    await loadBrainMemory();
  }
}

async function loadBrainMemory() {
  const content = document.querySelector('.brain-drawer-content');
  if (content) content.innerHTML = '<div class="brain-loading">Loading brain state...</div>';

  try {
    const resp = await fetch('/api/memory');
    if (!resp.ok) throw new Error("Failed to fetch memory");
    currentBrainMemory = await resp.json();
    renderBrain(currentBrainMemory);
  } catch (err) {
    if (content) content.innerHTML = `<div class="brain-loading" style="color:var(--red)">Error: ${err.message}</div>`;
  }
}

function renderBrain(mem) {
  const content = document.querySelector('.brain-drawer-content');
  if (!content) return;

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
      if (data.errors && data.errors.length) {
        alert("Upload warning:\n" + data.errors.join("\n"));
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