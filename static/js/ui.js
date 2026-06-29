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
  
  // Cooldown and Feedback widget logic
  if (!rawText.startsWith('**Error:**') && !rawText.startsWith('_No response')) {
    let responseCount = parseInt(localStorage.getItem('ai_response_count') || '0') + 1;
    localStorage.setItem('ai_response_count', responseCount);
    
    if (responseCount % 4 === 0) {
      const bubble = row.querySelector('.ai-bubble');
      const feedbackHtml = `
        <div class="style-feedback-widget" style="margin-top: 12px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.06); font-size: 11px; display: flex; align-items: center; gap: 8px; color: var(--text-muted); clear: both;">
          <span>Did this response match your style?</span>
          <button class="style-feedback-btn yes" onclick="submitStyleFeedback(this, 'positive')" style="background: var(--bg-3); border: 1px solid var(--border); color: var(--text); border-radius: 4px; padding: 2px 8px; font-size: 10.5px; cursor: pointer; transition: all 0.15s;">Yes</button>
          <button class="style-feedback-btn no" onclick="showStyleCorrectionInput(this)" style="background: var(--bg-3); border: 1px solid var(--border); color: var(--text); border-radius: 4px; padding: 2px 8px; font-size: 10.5px; cursor: pointer; transition: all 0.15s;">No</button>
        </div>
      `;
      bubble.insertAdjacentHTML('beforeend', feedbackHtml);
    }
  }

  // Refresh memory panels in the background
  setTimeout(async () => {
    try {
      if (typeof loadBrainMemory === 'function') await loadBrainMemory();
      if (typeof loadNotesMemory === 'function') await loadNotesMemory();
    } catch (e) {
      console.warn("[Memory Auto-Refresh] Failed to auto-refresh memory:", e);
    }
  }, 1500);

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

  // Strip thinking blocks from remaining content during stream
  remaining = remaining.replace(closedRe, '');
  const openMatch = remaining.match(openRe);
  if (openMatch) {
    remaining = remaining.replace(openRe, '');
  }

  // 3. Main response text (everything outside thinking tags)
  const responseText = remaining
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  if (responseText || !openMatch) {
    html += `<span class="stream-response">${responseText}<span class="stream-cursor"></span></span>`;
  }

  return html;
}


// ── Left Sidebar & Sliding Panels ────────
let activePanel = null;

function toggleSidebar() {
  togglePanel('brain');
}

function togglePanel(panelName) {
  if (activePanel === panelName) {
    closePanel();
  } else {
    openPanel(panelName);
  }
}

function openPanel(panelName) {
  activePanel = panelName;
  const panel = document.getElementById('slidingPanel');
  const overlay = document.getElementById('sidebarOverlay');
  
  // Update title
  const titleEl = document.getElementById('panelTitle');
  const titles = {
    models: 'AI Model Options',
    settings: 'Workspace Settings',
    brain: 'Oculus Brain (Memory)',
    notes: 'Style & Behavior Notes',
    actions: 'AI Action Log',
    docs: 'Generated Documents'
  };
  if (titleEl) titleEl.textContent = titles[panelName] || 'Oculus AI';
  
  // Show the correct view, hide others
  document.querySelectorAll('.panel-view').forEach(view => {
    view.style.display = 'none';
  });
  const currentView = document.getElementById(`view-${panelName}`);
  if (currentView) currentView.style.display = 'flex';
  
  // Set active class on dock buttons
  document.querySelectorAll('.dock-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  const activeBtn = document.getElementById(`dock-btn-${panelName}`);
  if (activeBtn) activeBtn.classList.add('active');
  
  // Slide out panel
  if (panel) panel.classList.add('open');
  if (overlay) overlay.classList.add('open');
  
  // Load dynamic data based on view
  if (panelName === 'brain') {
    loadBrainMemory();
  } else if (panelName === 'notes') {
    loadNotesMemory();
  } else if (panelName === 'actions') {
    loadActionHistoryLog();
  } else if (panelName === 'docs') {
    loadGeneratedDocs();
  }
}

function closePanel() {
  activePanel = null;
  const panel = document.getElementById('slidingPanel');
  const overlay = document.getElementById('sidebarOverlay');
  if (panel) panel.classList.remove('open');
  if (overlay) overlay.classList.remove('open');
  
  // Remove active class from dock buttons
  document.querySelectorAll('.dock-btn').forEach(btn => {
    btn.classList.remove('active');
  });
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
// ── Auto-grow textarea ────────────────────
