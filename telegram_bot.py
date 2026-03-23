from __future__ import annotations

import logging

from telegram import Bot
from telegram.constants import ParseMode

from config import Config

logger = logging.getLogger("f1bot.telegram")

MAX_MESSAGE_LENGTH = 4096


class TelegramNotifier:
    def __init__(self) -> None:
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.chat_id = Config.TELEGRAM_CHAT_ID

    async def send_message(self, text: str) -> bool:
        """Send a message to the configured chat. Splits if too long."""
        try:
            if len(text) <= MAX_MESSAGE_LENGTH:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
            else:
                # Split at blank lines near the limit
                chunks = self._split_message(text)
                for chunk in chunks:
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=chunk,
                        parse_mode=ParseMode.HTML,
                    )
            logger.info(f"Message sent to {self.chat_id} ({len(text)} chars)")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _split_message(self, text: str) -> list[str]:
        """Split a long message at section boundaries."""
        chunks = []
        current = ""
        for line in text.split("\n"):
            if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH - 100:
                chunks.append(current.rstrip())
                current = ""
            current += line + "\n"
        if current.strip():
            chunks.append(current.rstrip())
        return chunks
