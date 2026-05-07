from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from analyzers.food import analyze_food, is_food_related
from analyzers.sleep import analyze_sleep, is_sleep_report
from analyzers.typing_score import analyze_typing
from analyzers.workout import analyze_workout, is_workout_related
from cogs.roles import RoleTier, sync_member_role
from services.database import Database
from services.streak import BONUS_BITS, evaluate_streak
from utils.embeds import info_embed, report_embed


class ReportsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database) -> None:
        self.bot = bot
        self.db = db
        self.channel_map = {
            int(os.getenv("CHANNEL_WORKOUT", "0")): "workout",
            int(os.getenv("CHANNEL_FOOD", "0")): "food",
            int(os.getenv("CHANNEL_SLEEP", "0")): "sleep",
            int(os.getenv("CHANNEL_TYPING", "0")): "typing",
        }
        self.tz_offset = int(os.getenv("TZ_OFFSET_HOURS", "9"))
        self.bonus_points = {
            7: int(os.getenv("BONUS_7", "50")),
            30: int(os.getenv("BONUS_30", "250")),
            100: int(os.getenv("BONUS_100", "1000")),
        }
        self.role_tiers = self._build_role_tiers()

    def _build_role_tiers(self) -> list[RoleTier]:
        values = [
            ("ROLE_BEGINNER_ID", "POINT_TIER_BEGINNER"),
            ("ROLE_DISCIPLINED_ID", "POINT_TIER_DISCIPLINED"),
            ("ROLE_SIGMA_ID", "POINT_TIER_SIGMA"),
            ("ROLE_ELITE_ID", "POINT_TIER_ELITE"),
            ("ROLE_MONSTER_ID", "POINT_TIER_MONSTER"),
        ]
        tiers: list[RoleTier] = []
        for role_key, point_key in values:
            role_id = os.getenv(role_key, "").strip()
            if role_id:
                tiers.append(RoleTier(role_id=int(role_id), threshold=int(os.getenv(point_key, "0"))))
        return tiers

    async def _apply_streak_and_bonus(self, user_id: int) -> tuple[int, int]:
        user = self.db.get_or_create_user(user_id)
        streak_eval = evaluate_streak(user.last_report_date, user.streak_days, self.tz_offset, datetime.now(timezone.utc))
        bonus = 0
        if streak_eval.date_key != user.last_report_date:
            self.db.set_streak(user_id, streak_eval.streak_days, streak_eval.date_key)
            if streak_eval.bonus_triggered_day is not None:
                day = streak_eval.bonus_triggered_day
                bit = BONUS_BITS[day]
                if not self.db.has_claimed_bonus(user_id, bit):
                    bonus = self.bonus_points.get(day, 0)
                    self.db.add_bonus(user_id, bonus, bit)
        return streak_eval.streak_days, bonus

    def _today_key(self) -> str:
        tz = timezone(timedelta(hours=self.tz_offset))
        return datetime.now(timezone.utc).astimezone(tz).strftime("%Y-%m-%d")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        category = self.channel_map.get(message.channel.id)
        if not category:
            return
        if category == "workout" and not is_workout_related(message.content):
            return
        if category == "food" and not is_food_related(message.content):
            return
        if category == "sleep" and not is_sleep_report(message.content):
            return

        user_id = message.author.id
        today_key = self._today_key()
        inserted = self.db.add_daily_report(user_id, today_key, category)
        if not inserted:
            await message.reply(embed=info_embed("本日は記録済み", "同じカテゴリは1日1回までポイント加算されます。", kind="warning"))
            return

        if category == "workout":
            result = analyze_workout(message.content)
            title = "筋トレ報告を評価しました"
            extra = []
        elif category == "food":
            result = await analyze_food(message.content)
            title = "食事報告を評価しました"
            extra = [("分析方式", "LLM" if getattr(result, "source", "rule") == "llm" else "Rule")]
        elif category == "sleep":
            result = analyze_sleep(message.content)
            title = "睡眠報告を評価しました"
            extra = [("睡眠時間", f"{result.hours:.1f}h" if result.hours else "-")]
        else:
            result = analyze_typing(message.content)
            title = "タイピング報告を評価しました"
            extra = [("WPM", str(result.wpm) if result.wpm is not None else "-"), ("Accuracy", f"{result.accuracy}%" if result.accuracy is not None else "-")]

        user_state = self.db.update_user_points(user_id, category, result.points)
        self.db.add_report_log(user_id, category, result.points)
        streak_days, bonus = await self._apply_streak_and_bonus(user_id)
        if bonus > 0:
            user_state = self.db.get_or_create_user(user_id)
            extra.append(("継続ボーナス", f"+{bonus} pt"))
        extra.append(("現在ストリーク", f"{streak_days}日"))
        extra.append(("累計ポイント", f"{user_state.total_points} pt"))
        if category == "workout":
            total_rank = self.db.get_user_rank(user_id, "total_points")
            workout_rank = self.db.get_user_rank(user_id, "workout_points")
            weekly_rows = self.db.get_weekly_ranking(10)
            weekly_rank = next((i + 1 for i, row in enumerate(weekly_rows) if row["user_id"] == user_id), None)
            rank_text = f"総合 #{total_rank} / 筋トレ #{workout_rank}"
            if weekly_rank is not None:
                rank_text += f" / 週間 #{weekly_rank}"
            extra.append(("現在ランキング", rank_text))

        await message.reply(embed=report_embed(title=title, score=result.score, points=result.points, comment=result.comment, username=message.author.display_name, extra_fields=extra))
        if isinstance(message.author, discord.Member):
            try:
                await sync_member_role(message.author, user_state.total_points, self.role_tiers)
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot) -> None:
    db: Database = bot.db  # type: ignore[attr-defined]
    await bot.add_cog(ReportsCog(bot, db))
