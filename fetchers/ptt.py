from __future__ import annotations

import requests

PTT_HOT_BOARDS_URL = "https://www.ptt.cc/bbs/hotboards.html"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_ptt_hot(limit: int = 5) -> list[dict]:
    """Fetch top hot boards and their top post from PTT."""
    session = requests.Session()
    session.cookies.set("over18", "1", domain="www.ptt.cc")
    headers = {"User-Agent": USER_AGENT}

    resp = session.get(PTT_HOT_BOARDS_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    from html.parser import HTMLParser

    class HotBoardParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.boards: list[dict] = []
            self._in_board = False
            self._in_name = False
            self._in_class = False
            self._current: dict = {}

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            if tag == "a" and "board" in cls:
                self._in_board = True
                href = attrs_dict.get("href", "")
                self._current = {"url": f"https://www.ptt.cc{href}"}
            if self._in_board and tag == "div" and "board-name" in cls:
                self._in_name = True
            if self._in_board and tag == "div" and "board-class" in cls:
                self._in_class = True

        def handle_data(self, data):
            if self._in_name:
                self._current["name"] = data.strip()
                self._in_name = False
            if self._in_class:
                self._current["category"] = data.strip()
                self._in_class = False

        def handle_endtag(self, tag):
            if self._in_board and tag == "a":
                if self._current.get("name"):
                    self.boards.append(self._current)
                self._in_board = False
                self._current = {}

    parser = HotBoardParser()
    parser.feed(resp.text)
    boards = parser.boards[:limit]

    results = []
    for board in boards:
        try:
            top_post = _fetch_board_top_post(session, headers, board["url"])
            results.append({
                "board": board["name"],
                "category": board.get("category", ""),
                "top_post": top_post,
            })
        except Exception:
            results.append({
                "board": board["name"],
                "category": board.get("category", ""),
                "top_post": None,
            })
    return results


def _fetch_board_top_post(session: requests.Session, headers: dict, board_url: str) -> dict | None:
    resp = session.get(board_url, headers=headers, timeout=15)
    resp.raise_for_status()

    from html.parser import HTMLParser

    class PostParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.posts: list[dict] = []
            self._in_row = False
            self._in_title = False
            self._current: dict = {}
            self._depth = 0

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            if tag == "div" and "r-ent" in cls:
                self._in_row = True
                self._current = {}
            if self._in_row and tag == "a":
                href = attrs_dict.get("href", "")
                if "/bbs/" in href:
                    self._current["url"] = f"https://www.ptt.cc{href}"
                    self._in_title = True

        def handle_data(self, data):
            if self._in_title:
                self._current["title"] = data.strip()
                self._in_title = False

        def handle_endtag(self, tag):
            if self._in_row and tag == "div":
                if self._current.get("title"):
                    self.posts.append(self._current)
                self._in_row = False

    parser = PostParser()
    parser.feed(resp.text)
    return parser.posts[0] if parser.posts else None
