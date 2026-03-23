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

# 国旗 emoji 映射
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


def _format_weather(w: WeatherData) -> str:
    icon = "🌧" if w.rainfall else "☀️"
    parts = [icon]
    if w.air_temperature is not None:
        parts.append(f"{w.air_temperature:.0f}°C")
    if w.track_temperature is not None:
        parts.append(f"赛道{w.track_temperature:.0f}°C")
    if w.humidity is not None:
        parts.append(f"💧{w.humidity:.0f}%")
    if w.wind_speed is not None:
        parts.append(f"💨{w.wind_speed:.1f}m/s")
    return " │ ".join(parts)


def _divider(title: str) -> str:
    return f"\n╔═══ {title} ═══╗"


def _format_grid(grid: list[GridPosition]) -> str:
    lines = [_divider("🏎 发车格")]
    for g in grid:
        pos = g.position
        bar = "█" * (5 - pos) + "░" * (pos - 1)  # visual bar
        lines.append(
            f"  P{pos} {bar} {_e(t_driver(g.driver_name))}"
            f"\n       └─ {_e(t_team(g.team_name))}"
        )
    return "\n".join(lines)


def _format_results(results: list[RaceResult]) -> str:
    lines = [_divider("🏆 比赛成绩")]
    for r in results:
        medal = POSITION_EMOJI.get(r.position, f"P{r.position}")
        driver = _e(t_driver(r.driver_name))
        team = _e(t_team(r.team_name))
        time_str = f"  ⏱ {r.time}" if r.time else ""
        if r.position <= 3:
            lines.append(f"  {medal} <b>{driver}</b> │ {team}{time_str}")
        else:
            lines.append(f"  {medal}  {driver} │ {team}{time_str}")
    return "\n".join(lines)


def _format_fastest_lap(fl: FastestLap) -> str:
    return (
        f"\n⚡ <b>最快圈</b>\n"
        f"  {_e(t_driver(fl.driver_name))} │ "
        f"<b>{fl.lap_time}</b> │ 第{fl.lap_number}圈"
    )


def _format_driver_standings(standings: list[DriverStanding]) -> str:
    lines = [_divider("👤 车手积分榜")]
    max_pts = standings[0].points if standings else 1
    for s in standings:
        bar_len = int((s.points / max_pts) * 8) if max_pts > 0 else 0
        bar = "▓" * bar_len + "░" * (8 - bar_len)
        change = f" <i>(+{s.points_change:.0f})</i>" if s.points_change > 0 else ""
        lines.append(
            f"  {s.position}. {_e(t_driver(s.driver_name))}\n"
            f"     {bar} <b>{s.points:.0f}</b>分{change}"
        )
    return "\n".join(lines)


def _format_constructor_standings(standings: list[ConstructorStanding]) -> str:
    lines = [_divider("🏢 车队积分榜")]
    max_pts = standings[0].points if standings else 1
    for s in standings:
        bar_len = int((s.points / max_pts) * 8) if max_pts > 0 else 0
        bar = "▓" * bar_len + "░" * (8 - bar_len)
        change = f" <i>(+{s.points_change:.0f})</i>" if s.points_change > 0 else ""
        lines.append(
            f"  {s.position}. {_e(t_team(s.team_name))}\n"
            f"     {bar} <b>{s.points:.0f}</b>分{change}"
        )
    return "\n".join(lines)


def _format_incidents(
    dnf_list: list[RaceResult],
    penalties: list[RaceControlEvent],
    safety_cars: int,
    red_flags: int,
) -> str:
    parts = []
    if safety_cars > 0 or red_flags > 0:
        flags = []
        if safety_cars > 0:
            flags.append(f"🟡 安全车 ×{safety_cars}")
        if red_flags > 0:
            flags.append(f"🔴 红旗 ×{red_flags}")
        parts.append("  ".join(flags))
    if dnf_list:
        names = "、".join(t_driver(r.driver_name) for r in dnf_list)
        parts.append(f"💥 退赛: {_e(names)}")
    if penalties:
        for p in penalties:
            parts.append(f"⚠️ {_e(p.message)}")
    if not parts:
        return ""
    return _divider("📋 赛事事件") + "\n" + "\n".join(f"  {p}" for p in parts)


def format_pre_race_message(ctx: PreRaceContext, ai_summary: str) -> str:
    flag = _flag(ctx.meeting.country_name)
    gp = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)
    race_time = format_time(ctx.session.date_start) if ctx.session.date_start else "待定"

    header = (
        f"{flag} <b>{gp}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📍 {_e(ctx.meeting.circuit_short_name)} · {_e(country)}\n"
        f"🕐 {race_time} 北京时间\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )

    sections = [header]

    if ctx.grid:
        sections.append(_format_grid(ctx.grid))

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))

    if ctx.weather:
        sections.append(f"\n🌡 <b>天气</b>\n  {_format_weather(ctx.weather)}")

    if ai_summary:
        sections.append(f"\n💬 <b>赛前展望</b>\n  <i>{_e(ai_summary)}</i>")

    sections.append("\n━━━━━━━━━━━━━━━━━━━")

    return "\n".join(sections)


def format_post_race_message(ctx: PostRaceContext, ai_summary: str) -> str:
    flag = _flag(ctx.meeting.country_name)
    gp = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)
    label = "冲刺赛" if ctx.is_sprint else "正赛"

    header = (
        f"🏁 <b>{gp} · {label}报告</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{flag} {_e(ctx.meeting.circuit_short_name)} · {_e(country)}"
    )

    sections = [header]

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
        sections.append(f"\n🌡 <b>天气</b>\n  {_format_weather(ctx.weather)}")

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))

    if ai_summary:
        sections.append(f"\n💬 <b>赛后点评</b>\n  <i>{_e(ai_summary)}</i>")

    if ctx.next_meeting and not ctx.is_sprint:
        next_flag = _flag(ctx.next_meeting.country_name)
        next_gp = t_gp(ctx.next_meeting.meeting_name)
        next_country = t_country(ctx.next_meeting.country_name)
        next_time = ""
        if ctx.next_meeting.date_start:
            next_time = f"\n  🕐 {format_time(ctx.next_meeting.date_start)} 北京时间"
        sections.append(
            f"\n{'━' * 19}\n"
            f"📅 <b>下一站</b>\n"
            f"  {next_flag} {_e(next_gp)}\n"
            f"  📍 {_e(ctx.next_meeting.circuit_short_name)} · {_e(next_country)}"
            f"{next_time}"
        )

    sections.append(f"\n{'━' * 19}")

    return "\n".join(sections)


def format_pre_sprint_message(ctx: PreRaceContext, ai_summary: str) -> str:
    flag = _flag(ctx.meeting.country_name)
    gp = t_gp(ctx.meeting.meeting_name)
    country = t_country(ctx.meeting.country_name)
    sprint_time = format_time(ctx.session.date_start) if ctx.session.date_start else "待定"

    header = (
        f"🏎💨 <b>{gp} · 冲刺赛</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{flag} {_e(ctx.meeting.circuit_short_name)} · {_e(country)}\n"
        f"🕐 {sprint_time} 北京时间\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )

    sections = [header]

    if ctx.grid:
        sections.append(_format_grid(ctx.grid))

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))

    if ctx.weather:
        sections.append(f"\n🌡 <b>天气</b>\n  {_format_weather(ctx.weather)}")

    if ai_summary:
        sections.append(f"\n💬 <b>赛前展望</b>\n  <i>{_e(ai_summary)}</i>")

    sections.append(f"\n{'━' * 19}")

    return "\n".join(sections)
