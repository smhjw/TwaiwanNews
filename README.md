# 台湾素材热点日报

每天自动抓取台湾热点并推送到钉钉：

- PTT 热门版块及热帖
- Dcard 热门帖子
- TikTok 热门话题（台湾区）
- YouTube 台湾发烧影片

## 配置

复制 `.env.example` 为 `.env`（本地调试用），或在 GitHub 仓库配置 Secrets/Variables。

### Secrets
| 名称 | 说明 |
|------|------|
| `DINGTALK_WEBHOOK` | 钉钉自定义机器人 Webhook 地址（必填） |
| `DINGTALK_SECRET` | 钉钉加签密钥（启用加签时必填） |
| `YOUTUBE_API_KEY` | YouTube Data API v3 Key（可选，不填跳过 YouTube 板块） |

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
python main.py
```

## GitHub Actions

工作流文件：`.github/workflows/daily-taiwan-news.yml`

默认每天 UTC 01:00（北京时间 09:00）触发。也可在 GitHub Actions 页面手动触发。

## 获取 YouTube API Key

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 启用 YouTube Data API v3
3. 创建 API 密钥，填入 `YOUTUBE_API_KEY`
