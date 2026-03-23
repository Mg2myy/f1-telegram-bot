from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Meeting:
    meeting_key: int
    meeting_name: str  # e.g. "Australian Grand Prix"
    circuit_short_name: str  # e.g. "Albert Park"
    location: str  # e.g. "Melbourne"
    country_name: str  # e.g. "Australia"
    year: int
    date_start: datetime | None = None


@dataclass
class Session:
    session_key: int
    session_name: str  # e.g. "Race", "Sprint", "Qualifying"
    session_type: str  # e.g. "Race", "Sprint", "Qualifying", "Practice"
    meeting_key: int
    date_start: datetime | None = None
    date_end: datetime | None = None


@dataclass
class GridPosition:
    position: int
    driver_number: int
    driver_name: str
    team_name: str
    qualifying_time: str | None = None


@dataclass
class RaceResult:
    position: int
    driver_number: int
    driver_name: str
    team_name: str
    time: str  # winner's total time or gap to leader
    points: float = 0.0
    status: str = "Finished"  # "Finished", "DNF", "DNS", "DSQ"
    laps_completed: int = 0


@dataclass
class FastestLap:
    driver_name: str
    team_name: str
    lap_time: str
    lap_number: int


@dataclass
class DriverStanding:
    position: int
    driver_name: str
    team_name: str
    points: float
    points_change: float = 0.0  # points gained this race


@dataclass
class ConstructorStanding:
    position: int
    team_name: str
    points: float
    points_change: float = 0.0


@dataclass
class WeatherData:
    air_temperature: float | None = None
    track_temperature: float | None = None
    humidity: float | None = None
    rainfall: bool = False
    wind_speed: float | None = None
    wind_direction: int | None = None

    @property
    def summary(self) -> str:
        parts = []
        if self.rainfall:
            parts.append("Rain")
        else:
            parts.append("Dry")
        if self.air_temperature is not None:
            parts.append(f"{self.air_temperature:.0f}°C")
        if self.humidity is not None:
            parts.append(f"Humidity {self.humidity:.0f}%")
        if self.wind_speed is not None:
            parts.append(f"Wind {self.wind_speed:.1f} m/s")
        return ", ".join(parts)


@dataclass
class RaceControlEvent:
    category: str  # "SafetyCar", "Flag", "Penalty", etc.
    message: str
    driver_number: int | None = None
    flag: str | None = None  # "RED", "YELLOW", etc.
    lap_number: int | None = None


@dataclass
class PitStop:
    driver_number: int
    driver_name: str
    lap_number: int
    pit_duration: float | None = None  # seconds
    compound: str | None = None  # tire compound


@dataclass
class DriverInfo:
    driver_number: int
    full_name: str
    name_acronym: str  # e.g. "VER"
    team_name: str


@dataclass
class PreRaceContext:
    meeting: Meeting
    session: Session
    grid: list[GridPosition]
    driver_standings: list[DriverStanding]
    constructor_standings: list[ConstructorStanding]
    weather: WeatherData | None = None


@dataclass
class PostRaceContext:
    meeting: Meeting
    session: Session
    results: list[RaceResult]
    fastest_lap: FastestLap | None
    driver_standings: list[DriverStanding]
    constructor_standings: list[ConstructorStanding]
    dnf_list: list[RaceResult] = field(default_factory=list)
    penalties: list[RaceControlEvent] = field(default_factory=list)
    safety_cars: int = 0
    red_flags: int = 0
    weather: WeatherData | None = None
    next_meeting: Meeting | None = None
    is_sprint: bool = False
