# ================================================================
# tasks.py — Background tasks: tự động thu hồi role khi hết hạn
# ================================================================

from datetime import datetime
import discord
from discord.ext import tasks, commands

from bot.config import PACKAGES
from bot.data import load_data, save_data
from bot.embeds import build_dm_expired_embed


@tasks.loop(hours=1)
async def check_expired_roles(bot: commands.Bot):
    """
    Chạy mỗi giờ một lần:
    - Tìm các đơn approved đã hết hạn (expires_at < now)
    - Thu hồi role tương ứng khỏi thành viên
    - DM thông báo cho thành viên
    - Đánh dấu đơn là 'expired'
    """
    now = datetime.now()
    data = load_data()
    changed = False

    for donation in data["donations"]:
        # Chỉ xử lý đơn đã duyệt
        if donation["status"] != "approved":
            continue

        expires_at_str = donation.get("expires_at")
        if not expires_at_str:
            continue

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            continue

        # Bỏ qua nếu chưa hết hạn
        if expires_at > now:
            continue

        pkg = PACKAGES.get(donation.get("package_key"))
        if not pkg:
            continue

        # Tìm thành viên trong tất cả guild để thu hồi role
        for guild in bot.guilds:
            try:
                member = await guild.fetch_member(int(donation["target_id"]))
            except discord.NotFound:
                continue

            role = guild.get_role(pkg["role_id"])
            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason=f"Hết hạn donate {donation['code']}")
                except discord.Forbidden:
                    pass

            # DM thông báo hết hạn
            try:
                dm_embed = build_dm_expired_embed(pkg, donation["code"])
                await member.send(embed=dm_embed)
            except Exception:
                pass

            break  # Đã xử lý xong cho guild đầu tiên tìm thấy member

        # Đánh dấu đơn là expired
        donation["status"] = "expired"
        donation["expired_at"] = now.isoformat()
        changed = True

    if changed:
        save_data(data)


def setup_tasks(bot: discord.ext.commands.Bot) -> None:
    """
    Gọi hàm này từ on_ready để khởi động background tasks.
    KHÔNG gọi ở module-level vì cần event loop đang chạy.
    """
    if not check_expired_roles.is_running():
        check_expired_roles.start(bot)
