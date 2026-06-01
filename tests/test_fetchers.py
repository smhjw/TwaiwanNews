import json
import unittest
from unittest.mock import patch

import requests

from fetchers.bahamut import _extract_board_list
from fetchers.ptt import fetch_ptt_hot


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class PttFetchTests(unittest.TestCase):
    def test_fetch_ptt_hot_retries_transient_hotboards_connection_error(self):
        hotboards_html = """
        <a class="board" href="/bbs/Steam/index.html">
            <div class="board-name">Steam</div>
            <div class="board-class">遊戲</div>
        </a>
        """

        class FakeSession:
            def __init__(self):
                self.calls = 0

            def get(self, url, timeout):
                self.calls += 1
                if self.calls == 1:
                    raise requests.exceptions.ConnectionError("reset by peer")
                return FakeResponse(hotboards_html)

        session = FakeSession()

        with (
            patch("fetchers.ptt._session", return_value=session),
            patch("fetchers.ptt._fetch_board_top_post", return_value=None),
        ):
            results = fetch_ptt_hot(limit=1)

        self.assertEqual(session.calls, 2)
        self.assertEqual(results[0]["board"], "Steam")


class BahamutParseTests(unittest.TestCase):
    def test_extract_board_list_supports_react_router_stream_data(self):
        table = [
            "unused",
            "boardList",
            [3],
            {"_4": 5, "_6": 7, "_8": 9, "_10": 11, "_12": 13},
            "bsn",
            74934,
            "title",
            "鳴潮",
            "topicTitle",
            "《鳴潮》開發組特別對談",
            "topicSn",
            17265,
            "rank",
            1,
        ]
        payload = json.dumps(table, ensure_ascii=False)
        script_arg = json.dumps(payload, ensure_ascii=False)
        html = (
            "<script>"
            "window.__reactRouterContext.streamController.enqueue("
            f"{script_arg}"
            ");"
            "</script>"
        ).encode("utf-8")

        boards = _extract_board_list(html)

        self.assertEqual(
            boards,
            [
                {
                    "bsn": 74934,
                    "title": "鳴潮",
                    "topicTitle": "《鳴潮》開發組特別對談",
                    "topicSn": 17265,
                    "rank": 1,
                }
            ],
        )

    def test_extract_board_list_ignores_react_router_sentinel_references(self):
        table = [
            "unused",
            "boardList",
            [3, -5],
            {"_4": 5, "_6": -5},
            "bsn",
            74934,
            "title",
        ]
        payload = json.dumps(table, ensure_ascii=False)
        script_arg = json.dumps(payload, ensure_ascii=False)
        html = (
            "<script>"
            "window.__reactRouterContext.streamController.enqueue("
            f"{script_arg}"
            ");"
            "</script>"
        ).encode("utf-8")

        boards = _extract_board_list(html)

        self.assertEqual(boards, [{"bsn": 74934}])


if __name__ == "__main__":
    unittest.main()
