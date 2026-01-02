from datetime import datetime
import datetime
from urllib.parse import unquote


def extract_metadata(response=None, xpaths=None, raw_content="") -> dict:
    """
    Extract structured metadata from response or raw_content.
    Supports optional XPath config and hash/length calculations.
    Safe if response is None.
    """
    x = xpaths or {}
    raw = raw_content or (getattr(response, "text", None) or "")

    def try_xpath(key, default=""):
        if response and x.get(key):
            result = response.xpath(x.get(key, "")).get(default)
            return result.strip() if result else default
        return default
     # Decode referer if present
    referer = ""
    if response:
        raw_referer = response.request.headers.get(
            "Referer", b"").decode("utf-8", "ignore")
        referer = unquote(raw_referer)

    return {
        "status": getattr(response, "status", None),
        "headers": {
            "content_type": (response.headers.get("Content-Type", b"").decode("utf-8", "ignore")
                             if response else ""),
            "last_modified": (response.headers.get("Last-Modified", b"").decode("utf-8", "ignore")
                              if response else "")
        },
        "encoding": getattr(response, "encoding", "utf-8"),
        "depth": response.meta.get("depth", 0) if response else 0,
        "referer": referer,
        "html_length": len(raw) if raw else 0,
        "meta_description": try_xpath("meta_description", ""),
        "crawl_date": datetime.datetime.utcnow().isoformat()
    }
