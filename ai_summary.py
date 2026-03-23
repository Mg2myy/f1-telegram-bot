"""Generate race summaries using smart templates (no external API needed)."""

from __future__ import annotations

from models import PostRaceContext, PreRaceContext
from translations import t_country, t_driver, t_gp, t_team


class SummaryGenerator:
    def generate_pre_race_summary(self, ctx: PreRaceContext) -> str:
        parts = []

        if ctx.grid:
            pole = ctx.grid[0]
            pole_name = t_driver(pole.driver_name)
            team_name = t_team(pole.team_name)

            if len(ctx.grid) >= 2 and ctx.grid[0].team_name == ctx.grid[1].team_name:
                parts.append(f"{team_name}包揽头排，{pole_name}获得杆位")
            else:
                parts.append(f"{pole_name}从杆位出发")

        if len(ctx.driver_standings) >= 2:
            leader = ctx.driver_standings[0]
            second = ctx.driver_standings[1]
            gap = leader.points - second.points
            if gap <= 10:
                parts.append(
                    f"{t_driver(leader.driver_name)}仅以{gap:.0f}分领先"
                    f"{t_driver(second.driver_name)}，积分争夺白热化"
                )
            elif gap > 50:
                parts.append(
                    f"{t_driver(leader.driver_name)}以{gap:.0f}分优势领跑积分榜"
                )

        if ctx.weather and ctx.weather.rainfall:
            parts.append("雨战增添变数")

        if not parts:
            gp = t_gp(ctx.meeting.meeting_name)
            return f"{gp}即将开始，一场精彩对决值得期待。"

        return "，".join(parts) + "。"

    def generate_post_race_summary(self, ctx: PostRaceContext) -> str:
        sentences = []

        if ctx.results:
            winner_name = t_driver(ctx.results[0].driver_name)
            gp = t_gp(ctx.meeting.meeting_name)
            if ctx.is_sprint:
                sentences.append(f"{winner_name}赢得冲刺赛胜利")
            else:
                sentences.append(f"{winner_name}拿下{gp}冠军")

            podium_teams = {r.team_name for r in ctx.results[:3]}
            if len(podium_teams) == 3:
                p2 = t_driver(ctx.results[1].driver_name)
                p3 = t_driver(ctx.results[2].driver_name)
                sentences[-1] += f"，{p2}和{p3}登上领奖台"

        events = []
        if ctx.red_flags > 0:
            events.append(f"{ctx.red_flags}次红旗")
        if ctx.safety_cars > 0:
            events.append(f"{ctx.safety_cars}次安全车")
        if events:
            sentences.append(f"比赛出现{'和'.join(events)}")

        if ctx.dnf_list:
            names = "、".join(t_driver(r.driver_name) for r in ctx.dnf_list[:3])
            sentences.append(f"{names}遗憾退赛")

        if len(ctx.driver_standings) >= 2:
            leader = ctx.driver_standings[0]
            second = ctx.driver_standings[1]
            gap = leader.points - second.points
            sentences.append(
                f"{t_driver(leader.driver_name)}以{leader.points:.0f}分领跑积分榜，"
                f"领先{t_driver(second.driver_name)} {gap:.0f}分"
            )

        if ctx.next_meeting and not ctx.is_sprint:
            country = t_country(ctx.next_meeting.country_name)
            sentences.append(f"下一站转战{country} {ctx.next_meeting.circuit_short_name}")

        return "。".join(sentences) + "。" if sentences else ""
