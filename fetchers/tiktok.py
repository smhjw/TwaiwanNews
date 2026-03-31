from __future__ import annotations

import requests

# Google Trends daily search trends for Taiwan region
GOOGLE_TRENDS_URL = (
    "https://trends.google.com/trends/api/dailytrends"
    "?hl=zh-TW&tz=-480&geo=TW&ns=15"
)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def fetch_tiktok_trending(limit: int = 5) -> list[dict]:
    """Fetch Taiwan daily trending searches from Google Trends (replaces TikTok)."""
    import json

    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(GOOGLE_TRENDS_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    # Google Trends prepends ")]}'\n" to prevent XSSI
    text = resp.text
    for prefix in (")]}'\n", ")]}\'\n", ")]}'"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    data = json.loads(text)
    trending_searches = (
        data.get("default", {})
        .get("trendingSearchesDays", [{}])[0]
        .get("trendingSearches", [])
    )

    results = []
    for item in trending_searches[:limit]:
        title = item.get("title", {}).get("query", "")
        traffic = item.get("formattedTraffic", "")
        articles = item.get("articles", [])
        url = articles[0].get("url", "") if articles else ""
        results.append({
            "hashtag": title,
            "traffic": traffic,
            "url": url,
        })
    return results
