# ================================================================
# commands.py — Slash commands của bot donate
# ================================================================

from datetime import datetime, timedelta
import discord
from discord import app_commands

from bot.config import PACKAGES
from bot.data import gen_code, fmt_money, fmt_months, load_data, save_data
from bot.embeds import build_donate_list_embed, build_dm_success_embed
from bot.views import SimplePackageView, PublicDonateView


def register_commands(bot: discord.ext.commands.Bot) -> None:
    """Đăng ký tất cả slash commands vào bot tree."""

    # ── /donate — Mở menu donate (dành cho tất cả) ───────────────
    @bot.tree.command(name="donate", description="Donate để ủng hộ server")
    async def slash_donate(interaction: discord.Interaction):
        view = SimplePackageView(default_target=interaction.user)
        await interaction.response.send_message(view=view, ephemeral=True)

    # ── /donate_setup — Gửi panel donate vào kênh hiện tại ───────
    @bot.tree.command(name="donate_setup", description="[Admin] Gửi panel donate công khai")
    @app_commands.checks.has_permissions(administrator=True)
    async def donate_setup(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_data()

        # Xóa panel cũ nếu có
        old_channel_id = data.get("panel_channel_id")
        old_message_id = data.get("panel_message_id")
        if old_channel_id:
            old_channel = interaction.guild.get_channel(int(old_channel_id))
            if old_channel and old_message_id:
                try:
                    old_msg = await old_channel.fetch_message(int(old_message_id))
                    await old_msg.delete()
                except Exception:
                    pass

        # Gửi panel mới vào kênh hiện tại
        from bot.embeds import build_panel_embed
        msg = await interaction.channel.send(embed=build_panel_embed(), view=PublicDonateView())
        data["panel_message_id"] = str(msg.id)
        data["panel_channel_id"] = str(interaction.channel.id)
        save_data(data)

        await interaction.followup.send("✅ Panel donate đã được gửi thành công!", ephemeral=True)

    # ── /donate_list — Xem 10 đơn gần nhất ──────────────────────
    @bot.tree.command(name="donate_list", description="[Admin] Xem danh sách đơn donate gần nhất")
    @app_commands.checks.has_permissions(administrator=True)
    async def donate_list(interaction: discord.Interaction):
        data = load_data()
        donations = data.get("donations", [])

        if not donations:
            await interaction.response.send_message("📭 Chưa có đơn donate nào.", ephemeral=True)
            return

        embed = build_donate_list_embed(donations)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /add_role_month — Admin cấp role thủ công ────────────────
    @bot.tree.command(
        name="add_role_month",
        description="[Admin] Cấp role donate theo tháng cho thành viên",
    )
    @app_commands.describe(
        member="Thành viên cần cấp role",
        package="Gói donate",
        months="Số tháng",
    )
    @app_commands.choices(
        package=[
            app_commands.Choice(name=f"{pkg['emoji']} {pkg['name']}", value=key)
            for key, pkg in PACKAGES.items()
        ],
        months=[
            app_commands.Choice(name="1 tháng", value=1),
            app_commands.Choice(name="2 tháng", value=2),
            app_commands.Choice(name="3 tháng", value=3),
        ],
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_role_month(
        interaction: discord.Interaction,
        member: discord.Member,
        package: str,
        months: int,
    ):
        pkg = PACKAGES[package]
        role = interaction.guild.get_role(pkg["role_id"])

        if not role:
            await interaction.response.send_message(
                f"❌ Không tìm thấy role ID `{pkg['role_id']}`. Kiểm tra lại server roles.",
                ephemeral=True,
            )
            return

        try:
            await member.add_roles(role, reason=f"Admin cấp {pkg['name']} {months} tháng")
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bot không có quyền cấp role này.", ephemeral=True
            )
            return

        code = gen_code()
        now = datetime.now()
        expires_dt = now + timedelta(days=30 * months)

        # Lưu đơn với trạng thái approved ngay
        data = load_data()
        data["donations"].append({
            "code": code,
            "user_id": str(interaction.user.id),
            "user_name": interaction.user.display_name,
            "target_id": str(member.id),
            "target_name": member.display_name,
            "package_key": package,
            "package_name": pkg["name"],
            "months": str(months),
            "amount": pkg["prices"][str(months)],
            "status": "approved",
            "created_at": now.isoformat(),
            "approved_at": now.isoformat(),
            "approved_by": str(interaction.user.id),
            "expires_at": expires_dt.isoformat(),
            "note": "Admin cấp thủ công",
        })
        save_data(data)

        # Phản hồi cho admin
        embed = discord.Embed(
            title="✅ Cấp role thành công",
            description=f"Đã cấp {role.mention} cho {member.mention} trong **{months} tháng**.",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📦 Gói", value=pkg["name"], inline=True)
        embed.add_field(name="💰 Giá trị", value=fmt_money(pkg["prices"][str(months)]), inline=True)
        embed.set_footer(text=f"Cấp bởi: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

        # DM thông báo cho thành viên được cấp role
        try:
            dm_embed = build_dm_success_embed(
                pkg=pkg,
                amount=pkg["prices"][str(months)],
                code=code,
                created_at=now.strftime("%d/%m/%Y %H:%M:%S"),
                expires_at=expires_dt.strftime("%d/%m/%Y %H:%M:%S"),
                is_gift=True,
                donor_mention=interaction.user.mention,
                target=member,
            )
            await member.send(embed=dm_embed)
        except Exception:
            pass

    # ── Error handlers ────────────────────────────────────────────
    @donate_setup.error
    @donate_list.error
    @add_role_month.error
    async def admin_command_error(interaction: discord.Interaction, error: Exception):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bạn không có quyền sử dụng lệnh này.", ephemeral=True
            )
