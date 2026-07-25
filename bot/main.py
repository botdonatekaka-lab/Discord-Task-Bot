# ================================================================
# main.py — Entry point: khởi tạo bot, đăng ký events và commands
# ================================================================

import asyncio
import os
import discord
from discord.ext import commands

from bot.views import PublicDonateView, AdminApproveView
from bot.data import load_data
from bot.commands import register_commands
from bot.event import handle_event_message, is_event_active


# ── Khởi tạo bot ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cache invite: {guild_id: {invite_code: uses}}
bot.invite_cache: dict = {}


@bot.event
async def on_ready():
    """
    Được gọi khi bot đã kết nối Discord thành công.
    - Đăng ký lại persistent views (panel + các đơn pending)
    - Sync slash commands
    - Khởi động background tasks
    - Cache danh sách invite để theo dõi creator
    """
    print(f"✅ Bot đã sẵn sàng: {bot.user} (ID: {bot.user.id})")

    # Đăng ký lại panel donate (persistent view — tồn tại sau restart)
    bot.add_view(PublicDonateView())

    # Đăng ký lại admin approve views cho các đơn đang pending
    data = load_data()
    pending_count = 0
    for donation in data.get("donations", []):
        if donation["status"] == "pending":
            view = AdminApproveView(donation["code"])
            bot.add_view(view)
            pending_count += 1

    print(f"🔄 Đã khôi phục {pending_count} view đang pending")

    # Cache invite của tất cả guild để theo dõi creator
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            bot.invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
        except Exception:
            bot.invite_cache[guild.id] = {}
    print(f"📨 Đã cache invite cho {len(bot.guilds)} guild(s)")

    # Sync slash commands lên Discord (global)
    try:
        synced = await bot.tree.sync()
        print(f"⚙️  Đã sync {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Lỗi sync commands: {e}")

    # Khởi động background tasks (phải trong on_ready vì cần event loop)
    from bot.tasks import setup_tasks
    setup_tasks(bot)

    print("🚀 Bot sẵn sàng hoạt động!")


@bot.event
async def on_invite_create(invite: discord.Invite):
    """Cập nhật cache khi có invite mới được tạo."""
    guild_id = invite.guild.id
    if guild_id not in bot.invite_cache:
        bot.invite_cache[guild_id] = {}
    bot.invite_cache[guild_id][invite.code] = invite.uses


@bot.event
async def on_invite_delete(invite: discord.Invite):
    """Xóa invite khỏi cache khi bị xóa."""
    guild_id = invite.guild.id
    bot.invite_cache.get(guild_id, {}).pop(invite.code, None)


@bot.event
async def on_member_join(member: discord.Member):
    """Xử lý thành viên mới: theo dõi creator invite + gửi embed chào mừng."""
    guild = member.guild

    # ── 1. Theo dõi invite của creator ──────────────────────────
    try:
        new_invites = await guild.invites()
        old_cache = bot.invite_cache.get(guild.id, {})
        new_cache = {inv.code: inv.uses for inv in new_invites}
        bot.invite_cache[guild.id] = new_cache

        used_code = None
        for inv in new_invites:
            if inv.uses > old_cache.get(inv.code, 0):
                used_code = inv.code
                break

        if used_code:
            from bot.creator_data import load_creators, save_creators, get_creator_by_code
            creator_data = load_creators()
            creator = get_creator_by_code(creator_data, used_code)
            if creator:
                creator["join_count"] += 1
                save_creators(creator_data)
    except Exception:
        pass  # Không để lỗi tracking phá vỡ chào mừng

    # ── 2. Gửi embed chào mừng ───────────────────────────────────
    from bot.data import load_data
    data = load_data()
    cfg = data.get("welcome_config")
    if not cfg:
        return

    channel_id = cfg.get("channel_id")
    delete_after = cfg.get("delete_after", 0)
    message = cfg.get("message", "{user} đã tham gia server!")

    if not channel_id:
        return
    channel = guild.get_channel(int(channel_id))
    if not channel:
        return

    description = message.replace("{user}", member.mention)
    embed = discord.Embed(description=description, color=0x2B2D31)
    msg = await channel.send(embed=embed)

    if delete_after and delete_after > 0:
        await asyncio.sleep(delete_after * 60)
        try:
            await msg.delete()
        except Exception:
            pass


@bot.event
async def on_message(message: discord.Message):
    """Lắng nghe tin nhắn — xử lý chống trùng số trong event thread."""
    if message.author.bot:
        return
    if isinstance(message.channel, discord.Thread) and is_event_active(message.channel.id):
        await handle_event_message(message)
    await bot.process_commands(message)


# Đăng ký slash commands vào bot tree
register_commands(bot)


def run():
    """Khởi chạy bot với token từ biến môi trường."""
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ Thiếu DISCORD_TOKEN trong biến môi trường!")
    bot.run(token)
