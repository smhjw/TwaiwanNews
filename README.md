# 台湾素材热点日报

每天自动抓取台湾游戏热点并推送到钉钉：

- 巴哈姆特手游热帖（优先展示手游版块）
- PTT 游戏相关版块热帖
- App Store 台湾游戏免费榜 Top5
- Google Play 台湾游戏免费榜 Top5

## 配置

复制 `.env.example` 为 `.env`（本地调试用），或在 GitHub 仓库配置 Secrets/Variables。

### Secrets
| 名称 | 说明 |
|------|------|
| `DINGTALK_WEBHOOK` | 钉钉自定义机器人 Webhook 地址（必填） |
| `DINGTALK_SECRET` | 钉钉加签密钥（启用加签时必填） |

### Variables（可选）
| 名称 | 默认值 | 说明 |
|------|--------|------|
| `DRY_RUN` | `false` | `true` 时只打印不推送 |
| `FAIL_ON_PARTIAL_ERROR` | `false` | `true` 时任一数据源失败则任务失败 |

## 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env  # 填入你的配置
export $(cat .env | grep -v '#' | xargs)
PYTHONIOENCODING=utf-8 python main.py
```

## GitHub Actions

工作流文件：`.github/workflows/daily-taiwan-news.yml`

默认每个工作日 UTC 01:30（北京时间 09:30）触发。也可在 GitHub Actions 页面手动触发。

## 数据来源说明

| 板块 | 来源 | 说明 |
|------|------|------|
| 巴哈姆特手游热帖 | forum.gamer.com.tw | 抓取首页热门版块，优先手游分类 |
| PTT 游戏版热帖 | ptt.cc/bbs/hotboards | 仅展示游戏相关版块 |
| App Store 免费榜 | iTunes RSS API | 台湾地区游戏分类（genre=6014） |
| Google Play 免费榜 | google-play-scraper | 台湾地区搜索免費遊戲 |
