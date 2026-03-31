from __future__ import annotations

import json
import re

import requests

BAHAMUT_HOT_URL = "https://forum.gamer.com.tw/index.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

MOBILE_GAME_BSN = {
    "74934", "74604", "72822", "75703", "25908",
    "36390", "36730", "25052", "74860", "79354",
    "23805", "23772", "83054", "84500", "81995", "82913",
}


def _extract_board_list(html_bytes: bytes) -> list[dict]:
    """Extract board list from Next.js hydration data."""
    # Match chunks as raw bytes to preserve encoding
    chunks = re.findall(rb'self\.__next_f\.push\(\[\d+,"(.*?)"\]\)', html_bytes, re.DOTALL)
    for chunk in chunks:
        if b'topicTitle' not in chunk:
            continue
        # Wrap in quotes and parse as JSON string to unescape \" etc.
        try:
            decoded: str = json.loads(b'"' + chunk + b'"')
        except Exception:
            continue
        brace = decoded.find('{')
        if brace == -1:
            continue
        try:
            data = json.loads(decoded[brace:])
        except Exception:
            continue
        if isinstance(data, dict) and 'pages' in data:
            pages = data['pages']
            if pages and isinstance(pages[0], list):
                return pages[0]
    return []


def fetch_bahamut_hot(limit: int = 10) -> list[dict]:
    """Fetch hot posts from Bahamut forum index, prioritizing mobile games."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-TW,zh;q=0.9",
    }
    resp = requests.get(BAHAMUT_HOT_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    boards = _extract_board_list(resp.content)

    mobile_results = []
    other_results = []

    for board in boards:
        bsn = str(board.get("bsn", ""))
        topic_title = board.get("topicTitle", "").strip()
        topic_sn = board.get("topicSn", "")
        board_name = board.get("title", "").strip()
        if not topic_title or not topic_sn:
            continue
        url = f"https://forum.gamer.com.tw/C.php?bsn={bsn}&snA={topic_sn}"
        item = {"title": topic_title, "url": url, "board": board_name, "bsn": bsn}
        if bsn in MOBILE_GAME_BSN:
            mobile_results.append(item)
        else:
            other_results.append(item)

    results = mobile_results + other_results
    return results[:limit]
