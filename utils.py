from __future__ import annotations

import asyncio
import functools
import logging
import time
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import Config

logger = logging.getLogger("f1bot")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def to_local_time(dt: datetime) -> datetime:
    """Convert a UTC datetime to the configured local timezone."""
    tz = ZoneInfo(Config.TIMEZONE)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def format_time(dt: datetime) -> str:
    """Format datetime to a readable string in local timezone."""
    local = to_local_time(dt)
    return local.strftime("%m月%d日 %H:%M")


def format_date(dt: datetime) -> str:
    """Format datetime to date string in local timezone."""
    local = to_local_time(dt)
    return local.strftime("%m月%d日 (%A)")


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, per_second: int = 3, per_minute: int = 30):
        self.per_second = per_second
        self.per_minute = per_minute
        self._timestamps: deque[float] = deque()

    async def acquire(self) -> None:
        now = time.monotonic()
        # Purge timestamps older than 60s
        while self._timestamps and self._timestamps[0] < now - 60:
            self._timestamps.popleft()
        # Check per-minute limit
        if len(self._timestamps) >= self.per_minute:
            wait = 60 - (now - self._timestamps[0])
            if wait > 0:
                logger.debug(f"Rate limit (per-minute): waiting {wait:.1f}s")
                await asyncio.sleep(wait)
        # Check per-second limit
        recent = [t for t in self._timestamps if t > time.monotonic() - 1]
        if len(recent) >= self.per_second:
            wait = 1.0 - (time.monotonic() - recent[0])
            if wait > 0:
                logger.debug(f"Rate limit (per-second): waiting {wait:.1f}s")
                await asyncio.sleep(wait)
        self._timestamps.append(time.monotonic())


def retry(max_attempts: int = 3, backoff_base: float = 1.0):
    """Async retry decorator with exponential backoff."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        wait = backoff_base * (2**attempt)
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed: {e}, "
                            f"retrying in {wait:.1f}s"
                        )
                        await asyncio.sleep(wait)
            logger.error(f"{func.__name__} failed after {max_attempts} attempts: {last_exc}")
            return None

        return wrapper

    return decorator
