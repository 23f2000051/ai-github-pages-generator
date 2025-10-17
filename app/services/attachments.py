import re
import base64
from typing import List, Dict

# Matches: data:<mime>;base64,<data>
_DATA_URI_RE = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$", flags=re.I)

def parse_attachments(attachments: List[Dict]) -> List[Dict]:
    """Convert incoming attachments to file dicts usable for pushing.

    Each returned dict:
      - path: filename (from attachment['name'])
      - content: decoded UTF-8 text OR base64 string (raw base64 data)
      - encoding: "utf-8" or "base64" or "url" or "raw"
      - mime: mime type when available
    """
    out: List[Dict] = []
    for a in attachments or []:
        name = a.get("name")
        url = a.get("url", "")
        if not name or not url:
            continue

        m = _DATA_URI_RE.match(url)
        if m:
            mime = m.group("mime").lower()
            # Clean base64 data: remove whitespace, newlines that might have been added
            b64data = m.group("data").strip()
            b64data = ''.join(b64data.split())  # Remove ALL whitespace including newlines
            
            # Prefer treating text/* as UTF-8 if decodable
            if mime.startswith("text/") or mime in ("application/json", "application/javascript"):
                try:
                    decoded = base64.b64decode(b64data).decode("utf-8")
                    out.append({"path": name, "content": decoded, "encoding": "utf-8", "mime": mime})
                    continue
                except Exception:
                    # fallback to keeping base64
                    out.append({"path": name, "content": b64data, "encoding": "base64", "mime": mime})
                    continue
            else:
                # binary (image, etc.) — keep base64 (cleaned)
                out.append({"path": name, "content": b64data, "encoding": "base64", "mime": mime})
                continue

        # If it's an http(s) URL — caller may want to download
        if url.startswith("http://") or url.startswith("https://"):
            out.append({"path": name, "content": url, "encoding": "url", "mime": None})
            continue

        # Unknown format — treat as raw string
        out.append({"path": name, "content": url, "encoding": "raw", "mime": None})

    return out
