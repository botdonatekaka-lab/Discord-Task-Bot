# ================================================================
# main.py — Entry point: khởi tạo bot, đăng ký events và commands
# ================================================================

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

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """
    Được gọi khi bot đã kết nối Discord thành công.
    - Đăng ký lại persistent views (panel + các đơn pending)
    - Sync slash commands
    - Khởi động background tasks
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
