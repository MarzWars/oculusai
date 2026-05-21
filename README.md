<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Oculus AI</title>
</head>

<body style="margin:0; font-family:Arial, sans-serif; background:#0b0f14; color:#e6e6e6; line-height:1.6;">

<div style="max-width:900px; margin:0 auto; padding:40px 20px;">

  <!-- HEADER -->
  <div style="text-align:center; padding-bottom:30px; border-bottom:1px solid #222;">
    <h1 style="font-size:40px; margin:0; color:#7c5cff;">🧠 Oculus AI</h1>
    <p style="font-size:16px; color:#aaa; margin-top:10px;">
      Built for Lex Digitals • Designed by Alex • A real-world intelligence system
    </p>
  </div>

  <!-- INTRO -->
  <div style="padding:30px 0;">
    <p style="font-size:18px;">
      <b>Oculus AI</b> is a custom-built intelligent assistant that combines conversational AI, developer tooling,
      marketing intelligence, and long-term memory into one unified system.
    </p>

    <p style="color:#bbb;">
      It is built to think fast, respond cleanly, and handle real business and coding work without fluff or delay.
    </p>
  </div>

  <!-- CORE FEATURES -->
  <h2 style="color:#7c5cff;">⚙️ Core Capabilities</h2>

  <ul>
    <li><b>Conversational Intelligence:</b> Context-aware dialogue with memory of past interactions</li>
    <li><b>Long-Term Memory (Supabase):</b> Stores profile, projects, preferences, and business context</li>
    <li><b>Live Web Awareness:</b> Real-time search using DuckDuckGo when needed</li>
    <li><b>Developer Assistant:</b> Writes full working code, debugs issues, supports multiple languages</li>
    <li><b>Marketing Engine:</b> Ads, branding, SEO, customer replies, and content strategy</li>
  </ul>

  <!-- MEMORY -->
  <h2 style="color:#7c5cff;">🧠 Memory System</h2>

  <p>
    Oculus remembers key user data across sessions using Supabase:
  </p>

  <div style="background:#111826; padding:15px; border-radius:10px; font-family:monospace; font-size:13px; overflow:auto;">
{
  "profile": {
    "name": "",
    "role": "",
    "company": "",
    "location": "",
    "email": "",
    "phone": ""
  },
  "clients": [],
  "projects": [],
  "preferences": [],
  "important_facts": [],
  "topics_discussed": [],
  "deadlines": [],
  "conversation_count": 0
}
  </div>

  <!-- ARCHITECTURE -->
  <h2 style="color:#7c5cff;">🏗️ Architecture</h2>

  <div style="background:#111826; padding:15px; border-radius:10px; font-family:monospace; font-size:13px;">
Flask Backend  
│  
├── Gradio Client → Xoltron AI (darkc0de/chat)  
├── Supabase → Persistent memory system  
├── DuckDuckGo → Live web search  
├── JSON → Chat history + summaries  
└── Prompt Engine → Context + memory injection  
  </div>

  <!-- PHILOSOPHY -->
  <h2 style="color:#7c5cff;">⚡ Design Philosophy</h2>

  <ul>
    <li>Clarity over fluff</li>
    <li>Function over theory</li>
    <li>Real-world usefulness over academic noise</li>
  </ul>

  <p style="margin-top:10px;">
    Oculus is built to be:
  </p>

  <ul>
    <li><b>Uncensored in reasoning</b></li>
    <li><b>Unfiltered in output</b></li>
    <li><b>Zero-fluff by design</b></li>
  </ul>

  <p style="color:#aaa;">
    It does not waste time with corporate language or unnecessary explanation. It delivers direct, usable output.
  </p>

  <!-- DEPLOYMENT -->
  <h2 style="color:#7c5cff;">🚀 Deployment</h2>

  <p>Requirements:</p>
  <ul>
    <li>Python 3.10+</li>
    <li>Flask</li>
    <li>Supabase account</li>
    <li>Gradio Xoltron access</li>
    <li>DuckDuckGo Search</li>
  </ul>

  <p style="font-family:monospace; background:#111826; padding:10px; border-radius:8px;">
SUPABASE_URL=your_supabase_url<br>
SUPABASE_KEY=your_supabase_key
  </p>

  <!-- FINAL NOTE -->
  <div style="margin-top:40px; padding-top:20px; border-top:1px solid #222; text-align:center;">
    <h2 style="color:#7c5cff;">💀 Final Note</h2>
    <p style="color:#bbb;">
      Oculus is not just an assistant — it is a system that learns, adapts, and evolves with real usage.
    </p>

    <p style="font-weight:bold;">
      Built to think. Built to execute. Built for real work.
    </p>
  </div>

</div>

</body>
</html>
