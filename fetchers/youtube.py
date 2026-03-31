from __future__ import annotations

import requests

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"


def fetch_youtube_trending(api_key: str, limit: int = 5) -> list[dict]:
    """Fetch trending YouTube videos for Taiwan (regionCode=TW)."""
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": "TW",
        "maxResults": limit,
        "key": api_key,
    }
    resp = requests.get(YOUTUBE_API_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("items", [])[:limit]:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        vid_id = item.get("id", "")
        results.append({
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "view_count": int(stats.get("viewCount", 0)),
            "url": f"https://www.youtube.com/watch?v={vid_id}",
        })
    return results
