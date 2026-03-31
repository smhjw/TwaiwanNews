from __future__ import annotations

import requests
from bs4 import BeautifulSoup

PTT_HOT_BOARDS_URL = "https://www.ptt.cc/bbs/hotboards.html"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def _session() -> requests.Session:
    s = requests.Session()
    s.cookies.set("over18", "1", domain="www.ptt.cc")
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _fetch_board_top_post(s: requests.Session, board_url: str) -> dict | None:
    try:
        resp = s.get(board_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        entries = soup.select("div.r-ent")
        best = None
        best_push = -999
        for entry in entries:
            title_tag = entry.select_one("div.title a")
            if not title_tag:
                continue
            nrec = entry.select_one("div.nrec span")
            push = 0
            if nrec:
                txt = nrec.text.strip()
                if txt == "爆":
                    push = 100
                elif txt.startswith("X"):
                    push = -int(txt[1:]) if txt[1:].isdigit() else -1
                elif txt.isdigit():
                    push = int(txt)
            if push > best_push:
                best_push = push
                href = title_tag.get("href", "")
                best = {
                    "title": title_tag.text.strip(),
                    "url": f"https://www.ptt.cc{href}",
                    "push": push,
                }
        return best
    except Exception:
        return None


def fetch_ptt_hot(limit: int = 5) -> list[dict]:
    s = _session()
    resp = s.get(PTT_HOT_BOARDS_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for a_tag in soup.select("a.board")[:limit * 2]:
        name_tag = a_tag.select_one("div.board-name")
        cat_tag = a_tag.select_one("div.board-class")
        if not name_tag:
            continue
        board_name = name_tag.text.strip()
        category = cat_tag.text.strip() if cat_tag else ""
        href = a_tag.get("href", "")
        board_url = f"https://www.ptt.cc{href}"
        top_post = _fetch_board_top_post(s, board_url)
        results.append({
            "board": board_name,
            "category": category,
            "board_url": board_url,
            "top_post": top_post,
        })
        if len(results) >= limit:
            break
    return results
