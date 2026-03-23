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
)
from utils import format_time


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_grid(grid: list[GridPosition]) -> str:
    lines = ["<b>━━━ 发车格 (Top {}) ━━━</b>".format(len(grid))]
    for g in grid:
        lines.append(
            f"{g.position}. {_escape_html(g.driver_name)} ({_escape_html(g.team_name)})"
        )
    return "\n".join(lines)


def _format_results(results: list[RaceResult]) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = ["<b>━━━ 成绩 (Top {}) ━━━</b>".format(len(results))]
    for r in results:
        medal = medals.get(r.position, f"{r.position}.")
        prefix = f"{medal} " if r.position <= 3 else f"{r.position}.  "
        time_str = f" — {r.time}" if r.time else ""
        lines.append(
            f"{prefix}{_escape_html(r.driver_name)} ({_escape_html(r.team_name)}){time_str}"
        )
    return "\n".join(lines)


def _format_fastest_lap(fl: FastestLap) -> str:
    return (
        f"⚡ <b>最快圈:</b> {_escape_html(fl.driver_name)} — "
        f"{fl.lap_time} (第{fl.lap_number}圈)"
    )


def _format_driver_standings(standings: list[DriverStanding]) -> str:
    lines = ["<b>━━━ 车手积分榜 ━━━</b>"]
    for s in standings:
        change = ""
        if s.points_change > 0:
            change = f" <i>(+{s.points_change:.0f})</i>"
        lines.append(
            f"{s.position}. {_escape_html(s.driver_name)} — {s.points:.0f} pts{change}"
        )
    return "\n".join(lines)


def _format_constructor_standings(standings: list[ConstructorStanding]) -> str:
    lines = ["<b>━━━ 车队积分榜 ━━━</b>"]
    for s in standings:
        change = ""
        if s.points_change > 0:
            change = f" <i>(+{s.points_change:.0f})</i>"
        lines.append(f"{s.position}. {_escape_html(s.team_name)} — {s.points:.0f} pts{change}")
    return "\n".join(lines)


def _format_dnf(dnf_list: list[RaceResult]) -> str:
    if not dnf_list:
        return ""
    names = ", ".join(_escape_html(r.driver_name) for r in dnf_list)
    return f"❌ <b>退赛:</b> {names}"


def _format_penalties(penalties: list[RaceControlEvent]) -> str:
    if not penalties:
        return ""
    lines = []
    for p in penalties:
        lines.append(f"⚠️ {_escape_html(p.message)}")
    return "\n".join(lines)


def format_pre_race_message(ctx: PreRaceContext, ai_summary: str) -> str:
    """Format the pre-race Telegram notification."""
    race_time = format_time(ctx.session.date_start) if ctx.session.date_start else "TBD"

    sections = [
        f"🏁 <b>RACE DAY: {_escape_html(ctx.meeting.meeting_name)}</b>",
        f"📍 {_escape_html(ctx.meeting.circuit_short_name)}, {_escape_html(ctx.meeting.country_name)}",
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
        sections.append(f"🌤 <b>天气:</b> {_escape_html(ctx.weather.summary)}")
        sections.append("")

    if ai_summary:
        sections.append(f"📝 {_escape_html(ai_summary)}")

    return "\n".join(sections)


def format_post_race_message(ctx: PostRaceContext, ai_summary: str) -> str:
    """Format the post-race Telegram notification."""
    header = "SPRINT RESULT" if ctx.is_sprint else "RACE RESULT"

    sections = [
        f"🏆 <b>{header}: {_escape_html(ctx.meeting.meeting_name)}</b>",
        f"📍 {_escape_html(ctx.meeting.circuit_short_name)}, {_escape_html(ctx.meeting.country_name)}",
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

    # Safety car / red flag summary
    flags = []
    if ctx.safety_cars > 0:
        flags.append(f"安全车 x{ctx.safety_cars}")
    if ctx.red_flags > 0:
        flags.append(f"红旗 x{ctx.red_flags}")
    if flags:
        sections.append(f"🚩 {', '.join(flags)}")
        sections.append("")

    if ctx.weather:
        sections.append(f"🌤 <b>天气:</b> {_escape_html(ctx.weather.summary)}")
        sections.append("")

    if ctx.driver_standings:
        sections.append(_format_driver_standings(ctx.driver_standings))
        sections.append("")

    if ctx.constructor_standings:
        sections.append(_format_constructor_standings(ctx.constructor_standings))
        sections.append("")

    if ai_summary:
        sections.append(f"📝 {_escape_html(ai_summary)}")
        sections.append("")

    # Next race info (only for main race, not sprint)
    if ctx.next_meeting and not ctx.is_sprint:
        next_time = ""
        if ctx.next_meeting.date_start:
            next_time = f"\n🗓 {format_time(ctx.next_meeting.date_start)}"
        sections.append(
            f"📅 <b>下一站:</b> {_escape_html(ctx.next_meeting.meeting_name)}\n"
            f"📍 {_escape_html(ctx.next_meeting.circuit_short_name)}, "
            f"{_escape_html(ctx.next_meeting.country_name)}{next_time}"
        )

    return "\n".join(sections)


def format_pre_sprint_message(ctx: PreRaceContext, ai_summary: str) -> str:
    """Format the pre-sprint notification (lighter version)."""
    sprint_time = format_time(ctx.session.date_start) if ctx.session.date_start else "TBD"

    sections = [
        f"🏎 <b>SPRINT: {_escape_html(ctx.meeting.meeting_name)}</b>",
        f"📍 {_escape_html(ctx.meeting.circuit_short_name)}, {_escape_html(ctx.meeting.country_name)}",
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
        sections.append(f"🌤 <b>天气:</b> {_escape_html(ctx.weather.summary)}")
        sections.append("")

    if ai_summary:
        sections.append(f"📝 {_escape_html(ai_summary)}")

    return "\n".join(sections)
