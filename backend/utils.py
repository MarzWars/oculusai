import re

AD_CONTENT_PATTERNS = [
    r"\bred rooms?\b", r"\blocanto\b", r"\bphone entertainment\b",
    r"\boperator ad\b", r"\blooking for your dream\b",
    r"\bno strings\b", r"\bdiscrete\b", r"\bintimate\b",
    r"\bnaughty\b", r"\bsexy\b", r"\bescort\b",
]

def _esc(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def is_ad_content(text: str) -> bool:
    tl = text.lower()
    return any(re.search(p, tl) for p in AD_CONTENT_PATTERNS)

def _add_unique(lst: list, item: str, max_len: int = 30) -> bool:
    item = item.strip()
    if not item:
        return False
    for e in lst:
        val = (e.get("value") or e.get("name") or e.get("item") or "") if isinstance(e, dict) else e
        if str(val).lower() == item.lower():
            return False
    lst.append(item)
    if len(lst) > max_len:
        lst[:] = lst[-max_len:]
    return True

def _render_links(text: str) -> str:
    """Convert markdown links and bare URLs to clickable <a> tags."""
    # [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        text
    )
    # Bare URLs
    text = re.sub(
        r'(?<!["\(])(https?://[^\s<>")\]]+)',
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        text
    )
    return text
