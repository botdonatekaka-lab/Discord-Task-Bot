# ================================================================
# views.py — Tất cả UI components: Views, Selects, Buttons, Modals
# ================================================================

from datetime import datetime
import io
import discord
from discord.ui import Button, Select, Modal, TextInput, View

from bot.config import PACKAGES, ADMIN_CHANNEL_ID, THANKS_CHANNEL_ID, PRIVILEGE_CHANNEL_ID
from bot.data import gen_code, fmt_money, fmt_months, load_data, save_data
from bot.embeds import (
    build_panel_embed,
    build_package_embed,
    build_qr_embed,
    build_admin_embed,
    build_dm_success_embed,
    build_thanks_embed,
    build_reject_dm_embed,
)


# ── Hàm tiện ích: làm mới panel donate ──────────────────────────

async def refresh_panel(guild: discord.Guild, bot: discord.Client) -> None:
    """Xóa panel cũ và gửi lại panel donate mới vào kênh đã cài đặt."""
    data = load_data()
    channel_id = data.get("panel_channel_id")
    message_id = data.get("panel_message_id")

    if not channel_id:
        return

    channel = guild.get_channel(int(channel_id))
    if not channel:
        return

    # Xóa tin nhắn panel cũ nếu còn tồn tại
    if message_id:
        try:
            old_msg = await channel.fetch_message(int(message_id))
            await old_msg.delete()
        except Exception:
            pass

    # Gửi panel mới
    msg = await channel.send(embed=build_panel_embed(), view=PublicDonateView())
    data["panel_message_id"] = str(msg.id)
    save_data(data)


# ── Logic phê duyệt đơn ─────────────────────────────────────────

async def do_approve(interaction: discord.Interaction, code: str) -> None:
    """Xử lý duyệt đơn donate: cấp role, DM thông báo, đăng cảm ơn."""
    data = load_data()
    donation = next((d for d in data["donations"] if d["code"] == code), None)

    if not donation:
        await interaction.response.send_message("❌ Không tìm thấy đơn.", ephemeral=True)
        return
    if donation["status"] != "pending":
        await interaction.response.send_message("⚠️ Đơn này đã được xử lý rồi.", ephemeral=True)
        return

    guild = interaction.guild
    bot = interaction.client
    try:
        target = await guild.fetch_member(int(donation["target_id"]))
    except discord.NotFound:
        try:
            target = await bot.fetch_user(int(donation["target_id"]))
        except discord.NotFound:
            target = None
    pkg = PACKAGES[donation["package_key"]]
    role = guild.get_role(pkg["role_id"])

    # Cấp role cho thành viên
    if target and role:
        try:
            await target.add_roles(role, reason=f"Donate {code}")
        except discord.Forbidden:
            pass

    # Tính thời gian hết hạn dựa theo số tháng
    try:
        months_int = int(donation["months"])
    except (ValueError, TypeError):
        months_int = 1

    from datetime import timedelta
    expires_dt = datetime.now() + timedelta(days=30 * months_int)

    # Cập nhật trạng thái đơn
    donation["status"] = "approved"
    donation["approved_at"] = datetime.now().isoformat()
    donation["approved_by"] = str(interaction.user.id)
    donation["expires_at"] = expires_dt.isoformat()
    save_data(data)

    # Cập nhật embed admin → màu xanh lá + tiêu đề đã duyệt
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.green()
    embed.title = "✅ ĐÃ DUYỆT"
    embed.add_field(name="✅ Duyệt bởi", value=interaction.user.mention, inline=False)
    await interaction.message.edit(embed=embed, view=None)
    await interaction.response.send_message("✅ Đã duyệt đơn thành công!", ephemeral=True)

    # DM thông báo cho người nhận role
    if target:
        try:
            is_gift = donation["user_id"] != donation["target_id"]
            if is_gift:
                try:
                    donor = await guild.fetch_member(int(donation["user_id"]))
                except discord.NotFound:
                    try:
                        donor = await bot.fetch_user(int(donation["user_id"]))
                    except discord.NotFound:
                        donor = None
                donor_mention = donor.mention if donor else donation.get("user_name", "người donate")
            else:
                donor_mention = target.mention
            dm_embed = build_dm_success_embed(
                pkg=pkg,
                amount=donation["amount"],
                code=code,
                created_at=datetime.fromisoformat(donation["created_at"]).strftime("%d/%m/%Y %H:%M:%S"),
                expires_at=expires_dt.strftime("%d/%m/%Y %H:%M:%S"),
                is_gift=is_gift,
                donor_mention=donor_mention,
                target=target,
            )
            await target.send(embed=dm_embed)
        except Exception:
            pass

    # Gửi lời cảm ơn vào kênh thông báo
    thanks_channel = guild.get_channel(THANKS_CHANNEL_ID)
    if thanks_channel:
        role_mention = f"**{pkg['name']}** {pkg['emoji']}"
        fallback_name = donation.get("target_name") or donation.get("user_name") or "người donate"
        avatar_file = None
        avatar_attached = False
        if target:
            try:
                avatar_bytes = await target.display_avatar.read()
                avatar_file = discord.File(io.BytesIO(avatar_bytes), filename="avatar.png")
                avatar_attached = True
            except Exception:
                # Vẫn gửi embed nếu CDN avatar tạm thời không truy cập được.
                pass

        thanks_embed = build_thanks_embed(
            target,
            role_mention,
            fallback_name,
            avatar_attached=avatar_attached,
        )
        send_kwargs = {"embed": thanks_embed}
        if target:
            send_kwargs["content"] = target.mention
        if avatar_file:
            send_kwargs["file"] = avatar_file
        await thanks_channel.send(**send_kwargs)

    # Làm mới panel
    from bot.views import refresh_panel
    bot_ref = interaction.client
    await refresh_panel(guild, bot_ref)


