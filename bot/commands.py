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


async def is_owner(interaction: discord.Interaction) -> bool:
    """Chỉ cho phép chủ sở hữu bot sử dụng lệnh."""
    return await interaction.client.is_owner(interaction.user)


def register_commands(bot: discord.ext.commands.Bot) -> None:
    """Đăng ký tất cả slash commands vào bot tree."""

    # ── /donate — Mở menu donate (dành cho tất cả) ───────────────
    @bot.tree.command(name="donate", description="Donate để ủng hộ server")
    async def slash_donate(interaction: discord.Interaction):
        view = SimplePackageView(default_target=interaction.user)
        await interaction.response.send_message(
            content="Chọn gói donate và số tháng bạn muốn:",
            view=view,
            ephemeral=True,
        )

    # ── /donate_setup — Gửi panel donate vào kênh hiện tại ───────
    @bot.tree.command(name="donate_setup", description="[Owner] Gửi panel donate công khai")
    @app_commands.check(is_owner)
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
    @bot.tree.command(name="donate_list", description="[Owner] Xem danh sách đơn donate gần nhất")
    @app_commands.check(is_owner)
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
    @app_commands.check(is_owner)
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

    # ── /role_list — Xem danh sách role đang hoạt động ──────────
    @bot.tree.command(
        name="role_list",
        description="[Owner] Xem danh sách role donate đang hoạt động và thời gian hết hạn",
    )
    @app_commands.describe(member="Thành viên cụ thể (bỏ trống để xem tất cả)")
    @app_commands.check(is_owner)
    async def role_list(interaction: discord.Interaction, member: discord.Member = None):
        data = load_data()
        now = datetime.now()

        # Lọc các đơn đang approved và chưa hết hạn
        active = [
            d for d in data.get("donations", [])
            if d["status"] == "approved"
            and d.get("expires_at")
            and datetime.fromisoformat(d["expires_at"]) > now
            and (member is None or d["target_id"] == str(member.id))
        ]

        if not active:
            msg = (
                f"📭 {member.mention} không có role donate nào đang hoạt động."
                if member else "📭 Không có role donate nào đang hoạt động."
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        title = f"🎖️ Role đang hoạt động — {member.display_name}" if member else "🎖️ Tất cả role đang hoạt động"
        embed = discord.Embed(title=title, color=discord.Color.green())

        for d in active:
            expires_dt = datetime.fromisoformat(d["expires_at"])
            remaining = expires_dt - now
            days_left = remaining.days

            # Màu cảnh báo nếu sắp hết hạn trong 3 ngày
            warning = " ⚠️" if days_left <= 3 else ""

            try:
                t = await interaction.guild.fetch_member(int(d["target_id"]))
            except discord.NotFound:
                try:
                    t = await interaction.client.fetch_user(int(d["target_id"]))
                except discord.NotFound:
                    t = None
            target_str = t.mention if t else d.get("target_name", str(d["target_id"]))
            embed.add_field(
                name=f"📦 {d['package_name']} — `{d['code']}`{warning}",
                value=(
                    f"👤 {target_str}\n"
                    f"⏳ Hết hạn: **{expires_dt.strftime('%d/%m/%Y %H:%M')}**\n"
                    f"📅 Còn lại: **{days_left} ngày**"
                ),
                inline=False,
            )

        embed.set_footer(text=f"Tổng: {len(active)} role đang hoạt động")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /role_edit_expire — Đặt ngày hết hạn cụ thể cho member ──
    @bot.tree.command(
        name="role_edit_expire",
        description="[Owner] Đặt ngày hết hạn role donate của một thành viên",
    )
    @app_commands.describe(
        member="Thành viên cần chỉnh ngày hết hạn",
        expire_date="Ngày hết hạn mới (DD/MM/YYYY) — ví dụ: 15/08/2025",
        package="Gói cụ thể (bỏ trống để chỉnh tất cả gói đang có)",
    )
    @app_commands.choices(
        package=[
            app_commands.Choice(name=pkg["name"], value=key)
            for key, pkg in PACKAGES.items()
        ]
    )
    @app_commands.check(is_owner)
    async def role_edit_expire(
        interaction: discord.Interaction,
        member: discord.Member,
        expire_date: str,
        package: str = None,
    ):
        data = load_data()

        # Tìm các đơn approved của member (lọc theo gói nếu có)
        donations = [
            d for d in data["donations"]
            if d["status"] == "approved"
            and d["target_id"] == str(member.id)
            and (package is None or d.get("package_key") == package)
        ]

        if not donations:
            msg = (
                f"❌ {member.mention} không có đơn donate nào đang hoạt động"
                + (f" cho gói **{PACKAGES[package]['name']}**." if package else ".")
            )
            await interaction.response.send_message(msg, ephemeral=True)
            return

        # Parse ngày nhập vào (chấp nhận DD/MM/YYYY hoặc DD/MM/YYYY HH:MM)
        new_dt = None
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                new_dt = datetime.strptime(expire_date.strip(), fmt)
                break
            except ValueError:
                continue

        if not new_dt:
            await interaction.response.send_message(
                "❌ Định dạng ngày không hợp lệ.\n"
                "Vui lòng nhập theo dạng: `DD/MM/YYYY`\n"
                "Ví dụ: `15/08/2025`",
                ephemeral=True,
            )
            return

        # Cập nhật từng đơn, lưu lại ngày cũ để hiển thị
        updated = []
        for donation in donations:
            old_expires = donation.get("expires_at", "Chưa có")
            try:
                old_expires = datetime.fromisoformat(old_expires).strftime("%d/%m/%Y")
            except Exception:
                pass
            donation["expires_at"] = new_dt.isoformat()
            donation["expire_edited_at"] = datetime.now().isoformat()
            donation["expire_edited_by"] = str(interaction.user.id)
            updated.append((donation["code"], donation.get("package_name", "—"), old_expires))

        save_data(data)

        # Embed xác nhận
        embed = discord.Embed(title="✅ Đã cập nhật ngày hết hạn", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Thành viên", value=member.mention, inline=False)
        for code_val, pkg_name, old_exp in updated:
            embed.add_field(
                name=f"📦 {pkg_name} — `{code_val}`",
                value=(
                    f"📅 Cũ: ~~{old_exp}~~\n"
                    f"📅 Mới: **{new_dt.strftime('%d/%m/%Y')}**"
                ),
                inline=False,
            )
        embed.set_footer(text=f"Chỉnh bởi: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /check — Đếm số bình luận của thành viên trong một chủ đề ─
    @bot.tree.command(
        name="check",
        description="Kiểm tra số lần bình luận của một thành viên trong chủ đề",
    )
    @app_commands.describe(
        thread="Chủ đề (thread/forum post) cần kiểm tra",
        member="Thành viên muốn kiểm tra (bỏ trống = chính bạn)",
    )
    async def check_comments(
        interaction: discord.Interaction,
        thread: discord.Thread,
        member: discord.Member = None,
    ):
        target = member or interaction.user
        await interaction.response.defer(ephemeral=True)

        # Quét tối đa 500 tin nhắn gần nhất (mới → cũ) để tránh chờ lâu
        SCAN_LIMIT = 500
        messages = []
        async for msg in thread.history(limit=SCAN_LIMIT):
            if msg.author.id == target.id:
                messages.append(msg)

        count = len(messages)
        # messages hiện theo thứ tự mới → cũ, đảo lại để hiển thị cũ → mới
        messages.reverse()

        embed = discord.Embed(
            title="💬 Thống kê bình luận",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 Thành viên", value=target.mention, inline=True)
        embed.add_field(name="📌 Chủ đề", value=thread.mention, inline=True)
        embed.add_field(
            name="💬 Số lần bình luận",
            value=f"**{count}** lần" + (f" *(trong {SCAN_LIMIT} tin gần nhất)*" if count == SCAN_LIMIT else ""),
            inline=False,
        )

        # Hiển thị nội dung (tối đa 10 tin gần nhất)
        if messages:
            show = messages[-10:]
            lines = []
            for i, msg in enumerate(show, start=count - len(show) + 1):
                content = msg.content if msg.content else "*(không có text)*"
                if len(content) > 60:
                    content = content[:57] + "..."
                ts = msg.created_at.strftime("%d/%m %H:%M")
                lines.append(f"`{i}.` [{ts}]({msg.jump_url}) {content}")

            embed.add_field(
                name=f"📋 Nội dung bình luận{' (10 gần nhất)' if count > 10 else ''}",
                value="\n".join(lines),
                inline=False,
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /event — Bật/tắt chế độ chống trùng số trong chủ đề ──────
    @bot.tree.command(
        name="event",
        description="[Owner] Bật/tắt chế độ chống trùng số trong một chủ đề",
    )
    @app_commands.describe(
        thread="Chủ đề cần bật/tắt event",
        action="Bật hoặc tắt event",
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="🟢 Bật", value="start"),
        app_commands.Choice(name="🔴 Tắt", value="stop"),
    ])
    @app_commands.check(is_owner)
    async def event_command(
        interaction: discord.Interaction,
        thread: discord.Thread,
        action: str,
    ):
        from bot.event import load_events, save_events

        data = load_events()
        tid = str(thread.id)

        if action == "start":
            if tid in data["active_events"]:
                await interaction.response.send_message(
                    f"⚠️ Event trong {thread.mention} đã đang bật rồi.", ephemeral=True
                )
                return
            data["active_events"][tid] = {
                "numbers": {},
                "created_by": str(interaction.user.id),
                "created_at": datetime.now().isoformat(),
            }
            save_events(data)
            embed = discord.Embed(
                title="🟢 Event đã bật",
                description=(
                    f"Chủ đề {thread.mention} đang trong chế độ **chống trùng số**.\n"
                    f"Mọi bình luận trùng số sẽ bị **tự động xoá** và thành viên được thông báo."
                ),
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:  # stop
            if tid not in data["active_events"]:
                await interaction.response.send_message(
                    f"⚠️ Event trong {thread.mention} chưa được bật.", ephemeral=True
                )
                return
            event_info = data["active_events"].pop(tid)
            save_events(data)
            total_numbers = len(event_info.get("numbers", {}))
            embed = discord.Embed(
                title="🔴 Event đã tắt",
                description=(
                    f"Đã dừng event tại {thread.mention}.\n"
                    f"Tổng số đã được đăng ký: **{total_numbers}** số."
                ),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /welcome — Cài đặt kênh gửi thông báo chào mừng thành viên mới ─
    @bot.tree.command(name="welcome", description="[Admin] Cài đặt kênh gửi thông báo chào mừng thành viên mới")
    @app_commands.describe(channel="Kênh gửi thông báo chào mừng")
    @app_commands.default_permissions(administrator=True)
    async def welcome_config(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        from bot.data import load_data, save_data
        data = load_data()
        data["welcome_config"] = {"channel_id": str(channel.id)}
        save_data(data)

        embed = discord.Embed(
            title="✅ Đã cài đặt kênh chào mừng",
            color=discord.Color.green(),
        )
        embed.add_field(name="📢 Kênh", value=channel.mention, inline=False)
        embed.add_field(
            name="📋 Thông tin hiển thị",
            value=(
                "👤 **Thành viên** — mention người mới\n"
                "🎁 **Được mời bởi** — Creator sở hữu link (hoặc *Không xác định*)\n"
                "📈 **Tổng người đã mời** — thống kê của Creator\n"
                "🕒 **Thời gian** — giờ Việt Nam (UTC+7)"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /role-all — Thêm role cho tất cả thành viên ──────────────
    @bot.tree.command(name="role-all", description="[Admin] Thêm một role cho tất cả thành viên trong server")
    @app_commands.describe(role="Role muốn thêm cho tất cả thành viên")
    @app_commands.default_permissions(administrator=True)
    async def role_all(interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        # Kiểm tra bot có đủ quyền không
        if role >= guild.me.top_role:
            await interaction.followup.send(
                f"❌ Role {role.mention} cao hơn hoặc bằng role cao nhất của bot. Bot không thể gán role này.",
                ephemeral=True,
            )
            return

        members = [m for m in guild.members if not m.bot and role not in m.roles]

        if not members:
            await interaction.followup.send(
                f"ℹ️ Tất cả thành viên đã có role {role.mention} rồi.",
                ephemeral=True,
            )
            return

        success = 0
        failed = 0
        for member in members:
            try:
                await member.add_roles(role, reason=f"role-all bởi {interaction.user}")
                success += 1
            except Exception:
                failed += 1

        embed = discord.Embed(
            title="✅ Hoàn tất thêm role hàng loạt",
            color=discord.Color.green(),
        )
        embed.add_field(name="🎭 Role", value=role.mention, inline=False)
        embed.add_field(name="✅ Thành công", value=str(success), inline=True)
        if failed:
            embed.add_field(name="❌ Thất bại", value=str(failed), inline=True)
        embed.add_field(name="👥 Tổng xử lý", value=str(success + failed), inline=True)
        embed.set_footer(text=f"Thực hiện bởi: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── Error handlers ────────────────────────────────────────────
    @donate_setup.error
    @donate_list.error
    @add_role_month.error
    @role_list.error
    @role_edit_expire.error
    @event_command.error
    async def owner_command_error(interaction: discord.Interaction, error: Exception):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "❌ Lệnh này chỉ dành cho chủ sở hữu bot.", ephemeral=True
            )
