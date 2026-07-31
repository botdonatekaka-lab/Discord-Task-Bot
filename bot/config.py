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
        "emoji": discord.PartialEmoji(name="dangcapkhac", id=1532806537083490364),
        "role_id": 1512910004548669500,
        "prices": {
            "1": 200000,
            "2": 400000,
            "3": 500000,
        },
    },
    "co_dong_lon": {
        "name": "Cổ Đông Lớn",
        "emoji": discord.PartialEmoji(name="codonglon", id=1532803978595664055),
        "role_id": 1512099086990577675,
        "prices": {
            "1": 100000,
            "2": 200000,
            "3": 250000,
        },
    },
    "co_dong_nho": {
        "name": "Cổ Đông Nhỏ",
        "emoji": discord.PartialEmoji(name="codongnho", id=1532803887675867331),
        "role_id": 1514290379787079881,
        "prices": {
            "1": 25000,
            "2": 50000,
            "3": 65000,
        },
    },
    "cu_dan_dong_gop": {
        "name": "Cư Dân Đóng Góp",
        "emoji": discord.PartialEmoji(name="cudandonggop", id=1532803808285950133),
        "role_id": 1512799562149003275,
        "prices": {
            "1": 10000,
            "2": 20000,
            "3": 25000,
        },
    },
}
