// ─────────────────────────────────────────
// OCULUS AI — oculus.js  (single clean file)
// ─────────────────────────────────────────

// ── Load Highlight.js from CDN ───────────
(function loadHighlightJs() {
  const link  = document.createElement('link');
  link.rel    = 'stylesheet';
  link.href   = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css';
  document.head.appendChild(link);

  const script  = document.createElement('script');
  script.src    = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js';
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
    const label    = language || 'code';
    const escaped  = escapeHtml(code.trimEnd());
    const idx      = codeBlocks.length;
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

  // 2. Inline code
  html = html.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  // 3. Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // 4. Italic
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

  // 5. Headings
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm,  '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^# (.+)$/gm,   '<h1 class="md-h1">$1</h1>');

  // 6. Horizontal rule
  html = html.replace(/^---+$/gm, '<hr class="md-hr">');

  // 7. Tables
  html = renderTables(html);

  // 8. Bullet lists
  html = renderLists(html);

  // 9. Paragraphs
  html = renderParagraphs(html);

  // 10. Restore code blocks
  codeBlocks.forEach((block, idx) => {
    html = html.replace(`%%CODE_BLOCK_${idx}%%`, block);
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
      const tag   = i === 0 ? 'th' : 'td';
      out += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
    });
    return out + '</table></div>';
  });
}

function renderParagraphs(html) {
  return html.split(/\n{2,}/).map(block => {
    block = block.trim();
    if (!block) return '';
    if (/^<(div|ul|ol|h[1-6]|pre|table|hr|blockquote)/i.test(block)) return block;
    return `<p>${block.replace(/\n/g, '<br>')}</p>`;
  }).join('');
}


// ── Copy button ───────────────────────────
function copyCode(btn) {
  const text = btn.closest('.code-block').querySelector('pre code').innerText;
  navigator.clipboard.writeText(text).then(() => {
    const iconCopy  = btn.querySelector('.icon-copy');
    const iconCheck = btn.querySelector('.icon-check');
    const label     = btn.querySelector('.copy-label');
    iconCopy.style.display  = 'none';
    iconCheck.style.display = 'block';
    label.textContent       = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      iconCopy.style.display  = 'block';
      iconCheck.style.display = 'none';
      label.textContent       = 'Copy';
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
    const div  = document.createElement('div');
    div.className   = 'date-divider';
    div.textContent = 'Today';
    feed.insertBefore(div, feed.firstChild);
  }
}

function appendUserBubble(text) {
  const feed = document.getElementById('chatFeed');
  const row  = document.createElement('div');
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
  const row  = document.createElement('div');
  row.className = 'bubble-row ai-row';
  row.innerHTML = `
    ${AI_AVATAR}
    <div class="bubble ai-bubble rendered">${renderMarkdown(rawText)}</div>`;
  feed.insertBefore(row, document.getElementById('typingIndicator'));
  row.querySelectorAll('.code-block pre code').forEach(el => highlight(el));
  scrollToBottom();
}


// ── Send message ──────────────────────────
async function sendMessage() {
  const input   = document.getElementById('msgInput');
  const sendBtn = document.querySelector('.send-btn');
  const text    = input.value.trim();
  if (!text) return;

  input.value        = '';
  input.style.height = 'auto';
  input.disabled     = true;
  sendBtn.disabled   = true;

  removeEmptyState();
  appendUserBubble(text);
  showTyping();

  try {
    const resp = await fetch('/ask', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text }),
    });
    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
    const fullText = await resp.text();
    hideTyping();
    insertAiBubble(fullText);
  } catch (err) {
    hideTyping();
    insertAiBubble(`**Error:** ${err.message}`);
  } finally {
    input.disabled   = false;
    sendBtn.disabled = false;
    input.focus();
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
