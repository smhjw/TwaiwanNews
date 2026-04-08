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
        from google_play_scraper import search
        
        # In newer versions of google_play_scraper, collection('TOP_FREE') is broken
        # due to Google Play DOM changes. A reliable workaround is using 'search' 
        # with localized high-traffic keywords for Taiwan free game charts.
        results = search(
            "免費遊戲排行榜",
            lang="zh-TW",
            country="tw",
            n_hits=limit * 3,  # Fetch extra to filter out paid/duplicates
        )
        
        items = []
        seen = set()
        
        for r in results:
            title = r.get("title", "").strip()
            if not title:
                continue
                
            # Skip paid apps if any slip into search results
            price = r.get("price")
            if price and price != 0 and str(price) != "0":
                continue
                
            if title not in seen:
                seen.add(title)
                items.append({
                    "name": title,
                    "developer": r.get("developer", "").strip(),
                    "url": f"https://play.google.com/store/apps/details?id={r.get('appId', '')}",
                })
                
            if len(items) >= limit:
                break
                
        return items
    except Exception:
        return []
