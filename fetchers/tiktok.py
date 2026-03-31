from __future__ import annotations

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
# TikTok Creative Center trending songs (TW region)
TIKTOK_TRENDING_URL = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend/hashtag/list"


def fetch_tiktok_trending(limit: int = 5) -> list[dict]:
    """Fetch trending hashtags from TikTok Creative Center (TW region)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://ads.tiktok.com/",
    }
    params = {
        "period": 7,
        "country_code": "TW",
        "page": 1,
        "limit": limit,
    }
    resp = requests.get(TIKTOK_TRENDING_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = []
    # Navigate response structure: data.data.list
    raw_list = data.get("data", {}).get("list", [])
    for item in raw_list[:limit]:
        items.append({
            "hashtag": item.get("hashtag_name", ""),
            "posts_count": item.get("publish_cnt", 0),
            "views": item.get("video_views", 0),
        })
    return items
