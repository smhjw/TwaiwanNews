#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from zoneinfo import ZoneInfo
import datetime as dt

from dingtalk import DingTalkBot
from fetchers.ptt import fetch_ptt_hot
from fetchers.dcard import fetch_dcard_hot
from fetchers.tiktok import fetch_tiktok_trending
from fetchers.youtube import fetch_youtube_trending

TIMEZONE = ZoneInfo("Asia/Taipei")


def _fmt_number(n: int) -> str:
    if n >= 10000:
        return f"{n / 10000:.1f}万"
    return str(n)


def build_report(
    ptt: list[dict] | Exception,
    dcard: list[dict] | Exception,
    tiktok: list[dict] | Exception,
    youtube: list[dict] | Exception,
) -> str:
    now = dt.datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d %H:%M")
    lines = [f"## 🇹🇼 台湾素材热点日报\n{now}\n"]

    # PTT
    lines.append("### 💬 PTT 热门版块")
    if isinstance(ptt, Exception):
        lines.append(f"> 获取失败：{ptt}")
    elif not ptt:
        lines.append("> 暂无数据")
    else:
        for i, item in enumerate(ptt, 1):
            board = item["board"]
            cat = f"[{item['category']}] " if item.get("category") else ""
            top = item.get("top_post")
            if top:
                title = top.get("title", "(无标题)")
                url = top.get("url", "")
                lines.append(f"{i}. **{cat}{board}** — [{title}]({url})")
            else:
                lines.append(f"{i}. **{cat}{board}**")
    lines.append("")

    # Dcard
    lines.append("### 📱 Dcard 热门帖子")
    if isinstance(dcard, Exception):
        lines.append(f"> 获取失败：{dcard}")
    elif not dcard:
        lines.append("> 暂无数据")
    else:
        for i, item in enumerate(dcard, 1):
            title = item["title"]
            forum = item["forum"]
            likes = _fmt_number(item["like_count"])
            url = item["url"]
            lines.append(f"{i}. **[{forum}]** [{title}]({url}) 👍{likes}")
    lines.append("")

    # TikTok (replaced with Google Trends TW)
    lines.append("### 🔥 台湾热搜趋势（Google Trends）")
    if isinstance(tiktok, Exception):
        lines.append(f"> 获取失败：{tiktok}")
    elif not tiktok:
        lines.append("> 暂无数据")
    else:
        for i, item in enumerate(tiktok, 1):
            tag = item["hashtag"]
            traffic = item.get("traffic", "")
            url = item.get("url", "")
            if url:
                lines.append(f"{i}. **{tag}** {traffic} [详情]({url})")
            else:
                lines.append(f"{i}. **{tag}** {traffic}")
    lines.append("")

    # YouTube
    lines.append("### ▶️ YouTube 台湾发烧影片")
    if isinstance(youtube, Exception):
        lines.append(f"> 获取失败：{youtube}")
    elif not youtube:
        lines.append("> 暂无数据")
    else:
        for i, item in enumerate(youtube, 1):
            title = item["title"]
            channel = item["channel"]
            views = _fmt_number(item["view_count"])
            url = item["url"]
            lines.append(f"{i}. **{channel}** — [{title}]({url}) 👁{views}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    webhook = os.environ.get("DINGTALK_WEBHOOK", "")
    secret = os.environ.get("DINGTALK_SECRET", "")
    youtube_api_key = os.environ.get("YOUTUBE_API_KEY", "")
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    fail_on_partial = os.environ.get("FAIL_ON_PARTIAL_ERROR", "true").lower() == "true"

    if not dry_run and not webhook:
        print("ERROR: DINGTALK_WEBHOOK is required", file=sys.stderr)
        return 1

    # Fetch all sections, capturing errors individually
    def safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return e

    ptt = safe(fetch_ptt_hot, limit=5)
    dcard = safe(fetch_dcard_hot, limit=5)
    tiktok = safe(fetch_tiktok_trending, limit=5)
    if youtube_api_key:
        youtube = safe(fetch_youtube_trending, youtube_api_key, limit=5)
    else:
        youtube = Exception("未配置 YOUTUBE_API_KEY")

    report = build_report(ptt, dcard, tiktok, youtube)
    print(report)

    errors = [
        name
        for name, result in [("PTT", ptt), ("Dcard", dcard), ("TikTok", tiktok), ("YouTube", youtube)]
        if isinstance(result, Exception)
    ]

    if errors and fail_on_partial:
        print(f"部分数据源失败: {', '.join(errors)}", file=sys.stderr)
        return 1

    if dry_run:
        print("DRY_RUN=true，跳过钉钉推送")
        return 0

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
