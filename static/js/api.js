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

  // Check if this is a doc retrieval request — if so, show the gallery instead of calling AI
  const intercepted = await interceptDocRetrievalIntent(text);
  if (intercepted) {
    hideTyping();
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
    return;
  }

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
      
      // Cooldown and Feedback widget logic
      if (!accumulated.startsWith('**Error:**') && !accumulated.startsWith('_No response')) {
        let responseCount = parseInt(localStorage.getItem('ai_response_count') || '0') + 1;
        localStorage.setItem('ai_response_count', responseCount);
        
        if (responseCount % 4 === 0) {
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


// ── Style Feedback Handlers ─────────────────
function showStyleCorrectionInput(btn) {
  const widget = btn.closest('.style-feedback-widget');
  if (!widget) return;
  widget.innerHTML = `
    <div class="style-correction-container" style="display: flex; gap: 6px; align-items: center; width: 100%;">
      <span style="white-space: nowrap;">How can we adjust?</span>
      <input type="text" placeholder="e.g. less salesy, more dry" style="flex: 1; background: var(--bg-2); border: 1px solid var(--border); color: var(--text); padding: 3px 6px; border-radius: 4px; font-size: 11px; outline: none; font-family: var(--font-sans);">
      <button onclick="submitStyleFeedback(this, 'negative')" style="background: var(--accent); border: none; color: #fff; border-radius: 4px; padding: 3px 8px; font-size: 10.5px; cursor: pointer; font-weight: 500; font-family: var(--font-sans);">Submit</button>
      <button onclick="cancelStyleCorrection(this)" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 11px;">Cancel</button>
    </div>
  `;
  const input = widget.querySelector('input');
  if (input) input.focus();
}

function cancelStyleCorrection(btn) {
  const widget = btn.closest('.style-feedback-widget');
  if (!widget) return;
  widget.innerHTML = `
    <span>Did this response match your style?</span>
    <button class="style-feedback-btn yes" onclick="submitStyleFeedback(this, 'positive')" style="background: var(--bg-3); border: 1px solid var(--border); color: var(--text); border-radius: 4px; padding: 2px 8px; font-size: 10.5px; cursor: pointer; transition: all 0.15s;">Yes</button>
    <button class="style-feedback-btn no" onclick="showStyleCorrectionInput(this)" style="background: var(--bg-3); border: 1px solid var(--border); color: var(--text); border-radius: 4px; padding: 2px 8px; font-size: 10.5px; cursor: pointer; transition: all 0.15s;">No</button>
  `;
}

async function submitStyleFeedback(element, type) {
  const widget = element.closest('.style-feedback-widget');
  if (!widget) return;
  
  let correction = "";
  if (type === 'negative') {
    const input = widget.querySelector('input');
    if (input) {
      correction = input.value.trim();
      if (!correction) return;
    }
  }
  
  widget.innerHTML = `<span style="color: var(--text-muted);">Saving style preference...</span>`;
  
  try {
    const resp = await fetch('/api/memory/style_feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback: type, correction: correction })
    });
    
    if (resp.ok) {
      const data = await resp.json();
      if (data.status === 'ok' && data.memory) {
        if (typeof currentBrainMemory !== 'undefined') {
          currentBrainMemory = data.memory;
          const content = document.getElementById('notesDrawerContent') || document.querySelector('.notes-drawer-content');
          if (content) {
            renderNotesIntoEl(content, currentBrainMemory);
          }
        }
      }
      widget.innerHTML = `<span style="color: #a6e3a1; font-weight: 500;">✓ Style preference ${type === 'positive' ? 'reinforced' : 'updated'}</span>`;
    } else {
      throw new Error("Feedback submission failed");
    }
  } catch (err) {
    widget.innerHTML = `<span style="color: #f38ba8;">Error: ${err.message}</span>`;
    setTimeout(() => cancelStyleCorrection(element), 2000);
  }
}

async function togglePinListItem(key, value, pin) {
  try {
    const resp = await fetch('/api/memory/pin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value, pin })
    });
    if (resp.ok) {
      await loadBrainMemory();
    } else {
      const err = await resp.json();
      alert("Failed to pin/unpin item: " + (err.error || resp.statusText));
    }
  } catch (e) {
    console.error("Error pinning/unpinning item:", e);
  }
}

