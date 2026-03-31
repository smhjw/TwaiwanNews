from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import requests

GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=TW"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def fetch_google_trends_tw(limit: int = 10) -> list[dict]:
    """Fetch Taiwan daily trending searches from Google Trends RSS."""
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(GOOGLE_TRENDS_RSS, headers=headers, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    ht_ns = "https://trends.google.com/trending/rss"

    results = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", "").strip()
        # try to get first news article URL from ht:news_item
        news_url = ""
        news_title = ""
        for news_item in item.findall(f"{{{ht_ns}}}news_item"):
            news_url = news_item.findtext(f"{{{ht_ns}}}news_item_url", "").strip()
            news_title = news_item.findtext(f"{{{ht_ns}}}news_item_title", "").strip()
            if news_url:
                break
        traffic = item.findtext(f"{{{ht_ns}}}approx_traffic", "").strip()
        results.append({
            "query": title,
            "traffic": traffic,
            "news_title": news_title,
            "news_url": news_url,
        })
    return results
