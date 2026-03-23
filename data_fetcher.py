from __future__ import annotations

import logging
from datetime import datetime

import httpx

from config import Config
from models import (
    ConstructorStanding,
    DriverInfo,
    DriverStanding,
    FastestLap,
    GridPosition,
    Meeting,
    PitStop,
    RaceControlEvent,
    RaceResult,
    Session,
    WeatherData,
)
from utils import RateLimiter, retry

logger = logging.getLogger("f1bot.fetcher")


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class OpenF1Client:
    """Client for the OpenF1 API."""

    def __init__(self) -> None:
        self.base_url = Config.OPENF1_BASE_URL
        self._client = httpx.AsyncClient(timeout=30)
        self._limiter = RateLimiter(
            per_second=Config.OPENF1_RATE_PER_SECOND,
            per_minute=Config.OPENF1_RATE_PER_MINUTE,
        )

    async def _get(self, endpoint: str, params: dict | None = None) -> list[dict]:
        await self._limiter.acquire()
        url = f"{self.base_url}/{endpoint}"
        resp = await self._client.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()

    @retry()
    async def get_meetings(self, year: int) -> list[Meeting]:
        data = await self._get("meetings", {"year": year})
        meetings = []
        for item in data:
            meetings.append(
                Meeting(
                    meeting_key=item["meeting_key"],
                    meeting_name=item.get("meeting_name", ""),
                    circuit_short_name=item.get("circuit_short_name", ""),
                    location=item.get("location", ""),
                    country_name=item.get("country_name", ""),
                    year=item.get("year", year),
                    date_start=_parse_dt(item.get("date_start")),
                )
            )
        return meetings

    @retry()
    async def get_sessions(self, meeting_key: int) -> list[Session]:
        data = await self._get("sessions", {"meeting_key": meeting_key})
        sessions = []
        for item in data:
            sessions.append(
                Session(
                    session_key=item["session_key"],
                    session_name=item.get("session_name", ""),
                    session_type=item.get("session_type", ""),
                    meeting_key=meeting_key,
                    date_start=_parse_dt(item.get("date_start")),
                    date_end=_parse_dt(item.get("date_end")),
                )
            )
        return sessions

    @retry()
    async def get_drivers(self, session_key: int) -> dict[int, DriverInfo]:
        data = await self._get("drivers", {"session_key": session_key})
        drivers: dict[int, DriverInfo] = {}
        for item in data:
            num = item.get("driver_number")
            if num and num not in drivers:
                drivers[num] = DriverInfo(
                    driver_number=num,
                    full_name=item.get("full_name", f"Driver {num}"),
                    name_acronym=item.get("name_acronym", ""),
                    team_name=item.get("team_name", ""),
                )
        return drivers

    @retry()
    async def get_starting_grid(self, session_key: int) -> list[GridPosition]:
        """Get starting grid. session_key should be the qualifying session."""
        data = await self._get("position", {"session_key": session_key})
        if not data:
            return []

        # Get drivers info for names
        drivers = await self.get_drivers(session_key)

        # The position endpoint gives position changes over time.
        # We need the final positions at end of qualifying.
        # Group by driver, take the last entry for each.
        last_positions: dict[int, int] = {}
        for item in data:
            num = item.get("driver_number")
            pos = item.get("position")
            if num and pos:
                last_positions[num] = pos

        grid = []
        for num, pos in sorted(last_positions.items(), key=lambda x: x[1]):
            driver = drivers.get(num)
            grid.append(
                GridPosition(
                    position=pos,
                    driver_number=num,
                    driver_name=driver.full_name if driver else f"Driver {num}",
                    team_name=driver.team_name if driver else "",
                )
            )
        return sorted(grid, key=lambda g: g.position)

    @retry()
    async def get_race_results(self, session_key: int) -> list[RaceResult]:
        """Get race results from the position endpoint."""
        data = await self._get("position", {"session_key": session_key})
        if not data:
            return []

        drivers = await self.get_drivers(session_key)

        # Get final positions
        last_positions: dict[int, int] = {}
        for item in data:
            num = item.get("driver_number")
            pos = item.get("position")
            if num and pos:
                last_positions[num] = pos

        results = []
        for num, pos in sorted(last_positions.items(), key=lambda x: x[1]):
            driver = drivers.get(num)
            results.append(
                RaceResult(
                    position=pos,
                    driver_number=num,
                    driver_name=driver.full_name if driver else f"Driver {num}",
                    team_name=driver.team_name if driver else "",
                    time="",
                )
            )
        return sorted(results, key=lambda r: r.position)

    @retry()
    async def get_fastest_lap(self, session_key: int) -> FastestLap | None:
        """Find the fastest lap from lap data."""
        data = await self._get(
            "laps",
            {"session_key": session_key, "is_pit_out_lap": "false"},
        )
        if not data:
            return None

        drivers = await self.get_drivers(session_key)

        best_lap = None
        best_duration = float("inf")
        for item in data:
            duration = item.get("lap_duration")
            if duration and duration < best_duration:
                best_duration = duration
                best_lap = item

        if not best_lap:
            return None

        num = best_lap.get("driver_number")
        driver = drivers.get(num)

        # Convert duration (seconds) to mm:ss.sss
        mins, secs = divmod(best_duration, 60)
        time_str = f"{int(mins)}:{secs:06.3f}"

        return FastestLap(
            driver_name=driver.full_name if driver else f"Driver {num}",
            team_name=driver.team_name if driver else "",
            lap_time=time_str,
            lap_number=best_lap.get("lap_number", 0),
        )

    @retry()
    async def get_championship_drivers(
        self, session_key: int
    ) -> list[DriverStanding] | None:
        """Get driver championship standings (beta endpoint)."""
        data = await self._get("championship_drivers", {"session_key": session_key})
        if not data:
            return None

        # We need driver names - fetch from a recent session
        drivers = await self.get_drivers(session_key)

        standings = []
        for item in data:
            num = item.get("driver_number")
            driver = drivers.get(num)
            pts_current = item.get("points_current", 0)
            pts_start = item.get("points_start", 0)
            standings.append(
                DriverStanding(
                    position=item.get("position_current", 0),
                    driver_name=driver.full_name if driver else f"Driver {num}",
                    team_name=driver.team_name if driver else "",
                    points=pts_current,
                    points_change=pts_current - pts_start,
                )
            )
        return sorted(standings, key=lambda s: s.position)

    @retry()
    async def get_championship_teams(
        self, session_key: int
    ) -> list[ConstructorStanding] | None:
        """Get constructor championship standings (beta endpoint)."""
        data = await self._get("championship_teams", {"session_key": session_key})
        if not data:
            return None

        standings = []
        for item in data:
            pts_current = item.get("points_current", 0)
            pts_start = item.get("points_start", 0)
            standings.append(
                ConstructorStanding(
                    position=item.get("position_current", 0),
                    team_name=item.get("team_name", "Unknown"),
                    points=pts_current,
                    points_change=pts_current - pts_start,
                )
            )
        return sorted(standings, key=lambda s: s.position)

    @retry()
    async def get_weather(self, session_key: int) -> WeatherData | None:
        data = await self._get("weather", {"session_key": session_key})
        if not data:
            return None
        # Take the latest weather reading
        latest = data[-1]
        return WeatherData(
            air_temperature=latest.get("air_temperature"),
            track_temperature=latest.get("track_temperature"),
            humidity=latest.get("humidity"),
            rainfall=latest.get("rainfall", False),
            wind_speed=latest.get("wind_speed"),
            wind_direction=latest.get("wind_direction"),
        )

    @retry()
    async def get_race_control(self, session_key: int) -> list[RaceControlEvent]:
        data = await self._get("race_control", {"session_key": session_key})
        events = []
        for item in data:
            events.append(
                RaceControlEvent(
                    category=item.get("category", ""),
                    message=item.get("message", ""),
                    driver_number=item.get("driver_number"),
                    flag=item.get("flag"),
                    lap_number=item.get("lap_number"),
                )
            )
        return events

    @retry()
    async def get_pit_stops(self, session_key: int) -> list[PitStop]:
        data = await self._get("pit", {"session_key": session_key})
        drivers = await self.get_drivers(session_key)
        stops = []
        for item in data:
            num = item.get("driver_number")
            driver = drivers.get(num)
            stops.append(
                PitStop(
                    driver_number=num,
                    driver_name=driver.full_name if driver else f"Driver {num}",
                    lap_number=item.get("lap_number", 0),
                    pit_duration=item.get("pit_duration"),
                )
            )
        return stops

    async def close(self) -> None:
        await self._client.aclose()


