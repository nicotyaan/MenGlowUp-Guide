from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from services.database import Database
from utils.embeds import info_embed


def _ranking_embed(title: str, rows: list, value_key: str) -> discord.Embed:
    embed = discord.Embed(title=title, color=discord.Color.blurple())
    if not rows:
        embed.description = "まだデータがありません。"
        return embed
    lines = [f"`#{idx}` <@{row['user_id']}> - **{row[value_key]}**" for idx, row in enumerate(rows, 1)]
    embed.description = "\n".join(lines)
    return embed


class RankingCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database) -> None:
        self.bot = bot
        self.db = db
        self.tz_offset = int(os.getenv("TZ_OFFSET_HOURS", "9"))
        self.weekly_day = int(os.getenv("WEEKLY_RANKING_DAY", "0"))
        self.weekly_hour = int(os.getenv("WEEKLY_RANKING_HOUR", "21"))
        self.weekly_channel_id = int(os.getenv("CHANNEL_WEEKLY_RANKING", os.getenv("CHANNEL_WORKOUT", "0")))
        self.last_weekly_post_key: str | None = None
        self.weekly_ranking_poster.start()

    def cog_unload(self) -> None:
        self.weekly_ranking_poster.cancel()

    def _local_now(self) -> datetime:
        tz = timezone(timedelta(hours=self.tz_offset))
        return datetime.now(timezone.utc).astimezone(tz)

    def _weekly_embed(self) -> discord.Embed:
        rows = self.db.get_weekly_ranking(10)
        embed = discord.Embed(title="週間ランキング (直近7日)", color=discord.Color.gold())
        if not rows:
            embed.description = "今週の記録がまだありません。"
            return embed
        lines = [f"`#{i}` <@{row['user_id']}> - **{row['weekly_points']} pt**" for i, row in enumerate(rows, 1)]
        embed.description = "\n".join(lines)
        return embed

    @tasks.loop(minutes=10)
    async def weekly_ranking_poster(self) -> None:
        if self.weekly_channel_id <= 0:
            return
        now_local = self._local_now()
        week_key = now_local.strftime("%Y-W%U")
        if self.last_weekly_post_key == week_key:
            return
        if now_local.weekday() != self.weekly_day or now_local.hour != self.weekly_hour:
            return
        channel = self.bot.get_channel(self.weekly_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=self._weekly_embed())
            self.last_weekly_post_key = week_key

    @weekly_ranking_poster.before_loop
    async def before_weekly_ranking_poster(self) -> None:
        await self.bot.wait_until_ready()

    @app_commands.command(name="ranking", description="総合ポイントランキングを表示")
    async def ranking(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=_ranking_embed("総合ランキング", self.db.get_top_users("total_points", 10), "total_points"))

    @app_commands.command(name="workoutrank", description="筋トレランキングを表示")
    async def workoutrank(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=_ranking_embed("筋トレランキング", self.db.get_top_users("workout_points", 10), "workout_points"))

    @app_commands.command(name="typingrank", description="タイピングランキングを表示")
    async def typingrank(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=_ranking_embed("タイピングランキング", self.db.get_top_users("typing_points", 10), "typing_points"))

    @app_commands.command(name="sleeprank", description="睡眠ランキングを表示")
    async def sleeprank(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=_ranking_embed("睡眠ランキング", self.db.get_top_users("sleep_points", 10), "sleep_points"))

    @app_commands.command(name="streak", description="連続日数ランキングを表示")
    async def streak(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=_ranking_embed("ストリークランキング", self.db.get_top_users("streak_days", 10), "streak_days"))

    @app_commands.command(name="weeklyrank", description="直近7日間のランキングを表示")
    async def weeklyrank(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=self._weekly_embed())

    @app_commands.command(name="mypoint", description="自分のポイント内訳を表示")
    async def mypoint(self, interaction: discord.Interaction) -> None:
        user = self.db.get_or_create_user(interaction.user.id)
        embed = info_embed("あなたのポイント", "カテゴリ別の内訳です。")
        embed.add_field(name="Total", value=f"{user.total_points} pt")
        embed.add_field(name="Workout", value=f"{user.workout_points} pt")
        embed.add_field(name="Food", value=f"{user.food_points} pt")
        embed.add_field(name="Sleep", value=f"{user.sleep_points} pt")
        embed.add_field(name="Typing", value=f"{user.typing_points} pt")
        embed.add_field(name="Streak", value=f"{user.streak_days} 日")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    db: Database = bot.db  # type: ignore[attr-defined]
    await bot.add_cog(RankingCog(bot, db))
