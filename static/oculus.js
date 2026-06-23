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
    codeBlocks.push(`
<div class="code-block">
  <div class="code-header">
    <span class="code-lang">${label}</span>
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
  <pre><code class="language-${language}">${escaped}</code></pre>
</div>`);
    return `%%CODE_BLOCK_${idx}%%`;
  });

  // Handle <think> and <thinking> blocks (different models use different tags)
  // Build a combined tag pattern: think|thinking
  const thinkTagPattern = 'think(?:ing)?';

  // 1. Closed thinking blocks — <think>…</think> or <thinking>…</thinking>
  html = html.replace(new RegExp(`<(?:${thinkTagPattern})>([\\s\\S]*?)</(?:${thinkTagPattern})>`, 'gi'), (_, thought) => {
    return `
<details class="thinking-block">
  <summary class="thinking-header">
    <span class="thinking-icon">🧠</span>
    <span class="thinking-title">Thought Process</span>
  </summary>
  <div class="thinking-content">${thought}</div>
</details>`;
  });

  // 2. Open/streaming thinking blocks — tag opened but not yet closed
  html = html.replace(new RegExp(`<(?:${thinkTagPattern})>([\\s\\S]*)$`, 'gi'), (_, thought) => {
    return `
<details class="thinking-block" open>
  <summary class="thinking-header">
    <span class="thinking-icon">🧠</span>
    <span class="thinking-title">Thought Process</span>
  </summary>
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
  const text = btn.closest('.code-block').querySelector('pre code').innerText;
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
    html += `<div class="live-thinking">
  <div class="live-thinking-header">
    <span class="thinking-icon">🧠</span>
    <span>Thinking...</span>
  </div>
  <div class="live-thinking-content">${escapeHtml(thought)}</div>
</div>`;
  }

  // 2. Open (still streaming) thinking block
  const openMatch = remaining.match(openRe);
  if (openMatch) {
    remaining = remaining.replace(openRe, '');
    html += `<div class="live-thinking">
  <div class="live-thinking-header">
    <span class="thinking-icon">🧠</span>
    <span>Thinking...</span>
  </div>
  <div class="live-thinking-content">${escapeHtml(openMatch[1])}<span class="stream-cursor"></span></div>
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
  `;
}

function renderBrainListItems(key, lst) {
  if (!lst || lst.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return lst.map(item => `
    <div class="brain-list-item">
      <span class="brain-list-text">${escapeHtml(item)}</span>
      <button class="brain-delete-btn" onclick="deleteBrainListItem('${key}', \`${escapeHtml(item).replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete fact">×</button>
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