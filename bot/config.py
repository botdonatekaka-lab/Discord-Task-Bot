# ================================================================
# config.py — Cấu hình bot: hằng số, gói donate, thông tin ngân hàng
# ================================================================

import discord

# ── Thông tin ngân hàng ──────────────────────────────────────────
BANK_NAME = "MBBank"
BANK_ACCOUNT = "78911112003"
BANK_HOLDER = "NGUYEN VIET HIEU"

# ── Channel IDs ──────────────────────────────────────────────────
ADMIN_CHANNEL_ID   = 1515221397452882000   # Kênh admin nhận đơn donate
THANKS_CHANNEL_ID  = 1514934088870662184   # Kênh gửi lời cảm ơn sau duyệt
PRIVILEGE_CHANNEL_ID = 1513291802193559652 # Kênh giới thiệu đặc quyền

# ── Gói donate ───────────────────────────────────────────────────
# Mỗi gói có: tên hiển thị, emoji (custom server emoji), role ID, bảng giá
PACKAGES = {
    "dang_cap_khac": {
        "name": "Đẳng Cấp Khác",
        "emoji": discord.PartialEmoji(name="emoji_70", id=1522020810687250432),
        "role_id": 1512910004548669500,
        "prices": {
            "1": 199000,
            "2": 350000,
            "3": 400000,
        },
    },
    "co_dong_lon": {
        "name": "Cổ Đông Lớn",
        "emoji": discord.PartialEmoji(name="emoji_69", id=1522020653069242452),
        "role_id": 1512099086990577675,
        "prices": {
            "1": 99000,
            "2": 200000,
            "3": 300000,
        },
    },
    "co_dong_nho": {
        "name": "Cổ Đông Nhỏ",
        "emoji": discord.PartialEmoji(name="emoji_68", id=1522020595263471847),
        "role_id": 1514290379787079881,
        "prices": {
            "1": 25000,
            "2": 45000,
            "3": 60000,
        },
    },
    "cu_dan_dong_gop": {
        "name": "Cư Dân Đóng Góp",
        "emoji": discord.PartialEmoji(name="emoji_67", id=1522020541425520711),
        "role_id": 1512799562149003275,
        "prices": {
            "1": 10000,
            "2": 15000,
            "3": 20000,
        },
    },
}
