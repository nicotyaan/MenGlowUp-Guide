from __future__ import annotations

import discord


COLORS = {
    "success": discord.Color.green(),
    "warning": discord.Color.orange(),
    "info": discord.Color.blue(),
    "error": discord.Color.red(),
}


def report_embed(
    *,
    title: str,
    score: int,
    points: int,
    comment: str,
    username: str,
    extra_fields: list[tuple[str, str]] | None = None,
) -> discord.Embed:
    embed = discord.Embed(title=title, color=COLORS["success"])
    embed.add_field(name="点数", value=f"{score}/10", inline=True)
    embed.add_field(name="獲得ポイント", value=f"{points} pt", inline=True)
    embed.add_field(name="コメント", value=comment, inline=False)
    if extra_fields:
        for n, v in extra_fields:
            embed.add_field(name=n, value=v, inline=True)
    embed.set_footer(text=f"reported by {username}")
    return embed


def info_embed(title: str, description: str, kind: str = "info") -> discord.Embed:
    return discord.Embed(title=title, description=description, color=COLORS.get(kind, COLORS["info"]))
