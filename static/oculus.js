const feed         = document.getElementById("chatFeed");
const input        = document.getElementById("msgInput");
const typing       = document.getElementById("typingIndicator");
const streamRow    = document.getElementById("streamRow");
const streamBubble = document.getElementById("streamBubble");

function scrollBottom() {
    feed.scrollTop = feed.scrollHeight;
}
scrollBottom();

function fillMsg(el) {
    input.value = el.textContent;
    input.focus();
}

function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function esc(str) {
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function appendUserBubble(text) {
    const empty = feed.querySelector(".empty-state");
    if (empty) empty.remove();

    if (!feed.querySelector(".date-divider")) {
        const d = document.createElement("div");
        d.className = "date-divider";
        d.textContent = "Today";
        feed.insertBefore(d, typing);
    }

    const row = document.createElement("div");
    row.className = "bubble-row user-row";
    row.innerHTML = `
        <div class="bubble user-bubble"><p>${esc(text)}</p></div>
        <div class="avatar user-avatar">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="8" r="4" fill="currentColor"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
        </div>`;
    feed.insertBefore(row, typing);
    scrollBottom();
}

function appendAiBubble(text) {
    const row = document.createElement("div");
    row.className = "bubble-row ai-row";
    row.innerHTML = `
        <div class="avatar ai-avatar">O</div>
        <div class="bubble ai-bubble">${text.replace(/\n/g, '<br>')}</div>`;
    feed.insertBefore(row, typing);
    scrollBottom();
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    appendUserBubble(text);

    typing.classList.add("visible");
    scrollBottom();

    const response = await fetch("/ask", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ message: text })
    });

    typing.classList.remove("visible");
    streamRow.classList.add("visible");
    streamBubble.textContent = "";
    streamBubble.classList.remove("done");

    const reader  = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer    = "";

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        streamBubble.textContent = buffer;
        scrollBottom();
    }

    streamBubble.classList.add("done");
    streamRow.classList.remove("visible");
    streamBubble.textContent = "";
    appendAiBubble(buffer);
    input.focus();
}

async function clearChat() {
    await fetch("/clear", { method: "POST" });
    location.reload();
}