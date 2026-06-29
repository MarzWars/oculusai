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

    // Set reflection toggle state
    if (activeWs) {
      const reflectionToggle = document.getElementById('reflectionToggle');
      if (reflectionToggle) {
        const settings = activeWs.settings || {};
        reflectionToggle.checked = !!settings.self_reflection_enabled;
      }
      const budgetInput = document.getElementById('memoryBudgetInput');
      if (budgetInput) {
        const settings = activeWs.settings || {};
        budgetInput.value = settings.memory_token_budget !== undefined ? settings.memory_token_budget : 1500;
      }
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
  } else if (type === "generate_document") {
    icon = "📂";
    title = "Generate & Export Document";
    accentClass = "action-card-generic";
    const fmt = (args.format || 'docx').toLowerCase();
    formFields = `
      <div class="action-field">
        <label>Filename</label>
        <input type="text" data-key="filename" value="${escapeHtml(args.filename || '')}">
      </div>
      <div class="action-field">
        <label>Format</label>
        <select data-key="format" style="width:100%; background:var(--bg-3); color:var(--text); border:1px solid var(--border); border-radius:4px; padding:6px; font-size:13px;">
          <option value="docx" ${fmt === 'docx' ? 'selected' : ''}>DOCX (Word Document)</option>
          <option value="pdf" ${fmt === 'pdf' ? 'selected' : ''}>PDF (Portable Document)</option>
          <option value="txt" ${fmt === 'txt' ? 'selected' : ''}>TXT (Plain Text)</option>
        </select>
      </div>
      <div class="action-field">
        <label>Document Title</label>
        <input type="text" data-key="title" value="${escapeHtml(args.title || '')}">
      </div>
      <div class="action-field">
        <label>Document Content</label>
        <textarea data-key="content" rows="5">${escapeHtml(args.content || '')}</textarea>
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
        card.querySelectorAll('.action-card-body input, .action-card-body textarea, .action-card-body select').forEach(el => el.disabled = true);
      } else if (state === 'cancelled') {
        statusEl.className = "action-card-status cancelled";
        statusEl.textContent = "🚫 Action Rejected / Cancelled";
        btnEl.style.display = 'none';
        card.querySelectorAll('.action-card-body input, .action-card-body textarea, .action-card-body select').forEach(el => el.disabled = true);
      } else if (state === 'undone') {
        statusEl.className = "action-card-status undone";
        statusEl.textContent = "↩️ Action Reverted / Undone";
        btnEl.style.display = 'none';
        card.querySelectorAll('.action-card-body input, .action-card-body textarea, .action-card-body select').forEach(el => el.disabled = true);
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
  card.querySelectorAll('.action-card-body input, .action-card-body textarea, .action-card-body select').forEach(el => {
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
      card.querySelectorAll('.action-card-body input, .action-card-body textarea, .action-card-body select').forEach(el => el.disabled = true);

      // Sync UI components
      loadBrainIntoSidebar();
      loadActionHistoryLog();
      loadGeneratedDocs(); // Refresh generated docs panel
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
      card.querySelectorAll('.action-card-body input, .action-card-body textarea, .action-card-body select').forEach(el => el.disabled = true);
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
        else if (act.action_type === 'generate_document') { icon = "📂"; label = "Document Generated"; }

        let statusBadge = `<span class="act-badge status-${act.status}">${act.status.toUpperCase()}</span>`;

        let actionBtns = "";
        if (act.status === 'executed') {
          let btnTitle = "Undo Action";
          if (act.action_type === 'create_task') btnTitle = "Delete Task";
          else if (act.action_type === 'generate_proposal') btnTitle = "Delete Proposal File";
          else if (act.action_type === 'send_email') btnTitle = "Delete Email File";
          else if (act.action_type === 'generate_document') btnTitle = "Delete Document File";

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
        else if (act.action_type === 'generate_document') summaryText = `${args.filename || 'document.docx'} (${(args.format || 'docx').toUpperCase()})`;

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
// 🔄 CHAT STATE REHYDRATION
// Fetches action cards from Supabase and updates download links in existing
// rendered bubbles so they survive page refresh.
// ─────────────────────────────────────────

async function rehydrateChatState() {
  try {
    const resp = await fetch('/api/chat/state');
    if (!resp.ok) return;
    const data = await resp.json();
    if (data.status !== 'success') return;

    const cards = data.action_cards || [];
    if (!cards.length) return;

    for (const card of cards) {
      const aid = card.action_id;
      if (!aid) continue;

      // If the action card is already in the DOM, update its status
      const existingCard = document.getElementById(`action-card-${aid}`);
      if (existingCard) {
        updateActionCardStatusFromServer(aid);
        // Also update any download button inside the card with the permanent URL
        if (card.download_url && card.status === 'executed') {
          const statusEl = document.getElementById(`action-status-${aid}`);
          if (statusEl && !statusEl.querySelector('a.sandbox-download-btn')) {
            const existingOutcome = statusEl.innerHTML;
            // Inject a fresh download link if not present
            if (!existingOutcome.includes('sandbox-download-btn') && card.download_url) {
              const dlBtn = `<a href="${card.download_url}" class="sandbox-download-btn" target="_blank" rel="noopener noreferrer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="11" height="11"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg><span>Download</span></a>`;
              statusEl.innerHTML = statusEl.innerHTML + ' ' + dlBtn;
            }
          }
        }
      }
    }
  } catch (err) {
    console.warn('[Rehydrate] Chat state rehydration failed:', err.message);
  }
}


