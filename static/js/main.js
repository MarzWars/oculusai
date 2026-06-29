// ─────────────────────────────────────────
// OCULUS AI — oculus.js  (single clean file)
// ─────────────────────────────────────────

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

  // Load generated documents panel
  loadGeneratedDocs();

  // Initialize AI Action Engine hooks — MUST run before rehydrateChatState
  // so action card DOM elements exist when we update their status
  activateHistoricalProposals();
  loadActionHistoryLog();

  // Rehydrate action cards from Supabase (fixes download links after page refresh)
  // Runs AFTER activateHistoricalProposals so cards are in the DOM
  rehydrateChatState();

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

async function loadBrainMemory() {
  await loadBrainIntoSidebar();
  
  // Also load the notes drawer if the Notes panel content is present
  const notesContent = document.getElementById('brainNotesContent');
  if (notesContent && currentBrainMemory) {
    renderNotesIntoEl(notesContent, currentBrainMemory);
  }
}

async function loadNotesMemory() {
  const content = document.getElementById('brainNotesContent');
  if (!content) return;
  content.innerHTML = '<div class="brain-loading">Loading notes…</div>';
  try {
    const resp = await fetch('/api/memory');
    if (!resp.ok) throw new Error('Failed to fetch memory');
    currentBrainMemory = await resp.json();
    renderNotesIntoEl(content, currentBrainMemory);
  } catch (err) {
    content.innerHTML = `<div class="brain-loading" style="color:var(--red)">Error: ${err.message}</div>`;
  }
}

function renderNotesIntoEl(content, mem) {
  const notes = mem.ai_notes || [];
  content.innerHTML = `
    <div style="font-size:12px; color:var(--text-muted); margin-bottom:10px; line-height: 1.4;">
      Oculus automatically infers style and coding guidelines from your interactions. You can manage them manually below.
    </div>
    <div class="brain-list" id="brain-notes-list">
      ${renderBrainNotesItems(notes)}
    </div>
    <div class="brain-add-form" style="margin-top:12px;">
      <input type="text" class="brain-add-input" id="brain-note-add-input" placeholder="Add custom behavior note...">
      <button class="brain-add-btn" onclick="addBrainListItem('ai_notes', 'brain-note-add-input')">Add</button>
    </div>
  `;
}

function renderBrain(mem) {
  const content = document.getElementById('brainDrawerContent') || document.querySelector('.brain-drawer-content');
  if (!content) return;
  renderBrainIntoEl(content, mem);
}

function getConfidenceBadgeHtml(score, sourceType, reasoning, lastReinforced) {
  if (score === undefined || score === null) return '';
  let badgeClass = 'low';
  let badgeText = 'Low';
  if (score >= 0.8) {
    badgeClass = 'high';
    badgeText = 'High';
  } else if (score >= 0.65) {
    badgeClass = 'medium';
    badgeText = 'Medium';
  }
  let tooltip = `Confidence Score: ${score.toFixed(2)}`;
  if (sourceType) {
    tooltip += `\nSource: ${sourceType}`;
  }
  if (lastReinforced) {
    tooltip += `\nLast Reinforced: ${lastReinforced}`;
  }
  if (reasoning) {
    tooltip += `\nReasoning: ${reasoning}`;
  }
  return `<span class="conf-badge conf-${badgeClass}" title="${escapeHtml(tooltip)}">${badgeText}</span>`;
}

