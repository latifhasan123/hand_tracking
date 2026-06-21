"""Kết nối SQL Server và chuyển dữ liệu Góc học tập sang đúng format UI đang dùng."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    import pyodbc
except Exception:  # pyodbc chưa cài thì UI sẽ tự dùng data mẫu
    pyodbc = None


DB_DRIVER = os.getenv("VSL_DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_SERVER = os.getenv("VSL_DB_SERVER", r"localhost\SQLEXPRESS")
DB_NAME = os.getenv("VSL_DB_NAME", "VSLStudyDB")


ICON_BY_COLOR = {
    "blue": "A",
    "green": "👋",
    "orange": "👨‍👩‍👧",
    "purple": "🏫",
    "pink": "💬",
    "cyan": "123",
    "red": "★",
    "yellow": "★",
}

HAND_ICON = {
    "A": "✊", "Ă": "✊", "Â": "✊",
    "B": "🖐", "C": "🤏", "D": "☝", "Đ": "☝",
    "E": "✊", "Ê": "✊", "G": "👉", "H": "✌",
    "I": "🤙", "K": "✌", "L": "👆", "M": "✊",
    "N": "✊", "O": "👌", "Ô": "👌", "Ơ": "👌",
    "P": "👇", "Q": "👇", "R": "🤞", "S": "✊",
    "T": "✊", "U": "✌", "Ư": "✌", "V": "✌",
    "X": "☝", "Y": "🤙",
}


def connect_db():
    if pyodbc is None:
        raise RuntimeError("Chưa cài pyodbc. Chạy: python -m pip install pyodbc")

    conn_str = (
        rf"DRIVER={{{DB_DRIVER}}};"
        rf"SERVER={DB_SERVER};"
        rf"DATABASE={DB_NAME};"
        r"Trusted_Connection=yes;"
    )

    # Driver 18 thường cần dòng này để tránh lỗi certificate.
    if "18" in DB_DRIVER:
        conn_str += r"TrustServerCertificate=yes;"

    return pyodbc.connect(conn_str)


def _safe_color(value: Optional[str], fallback: str = "blue") -> str:
    value = (value or fallback).lower().strip()
    return value if value in {"blue", "green", "orange", "purple", "yellow", "cyan", "pink", "red"} else fallback


def _fetch_steps(cursor, lesson_id: int) -> List[str]:
    cursor.execute(
        """
        SELECT NoiDung
        FROM BuocHuongDan
        WHERE MaBaiHoc = ?
        ORDER BY ThuTu
        """,
        lesson_id,
    )
    return [str(row.NoiDung) for row in cursor.fetchall()]


def get_ui_data() -> Dict[str, Any]:
    """
    Trả dữ liệu đúng với các biến mà study_ui.py đang dùng:
    ALPHABET, TODAY_LESSONS, POPULAR_TOPICS, VOCAB_TOPICS,
    CONVERSATION_TOPICS, LETTER_HINTS, LESSON_DETAILS.
    Nếu SQL lỗi, raise exception để study_ui.py tự fallback về data.py.
    """
    conn = connect_db()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT MaChuDe, TenChuDe, LoaiChuDe, MoTa, Icon, MauSac
            FROM ChuDeHoc
            WHERE TrangThai = 1
            ORDER BY MaChuDe
            """
        )
        topic_rows = cursor.fetchall()

        topics: List[Dict[str, Any]] = []
        for row in topic_rows:
            color = _safe_color(row.MauSac)
            topics.append({
                "id": int(row.MaChuDe),
                "title": str(row.TenChuDe),
                "type": str(row.LoaiChuDe or "vocab").lower(),
                "desc": str(row.MoTa or ""),
                "icon": str(row.Icon or ICON_BY_COLOR.get(color, "★")),
                "color": color,
            })

        cursor.execute(
            """
            SELECT bh.MaBaiHoc, bh.MaChuDe, cd.TenChuDe, cd.LoaiChuDe,
                   bh.TieuDe, bh.NhanHienThi, bh.NoiDungMoTa, bh.MucDo,
                   bh.ThoiGianHoc, bh.DuongDanAnh, bh.DuongDanVideo,
                   bh.ModelLabel, bh.ThuTu
            FROM BaiHoc bh
            JOIN ChuDeHoc cd ON bh.MaChuDe = cd.MaChuDe
            WHERE bh.TrangThai = 1 AND cd.TrangThai = 1
            ORDER BY cd.MaChuDe, bh.ThuTu, bh.MaBaiHoc
            """
        )
        lesson_rows = cursor.fetchall()

        lessons_by_topic: Dict[int, List[Dict[str, Any]]] = {}
        lesson_details: Dict[str, Dict[str, Any]] = {}
        letter_hints: Dict[str, Any] = {}
        alphabet: List[str] = []

        for row in lesson_rows:
            lesson_id = int(row.MaBaiHoc)
            topic_id = int(row.MaChuDe)
            topic_type = str(row.LoaiChuDe or "").lower()
            label = str(row.NhanHienThi or row.TieuDe or "").strip()
            title = str(row.TieuDe or label).strip()
            desc = str(row.NoiDungMoTa or "").strip()
            icon = HAND_ICON.get(label, HAND_ICON.get(title.replace("Chữ ", ""), "☝"))
            steps = _fetch_steps(cursor, lesson_id)
            if not steps:
                steps = [desc or "Thực hiện ký hiệu theo mẫu.", "Giữ tay ổn định trước camera."]

            lesson = {
                "id": lesson_id,
                "topic_id": topic_id,
                "topic_title": str(row.TenChuDe),
                "topic_type": topic_type,
                "title": title,
                "label": label,
                "desc": desc,
                "difficulty": str(row.MucDo or "Dễ"),
                "duration": str(row.ThoiGianHoc or "2 phút"),
                "image": str(row.DuongDanAnh or ""),
                "video": str(row.DuongDanVideo or ""),
                "model_label": str(row.ModelLabel or label),
                "order": int(row.ThuTu or 0),
                "icon": icon,
                "steps": steps,
            }
            lessons_by_topic.setdefault(topic_id, []).append(lesson)

            # Cho phép tìm bài bằng label, title hoặc MaBaiHoc dạng string.
            for key in {label, title, str(lesson_id), title.replace("Chữ ", "")}:
                if key:
                    lesson_details[key] = lesson

            if topic_type == "alphabet" and label:
                alphabet.append(label)
                letter_hints[label] = (icon, desc)

        def count_done(total: int) -> int:
            # Khi chưa có bảng tiến độ thật, lấy số đã học demo khoảng 40–60%.
            if total <= 0:
                return 0
            return max(0, min(total, round(total * 0.5)))

        topic_cards: List[Dict[str, Any]] = []
        for topic in topics:
            topic_lessons = lessons_by_topic.get(topic["id"], [])
            total = len(topic_lessons)
            done = count_done(total)
            first = topic_lessons[0] if topic_lessons else None
            topic_cards.append({
                "id": topic["id"],
                "title": topic["title"],
                "icon": topic["icon"],
                "desc": topic["desc"] or (first["desc"] if first else "Chưa có mô tả"),
                "done": done,
                "total": max(total, 1),
                "count": f"{total} bài học",
                "color": topic["color"],
                "progress": done / max(total, 1),
                "first_label": first["label"] if first else "D",
                "type": topic["type"],
            })

        today_source = []
        # Ưu tiên bài alphabet, nếu ít thì lấy tất cả bài.
        alphabet_lessons = [l for topic_id, ls in lessons_by_topic.items() for l in ls if l["topic_type"] == "alphabet"]
        today_source = alphabet_lessons[:3] or [l for ls in lessons_by_topic.values() for l in ls][:3]
        today_lessons = []
        for idx, lesson in enumerate(today_source, 1):
            label = lesson["label"] or lesson["title"]
            today_lessons.append({
                "no": str(idx),
                "letter": lesson["title"],
                "hand": lesson["icon"],
                "desc": lesson["desc"] or "Bài học ngôn ngữ ký hiệu.",
                "progress": 0.5,
                "label": label,
            })

        vocab_topics = [t for t in topic_cards if t.get("type") == "vocab"]
        conversation_topics = [t for t in topic_cards if t.get("type") == "conversation"]
        popular_topics = [t for t in topic_cards if t.get("type") != "alphabet"][:3]

        return {
            "ALPHABET": alphabet,
            "TODAY_LESSONS": today_lessons,
            "POPULAR_TOPICS": popular_topics,
            "VOCAB_TOPICS": vocab_topics,
            "CONVERSATION_TOPICS": conversation_topics,
            "LETTER_HINTS": letter_hints,
            "LESSON_DETAILS": lesson_details,
            "SQL_STATUS": "Đang dùng dữ liệu SQL Server",
        }
    finally:
        conn.close()