async function updateMemoryTokenBudget(input) {
  const budget = parseInt(input.value, 10);
  if (isNaN(budget) || budget < 100 || budget > 10000) {
    alert("Please enter a valid token budget between 100 and 10000.");
    return;
  }
  try {
    const resp = await fetch(`/api/workspaces/${activeWorkspaceId}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ memory_token_budget: budget })
    });
    if (!resp.ok) {
      throw new Error('Failed to update workspace settings');
    }
    const activeWs = userWorkspaces.find(w => w.id === activeWorkspaceId);
    if (activeWs) {
      if (!activeWs.settings) activeWs.settings = {};
      activeWs.settings.memory_token_budget = budget;
    }
  } catch (err) {
    alert("Error saving setting: " + err.message);
  }
}

let brainDebugOpen = false;

function toggleBrainDebugView() {
  const container = document.getElementById('brainDebugContainer');
  if (!container) return;
  brainDebugOpen = !brainDebugOpen;
  container.style.display = brainDebugOpen ? 'block' : 'none';
  if (brainDebugOpen) {
    loadBrainRankingDebug();
  }
}

async function loadBrainRankingDebug() {
  const container = document.getElementById('brainDebugContainer');
  if (!container) return;
  try {
    const resp = await fetch('/api/memory/debug');
    if (!resp.ok) throw new Error("Failed to load debug info");
    const data = await resp.json();
    if (!data || !data.timestamp) {
      container.innerHTML = 'No debug info loaded. Ask Oculus something to generate context rankings.';
      return;
    }
    
    let html = `<div style="font-weight:700; color:var(--accent); margin-bottom:6px;">LATEST RANKING PROCESS</div>`;
    html += `<div><strong>Time:</strong> ${data.timestamp}</div>`;
    html += `<div><strong>Query:</strong> "${escapeHtml(data.query || '(None)')}"</div>`;
    html += `<div><strong>Memory Budget:</strong> ${data.memory_budget} tokens</div>`;
    html += `<div><strong>Est. Injected Tokens:</strong> ${data.estimated_tokens}</div>`;
    html += `<div><strong>Pruned due to Budget:</strong> ${data.pruned ? '<span style="color:var(--red)">YES</span>' : 'NO'}</div>`;
    html += `<div><strong>Low-Priority Summary Used:</strong> ${data.summary_used ? 'YES' : 'NO'}</div>`;
    
    if (data.protected_items && data.protected_items.length > 0) {
      html += `<div style="font-weight:700; color:var(--green); margin-top:10px; margin-bottom:4px;">PROTECTED ITEMS (Always Injected)</div>`;
      data.protected_items.forEach(item => {
        html += `<div style="padding-left:6px; margin-bottom:2px;">• ${escapeHtml(item)}</div>`;
      });
    }
    
    if (data.ranked_items) {
      html += `<div style="font-weight:700; color:var(--purple); margin-top:10px; margin-bottom:4px;">DYNAMIC RANKINGS (Score breakdown)</div>`;
      for (const [category, items] of Object.entries(data.ranked_items)) {
        if (!items || items.length === 0) continue;
        html += `<div style="text-transform:uppercase; font-weight:700; font-size:10px; margin-top:6px; color:var(--text);">${category}</div>`;
        items.forEach(x => {
          const scoreStr = x.score !== undefined ? x.score.toFixed(3) : 'N/A';
          const detailsStr = x.details ? `(rel: ${x.details.relevance.toFixed(2)}, conf: ${x.details.confidence.toFixed(2)}, rec: ${x.details.recency.toFixed(2)}, imp: ${x.details.importance.toFixed(2)})` : '';
          const style = x.injected ? 'color:var(--text)' : 'color:var(--text-faint); text-decoration:line-through;';
          html += `<div style="padding-left:6px; margin-bottom:2px; ${style}">`;
          html += `• [Score: ${scoreStr}] ${escapeHtml(x.text)} <span style="font-size:9.5px; opacity:0.7;">${detailsStr}</span>`;
          if (!x.injected) {
             html += ` <span style="color:var(--red); font-size:9px;">[Omitted]</span>`;
          }
          html += `</div>`;
        });
      }
    }
    
    html += `<div style="font-weight:700; color:var(--orange); margin-top:10px; margin-bottom:4px;">FINAL INJECTED CONTEXT</div>`;
    html += `<pre style="white-space:pre-wrap; word-break:break-all; background:rgba(0,0,0,0.15); border:1px solid rgba(255,255,255,0.05); padding:6px; border-radius:4px; font-size:9.5px;">${escapeHtml(data.injected_context)}</pre>`;
    
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--red)">Error: ${err.message}</div>`;
  }
}