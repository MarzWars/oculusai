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
