# ================================================================
# embeds.py — Tất cả embed builders cho bot donate
# ================================================================

from datetime import datetime
import discord
from bot.config import BANK_ACCOUNT, BANK_HOLDER, PACKAGES
from bot.data import fmt_money, fmt_months, gen_qr_url


def build_panel_embed() -> discord.Embed:
    """Embed hiển thị panel donate công khai."""
    embed = discord.Embed(
        title="ỦNG HỘ CHO SEVER",
        description="Hãy chọn nút bên dưới nhé!",
        color=discord.Color.gold(),
    )
    return embed


def build_package_embed(pkg: dict) -> discord.Embed:
    """Embed hiển thị gói đã chọn — chỉ tên, không có bảng giá."""
    embed = discord.Embed(
        title=f"Đã chọn: {pkg['emoji']} {pkg['name']}",
        description="Chọn số tháng bên dưới.",
        color=discord.Color.gold(),
    )
    return embed


def build_qr_embed(
    donor: discord.Member,
    target: discord.Member,
    amount: int,
    code: str,
    pkg: dict,
    months: str,
) -> discord.Embed:
    """Embed hiển thị mã QR thanh toán cho người donate."""
    qr_url = gen_qr_url(amount, code)
    embed = discord.Embed(
        title="🏦 MÃ QR THANH TOÁN",
        description=(
            "📌 **Quét mã hoặc chuyển khoản thủ công**\n\n"
            f"👤 **Người nhận:** {BANK_HOLDER}\n"
            f"🏦 **Ngân hàng:** MB BANK\n"
            f"💳 **STK:** `{BANK_ACCOUNT}`\n"
            f"💰 **Số tiền:** `{fmt_money(amount)}`\n"
            f"📝 **Nội dung CK:** `{code}`\n\n"
            "📸 **Lưu ý:** Khi chuyển khoản vui lòng chụp bill lại."
        ),
        color=discord.Color.green(),
    )
    embed.set_image(url=qr_url)
    embed.set_footer(text=f"Gói: {pkg['name']} • {fmt_months(months)} • Mã: {code}")
    return embed


