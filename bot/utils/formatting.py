import re
from datetime import datetime

_URL_RE = re.compile(r'https?://[^\s<>"\']+')
_IN_TAG_RE = re.compile(r'<a\s[^>]*>.*?</a>', re.IGNORECASE | re.DOTALL)


def linkify_urls(text: str) -> str:
    """Wrap plain URLs in <a> tags. Skip URLs already inside <a>."""
    protected: list[tuple[int, int]] = []
    for m in _IN_TAG_RE.finditer(text):
        protected.append((m.start(), m.end()))

    def _in_tag(start: int, end: int) -> bool:
        return any(ps <= start and end <= pe for ps, pe in protected)

    parts: list[str] = []
    last = 0
    for m in _URL_RE.finditer(text):
        if _in_tag(m.start(), m.end()):
            continue
        parts.append(text[last:m.start()])
        url = m.group()
        parts.append(f'<a href="{url}">{url}</a>')
        last = m.end()
    parts.append(text[last:])
    return "".join(parts)


def format_dt(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")