async def do_reject(interaction: discord.Interaction, code: str) -> None:
    """Xử lý từ chối đơn donate: cập nhật trạng thái, DM thông báo."""
    data = load_data()
    donation = next((d for d in data["donations"] if d["code"] == code), None)

    if not donation:
        await interaction.response.send_message("❌ Không tìm thấy đơn.", ephemeral=True)
        return
    if donation["status"] != "pending":
        await interaction.response.send_message("⚠️ Đơn này đã được xử lý rồi.", ephemeral=True)
        return

    # Cập nhật trạng thái đơn
    donation["status"] = "rejected"
    donation["rejected_at"] = datetime.now().isoformat()
    donation["rejected_by"] = str(interaction.user.id)
    save_data(data)

    # Cập nhật embed admin → màu đỏ + tiêu đề đã từ chối
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.red()
    embed.title = "❌ ĐÃ TỪ CHỐI"
    embed.add_field(name="❌ Từ chối bởi", value=interaction.user.mention, inline=False)
    await interaction.message.edit(embed=embed, view=None)

    # DM thông báo cho người donate
    try:
        target = await interaction.guild.fetch_member(int(donation["target_id"]))
    except discord.NotFound:
        target = None
    if target:
        try:
            await target.send(embed=build_reject_dm_embed(code))
        except Exception:
            pass

    await interaction.response.send_message(
        f"❌ Đã từ chối đơn `{donation['code']}`.", ephemeral=True
    )


# ── Xử lý hoàn tất luồng donate ─────────────────────────────────

async def finalize_donation(
    interaction: discord.Interaction,
    pkg_key: str,
    target: discord.Member,
    donor: discord.Member,
    months: str,
    amount: int,
) -> None:
    """Lưu đơn donate, gửi QR cho người dùng, gửi đơn vào kênh admin."""
    pkg = PACKAGES[pkg_key]
    code = gen_code()

    # Lưu đơn vào file dữ liệu
    data = load_data()
    data["donations"].append({
        "code": code,
        "user_id": str(donor.id),
        "user_name": donor.display_name,
        "target_id": str(target.id),
        "target_name": target.display_name,
        "package_key": pkg_key,
        "package_name": pkg["name"],
        "months": months,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    })
    save_data(data)

    # Hiển thị QR thanh toán cho người dùng
    qr_embed = build_qr_embed(donor, target, amount, code, pkg, months)
    await interaction.response.edit_message(embed=qr_embed, view=None)

    # Gửi đơn vào kênh admin với nút duyệt/từ chối
    admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        admin_embed = build_admin_embed(donor, target, pkg, months, amount, code)
        admin_view = AdminApproveView(code)
        interaction.client.add_view(admin_view)
        await admin_channel.send(embed=admin_embed, view=admin_view)



