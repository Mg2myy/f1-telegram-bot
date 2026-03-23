# F1 Telegram Notification Bot

自动推送 F1 赛事通知到 Telegram，支持赛前预告和赛后报告。

## 功能

### 赛前通知（正赛前 1 小时）
- 前 4 位发车格
- 车手积分榜前 5
- 车队积分榜前 5
- 天气状况
- 赛前总结

### 赛后通知（正赛后约 1 小时）
- 前 8 名成绩
- 最快圈速
- 退赛名单、罚时、安全车/红旗
- 车手积分榜前 5（含本场得分变化）
- 车队积分榜前 5
- 赛后总结 + 下一站预告

### 冲刺赛周末
冲刺赛前/后各额外推送一条通知（共 4 条）。

## 部署到 GitHub Actions（推荐）

1. Fork 本仓库
2. 在仓库 Settings → Secrets and variables → Actions 中添加：
   - `TELEGRAM_BOT_TOKEN` — 从 [@BotFather](https://t.me/BotFather) 获取
   - `TELEGRAM_CHAT_ID` — 你的 Telegram 用户 ID（可通过 [@userinfobot](https://t.me/userinfobot) 获取）
3. 完成！GitHub Actions 每 30 分钟自动检查，比赛日自动推送通知。

### 手动测试
在仓库 Actions 页面，选择 "F1 Race Notifications" workflow，点击 "Run workflow"，选择 `test` 模式。

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env 填入你的 token 和 chat_id

# 测试通知
python main.py --test

# 单次检查（GitHub Actions 模式）
python main.py --check

# 持续运行（守护进程模式）
python main.py
```

## 数据来源
- [OpenF1 API](https://openf1.org) — 赛事数据（免费，无需 API key）
- [Jolpica F1 API](https://github.com/jolpica/jolpica-f1) — 积分榜备用数据源

## 技术栈
- Python 3.9+
- httpx — 异步 HTTP 客户端
- python-telegram-bot — Telegram 消息推送
- APScheduler — 定时调度
- 无需任何付费 API
