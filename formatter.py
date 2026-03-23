from __future__ import annotations

from models import (
    ConstructorStanding,
    DriverStanding,
    FastestLap,
    GridPosition,
    PostRaceContext,
    PreRaceContext,
    RaceControlEvent,
    RaceResult,
    WeatherData,
)
from translations import t_circuit, t_country, t_driver, t_gp, t_team
from utils import format_time

COUNTRY_FLAGS: dict[str, str] = {
    "Australia": "🇦🇺", "China": "🇨🇳", "Japan": "🇯🇵",
    "Bahrain": "🇧🇭", "Saudi Arabia": "🇸🇦", "United States": "🇺🇸",
    "Canada": "🇨🇦", "Monaco": "🇲🇨", "Spain": "🇪🇸",
    "Austria": "🇦🇹", "United Kingdom": "🇬🇧", "Hungary": "🇭🇺",
    "Belgium": "🇧🇪", "Netherlands": "🇳🇱", "Italy": "🇮🇹",
    "Azerbaijan": "🇦🇿", "Singapore": "🇸🇬", "Mexico": "🇲🇽",
    "Brazil": "🇧🇷", "Qatar": "🇶🇦", "United Arab Emirates": "🇦🇪",
}

POSITION_EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}


def _e(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _flag(country: str) -> str:
    return COUNTRY_FLAGS.get(country, "🏁")


def _pad(text: str, width: int) -> str:
    """Pad CJK-aware: CJK chars count as width 2."""
    current = 0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff" or "\u3000" <= ch <= "\u303f":
            current += 2
        else:
            current += 1
    return text + " " * max(0, width - current)


def _format_weather(w: WeatherData) -> str:
    icon = "🌧" if w.rainfall else "☀️"
    parts = [icon]
    if w.air_temperature is not None:
        parts.append(f"{w.air_temperature:.0f}°C")
    if w.track_temperature is not None:
        parts.append(f"赛道{w.track_temperature:.0f}°C")
    if w.humidity is not None:
        parts.append(f"💧 {w.humidity:.0f}%")
    if w.wind_speed is not None:
        parts.append(f"💨 {w.wind_speed:.1f}m/s")
    return "  ".join(parts)


def _format_grid(grid: list[GridPosition]) -> str:
    lines = []
    for g in grid:
        driver = t_driver(g.driver_name)
        team = t_team(g.team_name)
        lines.append(f"  P{g.position}  {_pad(driver, 10)} {team}")
    table = "\n".join(lines)
    return f"🏎 <b>发车格</b>\n<pre>{table}</pre>"


def _format_results(results: list[RaceResult]) -> str:
    lines = []
    for r in results:
        medal = POSITION_EMOJI.get(r.position, f"P{r.position}")
        driver = t_driver(r.driver_name)
        team = t_team(r.team_name)
        time_str = f"  {r.time}" if r.time else ""
        lines.append(f"  {medal} {_pad(driver, 10)} {team}{time_str}")
    table = "\n".join(lines)
    return f"🏆 <b>比赛成绩</b>\n<pre>{table}</pre>"


def _format_fastest_lap(fl: FastestLap) -> str:
    driver = t_driver(fl.driver_name)
    return f"⚡ <b>最快圈</b>  {driver}  <code>{fl.lap_time}</code>  第{fl.lap_number}圈"


def _format_driver_standings(standings: list[DriverStanding]) -> str:
    lines = []
    for s in standings:
        driver = t_driver(s.driver_name)
        change = f"(+{s.points_change:.0f})" if s.points_change > 0 else ""
        pts = f"{s.points:.0f}分"
        lines.append(f"  {s.position}. {_pad(driver, 10)} {_pad(pts, 6)} {change}")
    table = "\n".join(lines)
    return f"👤 <b>车手积分榜</b>\n<pre>{table}</pre>"


def _format_constructor_standings(standings: list[ConstructorStanding]) -> str:
    lines = []
    for s in standings:
        team = t_team(s.team_name)
        change = f"(+{s.points_change:.0f})" if s.points_change > 0 else ""
        pts = f"{s.points:.0f}分"
        lines.append(f"  {s.position}. {_pad(team, 12)} {_pad(pts, 6)} {change}")
    table = "\n".join(lines)
    return f"🏢 <b>车队积分榜</b>\n<pre>{table}</pre>"


def _format_incidents(
    dnf_list: list[RaceResult],
    penalties: list[RaceControlEvent],
    safety_cars: int,
    red_flags: int,
) -> str:
    parts = []
    if safety_cars > 0:
        parts.append(f"🟡 安全车 ×{safety_cars}")
    if red_flags > 0:
        parts.append(f"🔴 红旗 ×{red_flags}")
    if dnf_list:
        names = "、".join(t_driver(r.driver_name) for r in dnf_list)
        parts.append(f"💥 退赛: {_e(names)}")
    if penalties:
        for p in penalties:
            parts.append(f"⚠️ {_e(p.message)}")
    if not parts:
        return ""
    return "📋 <b>赛事事件</b>\n" + "\n".join(parts)


# ─────────────────────────────────────
#  赛前通知
# ─────────────────────────────────────

def format_pre_race_message(ctx: PreRaceContext, ai_summary: str) -> str:
    flag = _flag(ctx.meeting.country_name)
    gp = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)
    circuit = t_circuit(ctx.meeting.circuit_short_name)
    race_time = format_time(ctx.session.date_start) if ctx.session.date_start else "待定"

    sections = [
        f"🏁 <b>{_e(gp)} · 赛前预告</b>\n{flag} {_e(circuit)} · {_e(country)}\n🕐 {race_time} 北京时间",
    ]

    if ctx.grid:
        sections.append(_format_grid(ctx.grid))

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))

    if ctx.weather:
        sections.append(f"🌡 <b>天气</b>  {_format_weather(ctx.weather)}")

    if ai_summary:
        sections.append(f"💬 <i>{_e(ai_summary)}</i>")

    return "\n\n".join(sections)