# ── Dropdown chọn số tháng (có hiển thị giá tiền) ───────────────

class MonthSelect(Select):
    def __init__(self, pkg_key: str, target: discord.Member, donor: discord.Member):
        self.pkg_key = pkg_key
        self.target = target
        self.donor = donor
        pkg = PACKAGES[pkg_key]

        # Hiển thị giá tiền bên cạnh số tháng
        options = [
            discord.SelectOption(
                label=f"{m} tháng — {fmt_money(p)}",
                value=m,
                emoji="📅",
            )
            for m, p in pkg["prices"].items()
        ]
        super().__init__(placeholder="📅 Chọn số tháng...", options=options)

    async def callback(self, interaction: discord.Interaction):
        months = self.values[0]
        pkg = PACKAGES[self.pkg_key]
        amount = pkg["prices"][months]
        await finalize_donation(interaction, self.pkg_key, self.target, self.donor, months, amount)


class MonthSelectView(View):
    def __init__(self, pkg_key: str, target: discord.Member, donor: discord.Member):
        super().__init__(timeout=300)
        self.add_item(MonthSelect(pkg_key, target, donor))


# ── Dropdown chọn gói donate ─────────────────────────────────────

class PackageSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=pkg["name"], value=key, emoji=pkg["emoji"])
            for key, pkg in PACKAGES.items()
        ]
        super().__init__(placeholder="Chọn Role...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        pkg_key = self.values[0]
        pkg = PACKAGES[pkg_key]
        # Lấy người nhận từ view cha (có thể là gift hoặc chính người donate)
        target = self.view.target_user or interaction.user

        embed = build_package_embed(pkg)
        view = MonthSelectView(pkg_key, target, interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)


# ── User select để chọn người nhận gift ──────────────────────────

class GiftTargetSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="Chọn Cho Người Khác...",
            min_values=0,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        # Cập nhật người nhận trong view cha
        self.view.target_user = self.values[0] if self.values else interaction.user
        await interaction.response.defer()


class SimplePackageView(View):
    """View chính: dropdown chọn gói + dropdown chọn người nhận."""
    def __init__(self, default_target: discord.Member = None):
        super().__init__(timeout=300)
        self.target_user = default_target
        self.add_item(PackageSelect())
        self.add_item(GiftTargetSelect())


# ── View admin: nút Duyệt / Từ chối ─────────────────────────────

class AdminApproveView(View):
    """View persistent gắn với mỗi đơn donate, dùng custom_id để khôi phục sau restart."""
    def __init__(self, code: str):
        super().__init__(timeout=None)
        self.code = code

        approve_btn = Button(
            label="✅ Duyệt",
            style=discord.ButtonStyle.success,
            custom_id=f"approve_{code}",
        )
        reject_btn = Button(
            label="❌ Từ Chối",
            style=discord.ButtonStyle.danger,
            custom_id=f"reject_{code}",
        )
        approve_btn.callback = self._approve
        reject_btn.callback = self._reject
        self.add_item(approve_btn)
        self.add_item(reject_btn)

    async def _approve(self, interaction: discord.Interaction):
        await do_approve(interaction, self.code)

    async def _reject(self, interaction: discord.Interaction):
        await do_reject(interaction, self.code)


# ── Panel donate công khai (persistent) ──────────────────────────

class PublicDonateView(View):
    """View panel công khai — persistent, tồn tại sau khi bot restart."""
    def __init__(self):
        super().__init__(timeout=None)
        # Nút Donate — bên trái
        donate_btn = discord.ui.Button(
            label="💸 DONATE",
            style=discord.ButtonStyle.primary,
            custom_id="public_donate_btn",
        )
        donate_btn.callback = self._donate_callback
        self.add_item(donate_btn)
        # Nút Đặc Quyền — bên phải (cùng hàng với nút donate)
        self.add_item(discord.ui.Button(
            label="🎟️ ĐẶC QUYỀN",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1363986043509932093/1513291802193559652",
        ))

    async def _donate_callback(self, interaction: discord.Interaction):
        """Mở menu chọn gói donate (ephemeral)."""
        view = SimplePackageView(default_target=interaction.user)
        await interaction.response.send_message(
            content="Chọn gói donate và số tháng bạn muốn:",
            view=view,
            ephemeral=True,
        )
