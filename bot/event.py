# ================================================================
# event.py — Quản lý tính năng Event: chống trùng số trong chủ đề
# ================================================================

import json
import os
import re

EVENT_FILE = "bot/event_data.json"


# ── Đọc / ghi dữ liệu event ──────────────────────────────────────

def load_events() -> dict:
    """Đọc danh sách event đang hoạt động."""
    if not os.path.exists(EVENT_FILE):
        return {"active_events": {}}
    with open(EVENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(data: dict) -> None:
    """Ghi dữ liệu event xuống file."""
    os.makedirs(os.path.dirname(EVENT_FILE), exist_ok=True)
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Tiện ích ─────────────────────────────────────────────────────

def extract_number(content: str) -> str | None:
    """
    Trích xuất số đầu tiên xuất hiện trong tin nhắn.
    Ví dụ: '  42  ' → '42', 'mình chọn số 7' → '7'
    Trả về None nếu không tìm thấy số.
    """
    content = content.strip()
    # Ưu tiên: nếu toàn bộ tin nhắn chỉ là 1 số (có thể có khoảng trắng)
    if re.fullmatch(r"\s*\d+\s*", content):
        return content.strip()
    # Nếu không, lấy số đầu tiên tìm thấy trong tin nhắn
    match = re.search(r"\b(\d+)\b", content)
    return match.group(1) if match else None


def is_event_active(thread_id: int) -> bool:
    """Kiểm tra xem thread có đang trong chế độ event không."""
    data = load_events()
    return str(thread_id) in data["active_events"]


# ── Xử lý tin nhắn trong event thread ───────────────────────────

async def handle_event_message(message) -> None:
    """
    Được gọi từ on_message.
    Nếu tin nhắn ở trong event thread:
      - Trích xuất số từ nội dung
      - Nếu số đã bị lấy → xoá tin nhắn + thông báo
      - Nếu số chưa bị lấy → ghi nhận
      - Nếu không có số → bỏ qua (không xoá)
    """
    data = load_events()
    thread_id = str(message.channel.id)

    if thread_id not in data["active_events"]:
        return

    event = data["active_events"][thread_id]
    number = extract_number(message.content)

    if number is None:
        return

    numbers = event.setdefault("numbers", {})

    if number in numbers:
        # Số đã được sử dụng — xoá tin nhắn và thông báo
        owner_id = numbers[number]
        try:
            await message.delete()
        except Exception:
            pass

        try:
            await message.author.send(
                f"❌ **Số {number} đã được sử dụng** bởi <@{owner_id}>!\n"
                f"Vui lòng chọn số khác trong <#{message.channel.id}>."
            )
        except Exception:
            # Không DM được → gửi vào kênh rồi tự xoá sau 5 giây
            try:
                notice = await message.channel.send(
                    f"⚠️ {message.author.mention} Số **{number}** đã được sử dụng! "
                    f"Vui lòng chọn số khác.",
                    delete_after=5,
                )
            except Exception:
                pass
    else:
        # Số mới — ghi nhận
        numbers[number] = str(message.author.id)
        save_events(data)
