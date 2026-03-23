#!/usr/bin/env python3
"""F1 Telegram Notification Bot - Entry Point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys

from config import Config
from scheduler import RaceScheduler
from utils import setup_logging

logger = logging.getLogger("f1bot")


def validate_config() -> bool:
    """Check that required environment variables are set."""
    missing = []
    if not Config.TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not Config.TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set them in .env file. See .env.example for reference.")
        return False
    return True


async def run_bot() -> None:
    """Main bot loop: load schedule and wait for notifications."""
    race_scheduler = RaceScheduler()

    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def handle_signal() -> None:
        logger.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    try:
        await race_scheduler.load_schedule()
        race_scheduler.start()
        logger.info("F1 Bot is running. Press Ctrl+C to stop.")
        await shutdown_event.wait()
    finally:
        await race_scheduler.shutdown()


async def run_check() -> None:
    """One-shot check for GitHub Actions: send notifications if due now."""
    race_scheduler = RaceScheduler()
    try:
        await race_scheduler.check_and_notify()
    finally:
        await race_scheduler.shutdown()


async def run_test() -> None:
    """Send a test notification using recent race data."""
    race_scheduler = RaceScheduler()
    try:
        await race_scheduler.send_test_notification()
        logger.info("Test notification sent!")
    finally:
        await race_scheduler.shutdown()


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(description="F1 Telegram Notification Bot")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send a test notification and exit",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="One-shot check: send notification if due now, then exit (for GitHub Actions)",
    )
    args = parser.parse_args()

    if not validate_config():
        sys.exit(1)

    if args.test:
        asyncio.run(run_test())
    elif args.check:
        asyncio.run(run_check())
    else:
        asyncio.run(run_bot())


if __name__ == "__main__":
    main()
