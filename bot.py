from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from services.database import Database
from utils.embeds import info_embed


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True, encoding="utf-8-sig")


class MenGlowUpBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = os.getenv("ENABLE_MEMBERS_INTENT", "false").lower() == "true"
        super().__init__(command_prefix="!", intents=intents)
        self.db = Database("data/bot.db")

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.reports")
        await self.load_extension("cogs.ranking")

        guild_id = os.getenv("GUILD_ID", "").strip()
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            try:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logging.info("Synced commands to guild %s", guild_id)
            except discord.Forbidden:
                logging.warning("No access to guild %s. Falling back to global sync.", guild_id)
                await self.tree.sync()
                logging.info("Synced global commands")
        else:
            await self.tree.sync()
            logging.info("Synced global commands")

    async def close(self) -> None:
        self.db.close()
        await super().close()


bot = MenGlowUpBot()


@bot.event
async def on_ready() -> None:
    logging.info("Logged in as %s (%s)", bot.user, bot.user.id if bot.user else "unknown")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    logging.exception("App command error: %s", error)
    msg = info_embed("エラー", "コマンド実行中に問題が発生しました。時間をおいて再試行してください。", "error")
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=msg, ephemeral=True)
        else:
            await interaction.response.send_message(embed=msg, ephemeral=True)
    except discord.HTTPException:
        pass


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set.")
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