class JolpicaClient:
    """Fallback client for standings via Jolpica (Ergast replacement)."""

    def __init__(self) -> None:
        self.base_url = Config.JOLPICA_BASE_URL
        self._client = httpx.AsyncClient(timeout=30)

    async def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}/{endpoint}"
        resp = await self._client.get(url)
        resp.raise_for_status()
        return resp.json()

    @retry()
    async def get_driver_standings(self) -> list[DriverStanding] | None:
        data = await self._get("current/driverStandings.json")
        try:
            standings_list = data["MRData"]["StandingsTable"]["StandingsLists"][0][
                "DriverStandings"
            ]
        except (KeyError, IndexError):
            return None

        standings = []
        for item in standings_list:
            driver = item.get("Driver", {})
            constructor = item.get("Constructors", [{}])[0] if item.get("Constructors") else {}
            standings.append(
                DriverStanding(
                    position=int(item.get("position", 0)),
                    driver_name=f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    team_name=constructor.get("name", ""),
                    points=float(item.get("points", 0)),
                )
            )
        return standings

    @retry()
    async def get_constructor_standings(self) -> list[ConstructorStanding] | None:
        data = await self._get("current/constructorStandings.json")
        try:
            standings_list = data["MRData"]["StandingsTable"]["StandingsLists"][0][
                "ConstructorStandings"
            ]
        except (KeyError, IndexError):
            return None

        standings = []
        for item in standings_list:
            constructor = item.get("Constructor", {})
            standings.append(
                ConstructorStanding(
                    position=int(item.get("position", 0)),
                    team_name=constructor.get("name", ""),
                    points=float(item.get("points", 0)),
                )
            )
        return standings

    async def close(self) -> None:
        await self._client.aclose()


