"""Generate race summaries using smart templates (no external API needed)."""

from __future__ import annotations

from models import PostRaceContext, PreRaceContext


class SummaryGenerator:
    def generate_pre_race_summary(self, ctx: PreRaceContext) -> str:
        parts = []

        # Pole sitter narrative
        if ctx.grid:
            pole = ctx.grid[0]
            parts.append(f"{pole.driver_name}从杆位出发")

            # If two drivers from same team on front row
            if len(ctx.grid) >= 2 and ctx.grid[0].team_name == ctx.grid[1].team_name:
                parts[0] = (
                    f"{ctx.grid[0].team_name}包揽头排，"
                    f"{ctx.grid[0].driver_name}获得杆位"
                )

        # Championship battle context
        if len(ctx.driver_standings) >= 2:
            leader = ctx.driver_standings[0]
            second = ctx.driver_standings[1]
            gap = leader.points - second.points
            if gap <= 10:
                parts.append(
                    f"{leader.driver_name}仅以{gap:.0f}分领先{second.driver_name}，"
                    f"积分争夺白热化"
                )
            elif gap > 50:
                parts.append(f"{leader.driver_name}以{gap:.0f}分优势领跑积分榜")

        # Weather factor
        if ctx.weather and ctx.weather.rainfall:
            parts.append("雨战增添变数")

        if not parts:
            return f"{ctx.meeting.meeting_name}即将开始，一场精彩对决值得期待。"

        return "，".join(parts) + "。"

    def generate_post_race_summary(self, ctx: PostRaceContext) -> str:
        sentences = []

        # Winner narrative
        if ctx.results:
            winner = ctx.results[0]
            if ctx.is_sprint:
                sentences.append(f"{winner.driver_name}赢得冲刺赛胜利")
            else:
                sentences.append(f"{winner.driver_name}拿下{ctx.meeting.meeting_name}冠军")

            # Podium surprises
            podium_teams = {r.team_name for r in ctx.results[:3]}
            if len(podium_teams) == 3:
                sentences[-1] += f"，{ctx.results[1].driver_name}和{ctx.results[2].driver_name}登上领奖台"

        # Red flags / safety cars
        events = []
        if ctx.red_flags > 0:
            events.append(f"{ctx.red_flags}次红旗")
        if ctx.safety_cars > 0:
            events.append(f"{ctx.safety_cars}次安全车")
        if events:
            sentences.append(f"比赛出现{'和'.join(events)}")

        # DNFs
        if ctx.dnf_list:
            names = "、".join(r.driver_name for r in ctx.dnf_list[:3])
            sentences.append(f"{names}遗憾退赛")

        # Championship impact
        if len(ctx.driver_standings) >= 2:
            leader = ctx.driver_standings[0]
            second = ctx.driver_standings[1]
            gap = leader.points - second.points
            sentences.append(
                f"{leader.driver_name}以{leader.points:.0f}分领跑积分榜，"
                f"领先{second.driver_name} {gap:.0f}分"
            )

        # Next race preview
        if ctx.next_meeting and not ctx.is_sprint:
            sentences.append(f"下一站转战{ctx.next_meeting.country_name} {ctx.next_meeting.circuit_short_name}")

        return "。".join(sentences) + "。" if sentences else ""
