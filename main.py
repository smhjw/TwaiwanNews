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
from fetchers.youtube import fetch_youtube_trending

TIMEZONE = ZoneInfo(\"Asia/Taipei\")


def _fmt_number(n: int) -> str:
    if n >= 10000:
        return f\"{n / 10000:.1f}万\"
    return str(n)


def build_report(
    ptt: list[dict] | Exception,
    bahamut: list[dict] | Exception,
    trends: list[dict] | Exception,
    youtube: list[dict] | Exception,
) -> str:
    now = dt.datetime.now(tz=TIMEZONE).strftime(\"%Y-%m-%d %H:%M\")
    lines = [f\"## \U0001f1f9\U0001f1fc 台湾素材热点日报\
{now}\
\"]

    # PTT
    lines.append(\"### \U0001f4ac PTT 热门版块\")
    if isinstance(ptt, Exception):
        lines.append(f\"> 获取失败：{ptt}\")
    elif not ptt:
        lines.append(\"> 暂无数据\")
    else:
        for i, item in enumerate(ptt, 1):
            board = item[\"board\"]
            cat = f\"[{item['category']}] \" if item.get(\"category\") else \"\"
            top = item.get(\"top_post\")
            if top:
                title = top.get(\"title\", \"(無標題)\")
                url = top.get(\"url\", \"\")
                push = top.get(\"push\", 0)
                push_str = f\" \U0001f525爆\" if push >= 100 else (f\" \U0001f44d{push}\" if push > 0 else \"\")
                lines.append(f\"{i}. **{cat}{board}** — [{title}]({url}){push_str}\")
            else:
                lines.append(f\"{i}. **{cat}{board}** — [前往版块](https://www.ptt.cc/bbs/{board}/index.html)\")
    lines.append(\"\")

    # Bahamut
    lines.append(\"### \U0001f3ae 巴哈姆特手游热帖\")
    if isinstance(bahamut, Exception):
        lines.append(f\"> 获取失败：{bahamut}\")
    elif not bahamut:
        lines.append(\"> 暂无数据\")
    else:
        for i, item in enumerate(bahamut, 1):
            title = item[\"title\"]
            board = item[\"board\"]
            url = item[\"url\"]
            board_str = f\"**[{board}]** \" if board else \"\"
            lines.append(f\"{i}. {board_str}[{title}]({url})\")
    lines.append(\"\")

    # Google Trends
    lines.append(\"### \U0001f525 台湾今日热搜\")
    if isinstance(trends, Exception):
        lines.append(f\"> 获取失败：{trends}\")
    elif not trends:
        lines.append(\"> 暂无数据\")
    else:
        for i, item in enumerate(trends, 1):
            query = item[\"query\"]
            traffic = f\" ({item['traffic']}+)\" if item.get(\"traffic\") else \"\"
            news_title = item.get(\"news_title\", \"\")
            news_url = item.get(\"news_url\", \"\")
            if news_url and news_title:
                lines.append(f\"{i}. **{query}**{traffic} — [{news_title}]({news_url})\")
            else:
                lines.append(f\"{i}. **{query}**{traffic}\")
    lines.append(\"\")

    # YouTube
    lines.append(\"### \u25b6\ufe0f YouTube 台湾发烧影片\")
    if isinstance(youtube, Exception):
        lines.append(f\"> 获取失败：{youtube}\")
    elif not youtube:
        lines.append(\"> 暂无数据\")
    else:
        for i, item in enumerate(youtube, 1):
            title = item[\"title\"]
            channel = item.get(\"channel\", \"\")
            url = item.get(\"url\", \"\")
            channel_str = f\" — {channel}\" if channel else \"\"
            lines.append(f\"{i}. [{title}]({url}){channel_str}\")
    lines.append(\"\")

    return \"\
\".join(lines)


def main() -> int:
    webhook = os.environ.get(\"DINGTALK_WEBHOOK\", \"\")
    secret = os.environ.get(\"DINGTALK_SECRET\", \"\")
    youtube_api_key = os.environ.get(\"YOUTUBE_API_KEY\", \"\")
    dry_run = os.environ.get(\"DRY_RUN\", \"false\").lower() == \"true\"
    fail_on_partial = os.environ.get(\"FAIL_ON_PARTIAL_ERROR\", \"false\").lower() == \"true\"

    if not dry_run and not webhook:
        print(\"ERROR: DINGTALK_WEBHOOK is required\", file=sys.stderr)
        return 1

    def safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return e

    ptt = safe(fetch_ptt_hot, limit=5)
    bahamut = safe(fetch_bahamut_hot, limit=10)
    trends = safe(fetch_google_trends_tw, limit=10)
    if youtube_api_key:
        youtube = safe(fetch_youtube_trending, youtube_api_key, limit=5)
    else:
        youtube = Exception(\"未配置 YOUTUBE_API_KEY\")

    report = build_report(ptt, bahamut, trends, youtube)
    print(report)

    errors = [
        name
        for name, result in [(\"PTT\", ptt), (\"巴哈姆特\", bahamut), (\"Google Trends\", trends), (\"YouTube\", youtube)]
        if isinstance(result, Exception)
    ]

    if errors and fail_on_partial:
        print(f\"部分数据源失败: {', '.join(errors)}\", file=sys.stderr)
        return 1

    if dry_run:
        print(\"DRY_RUN=true，跳过钉钉推送\")
        return 0

    try:
        bot = DingTalkBot(webhook, secret)
        bot.send_markdown(\"台湾素材热点日报\", report)
        print(\"钉钉推送成功\")
    except Exception as e:
        print(f\"钉钉推送失败: {e}\", file=sys.stderr)
        return 1

    return 0


if __name__ == \"__main__\":
    raise SystemExit(main())