class F1DataFetcher:
    """Unified data fetcher with fallback logic."""

    def __init__(self) -> None:
        self.openf1 = OpenF1Client()
        self.jolpica = JolpicaClient()

    async def get_meetings(self, year: int) -> list[Meeting]:
        result = await self.openf1.get_meetings(year)
        return result or []

    async def get_sessions(self, meeting_key: int) -> list[Session]:
        result = await self.openf1.get_sessions(meeting_key)
        return result or []

    async def get_starting_grid(self, session_key: int, top_n: int = 4) -> list[GridPosition]:
        grid = await self.openf1.get_starting_grid(session_key)
        return (grid or [])[:top_n]

    async def get_race_results(self, session_key: int, top_n: int = 8) -> list[RaceResult]:
        results = await self.openf1.get_race_results(session_key)
        return (results or [])[:top_n]

    async def get_all_race_results(self, session_key: int) -> list[RaceResult]:
        """Get all results (used for DNF detection)."""
        return await self.openf1.get_race_results(session_key) or []

    async def get_fastest_lap(self, session_key: int) -> FastestLap | None:
        return await self.openf1.get_fastest_lap(session_key)

    async def get_driver_standings(
        self, session_key: int, top_n: int = 5
    ) -> list[DriverStanding]:
        """Get driver standings with Jolpica fallback."""
        result = await self.openf1.get_championship_drivers(session_key)
        if not result:
            logger.warning("OpenF1 standings unavailable, falling back to Jolpica")
            result = await self.jolpica.get_driver_standings()
        return (result or [])[:top_n]

    async def get_constructor_standings(
        self, session_key: int, top_n: int = 5
    ) -> list[ConstructorStanding]:
        """Get constructor standings with Jolpica fallback."""
        result = await self.openf1.get_championship_teams(session_key)
        if not result:
            logger.warning("OpenF1 constructor standings unavailable, falling back to Jolpica")
            result = await self.jolpica.get_constructor_standings()
        return (result or [])[:top_n]

    async def get_weather(self, session_key: int) -> WeatherData | None:
        return await self.openf1.get_weather(session_key)

    async def get_race_control(self, session_key: int) -> list[RaceControlEvent]:
        return await self.openf1.get_race_control(session_key) or []

    async def get_pit_stops(self, session_key: int) -> list[PitStop]:
        return await self.openf1.get_pit_stops(session_key) or []

    def find_qualifying_session(
        self, sessions: list[Session], target_name: str = "Race"
    ) -> Session | None:
        """Find the qualifying session that produces the grid for the target session.

        OpenF1 uses session_name to distinguish sessions:
        - "Sprint Qualifying" -> grid for Sprint
        - "Qualifying" -> grid for Race
        """
        if target_name == "Sprint":
            for s in sessions:
                if s.session_name in ("Sprint Qualifying", "Sprint Shootout"):
                    return s
        else:
            for s in sessions:
                if s.session_name == "Qualifying":
                    return s
        return None

    def find_session_by_type(
        self, sessions: list[Session], session_name: str
    ) -> Session | None:
        """Find a session by its name (e.g. 'Race', 'Sprint', 'Qualifying')."""
        for s in sessions:
            if s.session_name == session_name:
                return s
        return None

    async def get_next_meeting(
        self, meetings: list[Meeting], current_meeting_key: int
    ) -> Meeting | None:
        """Find the next meeting after the current one."""
        found_current = False
        for m in meetings:
            if found_current:
                return m
            if m.meeting_key == current_meeting_key:
                found_current = True
        return None

    async def close(self) -> None:
        await self.openf1.close()
        await self.jolpica.close()
