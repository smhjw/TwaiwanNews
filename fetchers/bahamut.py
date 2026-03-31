from __future__ import annotations

import requests
from bs4 import BeautifulSoup

BAHAMUT_HOT_URL = "https://forum.gamer.com.tw/index.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

MOBILE_GAME_BSN = {
    "74934",  # 鳴潮
    "74604",  # 明日方舟：終末地
    "72822",  # 崩壞：星穹鐵道
    "75703",  # 燕雲十六聲
    "25908",  # 天堂 Mobile
    "36390",  # 勝利女神：妮姬
    "36730",  # 原神
    "25052",  # 怪物彈珠
    "74860",  # 絕區零
    "79354",  # MapleStory Worlds
    "23805",  # 神魔之塔
    "23772",  # 貓咪大戰爭
    "83054",  # RO 仙境傳說：世界之旅
    "84500",  # RO 仙境傳說：愛如初見 Classic
    "81995",  # 星之救援者
    "82913",  # AION2
}


def fetch_bahamut_hot(limit: int = 10) -> list[dict]:
    """Fetch hot posts from Bahamut forum index, prioritizing mobile games."""
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(BAHAMUT_HOT_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    mobile_results = []
    other_results = []

    for row in soup.select("tr"):
        title_td = row.select_one("td.b-list__main")
        if not title_td:
            continue
        a_tag = title_td.select_one("a")
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "")
        if not href:
            continue
        url = href if href.startswith("http") else f"https://forum.gamer.com.tw/{href}"

        # extract bsn from URL
        bsn = ""
        for part in href.split("&"):
            if part.startswith("bsn="):
                bsn = part[4:]
                break

        # get board name
        board_td = row.select_one("td.b-list__game")
        board = board_td.get_text(strip=True) if board_td else ""

        item = {"title": title, "url": url, "board": board, "bsn": bsn}
        if bsn in MOBILE_GAME_BSN:
            mobile_results.append(item)
        else:
            other_results.append(item)

    # mobile games first, then others
    results = mobile_results + other_results
    return results[:limit]
