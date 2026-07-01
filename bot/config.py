# ================================================================
# config.py — Cấu hình bot: hằng số, gói donate, thông tin ngân hàng
# ================================================================

# ── Thông tin ngân hàng ──────────────────────────────────────────
BANK_NAME = "MBBank"
BANK_ACCOUNT = "78911112003"
BANK_HOLDER = "NGUYEN VIET HIEU"

# ── Channel IDs ──────────────────────────────────────────────────
ADMIN_CHANNEL_ID   = 1515221397452882000   # Kênh admin nhận đơn donate
THANKS_CHANNEL_ID  = 1514934088870662184   # Kênh gửi lời cảm ơn sau duyệt
PRIVILEGE_CHANNEL_ID = 1513291802193559652 # Kênh giới thiệu đặc quyền

# ── Gói donate ───────────────────────────────────────────────────
# Mỗi gói có: tên hiển thị, emoji, role ID discord, bảng giá theo tháng
PACKAGES = {
    "dang_cap_khac": {
        "name": "Đẳng Cấp Khác",
        "emoji": "💲",
        "role_id": 1512910004548669500,
        "prices": {
            "1": 199000,
            "2": 350000,
            "3": 400000,
        },
    },
    "co_dong_lon": {
        "name": "Cổ Đông Lớn",
        "emoji": "💸",
        "role_id": 1512099086990577675,
        "prices": {
            "1": 99000,
            "2": 200000,
            "3": 300000,
        },
    },
    "co_dong_nho": {
        "name": "Cổ Đông Nhỏ",
        "emoji": "💠",
        "role_id": 1514290379787079881,
        "prices": {
            "1": 25000,
            "2": 45000,
            "3": 60000,
        },
    },
    "cu_dan_dong_gop": {
        "name": "Cư Dân Đóng Góp",
        "emoji": "🏅",
        "role_id": 1512799562149003275,
        "prices": {
            "1": 10000,
            "2": 15000,
            "3": 20000,
        },
    },
}
