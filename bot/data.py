# ================================================================
# data.py — Quản lý dữ liệu: đọc/ghi file JSON, tạo mã donate
# ================================================================

import json
import os
import random
import string

DATA_FILE = "bot/donate_data.json"

# ── Cấu trúc dữ liệu mặc định khi chưa có file ──────────────────
DEFAULT_DATA = {
    "donations": [],          # Danh sách tất cả đơn donate
    "panel_message_id": None, # ID tin nhắn panel đang hiển thị
    "panel_channel_id": None, # ID kênh chứa panel
}


def load_data() -> dict:
    """Đọc dữ liệu từ file JSON. Trả về cấu trúc mặc định nếu chưa tồn tại."""
    if not os.path.exists(DATA_FILE):
        return DEFAULT_DATA.copy()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict) -> None:
    """Ghi dữ liệu xuống file JSON."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def gen_code() -> str:
    """Tạo mã donate duy nhất dạng KAIAxxxxxx (6 chữ số ngẫu nhiên)."""
    digits = "".join(random.choices(string.digits, k=6))
    return f"KAIA{digits}"


def fmt_money(amount: int) -> str:
    """Định dạng số tiền: 199000 → 199.000đ"""
    return f"{amount:,}đ".replace(",", ".")


def fmt_months(months: str) -> str:
    """Hiển thị số tháng hoặc 'Tùy chọn' nếu là custom."""
    try:
        return f"{int(months)} tháng"
    except (ValueError, TypeError):
        return "Tùy chọn"


def gen_qr_url(amount: int, code: str) -> str:
    """Tạo URL ảnh QR thanh toán qua SePay."""
    from bot.config import BANK_NAME, BANK_ACCOUNT, BANK_HOLDER
    holder_encoded = BANK_HOLDER.replace(" ", "%20")
    return (
        f"https://qr.sepay.vn/img?bank={BANK_NAME}"
        f"&acc={BANK_ACCOUNT}&amount={amount}"
        f"&des={code}&showinfo=true&fullacc=true&holder={holder_encoded}"
    )