function renderBrainIntoEl(content, mem) {
  const profile = mem.profile || {};
  const clients = mem.clients || [];
  const projects = mem.projects || [];
  const preferences = mem.preferences || [];
  const importantFacts = mem.important_facts || [];
  const deadlines = mem.deadlines || [];
  const conflicts = mem.conflicts || [];

  // ⚠️ Conflicts Resolver UI
  let conflictsHtml = '';
  if (conflicts.length > 0) {
    conflictsHtml = `
      <div class="brain-section conflicts-section" style="border: 1px solid rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.06); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
        <div class="brain-section-title" style="color: #f38ba8; font-weight: 600; display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-size: 13px;">
          <span style="display:flex; align-items:center; gap:6px;">⚠️ Resolve Memory Conflicts</span>
          <span style="background: #f38ba8; color: #11111b; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 10px; display: inline-block;">${conflicts.length}</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${conflicts.map(c => {
            const keyPath = c.key;
            const existingVal = c.existing.value || c.existing.name || c.existing.item || '';
            const newVal = c.new.value || c.new.name || c.new.item || '';
            return `
              <div class="conflict-card" style="background: var(--bg-3); border: 1px solid var(--border); border-radius: 6px; padding: 10px; font-size: 12.5px;">
                <div style="font-weight: 700; text-transform: uppercase; font-size: 10px; color: var(--text-muted); margin-bottom: 6px; letter-spacing:0.04em;">Field: ${keyPath.replace(/\./g, ' → ')}</div>
                <div style="display: flex; flex-direction: column; gap: 6px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); padding: 6px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.03);">
                    <div style="flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; margin-right: 6px; font-size: 12px; color: var(--text-muted);">
                      <strong style="color:var(--text)">Current:</strong> ${escapeHtml(existingVal)}
                      <span style="font-size: 10.5px; color: #a6e3a1; font-weight: 500;">(${c.existing.confidence.toFixed(2)})</span>
                    </div>
                    <button class="conflict-choice-btn" onclick="resolveConflict('${c.id}', 'keep_existing')" style="background: var(--bg-2); border: 1px solid var(--border); color: var(--text); border-radius: 4px; padding: 3px 8px; font-size: 10.5px; font-weight:500; cursor: pointer;">Keep</button>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); padding: 6px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.03);">
                    <div style="flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; margin-right: 6px; font-size: 12px; color: var(--text-muted);">
                      <strong style="color:var(--text)">New:</strong> ${escapeHtml(newVal)}
                      <span style="font-size: 10.5px; color: #a6e3a1; font-weight: 500;">(${c.new.confidence.toFixed(2)})</span>
                    </div>
                    <button class="conflict-choice-btn" onclick="resolveConflict('${c.id}', 'use_new')" style="background: var(--accent); border: none; color: #fff; border-radius: 4px; padding: 3px 8px; font-size: 10.5px; font-weight:500; cursor: pointer;">Use New</button>
                  </div>
                  ${!keyPath.startsWith('profile.') ? `
                  <div style="text-align: center; margin-top: 2px;">
                    <button class="conflict-choice-btn" onclick="resolveConflict('${c.id}', 'keep_both')" style="background: none; border: none; color: var(--accent); font-size: 11px; font-weight: 500; cursor: pointer; text-decoration: underline;">Keep Both Versions</button>
                  </div>
                  ` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  const getProfileFieldHtml = (field, label, type = "text") => {
    const fObj = profile[field] || {};
    const val = typeof fObj === 'object' ? (fObj.value || '') : fObj || '';
    const score = typeof fObj === 'object' ? (fObj.confidence !== undefined ? fObj.confidence : 1.0) : 1.0;
    const reasoning = typeof fObj === 'object' ? fObj.reasoning : '';
    const sourceType = typeof fObj === 'object' ? fObj.source_type : 'manual';
    const lastReinforced = typeof fObj === 'object' ? fObj.last_reinforced : '';
    const badge = getConfidenceBadgeHtml(score, sourceType, reasoning, lastReinforced);
    const overrideBtn = (score < 1.0 && val) ? `
      <button class="brain-trust-btn" onclick="overrideProfileConfidence('${field}')" title="Trust (Force 1.0) field value: ${escapeHtml(reasoning)}" style="margin-left: 2px;">👍</button>
    ` : '';
    
    return `
      <div class="brain-profile-field" title="${escapeHtml(reasoning)}">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
          <label>${label}</label>
          <div style="display:flex; align-items:center; gap:4px;">
            ${badge}
            ${overrideBtn}
          </div>
        </div>
        <input type="${type}" id="bp-${field}" value="${escapeHtml(val)}">
      </div>
    `;
  };

  content.innerHTML = `
    ${conflictsHtml}
    
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid var(--border); padding-bottom:10px;">
      <span style="font-size:11px; color:var(--text-muted);">Last decay audit: ${escapeHtml(mem.last_decay_run || 'Never')}</span>
      <button class="decay-run-btn" onclick="runDecayJob()" style="background:transparent; border:1px solid var(--border); color:var(--text-muted); border-radius:4px; padding:3px 8px; font-size:10.5px; cursor:pointer; font-family:var(--font-sans); transition:all 0.15s;">🔄 Review Old Memories</button>
    </div>

    <!-- PROFILE SECTION -->
    <div class="brain-section">
      <div class="brain-section-title">User Profile</div>
      <div class="brain-profile-grid">
        ${getProfileFieldHtml("name", "Name")}
        ${getProfileFieldHtml("role", "Role")}
        ${getProfileFieldHtml("company", "Company")}
        ${getProfileFieldHtml("location", "Location")}
        ${getProfileFieldHtml("email", "Email", "email")}
        ${getProfileFieldHtml("phone", "Phone")}
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
  return lst.map(item => {
    const val = typeof item === 'object' ? item.value : item;
    const score = typeof item === 'object' ? (item.confidence !== undefined ? item.confidence : 1.0) : 1.0;
    const reasoning = typeof item === 'object' ? item.reasoning : '';
    const sourceType = typeof item === 'object' ? item.source_type : 'conversation';
    const lastReinforced = typeof item === 'object' ? item.last_reinforced : '';
    const badge = getConfidenceBadgeHtml(score, sourceType, reasoning, lastReinforced);
    const escapedVal = escapeHtml(val);
    const escapedReasoning = escapeHtml(reasoning);
    const isPinned = typeof item === 'object' ? (item.pinned || item.is_pinned || false) : false;
    
    const overrideBtn = score < 1.0 ? `
      <button class="brain-trust-btn" onclick="overrideConfidence('${key}', \`${escapedVal.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Trust fact (Force 1.0): ${escapedReasoning}">👍</button>
    ` : '';

    return `
      <div class="brain-list-item ${isPinned ? 'pinned' : ''}" title="${escapedReasoning}">
        <div style="display:flex; align-items:center; gap:6px; flex:1; min-width:0;">
          <span class="brain-list-text" style="flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapedVal}</span>
          ${badge}
        </div>
        <div style="display:flex; align-items:center; gap:4px; margin-left:6px;">
          ${overrideBtn}
          <button class="brain-pin-btn ${isPinned ? 'pinned' : ''}" onclick="togglePinListItem('${key}', \`${escapedVal.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`, ${!isPinned})" title="${isPinned ? 'Unpin item' : 'Pin item (give maximum importance boost)'}">📌</button>
          <button class="brain-delete-btn" onclick="deleteBrainListItem('${key}', \`${escapedVal.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete item">×</button>
        </div>
      </div>
    `;
  }).join('');
}

function renderBrainNotesItems(lst) {
  if (!lst || lst.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return lst.map(item => {
    const val = typeof item === 'object' ? item.value : item;
    const score = typeof item === 'object' ? (item.confidence !== undefined ? item.confidence : 1.0) : 1.0;
    const reasoning = typeof item === 'object' ? item.reasoning : '';
    const sourceType = typeof item === 'object' ? item.source_type : 'conversation';
    const lastReinforced = typeof item === 'object' ? item.last_reinforced : '';
    const badge = getConfidenceBadgeHtml(score, sourceType, reasoning, lastReinforced);
    const escapedVal = escapeHtml(val);
    const escapedReasoning = escapeHtml(reasoning);
    const isPinned = typeof item === 'object' ? (item.pinned || item.is_pinned || false) : false;
    
    const overrideBtn = score < 1.0 ? `
      <button class="brain-trust-btn" onclick="overrideConfidence('ai_notes', \`${escapedVal.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Trust: ${escapedReasoning}">👍</button>
    ` : '';

    return `
      <div class="brain-notes-card ${isPinned ? 'pinned' : ''}" title="${escapedReasoning}">
        <div style="display:flex; align-items:center; gap:6px; flex:1; min-width:0; margin-bottom:4px;">
          <span class="brain-list-text" style="flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapedVal}</span>
          ${badge}
        </div>
        <div style="display:flex; justify-content:flex-end; gap:4px; align-items:center;">
          ${overrideBtn}
          <button class="brain-pin-btn ${isPinned ? 'pinned' : ''}" onclick="togglePinListItem('ai_notes', \`${escapedVal.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`, ${!isPinned})" title="${isPinned ? 'Unpin note' : 'Pin note (give maximum importance boost)'}">📌</button>
          <button class="brain-delete-btn" onclick="deleteBrainListItem('ai_notes', \`${escapedVal.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete behavioral note">×</button>
        </div>
      </div>
    `;
  }).join('');
}

function renderBrainProjectItems(projects) {
  if (!projects || projects.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return projects.map(proj => {
    const name = proj.name || proj.value || '';
    const score = proj.confidence !== undefined ? proj.confidence : 0.85;
    const reasoning = proj.reasoning || '';
    const sourceType = proj.source_type || 'conversation';
    const lastReinforced = proj.last_reinforced || '';
    const badge = getConfidenceBadgeHtml(score, sourceType, reasoning, lastReinforced);
    const escapedName = escapeHtml(name);
    const isPinned = proj.pinned || proj.is_pinned || false;
    
    const overrideBtn = score < 1.0 ? `
      <button class="brain-trust-btn" onclick="overrideConfidence('projects', \`${escapedName.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Trust Project: ${escapeHtml(reasoning)}">👍</button>
    ` : '';
    
    return `
      <div class="brain-list-item ${isPinned ? 'pinned' : ''}" title="${escapeHtml(reasoning)}">
        <div class="brain-deadline-info" style="flex:1; min-width:0;">
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="brain-list-text" style="color:var(--text); font-weight:500; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${escapedName}</span>
            ${badge}
          </div>
          <span>Added: ${escapeHtml(proj.added || '')}</span>
        </div>
        <div style="display:flex; align-items:center; gap:4px;">
          ${overrideBtn}
          <button class="brain-pin-btn ${isPinned ? 'pinned' : ''}" onclick="togglePinListItem('projects', \`${escapedName.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`, ${!isPinned})" title="${isPinned ? 'Unpin project' : 'Pin project (give maximum importance boost)'}">📌</button>
          <button class="brain-delete-btn" onclick="deleteBrainProject(\`${escapedName.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete project">×</button>
        </div>
      </div>
    `;
  }).join('');
}

function renderBrainDeadlineItems(deadlines) {
  if (!deadlines || deadlines.length === 0) return '<div style="font-size:12px; color:var(--text-faint); padding: 4px;">None recorded yet.</div>';
  return deadlines.map(dl => {
    const item = dl.item || dl.value || '';
    const score = dl.confidence !== undefined ? dl.confidence : 0.85;
    const reasoning = dl.reasoning || '';
    const sourceType = dl.source_type || 'conversation';
    const lastReinforced = dl.last_reinforced || '';
    const badge = getConfidenceBadgeHtml(score, sourceType, reasoning, lastReinforced);
    const escapedItem = escapeHtml(item);
    const isPinned = dl.pinned || dl.is_pinned || false;
    
    const overrideBtn = score < 1.0 ? `
      <button class="brain-trust-btn" onclick="overrideConfidence('deadlines', \`${escapedItem.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Trust Deadline: ${escapeHtml(reasoning)}">👍</button>
    ` : '';
    
    return `
      <div class="brain-list-item ${isPinned ? 'pinned' : ''}" title="${escapeHtml(reasoning)}">
        <div class="brain-deadline-info" style="flex:1; min-width:0;">
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="brain-list-text" style="color:var(--text); font-weight:500; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${escapedItem}</span>
            ${badge}
          </div>
          <span style="color:var(--purple); font-weight:500;">Due: ${escapeHtml(dl.date || '')}</span>
        </div>
        <div style="display:flex; align-items:center; gap:4px;">
          ${overrideBtn}
          <button class="brain-pin-btn ${isPinned ? 'pinned' : ''}" onclick="togglePinListItem('deadlines', \`${escapedItem.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`, ${!isPinned})" title="${isPinned ? 'Unpin deadline' : 'Pin deadline (give maximum importance boost)'}">📌</button>
          <button class="brain-delete-btn" onclick="deleteBrainDeadline(\`${escapedItem.replace(/`/g, '\\`').replace(/'/g, "\\'")}\`)" title="Delete deadline">×</button>
        </div>
      </div>
    `;
  }).join('');
}

async function saveBrainProfile() {
  const fields = ["name", "role", "company", "location", "email", "phone"];
  let updatedCount = 0;

  for (const field of fields) {
    const el = document.getElementById(`bp-${field}`);
    if (!el) continue;

    const newVal = el.value.trim();
    const fieldObj = (currentBrainMemory.profile || {})[field] || {};
    const oldVal = typeof fieldObj === 'object' ? (fieldObj.value || "") : (fieldObj || "");

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

async function overrideConfidence(key, value) {
  try {
    const resp = await fetch('/api/memory/override_confidence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: key, value: value, confidence: 1.0 })
    });
    if (resp.ok) {
      await loadBrainMemory();
    } else {
      const err = await resp.json();
      alert(err.error || "Failed to override confidence.");
    }
  } catch (e) {
    console.error("Failed to override confidence:", e);
  }
}

async function overrideProfileConfidence(field) {
  try {
    const resp = await fetch('/api/memory/override_confidence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: "profile", field: field, confidence: 1.0 })
    });
    if (resp.ok) {
      await loadBrainMemory();
    } else {
      const err = await resp.json();
      alert(err.error || "Failed to override profile confidence.");
    }
  } catch (e) {
    console.error("Failed to override profile confidence:", e);
  }
}

async function resolveConflict(conflictId, action) {
  try {
    const resp = await fetch('/api/memory/resolve_conflict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conflict_id: conflictId, action: action })
    });
    if (resp.ok) {
      await loadBrainMemory();
    } else {
      const err = await resp.json();
      alert(err.error || "Failed to resolve conflict.");
    }
  } catch (e) {
    console.error("Failed to resolve conflict:", e);
  }
}

async function runDecayJob() {
  try {
    const resp = await fetch('/api/memory/run_decay', { method: 'POST' });
    if (resp.ok) {
      await loadBrainMemory();
      alert("Memory decay and review job completed successfully!");
    } else {
      const err = await resp.json();
      alert(err.error || "Failed to run memory decay.");
    }
  } catch (e) {
    console.error("Failed to run decay job:", e);
  }
}

async function toggleSelfReflection(checkbox) {
  const enabled = checkbox.checked;
  try {
    const resp = await fetch(`/api/workspaces/${activeWorkspaceId}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ self_reflection_enabled: enabled })
    });
    if (!resp.ok) {
      throw new Error('Failed to update workspace settings');
    }
    const activeWs = userWorkspaces.find(w => w.id === activeWorkspaceId);
    if (activeWs) {
      if (!activeWs.settings) activeWs.settings = {};
      activeWs.settings.self_reflection_enabled = enabled;
    }
  } catch (err) {
    alert("Error saving setting: " + err.message);
    checkbox.checked = !enabled;
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
      // Always fetch the authoritative list from the server so that
      // RAG-ingested PDFs/DOCXs (which don't go into data.files) also appear.
      let fileList = data.files || [];
      try {
        const listResp = await fetch('/api/upload/list');
        if (listResp.ok) {
          const listData = await listResp.json();
          if (listData.files && listData.files.length > 0) {
            fileList = listData.files;
          }
        }
      } catch (listErr) {
        console.warn('[Upload] Could not fetch file list:', listErr);
      }

      renderUploadedChips(fileList);

      // Show informative messages only
      let msg = "";
      if (data.rag_ingested && data.rag_ingested.length) {
        msg += "✅ Ingested to Workspace Knowledge:\n" + data.rag_ingested.join("\n") + "\n\n";
      }
      if (data.errors && data.errors.length) {
        msg += "⚠️ Upload warning:\n" + data.errors.join("\n");
      }
      if (msg) {
        alert(msg.trim());
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

  // Helper: pick the right icon for the file extension
  function fileIcon(name, isRag) {
    const ext = (name || '').split('.').pop().toLowerCase();
    if (ext === 'pdf')  return '📕';
    if (ext === 'docx') return '📘';
    if (ext === 'py' || ext === 'js' || ext === 'ts' || ext === 'jsx' || ext === 'tsx') return '💻';
    if (ext === 'csv' || ext === 'json') return '📊';
    if (ext === 'md')   return '📝';
    return '📄';
  }

  container.innerHTML = files.map(file => {
    const isLarge = file.size > 512000;
    const isRag   = !!file.is_rag;
    const warningClass = isLarge ? 'warning' : '';
    const ragClass     = isRag   ? 'rag-chip' : '';
    const displaySize  = (file.size / 1024).toFixed(1) + ' KB';
    const warningTitle = isLarge ? 'title="Large file — may consume substantial context window"' : '';
    const ragBadge     = isRag
      ? '<span class="chip-rag-badge" title="Ingested into Workspace Knowledge">⚡ Knowledge</span>'
      : '';

    return `
      <div class="upload-chip ${warningClass} ${ragClass}" ${warningTitle}>
        <span class="chip-icon">${fileIcon(file.name, isRag)}</span>
        <span class="chip-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
        <span class="chip-size">(${displaySize})</span>
        ${ragBadge}
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
