#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from zoneinfo import ZoneInfo
import datetime as dt

from dingtalk import DingTalkBot
from fetchers.ptt import fetch_ptt_hot
from fetchers.bahamut import fetch_bahamut_hot
from fetchers.google_trends import fetch_google_trends_tw

TIMEZONE = ZoneInfo("Asia/Taipei")

# 政治相关关键词过滤
POLITICS_KEYWORDS = (
    "選舉", "選票", "投票", "罷免", "立委", "立法院", "國會", "民進黨", "國民黨",
    "民眾黨", "總統", "行政院", "黨", "政府", "政治", "蔡英文", "賴清德", "柯文哲",
    "韓國瑜", "侯友宜", "朱立倫", "蕭敬嚴", "徐巧芯", "葉元之", "兩岸", "統獨",
    "台獨", "中共", "解放軍", "美中", "台美", "制裁", "外交", "國防", "軍事",
    "烏克蘭", "俄羅斯", "以色列", "Gaza", "戰爭", "戰火", "抗議", "示威",
)

# 捕鱼游戏相关关键词（台湾地区）
FISHING_GAME_KEYWORDS = (
    "捕魚", "捕鱼", "打魚", "打鱼", "釣魚達人", "海底撈", "魚機",
    "電子捕魚", "手機捕魚", "捕魚機",
)


def _is_political(text: str) -> bool:
    return any(kw in text for kw in POLITICS_KEYWORDS)


def _filter_political(items: list[dict], text_keys: tuple) -> list[dict]:
    result = []
    for item in items:
        combined = " ".join(str(item.get(k, "")) for k in text_keys)
        if not _is_political(combined):
            result.append(item)
    return result


def fetch_fishing_game_news(limit: int = 5) -> list[dict]:
    """Fetch recent Taiwan fishing game news via Google News RSS."""
    try:
        import feedparser
    except ImportError:
        return []
    results = []
    for kw in ("台灣捕魚遊戲", "捕魚機 台灣", "捕魚遊戲 手機"):
        url = f"https://news.google.com/rss/search?q={kw}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue
                if any(r["title"] == title for r in results):
                    continue
                results.append({"title": title, "url": link})
                if len(results) >= limit:
                    return results
        except Exception:
            continue
    return results[:limit]


def build_report(
    ptt: list[dict] | Exception,
    bahamut: list[dict] | Exception,
    trends: list[dict] | Exception,
    fishing: list[dict] | Exception,
) -> str:
    now = dt.datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d %H:%M")
    lines = [f"## 🇹🇼 台湾素材热点日报\n{now}\n"]

    # 巴哈姆特（最上方）
    lines.append("### 🎮 巴哈姆特手游热帖")
    if isinstance(bahamut, Exception):
        lines.append(f"> 获取失败：{bahamut}")
    elif not bahamut:
        lines.append("> 暂无数据")
    else:
        filtered = _filter_political(bahamut, ("title", "board"))
        if not filtered:
            lines.append("> 今日热帖均为政治相关，已过滤")
        for i, item in enumerate(filtered, 1):
            board = item.get("board", "")
            title = item["title"]
            url = item["url"]
            lines.append(f"{i}. **[{board}]** [{title}]({url})")
    lines.append("")

    # PTT 游戏版块
    lines.append("### 💬 PTT 游戏版热帖")
    if isinstance(ptt, Exception):
        lines.append(f"> 获取失败：{ptt}")
    elif not ptt:
        lines.append("> 暂无游戏相关版块数据")
    else:
        for item in ptt:
            board = item["board"]
            board_url = item["board_url"]
            top = item.get("top_post")
            if top and not _is_political(top["title"]):
                lines.append(f"- **[{board}]({board_url})** 热帖：[{top['title']}]({top['url']}) ({top['push']} 推)")
            else:
                lines.append(f"- **[{board}]({board_url})**")
    lines.append("")

    # Google Trends Top5
    lines.append("### 🔥 台湾今日热搜 Top5（Google Trends）")
    if isinstance(trends, Exception):
        lines.append(f"> 获取失败：{trends}")
    elif not trends:
        lines.append("> 暂无数据")
    else:
        filtered = _filter_political(trends, ("query", "news_title"))
        if not filtered:
            lines.append("> 今日热搜均为政治相关，已过滤")
        for i, item in enumerate(filtered[:5], 1):
            query = item["query"]
            traffic = item.get("traffic", "")
            news_title = item.get("news_title", "")
            news_url = item.get("news_url", "")
            traffic_str = f" ({traffic})" if traffic else ""
            if news_url and news_title:
                lines.append(f"{i}. **{query}**{traffic_str} — [{news_title}]({news_url})")
            else:
                lines.append(f"{i}. **{query}**{traffic_str}")
    lines.append("")

    # 捕鱼游戏新闻
    lines.append("### 🎣 近期台湾捕鱼游戏相关新闻")
    if isinstance(fishing, Exception):
        lines.append(f"> 获取失败：{fishing}")
    elif not fishing:
        lines.append("> 暂无相关新闻")
    else:
        for i, item in enumerate(fishing, 1):
            lines.append(f"{i}. [{item['title']}]({item['url']})")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    webhook = os.environ.get("DINGTALK_WEBHOOK", "")
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    fail_on_partial = os.environ.get("FAIL_ON_PARTIAL_ERROR", "false").lower() == "true"

    if not dry_run and not webhook:
        print("ERROR: DINGTALK_WEBHOOK is required", file=sys.stderr)
        return 1

    def safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return e

    bahamut = safe(fetch_bahamut_hot, limit=10)
    ptt = safe(fetch_ptt_hot, limit=5)
    trends = safe(fetch_google_trends_tw, limit=10)
    fishing = safe(fetch_fishing_game_news, limit=5)

    report = build_report(ptt, bahamut, trends, fishing)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(report)

    errors = [
        name
        for name, result in [
            ("PTT", ptt), ("巴哈姆特", bahamut),
            ("Google Trends", trends), ("捕鱼新闻", fishing),
        ]
        if isinstance(result, Exception)
    ]

    if errors and fail_on_partial:
        print(f"部分数据源失败: {', '.join(errors)}", file=sys.stderr)
        return 1

    if dry_run:
        print("DRY_RUN=true，跳过钉钉推送")
        return 0

    secret = os.environ.get("DINGTALK_SECRET", "")
    try:
        bot = DingTalkBot(webhook, secret)
        bot.send_markdown("台湾素材热点日报", report)
        print("钉钉推送成功")
    except Exception as e:
        print(f"钉钉推送失败: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
