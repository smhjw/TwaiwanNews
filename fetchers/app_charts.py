from __future__ import annotations

import requests


def fetch_appstore_tw_free_games(limit: int = 5) -> list[dict]:
    """Fetch Taiwan App Store top free games via iTunes RSS API."""
    url = f"https://itunes.apple.com/tw/rss/topfreeapplications/limit=25/genre=6014/json"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    entries = data.get("feed", {}).get("entry", [])
    results = []
    for e in entries:
        name = e.get("im:name", {}).get("label", "").strip()
        artist = e.get("im:artist", {}).get("label", "").strip()
        links = e.get("link", [])
        if not isinstance(links, list):
            links = [links]
        href = ""
        for lk in links:
            h = lk.get("attributes", {}).get("href", "")
            if "apps.apple.com" in h:
                href = h
                break
        if name:
            results.append({"name": name, "developer": artist, "url": href})
        if len(results) >= limit:
            break
    return results


def fetch_googleplay_tw_free_games(limit: int = 5) -> list[dict]:
    """Fetch Taiwan Google Play top free games via google-play-scraper."""
    try:
        from google_play_scraper import app as gp_app
    except ImportError:
        return []
    # Top free game app IDs for Taiwan (manually maintained popular ones as seed,
    # then fetch live data for each)
    # Use search to find top results
    try:
        from google_play_scraper import search
        results = search(
            "免費遊戲",
            lang="zh-TW",
            country="tw",
            n_hits=limit,
        )
        items = []
        for r in results[:limit]:
            items.append({
                "name": r.get("title", ""),
                "developer": r.get("developer", ""),
                "url": f"https://play.google.com/store/apps/details?id={r.get('appId', '')}",
            })
        return items
    except Exception:
        return []
