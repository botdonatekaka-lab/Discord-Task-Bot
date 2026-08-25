# ================================================================
# creator_data.py — Lưu trữ dữ liệu hệ thống Creator/Nhà quảng bá
# ================================================================

import json
import os
from datetime import datetime

CREATOR_FILE = "bot/creator_data.json"

def load_creators() -> dict:
    """Đọc dữ liệu creator từ file JSON."""
    if not os.path.exists(CREATOR_FILE):
        return {"creators": []}
    with open(CREATOR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_creators(data: dict) -> None:
    """Ghi dữ liệu creator xuống file JSON."""
    os.makedirs(os.path.dirname(CREATOR_FILE), exist_ok=True)
    with open(CREATOR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_creator_by_user(data: dict, user_id: int) -> dict | None:
    """Tìm creator theo user_id."""
    uid = str(user_id)
    return next((c for c in data["creators"] if c["user_id"] == uid), None)


def get_creator_by_code(data: dict, invite_code: str) -> dict | None:
    """Tìm creator theo invite code."""
    return next((c for c in data["creators"] if c["invite_code"] == invite_code), None)


def add_creator(data: dict, user_id: int, username: str,
                invite_code: str, invite_url: str) -> dict:
    """Thêm creator mới vào danh sách."""
    entry = {
        "user_id": str(user_id),
        "username": username,
        "invite_code": invite_code,
        "invite_url": invite_url,
        "join_count": 0,
        "created_at": datetime.now().isoformat(),
    }
    data["creators"].append(entry)
    return entry
