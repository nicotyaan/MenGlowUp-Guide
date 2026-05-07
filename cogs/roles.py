from __future__ import annotations

from dataclasses import dataclass

import discord


@dataclass
class RoleTier:
    role_id: int
    threshold: int


async def sync_member_role(member: discord.Member, total_points: int, tiers: list[RoleTier]) -> None:
    if not tiers:
        return
    sorted_tiers = sorted(tiers, key=lambda x: x.threshold)
    target: RoleTier | None = None
    for tier in sorted_tiers:
        if total_points >= tier.threshold:
            target = tier

    if target is None:
        return

    guild = member.guild
    target_role = guild.get_role(target.role_id)
    if target_role is None:
        return

    tier_role_ids = {tier.role_id for tier in sorted_tiers}
    removable = [r for r in member.roles if r.id in tier_role_ids and r.id != target_role.id]
    if removable:
        await member.remove_roles(*removable, reason="Role tier update")
    if target_role not in member.roles:
        await member.add_roles(target_role, reason="Role tier update")
