#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from zoneinfo import ZoneInfo
import datetime as dt

from dingtalk import DingTalkBot
from fetchers.ptt import fetch_ptt_hot
from fetchers.bahamut import fetch_bahamut_hot
from fetchers.app_charts import fetch_appstore_tw_free_games, fetch_googleplay_tw_free_games

TIMEZONE = ZoneInfo("Asia/Taipei")

# 政治相关关键词过滤
POLITICS_KEYWORDS = (
    "選舉", "選票", "投票", "罷免", "立委", "立法院", "國會", "民進黨", "國民黨",
    "民眾黨", "總統", "行政院", "黨", "政府", "政治", "蔡英文", "賴清德", "柯文哲",
    "韓國瑜", "侯友宜", "朱立倫", "蕭敬嚴", "徐巧芯", "葉元之", "兩岸", "統獨",
    "台獨", "中共", "解放軍", "美中", "台美", "制裁", "外交", "國防", "軍事",
    "烏克蘭", "俄羅斯", "以色列", "Gaza", "戰爭", "戰火", "抗議", "示威",
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


def build_report(
    ptt: list[dict] | Exception,
    bahamut: list[dict] | Exception,
    appstore: list[dict] | Exception,
    googleplay: list[dict] | Exception,
) -> str:
    now = dt.datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d %H:%M")
    lines = [f"## \U0001f1f9\U0001f1fc 台湾素材热点日报\n{now}\n"]

    # 巴哈姆特
    lines.append("### \U0001f3ae 巴哈姆特手游热帖")
    if isinstance(bahamut, Exception):
        lines.append(f"> 获取失败：{bahamut}")
    elif not bahamut:
        lines.append("> 暂无数据")
    else:
        filtered = _filter_political(bahamut, ("title",))
        for i, item in enumerate(filtered, 1):
            board = item.get("board", "")
            title = item["title"]
            url = item["url"]
            lines.append(f"{i}. **[{board}]** [{title}]({url})")
    lines.append("")

    # PTT
    lines.append("### \U0001f4ac PTT 游戏版热帖")
    if isinstance(ptt, Exception):
        lines.append(f"> 获取失败：{ptt}")
    elif not ptt:
        lines.append("> 暂无数据")
    else:
        for item in ptt:
            board = item["board"]
            board_url = item["board_url"]
            top = item.get("top_post")
            if top and not _is_political(top["title"]):
                lines.append(f"- **[{board}]({board_url})** 热帖：[{top['title']}]({top['url']}) ({top['push']} 推)")
            else:
                lines.append(f"- **[{board}]({board_url})** 暂无热帖")
    lines.append("")

    # App Store 台湾游戏免费榜
    lines.append("### \U0001f34f App Store 台湾游戏免费榜 Top5")
    if isinstance(appstore, Exception):
        lines.append(f"> 获取失败：{appstore}")
    elif not appstore:
        lines.append("> 暂无数据")
    else:
        for i, item in enumerate(appstore, 1):
            name = item["name"]
            dev = item.get("developer", "")
            url = item.get("url", "")
            dev_str = f" — {dev}" if dev else ""
            if url:
                lines.append(f"{i}. [{name}]({url}){dev_str}")
            else:
                lines.append(f"{i}. **{name}**{dev_str}")
    lines.append("")

    # Google Play 台湾游戏免费榜
    lines.append("### \U0001f916 Google Play 台湾游戏免费榜 Top5")
    if isinstance(googleplay, Exception):
        lines.append(f"> 获取失败：{googleplay}")
    elif not googleplay:
        lines.append("> 暂无数据（需安装 google-play-scraper）")
    else:
        for i, item in enumerate(googleplay, 1):
            name = item["name"]
            dev = item.get("developer", "")
            url = item.get("url", "")
            dev_str = f" — {dev}" if dev else ""
            if url:
                lines.append(f"{i}. [{name}]({url}){dev_str}")
            else:
                lines.append(f"{i}. **{name}**{dev_str}")
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

    bahamut = safe(fetch_bahamut_hot, limit=5)
    ptt = safe(fetch_ptt_hot, limit=5)
    appstore = safe(fetch_appstore_tw_free_games, limit=5)
    googleplay = safe(fetch_googleplay_tw_free_games, limit=5)

    report = build_report(ptt, bahamut, appstore, googleplay)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(report)

    errors = [
        name
        for name, result in [
            ("PTT", ptt), ("巴哈姆特", bahamut),
            ("App Store", appstore), ("Google Play", googleplay),
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
