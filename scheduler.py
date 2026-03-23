from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from ai_summary import SummaryGenerator
from config import Config
from data_fetcher import F1DataFetcher
from formatter import (
    format_post_race_message,
    format_pre_race_message,
    format_pre_sprint_message,
)
from models import (
    Meeting,
    PostRaceContext,
    PreRaceContext,
    RaceControlEvent,
    Session,
)
from telegram_bot import TelegramNotifier

logger = logging.getLogger("f1bot.scheduler")


class RaceScheduler:
    def __init__(self) -> None:
        self.fetcher = F1DataFetcher()
        self.notifier = TelegramNotifier()
        self.ai = SummaryGenerator()
        self.scheduler = AsyncIOScheduler()
        self._meetings: list[Meeting] = []

    async def load_schedule(self) -> None:
        """Fetch the race calendar and schedule all notifications."""
        logger.info(f"Loading {Config.F1_SEASON} race calendar...")
        self._meetings = await self.fetcher.get_meetings(Config.F1_SEASON)
        logger.info(f"Found {len(self._meetings)} meetings")

        now = datetime.now(timezone.utc)

        for meeting in self._meetings:
            sessions = await self.fetcher.get_sessions(meeting.meeting_key)

            for session in sessions:
                if not session.date_start:
                    continue

                # OpenF1 uses session_type="Race" for both Race and Sprint,
                # so we distinguish by session_name
                if session.session_name == "Race":
                    self._schedule_race(meeting, session, sessions, now)
                elif session.session_name == "Sprint":
                    self._schedule_sprint(meeting, session, sessions, now)

    def _schedule_race(
        self,
        meeting: Meeting,
        race_session: Session,
        all_sessions: list[Session],
        now: datetime,
    ) -> None:
        """Schedule pre-race and post-race notifications for a main race."""
        pre_time = race_session.date_start - timedelta(minutes=Config.PRE_RACE_OFFSET)
        post_check_time = race_session.date_start + timedelta(
            minutes=Config.ESTIMATED_RACE_DURATION + 30
        )

        if pre_time > now:
            self.scheduler.add_job(
                self._send_pre_race,
                trigger=DateTrigger(run_date=pre_time),
                args=[meeting, race_session, all_sessions],
                id=f"pre_race_{meeting.meeting_key}",
                name=f"Pre-race: {meeting.meeting_name}",
            )
            logger.info(
                f"Scheduled pre-race for {meeting.meeting_name} at {pre_time.isoformat()}"
            )

        if post_check_time > now:
            self.scheduler.add_job(
                self._poll_and_send_post_race,
                trigger=DateTrigger(run_date=post_check_time),
                args=[meeting, race_session, False],
                id=f"post_race_{meeting.meeting_key}",
                name=f"Post-race: {meeting.meeting_name}",
            )
            logger.info(
                f"Scheduled post-race check for {meeting.meeting_name} at {post_check_time.isoformat()}"
            )

    def _schedule_sprint(
        self,
        meeting: Meeting,
        sprint_session: Session,
        all_sessions: list[Session],
        now: datetime,
    ) -> None:
        """Schedule pre-sprint and post-sprint notifications."""
        pre_time = sprint_session.date_start - timedelta(minutes=Config.PRE_RACE_OFFSET)
        post_check_time = sprint_session.date_start + timedelta(
            minutes=Config.ESTIMATED_SPRINT_DURATION + 30
        )

        if pre_time > now:
            self.scheduler.add_job(
                self._send_pre_sprint,
                trigger=DateTrigger(run_date=pre_time),
                args=[meeting, sprint_session, all_sessions],
                id=f"pre_sprint_{meeting.meeting_key}",
                name=f"Pre-sprint: {meeting.meeting_name}",
            )
            logger.info(
                f"Scheduled pre-sprint for {meeting.meeting_name} at {pre_time.isoformat()}"
            )

        if post_check_time > now:
            self.scheduler.add_job(
                self._poll_and_send_post_race,
                trigger=DateTrigger(run_date=post_check_time),
                args=[meeting, sprint_session, True],
                id=f"post_sprint_{meeting.meeting_key}",
                name=f"Post-sprint: {meeting.meeting_name}",
            )
            logger.info(
                f"Scheduled post-sprint check for {meeting.meeting_name} at {post_check_time.isoformat()}"
            )

    async def _send_pre_race(
        self,
        meeting: Meeting,
        race_session: Session,
        all_sessions: list[Session],
    ) -> None:
        """Assemble and send the pre-race notification."""
        logger.info(f"Sending pre-race notification for {meeting.meeting_name}")

        # Find qualifying session for starting grid
        quali = self.fetcher.find_qualifying_session(all_sessions, "Race")
        quali_key = quali.session_key if quali else race_session.session_key

        grid = await self.fetcher.get_starting_grid(quali_key, top_n=4)
        driver_standings = await self.fetcher.get_driver_standings(
            race_session.session_key
        )
        constructor_standings = await self.fetcher.get_constructor_standings(
            race_session.session_key
        )
        weather = await self.fetcher.get_weather(race_session.session_key)

        ctx = PreRaceContext(
            meeting=meeting,
            session=race_session,
            grid=grid,
            driver_standings=driver_standings,
            constructor_standings=constructor_standings,
            weather=weather,
        )

        summary = self.ai.generate_pre_race_summary(ctx)
        message = format_pre_race_message(ctx, summary)
        await self.notifier.send_message(message)

    async def _send_pre_sprint(
        self,
        meeting: Meeting,
        sprint_session: Session,
        all_sessions: list[Session],
    ) -> None:
        """Assemble and send the pre-sprint notification."""
        logger.info(f"Sending pre-sprint notification for {meeting.meeting_name}")

        quali = self.fetcher.find_qualifying_session(all_sessions, "Sprint")
        quali_key = quali.session_key if quali else sprint_session.session_key

        grid = await self.fetcher.get_starting_grid(quali_key, top_n=4)
        driver_standings = await self.fetcher.get_driver_standings(
            sprint_session.session_key
        )
        constructor_standings = await self.fetcher.get_constructor_standings(
            sprint_session.session_key
        )
        weather = await self.fetcher.get_weather(sprint_session.session_key)

        ctx = PreRaceContext(
            meeting=meeting,
            session=sprint_session,
            grid=grid,
            driver_standings=driver_standings,
            constructor_standings=constructor_standings,
            weather=weather,
        )

        summary = self.ai.generate_pre_race_summary(ctx)
        message = format_pre_sprint_message(ctx, summary)
        await self.notifier.send_message(message)

    async def _poll_and_send_post_race(
        self,
        meeting: Meeting,
        session: Session,
        is_sprint: bool,
    ) -> None:
        """Poll for race results and send post-race notification."""
        logger.info(
            f"Checking for {'sprint' if is_sprint else 'race'} results: {meeting.meeting_name}"
        )

        # Poll up to 4 times, 15 minutes apart
        for attempt in range(4):
            results = await self.fetcher.get_race_results(session.session_key, top_n=8)
            if results:
                # Wait the configured delay before sending
                if attempt == 0:
                    logger.info(
                        f"Results found, waiting {Config.POST_RACE_DELAY} minutes before sending"
                    )
                    await asyncio.sleep(Config.POST_RACE_DELAY * 60)
                await self._send_post_race(meeting, session, is_sprint)
                return

            logger.warning(
                f"No results yet (attempt {attempt + 1}/4), retrying in 15 minutes"
            )
            await asyncio.sleep(15 * 60)

        logger.error(f"Could not get results for {meeting.meeting_name} after 4 attempts")

    async def _send_post_race(
        self,
        meeting: Meeting,
        session: Session,
        is_sprint: bool,
    ) -> None:
        """Assemble and send the post-race notification."""
        logger.info(
            f"Sending post-{'sprint' if is_sprint else 'race'} notification for {meeting.meeting_name}"
        )

        results = await self.fetcher.get_race_results(session.session_key, top_n=8)
        all_results = await self.fetcher.get_all_race_results(session.session_key)
        fastest_lap = await self.fetcher.get_fastest_lap(session.session_key)
        driver_standings = await self.fetcher.get_driver_standings(session.session_key)
        constructor_standings = await self.fetcher.get_constructor_standings(
            session.session_key
        )
        weather = await self.fetcher.get_weather(session.session_key)
        race_control = await self.fetcher.get_race_control(session.session_key)

        # Extract DNFs
        dnf_list = [r for r in all_results if r.status != "Finished"]

        # Extract penalties
        penalties = [
            e for e in race_control if "penalty" in e.category.lower()
        ]

        # Count safety cars and red flags
        safety_cars = sum(
            1 for e in race_control if "safety car" in e.message.lower()
            and "deployed" in e.message.lower()
        )
        red_flags = sum(
            1 for e in race_control if e.flag == "RED"
        )

        # Get next meeting (only for main race)
        next_meeting = None
        if not is_sprint:
            next_meeting = await self.fetcher.get_next_meeting(
                self._meetings, meeting.meeting_key
            )

        ctx = PostRaceContext(
            meeting=meeting,
            session=session,
            results=results,
            fastest_lap=fastest_lap,
            driver_standings=driver_standings,
            constructor_standings=constructor_standings,
            dnf_list=dnf_list,
            penalties=penalties,
            safety_cars=safety_cars,
            red_flags=red_flags,
            weather=weather,
            next_meeting=next_meeting,
            is_sprint=is_sprint,
        )

        summary = self.ai.generate_post_race_summary(ctx)
        message = format_post_race_message(ctx, summary)
        await self.notifier.send_message(message)

    async def check_and_notify(self) -> None:
        """One-shot check: if a notification is due now, send it.

        Designed for GitHub Actions cron (runs every 30 min).
        Checks if any session starts within the notification window.
        """
        logger.info("Running one-shot check...")

        if not self._meetings:
            await self.load_schedule()

        now = datetime.now(timezone.utc)
        window = timedelta(minutes=20)  # ±20 min tolerance for cron

        for meeting in self._meetings:
            sessions = await self.fetcher.get_sessions(meeting.meeting_key)

            for session in sessions:
                if not session.date_start:
                    continue
                if session.session_name not in ("Race", "Sprint"):
                    continue

                is_sprint = session.session_name == "Sprint"

                # Pre-race window: should we send pre-race notification?
                pre_target = session.date_start - timedelta(
                    minutes=Config.PRE_RACE_OFFSET
                )
                if abs((now - pre_target).total_seconds()) < window.total_seconds():
                    logger.info(
                        f"Pre-{'sprint' if is_sprint else 'race'} window hit: "
                        f"{meeting.meeting_name}"
                    )
                    if is_sprint:
                        await self._send_pre_sprint(meeting, session, sessions)
                    else:
                        await self._send_pre_race(meeting, session, sessions)

                # Post-race window: check if race is done
                est_end = session.date_start + timedelta(
                    minutes=(
                        Config.ESTIMATED_SPRINT_DURATION
                        if is_sprint
                        else Config.ESTIMATED_RACE_DURATION
                    )
                )
                post_target = est_end + timedelta(
                    minutes=Config.POST_RACE_DELAY
                )
                if abs((now - post_target).total_seconds()) < window.total_seconds():
                    results = await self.fetcher.get_race_results(
                        session.session_key, top_n=8
                    )
                    if results:
                        logger.info(
                            f"Post-{'sprint' if is_sprint else 'race'} window hit: "
                            f"{meeting.meeting_name}"
                        )
                        await self._send_post_race(meeting, session, is_sprint)
                    else:
                        logger.warning(
                            f"Post-race window hit but no results yet for "
                            f"{meeting.meeting_name}"
                        )

        logger.info("One-shot check complete")

    async def send_test_notification(self) -> None:
        """Send a test notification using the most recent completed race data."""
        logger.info("Sending test notification...")

        if not self._meetings:
            await self.load_schedule()

        # Find the most recent meeting with available data
        now = datetime.now(timezone.utc)
        past_meetings = [
            m for m in self._meetings
            if m.date_start and m.date_start < now
        ]

        if not past_meetings:
            await self.notifier.send_message(
                "🏎 <b>F1 Bot 测试</b>\n\n机器人已启动，等待下一场比赛！"
            )
            return

        meeting = past_meetings[-1]
        sessions = await self.fetcher.get_sessions(meeting.meeting_key)
        race_session = self.fetcher.find_session_by_type(sessions, "Race")

        if not race_session:
            await self.notifier.send_message(
                f"🏎 <b>F1 Bot 测试</b>\n\n已连接！最近的赛事: {meeting.meeting_name}"
            )
            return

        # Send a sample post-race notification
        await self._send_post_race(meeting, race_session, is_sprint=False)

    def start(self) -> None:
        self.scheduler.start()
        logger.info("Scheduler started")

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
        await self.fetcher.close()
        logger.info("Shut down complete")
