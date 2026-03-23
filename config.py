import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # OpenF1
    OPENF1_BASE_URL: str = "https://api.openf1.org/v1"

    # Jolpica (Ergast replacement)
    JOLPICA_BASE_URL: str = "http://api.jolpi.ca/ergast/f1"

    # Season
    F1_SEASON: int = int(os.getenv("F1_SEASON", "2026"))

    # Notification timing (minutes)
    PRE_RACE_OFFSET: int = 60  # 赛前 1 小时
    POST_RACE_DELAY: int = 60  # 赛后 1 小时
    ESTIMATED_RACE_DURATION: int = 120  # 预估正赛时长
    ESTIMATED_SPRINT_DURATION: int = 45  # 预估冲刺赛时长

    # Display timezone
    TIMEZONE: str = "Asia/Shanghai"

    # Rate limits
    OPENF1_RATE_PER_SECOND: int = 3
    OPENF1_RATE_PER_MINUTE: int = 30
