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

  let detailMarkup = "";
  if (thoughtText && thoughtText.trim().length > 0) {
    detailMarkup = `
      <details class="thinking-details" style="border-top: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.15);">
        <summary style="padding: 10px 16px; font-size: 12px; font-weight: 600; color: var(--text-muted); cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; user-select: none;">
          <span>📋 View Reflection / Critique</span>
          <span class="details-chevron" style="transition: transform 0.2s; font-size: 10px;">▼</span>
        </summary>
        <div class="thinking-details-content" style="padding: 12px 16px; font-family: var(--font-mono); font-size: 12.5px; line-height: 1.6; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.04); white-space: pre-wrap; overflow-x: auto;">${escapeHtml(thoughtText)}</div>
      </details>
    `;
  }

  return { markup: stagesMarkup + detailMarkup, statusText: currentStatus, stage: stage };
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

  // Completely strip closed and open thinking blocks from output
  html = html.replace(new RegExp(`<(?:${thinkTagPattern})>[\\s\\S]*?<\\/(?:${thinkTagPattern})>`, 'gi'), '');
  html = html.replace(new RegExp(`<(?:${thinkTagPattern})>[\\s\\S]*$`, 'gi'), '');

  // Strip details blocks (legacy or existing self-reflection output formats)
  html = html.replace(/<details class="thinking-block"[\s\S]*?<\/details>/gi, '');
  html = html.replace(/<details class="thinking-block"[\s\S]*$/gi, '');
  
  html = html.replace(/<div class="thinking-block">[\s\S]*?<\/div>/gi, '');
  html = html.replace(/<div class="thinking-block-streaming">[\s\S]*?<\/div>/gi, '');

  const thinkingBlocks = [];

  // 2. Inline code
  html = html.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

  // 3. Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // 4. Italic
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

  // 5. Links — [text](url) and bare https:// URLs
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+|\/[^\s\)]+)\)/g, (match, text, url) => {
    // Detect download links: local sandbox API OR Supabase Storage signed URLs
    const isDownloadUrl = url.includes('/api/sandbox/download')
      || url.includes('/api/generated-docs/')
      || url.includes('supabase.co/storage')
      || url.includes('/storage/v1/s3')
      || url.includes('/storage/v1/object/sign');

    if (isDownloadUrl) {
      const ext = url.split('?')[0].split('.').pop().toLowerCase();
      let btnLabel = text || "Download File";
      // If the link text already has a good label, use it, otherwise pick one from extension
      if (btnLabel === text && text.length < 50) {
        btnLabel = text;
      } else if (ext === 'docx') {
        btnLabel = "Download DOCX";
      } else if (ext === 'pdf') {
        btnLabel = "Download PDF";
      } else if (ext === 'html') {
        btnLabel = "Preview HTML";
      }
      return `<a href="${url}" class="sandbox-download-btn" target="_blank" rel="noopener noreferrer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="11" height="11"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg><span>${btnLabel}</span></a>`;
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
