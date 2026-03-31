from __future__ import annotations

import requests

DCARD_API = "https://www.dcard.tw/service/api/v2/posts"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_dcard_hot(limit: int = 5) -> list[dict]:
    """Fetch hot posts from Dcard public API."""
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://www.dcard.tw/",
    }
    params = {
        "popular": "true",
        "limit": limit,
    }
    resp = requests.get(DCARD_API, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    posts = resp.json()
    results = []
    for post in posts[:limit]:
        results.append({
            "title": post.get("title", ""),
            "forum": post.get("forumName", ""),
            "like_count": post.get("likeCount", 0),
            "comment_count": post.get("commentCount", 0),
            "url": f"https://www.dcard.tw/f/{post.get('forumAlias', '')}/p/{post.get('id', '')}",
        })
    return results
