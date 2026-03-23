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
from translations import t_country, t_driver, t_gp, t_team
from utils import format_time


def _e(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_weather(w: WeatherData) -> str:
    parts = []
    if w.rainfall:
        parts.append("雨")
    else:
        parts.append("晴")
    if w.air_temperature is not None:
        parts.append(f"气温{w.air_temperature:.0f}°C")
    if w.humidity is not None:
        parts.append(f"湿度{w.humidity:.0f}%")
    if w.wind_speed is not None:
        parts.append(f"风速{w.wind_speed:.1f}m/s")
    return "，".join(parts)


def _format_grid(grid: list[GridPosition]) -> str:
    lines = [f"<b>━━━ 发车格 (前{len(grid)}位) ━━━</b>"]
    for g in grid:
        lines.append(
            f"{g.position}. {_e(t_driver(g.driver_name))} ({_e(t_team(g.team_name))})"
        )
    return "\n".join(lines)


def _format_results(results: list[RaceResult]) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = [f"<b>━━━ 成绩 (前{len(results)}名) ━━━</b>"]
    for r in results:
        medal = medals.get(r.position, f"{r.position}.")
        prefix = f"{medal} " if r.position <= 3 else f"{r.position}.  "
        time_str = f" — {r.time}" if r.time else ""
        lines.append(
            f"{prefix}{_e(t_driver(r.driver_name))} ({_e(t_team(r.team_name))}){time_str}"
        )
    return "\n".join(lines)


def _format_fastest_lap(fl: FastestLap) -> str:
    return (
        f"⚡ <b>最快圈:</b> {_e(t_driver(fl.driver_name))} — "
        f"{fl.lap_time} (第{fl.lap_number}圈)"
    )


def _format_driver_standings(standings: list[DriverStanding]) -> str:
    lines = ["<b>━━━ 车手积分榜 ━━━</b>"]
    for s in standings:
        change = ""
        if s.points_change > 0:
            change = f" <i>(+{s.points_change:.0f})</i>"
        lines.append(
            f"{s.position}. {_e(t_driver(s.driver_name))} — {s.points:.0f}分{change}"
        )
    return "\n".join(lines)


def _format_constructor_standings(standings: list[ConstructorStanding]) -> str:
    lines = ["<b>━━━ 车队积分榜 ━━━</b>"]
    for s in standings:
        change = ""
        if s.points_change > 0:
            change = f" <i>(+{s.points_change:.0f})</i>"
        lines.append(f"{s.position}. {_e(t_team(s.team_name))} — {s.points:.0f}分{change}")
    return "\n".join(lines)


def _format_dnf(dnf_list: list[RaceResult]) -> str:
    if not dnf_list:
        return ""
    names = "、".join(t_driver(r.driver_name) for r in dnf_list)
    return f"❌ <b>退赛:</b> {_e(names)}"


def _format_penalties(penalties: list[RaceControlEvent]) -> str:
    if not penalties:
        return ""
    lines = []
    for p in penalties:
        lines.append(f"⚠️ {_e(p.message)}")
    return "\n".join(lines)


def format_pre_race_message(ctx: PreRaceContext, ai_summary: str) -> str:
    """Format the pre-race Telegram notification."""
    race_time = format_time(ctx.session.date_start) if ctx.session.date_start else "待定"
    gp_name = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)

    sections = [
        f"🏁 <b>正赛日: {_e(gp_name)}</b>",
        f"📍 {_e(ctx.meeting.circuit_short_name)}，{_e(country)}",
        f"🕐 发车时间: {race_time} (北京时间)",
        "",
    ]

    if ctx.grid:
        sections.append(_format_grid(ctx.grid))
        sections.append("")

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))
        sections.append("")

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))
        sections.append("")

    if ctx.weather:
        sections.append(f"🌤 <b>天气:</b> {_format_weather(ctx.weather)}")
        sections.append("")

    if ai_summary:
        sections.append(f"📝 {_e(ai_summary)}")

    return "\n".join(sections)


def format_post_race_message(ctx: PostRaceContext, ai_summary: str) -> str:
    """Format the post-race Telegram notification."""
    header = "冲刺赛成绩" if ctx.is_sprint else "正赛成绩"
    gp_name = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)

    sections = [
        f"🏆 <b>{header}: {_e(gp_name)}</b>",
        f"📍 {_e(ctx.meeting.circuit_short_name)}，{_e(country)}",
        "",
    ]

    if ctx.results:
        sections.append(_format_results(ctx.results))
        sections.append("")

    if ctx.fastest_lap:
        sections.append(_format_fastest_lap(ctx.fastest_lap))
        sections.append("")

    dnf_str = _format_dnf(ctx.dnf_list)
    if dnf_str:
        sections.append(dnf_str)

    penalty_str = _format_penalties(ctx.penalties)
    if penalty_str:
        sections.append(penalty_str)

    if dnf_str or penalty_str:
        sections.append("")

    flags = []
    if ctx.safety_cars > 0:
        flags.append(f"安全车 x{ctx.safety_cars}")
    if ctx.red_flags > 0:
        flags.append(f"红旗 x{ctx.red_flags}")
    if flags:
        sections.append(f"🚩 {'，'.join(flags)}")
        sections.append("")

    if ctx.weather:
        sections.append(f"🌤 <b>天气:</b> {_format_weather(ctx.weather)}")
        sections.append("")

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))
        sections.append("")

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))
        sections.append("")

    if ai_summary:
        sections.append(f"📝 {_e(ai_summary)}")
        sections.append("")

    if ctx.next_meeting and not ctx.is_sprint:
        next_gp = t_gp(ctx.next_meeting.meeting_name)
        next_country = t_country(ctx.next_meeting.country_name)
        next_time = ""
        if ctx.next_meeting.date_start:
            next_time = f"\n🗓 {format_time(ctx.next_meeting.date_start)}"
        sections.append(
            f"📅 <b>下一站:</b> {_e(next_gp)}\n"
            f"📍 {_e(ctx.next_meeting.circuit_short_name)}，{_e(next_country)}{next_time}"
        )

    return "\n".join(sections)


def format_pre_sprint_message(ctx: PreRaceContext, ai_summary: str) -> str:
    """Format the pre-sprint notification."""
    sprint_time = format_time(ctx.session.date_start) if ctx.session.date_start else "待定"
    gp_name = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)

    sections = [
        f"🏎 <b>冲刺赛: {_e(gp_name)}</b>",
        f"📍 {_e(ctx.meeting.circuit_short_name)}，{_e(country)}",
        f"🕐 发车时间: {sprint_time} (北京时间)",
        "",
    ]

    if ctx.grid:
        sections.append(_format_grid(ctx.grid))
        sections.append("")

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))
        sections.append("")

    if ctx.weather:
        sections.append(f"🌤 <b>天气:</b> {_format_weather(ctx.weather)}")
        sections.append("")

    if ai_summary:
        sections.append(f"📝 {_e(ai_summary)}")

    return "\n".join(sections)
