import re
from backend.extensions import tavily
from backend.utils import is_ad_content

SEARCH_YES = [
    r"\blatest\b", r"\bcurrent(ly)?\b", r"\bthis week\b", r"\bthis month\b", r"\brecent(ly)?\b",
    r"\bnews\b", r"\btrend(ing|s)?\b", r"\bstats?\b", r"\bstatistics\b",
    r"\bhow much (does|is|are|do)\b", r"\bwhat('s| is) the (price|cost|rate)\b",
    r"\blook up\b", r"\bsearch for\b", r"\bfind (me )?info\b", r"\bgoogle\b",
    r"\b202[4-9]\b",
    r"\bcompetitor(s)?\b", r"\bmarket (share|size|research|data)\b",
    r"\b(instagram|facebook|tiktok|google) (algorithm|update|feature|change)\b",
    r"\bsocial media (trend|stat|update|news)\b",
    r"\b(sa|south african?) (law|regulation|budget|news|vat|tax)\b",
    r"\bexchange rate\b", r"\brand.{0,10}dollar\b",
    r"\bdigital marketing (trend|stat|news)\b",
    r"\blatest version\b", r"\bchangelog\b", r"\bnew release\b",
    r"\bdoes .+ support\b", r"\bcompatib",
]

SEARCH_NO = [
    r"\bwhat (day|date|time) is it\b",
    r"\bwhat('s| is) (today|the date|the time|the day)\b",
    r"\btoday('s)? date\b", r"\bcurrent (date|time|day)\b",
    r"\bwhat day (is it|are we|of the week)\b",
    r"\bwhat (year|month) (is it|are we in)\b",
    r"\btell me the (date|time|day)\b",
    r"\bwhat time (is it|in south africa)\b",
    r"^write (a|an|me )", r"^create (a|an|me )", r"^draft (a|an|me )",
    r"^give me (a|an )", r"^generate (a|an )", r"^make (a|an|me )",
    r"^help me (write|create|draft|rewrite|improve)",
    r"^(rewrite|improve|edit|fix|rephrase|shorten|lengthen)\b",
    r"^what should i\b",
    r"\bred rooms?\b", r"\blocanto\b", r"\bphone entertainment\b",
    r"\boperator ad\b", r"\bwrite.*ad\b", r"\bad for\b",
    r"\bcreate.*ad\b", r"\bad copy\b", r"\bcopy for\b",
    r"^(write|build|create|make|code|implement|generate) (a |an |me )?(function|script|class|component|app|api|route|query|snippet|module|bot|tool)",
    r"^(fix|debug|review|refactor|optimise|optimize|explain|simplify) (my |this |the )?(code|script|function|class|error|bug|file)",
    r"^how (do i|can i|should i) (code|write|build|implement|fix|use|set up|install)",
    r"\bwrite (a |the )?(function|class|script|component|query|loop|api|endpoint)\b",
]

def should_search(text: str) -> bool:
    if not text or len(text.strip()) < 6:
        return False
    tl = text.lower().strip()
    for pat in SEARCH_NO:
        if re.search(pat, tl):
            return False
    for pat in SEARCH_YES:
        if re.search(pat, tl):
            return True
    return False

def refine_query(text: str) -> str:
    t = text.strip()
    fillers = [
        r"^(can you |could you |please |just |quickly )?(look up|search for|find|google|check)\s+(me\s+)?(the\s+)?",
        r"^(what is|what are|who is|tell me about|do you know|i want to know about)\s+",
        r"^(give me|show me)\s+(the\s+)?",
        r"^(i need|i want)\s+(to know|info on|information on|to find out)?\s+",
    ]
    for pat in fillers:
        t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()
    return " ".join(t.split()[:10])

def web_search(raw_query: str, max_results: int = 6) -> str:
    query = refine_query(raw_query) or raw_query
    try:
        resp = tavily.search(query=query, max_results=max_results)
        results = resp.get("results", [])
        if not results:
            broad = " ".join(query.split()[:4])
            resp = tavily.search(query=broad, max_results=3)
            results = resp.get("results", [])
        if not results:
            return ""
        blocks = []
        for i, r in enumerate(results, 1):
            title  = (r.get("title") or "").strip()
            body   = (r.get("content") or "").strip()
            source = (r.get("url") or "").strip()
            if len(body) > 280:
                body = body[:280].rsplit(" ", 1)[0] + "…"
            blocks.append(f"[{i}] {title}\n{body}\nSource: {source}")
        return f'Search query: "{query}"\n\n' + "\n\n".join(blocks)
    except Exception as e:
        return f"Web search unavailable ({type(e).__name__})."