# ─────────────────────────────────────
#  赛后通知
# ─────────────────────────────────────

def format_post_race_message(ctx: PostRaceContext, ai_summary: str) -> str:
    flag = _flag(ctx.meeting.country_name)
    gp = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)
    circuit = t_circuit(ctx.meeting.circuit_short_name)
    label = "冲刺赛" if ctx.is_sprint else "正赛"

    sections = [
        f"🏁 <b>{_e(gp)} · {label}报告</b>\n{flag} {_e(circuit)} · {_e(country)}",
    ]

    if ctx.results:
        sections.append(_format_results(ctx.results))

    if ctx.fastest_lap:
        sections.append(_format_fastest_lap(ctx.fastest_lap))

    incidents = _format_incidents(
        ctx.dnf_list, ctx.penalties, ctx.safety_cars, ctx.red_flags
    )
    if incidents:
        sections.append(incidents)

    if ctx.weather:
        sections.append(f"🌡 <b>天气</b>  {_format_weather(ctx.weather)}")

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))

    if ai_summary:
        sections.append(f"💬 <i>{_e(ai_summary)}</i>")

    if ctx.next_meeting and not ctx.is_sprint:
        nf = _flag(ctx.next_meeting.country_name)
        ngp = t_gp(ctx.next_meeting.meeting_name)
        nc = t_country(ctx.next_meeting.country_name)
        ncircuit = t_circuit(ctx.next_meeting.circuit_short_name)
        next_time = ""
        if ctx.next_meeting.date_start:
            next_time = f"\n🕐 {format_time(ctx.next_meeting.date_start)} 北京时间"
        sections.append(
            f"─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n"
            f"📅 <b>下一站</b>  {nf} {_e(ngp)}\n"
            f"📍 {_e(ncircuit)} · {_e(nc)}{next_time}"
        )

    return "\n\n".join(sections)


# ─────────────────────────────────────
#  冲刺赛前通知
# ─────────────────────────────────────

def format_pre_sprint_message(ctx: PreRaceContext, ai_summary: str) -> str:
    flag = _flag(ctx.meeting.country_name)
    gp = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)
    circuit = t_circuit(ctx.meeting.circuit_short_name)
    sprint_time = format_time(ctx.session.date_start) if ctx.session.date_start else "待定"

    sections = [
        f"🏎💨 <b>{_e(gp)} · 冲刺赛预告</b>\n{flag} {_e(circuit)} · {_e(country)}\n🕐 {sprint_time} 北京时间",
    ]

    if ctx.grid:
        sections.append(_format_grid(ctx.grid))

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))

    if ctx.weather:
        sections.append(f"🌡 <b>天气</b>  {_format_weather(ctx.weather)}")

    if ai_summary:
        sections.append(f"💬 <i>{_e(ai_summary)}</i>")

    return "\n\n".join(sections)
