from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

DCARD_RSS = "https://www.dcard.tw/rss"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def fetch_dcard_hot(limit: int = 5) -> list[dict]:
    """Fetch hot posts from Dcard RSS feed."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml",
    }
    resp = requests.get(DCARD_RSS, headers=headers, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    ns = {"dc": "http://purl.org/dc/elements/1.1/"}

    items = root.findall(".//item")
    results = []
    for item in items[:limit]:
        title = item.findtext("title", "").strip()
        url = item.findtext("link", "").strip()
        category = item.findtext("category", "").strip()
        results.append({
            "title": title,
            "forum": category,
            "url": url,
            "like_count": 0,
        })
    return results