def build_admin_embed(
    donor: discord.Member,
    target: discord.Member,
    pkg: dict,
    months: str,
    amount: int,
    code: str,
) -> discord.Embed:
    """Embed gửi vào kênh admin khi có đơn donate mới."""
    embed = discord.Embed(title="📥 ĐƠN DONATE MỚI", color=discord.Color.orange())
    embed.set_author(
        name=f"{donor.display_name} ({donor})",
        icon_url=donor.display_avatar.url,
    )
    embed.add_field(name="👤 Người donate", value=donor.mention, inline=True)
    if target.id != donor.id:
        embed.add_field(name="🎁 Donate cho", value=target.mention, inline=True)
    embed.add_field(name="📦 Gói", value=pkg["name"], inline=True)
    embed.add_field(name="📅 Số tháng", value=fmt_months(months), inline=True)
    embed.add_field(name="💰 Số tiền", value=fmt_money(amount), inline=True)
    embed.add_field(name="📝 Mã", value=f"`{code}`", inline=True)
    embed.set_footer(text=f"Tạo lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    return embed


def build_dm_success_embed(
    pkg: dict,
    amount: int,
    code: str,
    created_at: str,
    expires_at: str,
    is_gift: bool,
    donor_mention: str,
    target: discord.Member,
) -> discord.Embed:
    """Embed DM gửi cho người nhận role sau khi đơn được duyệt."""
    if is_gift:
        desc = (
            f"Cảm ơn {donor_mention} đã ủng hộ server **Quần Đảo Kaia**! 💖\n\n"
            "Sự ủng hộ của họ giúp server ngày càng phát triển hơn. 🚀"
        )
    else:
        desc = (
            "Cảm ơn bạn đã ủng hộ server **Quần Đảo Kaia**! 💖\n\n"
            "Sự ủng hộ của bạn giúp server ngày càng phát triển hơn. 🚀"
        )
    embed = discord.Embed(title="💎 DONATE THÀNH CÔNG!", description=desc, color=discord.Color.gold())
    embed.add_field(name="📦 Gói", value=f"{pkg['emoji']} {pkg['name']}", inline=True)
    embed.add_field(name="💰 Số tiền", value=fmt_money(amount), inline=True)
    embed.add_field(name="📝 Mã", value=f"`{code}`", inline=True)
    embed.add_field(name="🕐 Thời gian đăng ký", value=created_at, inline=False)
    embed.add_field(name="⏳ Thời gian hết hạn", value=expires_at, inline=False)
    embed.set_footer(text="Hẹn gặp lại bạn ở lần donate tiếp theo! 🌴")
    embed.set_thumbnail(url=target.display_avatar.url)
    return embed


def build_dm_expired_embed(pkg: dict, code: str) -> discord.Embed:
    """Embed DM gửi cho thành viên khi role bị thu hồi do hết hạn."""
    embed = discord.Embed(
        title="⏰ Role Đã Hết Hạn",
        description=(
            f"Role **{pkg['name']}** của bạn đã hết hạn và đã được thu hồi.\n\n"
            "Cảm ơn bạn đã đồng hành cùng server **Quần Đảo Kaia**! 💖\n"
            "Bạn có thể donate lại để tiếp tục nhận role nhé."
        ),
        color=discord.Color.red(),
    )
    embed.add_field(name="📦 Gói đã hết hạn", value=f"{pkg['emoji']} {pkg['name']}", inline=True)
    embed.add_field(name="📝 Mã", value=f"`{code}`", inline=True)
    embed.set_footer(text="Hẹn gặp lại bạn! 🌴")
    return embed


def build_thanks_embed(
    target: discord.Member | discord.User | None,
    role_mention: str,
) -> discord.Embed:
    """Embed gửi vào kênh cảm ơn sau khi đơn được duyệt."""
    # ── DEBUG ────────────────────────────────────────────────────
    print(f"[DEBUG build_thanks] type(target)   = {type(target)}")
    print(f"[DEBUG build_thanks] repr(target)   = {repr(target)}")
    user_display = target.mention if target else "người donate"
    print(f"[DEBUG build_thanks] user_display   = {repr(user_display)}")
    # ────────────────────────────────────────────────────────────
    embed = discord.Embed(
        description=(
            f"💎✨ Xin gửi lời cảm ơn đặc biệt đến {user_display} vì đã donate cho server!\n\n"
            "Nhờ những người tuyệt vời như bạn mà bot có thể tiếp tục được duy trì, nâng cấp "
            "và mang đến nhiều trải nghiệm tốt hơn cho mọi người. 🚀\n\n"
            f"🎖️ Role {role_mention} đã được trao như một lời cảm ơn nhỏ từ server!"
        ),
        color=discord.Color.gold(),
    )
    if target:
        embed.set_thumbnail(url="attachment://avatar.png")
    return embed


def build_reject_dm_embed(code: str) -> discord.Embed:
    """Embed DM gửi cho người dùng khi đơn bị từ chối."""
    embed = discord.Embed(
        title="❌ Đơn donate bị từ chối",
        description=(
            f"Đơn donate của bạn với mã `{code}` đã bị từ chối.\n"
            "Vui lòng liên hệ admin nếu bạn đã thực hiện chuyển khoản."
        ),
        color=discord.Color.red(),
    )
    return embed


def build_donate_list_embed(donations: list) -> discord.Embed:
    """Embed hiển thị 10 đơn donate gần nhất cho admin."""
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌", "expired": "🕐"}
    embed = discord.Embed(title="📋 DANH SÁCH DONATE GẦN ĐÂY", color=discord.Color.blue())

    for d in reversed(donations[-10:]):
        emoji = status_emoji.get(d["status"], "❓")
        target_str = f" → {d['target_name']}" if d["target_id"] != d["user_id"] else ""
        embed.add_field(
            name=f"{emoji} `{d['code']}` – {d['package_name']}",
            value=(
                f"👤 {d['user_name']}{target_str}\n"
                f"💰 {fmt_money(d['amount'])} • {fmt_months(d['months'])}\n"
                f"📅 {d['created_at'][:10]}"
            ),
            inline=False,
        )

    total = len(donations)
    approved = sum(1 for d in donations if d["status"] == "approved")
    pending = sum(1 for d in donations if d["status"] == "pending")
    embed.set_footer(
        text=f"Tổng: {total} | ✅ {approved} duyệt | ⏳ {pending} chờ | Hiển thị 10 gần nhất"
    )
    return embed