// ─────────────────────────────────────────
// 📁 GENERATED DOCUMENTS PANEL
// Loads and renders docs from oculus_generated_docs via /api/generated-docs
// ─────────────────────────────────────────

async function loadGeneratedDocs(searchQuery = '') {
  const container = document.getElementById('generatedDocsContent');
  if (!container) return;

  container.innerHTML = '<div style="font-size:12px; color:var(--text-muted); padding:8px 0;">Loading generated documents…</div>';

  try {
    const url = searchQuery
      ? `/api/generated-docs?q=${encodeURIComponent(searchQuery)}`
      : '/api/generated-docs';
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    const docs = data.docs || [];
    if (!docs.length) {
      container.innerHTML = `
        <div style="font-size:12px; color:var(--text-faint); padding:16px 0; text-align:center;">
          ${searchQuery ? `No documents matching "<strong>${escapeHtml(searchQuery)}</strong>"` : 'No documents generated yet.'}
        </div>`;
      return;
    }

    container.innerHTML = docs.map(doc => {
      const iconMap = { proposal: '📝', document: '📂', email: '✉️', quote: '💰' };
      const icon = iconMap[doc.doc_type] || '📄';
      const date = new Date(doc.created_at).toLocaleDateString('en-ZA', {
        day: '2-digit', month: 'short', year: 'numeric'
      });
      const sizeKB = doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : '';
      const typeBadge = doc.doc_type
        ? `<span class="act-badge status-executed" style="font-size:9px; padding:1px 5px;">${doc.doc_type}</span>`
        : '';
      const fmtBadge = doc.format
        ? `<span style="font-size:9px; color:var(--text-faint); margin-left:4px;">${doc.format.toUpperCase()}</span>`
        : '';

      const dlUrl = doc.download_url || `/api/generated-docs/${doc.id}/download`;

      return `
        <div class="generated-doc-item" style="border:1px solid var(--border); border-radius:8px; padding:10px 12px; margin-bottom:8px; background:var(--bg-2);">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
            <div style="flex:1; min-width:0;">
              <div style="display:flex; align-items:center; gap:6px; margin-bottom:3px; flex-wrap:wrap;">
                <span style="font-size:14px;">${icon}</span>
                <span style="font-size:12.5px; font-weight:600; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(doc.title || doc.filename)}">${escapeHtml(doc.title || doc.filename)}</span>
                ${typeBadge}${fmtBadge}
              </div>
              ${doc.description ? `<div style="font-size:11px; color:var(--text-muted); margin-bottom:4px; line-height:1.4;">${escapeHtml(doc.description.substring(0, 80))}${doc.description.length > 80 ? '…' : ''}</div>` : ''}
              <div style="font-size:10.5px; color:var(--text-faint);">${date}${sizeKB ? ' · ' + sizeKB : ''}</div>
            </div>
            <a href="${dlUrl}" class="sandbox-download-btn" target="_blank" rel="noopener noreferrer" style="flex-shrink:0; white-space:nowrap;" title="Download">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="11" height="11"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              <span>Download</span>
            </a>
          </div>
        </div>`;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div style="font-size:12px; color:var(--red); padding:8px 0;">Error: ${err.message}</div>`;
  }
}

// Called by the search input in the generated docs panel
function searchGeneratedDocs() {
  const input = document.getElementById('generatedDocsSearch');
  const q = input ? input.value.trim() : '';
  loadGeneratedDocs(q);
}


// ─────────────────────────────────────────
// 🔍 NATURAL LANGUAGE DOC RETRIEVAL
// Intercepts messages like "show me the proposal for Red Rooms"
// and renders a docs gallery card instead of / alongside the AI response.
// ─────────────────────────────────────────

const DOC_RETRIEVAL_PATTERN = /(show|give|find|list|what|get).{0,20}(proposal|quote|document|email|doc|draft)/i;

async function interceptDocRetrievalIntent(text) {
  if (!DOC_RETRIEVAL_PATTERN.test(text)) return false;

  // Extract a search term: everything after the action verb up to end
  const termMatch = text.match(/(?:proposal|quote|document|email|doc|draft)\s+(?:for|about|on|named|called)?\s*(.+)/i);
  const searchTerm = termMatch ? termMatch[1].trim() : text.replace(/(show|give|find|list|what|get)\s*(me\s*)?(the\s*)?/i, '').trim();

  // Fetch matching docs
  try {
    const resp = await fetch(`/api/generated-docs?q=${encodeURIComponent(searchTerm)}`);
    if (!resp.ok) return false;
    const data = await resp.json();
    const docs = data.docs || [];

    if (!docs.length) return false; // Let the AI handle it

    // Render a doc gallery card in the feed
    const feed = document.getElementById('chatFeed');
    const row = document.createElement('div');
    row.className = 'bubble-row ai-row';

    const iconMap = { proposal: '📝', document: '📂', email: '✉️', quote: '💰' };
    const cardsHtml = docs.slice(0, 8).map(doc => {
      const icon = iconMap[doc.doc_type] || '📄';
      const date = new Date(doc.created_at).toLocaleDateString('en-ZA', { day:'2-digit', month:'short', year:'numeric' });
      const dlUrl = doc.download_url || `/api/generated-docs/${doc.id}/download`;
      return `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px; border:1px solid var(--border); border-radius:8px; background:var(--bg-2); margin-bottom:6px; gap:10px;">
          <div style="min-width:0; flex:1;">
            <div style="font-size:12.5px; font-weight:600; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${icon} ${escapeHtml(doc.title || doc.filename)}</div>
            <div style="font-size:10.5px; color:var(--text-faint); margin-top:2px;">${date} · ${(doc.format || 'file').toUpperCase()}</div>
          </div>
          <a href="${dlUrl}" class="sandbox-download-btn" target="_blank" rel="noopener noreferrer" style="flex-shrink:0;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="11" height="11"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            <span>Download</span>
          </a>
        </div>`;
    }).join('');

    row.innerHTML = `
      ${AI_AVATAR}
      <div class="bubble ai-bubble rendered">
        <p style="font-weight:600; margin-bottom:10px;">📁 Found ${docs.length} document${docs.length !== 1 ? 's' : ''} matching <em>"${escapeHtml(searchTerm)}"</em>:</p>
        ${cardsHtml}
        ${docs.length > 8 ? `<div style="font-size:11px; color:var(--text-muted); margin-top:4px;">+ ${docs.length - 8} more. Refine your search for more specific results.</div>` : ''}
      </div>`;

    feed.insertBefore(row, document.getElementById('typingIndicator'));
    scrollToBottom();
    return true; // Intercepted — don't send to AI
  } catch (err) {
    console.warn('[DocRetrieval] Failed:', err.message);
    return false;
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

