"""
Giao diện Góc học tập cho dự án hand_tracking.

Cách dùng độc lập:
    python user/goc_hoc_tap/main_study.py

Cách nhúng vào user/ui_user.py:
    from goc_hoc_tap.study_ui import open_study_window
    # sau đó gọi: open_study_window(root)
"""

from __future__ import annotations

import math
import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Dict, Optional

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk

try:
    from . import theme as T
    from .data import (
        ALPHABET,
        CONVERSATION_TOPICS,
        LETTER_HINTS,
        POPULAR_TOPICS,
        REVIEW_CARDS,
        TODAY_LESSONS,
        TOP_MODULES,
        VOCAB_TOPICS,
    )
except ImportError:  # chạy trực tiếp file trong thư mục goc_hoc_tap
    import theme as T
    from data import (
        ALPHABET,
        CONVERSATION_TOPICS,
        LETTER_HINTS,
        POPULAR_TOPICS,
        REVIEW_CARDS,
        TODAY_LESSONS,
        TOP_MODULES,
        VOCAB_TOPICS,
    )


COLOR_MAP = {
    "blue": T.BLUE,
    "green": T.GREEN,
    "orange": T.ORANGE,
    "purple": T.PURPLE,
    "yellow": T.YELLOW,
    "cyan": T.CYAN,
    "pink": T.PINK,
    "red": T.RED,
}

# ==========================================
# NẠP DỮ LIỆU THẬT TỪ SQL SERVER
# ==========================================
# Nếu SQL lỗi hoặc chưa có bảng, giao diện vẫn chạy bằng dữ liệu mẫu trong data.py.
LESSON_DETAILS = {}
SQL_STATUS = "Đang dùng dữ liệu mẫu"
try:
    try:
        from .study_db import get_ui_data
    except ImportError:
        from study_db import get_ui_data

    _sql_data = get_ui_data()
    if _sql_data.get("ALPHABET"):
        ALPHABET = _sql_data["ALPHABET"]
    if _sql_data.get("TODAY_LESSONS"):
        TODAY_LESSONS = _sql_data["TODAY_LESSONS"]
    if _sql_data.get("POPULAR_TOPICS"):
        POPULAR_TOPICS = _sql_data["POPULAR_TOPICS"]
    if _sql_data.get("VOCAB_TOPICS"):
        VOCAB_TOPICS = _sql_data["VOCAB_TOPICS"]
    if _sql_data.get("CONVERSATION_TOPICS"):
        CONVERSATION_TOPICS = _sql_data["CONVERSATION_TOPICS"]
    if _sql_data.get("LETTER_HINTS"):
        LETTER_HINTS.update(_sql_data["LETTER_HINTS"])
    if _sql_data.get("LESSON_DETAILS"):
        LESSON_DETAILS = _sql_data["LESSON_DETAILS"]
        
    SQL_STATUS = _sql_data.get("SQL_STATUS", "Đang dùng dữ liệu SQL Server")
except Exception as _db_error:
    print("[Góc học tập] Không nạp được dữ liệu SQL, dùng dữ liệu mẫu:", _db_error)



class ProgressRing(tk.Canvas):
    """Canvas nhỏ để vẽ vòng tiến độ giống dashboard."""

    def __init__(self, master, percent: float, size: int = 126, color: str = T.BLUE, **kwargs):
        super().__init__(master, width=size, height=size, bg=kwargs.pop("bg", T.PANEL_2), highlightthickness=0)
        self.size = size
        self.percent = max(0, min(1, percent))
        self.color = color
        self.draw()       
        
    
    def draw(self):
        pad = 15
        self.create_arc(
            pad,
            pad,
            self.size - pad,
            self.size - pad,
            start=90,
            extent=-359,
            width=13,
            outline="#2A3038",
            style="arc",
        )
        self.create_arc(
            pad,
            pad,
            self.size - pad,
            self.size - pad,
            start=90,
            extent=-359 * self.percent,
            width=13,
            outline=self.color,
            style="arc",
        )
        self.create_text(
            self.size / 2,
            self.size / 2,
            text=f"{int(self.percent * 100)}%",
            fill=T.TEXT,
            font=(T.FONT, 18, "bold"),
        )


class StudyApp(ctk.CTkFrame):
    def __init__(self, master, show_sidebar=True, on_back=None):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.master = master
        self.show_sidebar = show_sidebar
        self.on_back = on_back
        self.active_page = "home"
        self.page_frame: Optional[ctk.CTkFrame] = None
        self.sidebar_buttons: Dict[str, ctk.CTkButton] = {}
        self.content_column = 1 if self.show_sidebar else 0

        # Camera riêng cho màn hình "Luyện tập bằng camera".
        # Không dùng chung với camera của màn hình Dịch tự do để tránh xung đột.
        self.practice_cap = None
        self.practice_camera_on = False
        self.practice_after_id = None
        self.practice_video_label = None
        self.practice_status_label = None

        self.pack(fill="both", expand=True)
        if self.show_sidebar:
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
        else:
            self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if self.show_sidebar:
            self._build_sidebar()
        self.show_home()

    # ---------- BASE UI ----------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=335, fg_color=T.SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        logo = ctk.CTkLabel(
            sidebar,
            text="🌐  VSL TRANSLATE",
            font=ctk.CTkFont(family=T.FONT, size=23, weight="bold"),
            text_color="#28A8FF",
        )
        logo.grid(row=0, column=0, sticky="w", padx=52, pady=(38, 45))

        def side_btn(row, key, text, command, active=False, color=None):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                height=58,
                corner_radius=7,
                anchor="w",
                font=ctk.CTkFont(family=T.FONT, size=17, weight="bold" if active else "normal"),
                fg_color=color or (T.BLUE if active else "transparent"),
                hover_color=T.BLUE_DARK if active else "#222931",
                text_color=T.TEXT,
                command=command,
            )
            btn.grid(row=row, column=0, sticky="ew", padx=20, pady=5)
            self.sidebar_buttons[key] = btn

        side_btn(1, "translate", "🎙   Dịch tự do (1 & 2 Tay)", self.on_back if self.on_back else lambda: messagebox.showinfo("VSL Translate", "Mở lại màn hình dịch tự do trong file ui_user.py."))
        side_btn(2, "study", "📚   Góc học tập", self.show_home, active=True)
        side_btn(3, "game", "🎮   Minigame", lambda: self.show_placeholder("MINIGAME", "Phần minigame có thể phát triển thêm sau."))

        divider = ctk.CTkFrame(sidebar, height=1, fg_color="#4C4C4C")
        divider.grid(row=4, column=0, sticky="ew", padx=25, pady=22)

        side_btn(5, "dict", "📖   Từ điển (Cheat Sheet)", lambda: self.show_placeholder("TỪ ĐIỂN", "Danh sách ký hiệu mẫu và mẹo ghi nhớ."), active=False, color=T.ORANGE)
        def open_auth_popup():
            import sys, os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            import auth_ui
            
            if auth_ui.CURRENT_USER is not None:
                messagebox.showinfo("Tài khoản", f"Bạn đang đăng nhập với tài khoản: {auth_ui.CURRENT_USER['username']}")
                return
                
            def on_login_success():
                self.account_btn.configure(text=f"👤   Chào, {auth_ui.CURRENT_USER['username']}", text_color=T.GREEN)
                if hasattr(self, 'active_page') and self.active_page == "home":
                    self.show_home()
                    
            auth_ui.show_auth_window(self.winfo_toplevel(), on_success=on_login_success)

        self.account_btn = ctk.CTkButton(
            sidebar,
            text="👤   Đăng nhập / Đăng ký",
            height=58,
            corner_radius=7,
            anchor="w",
            font=ctk.CTkFont(family=T.FONT, size=17, weight="bold"),
            fg_color="transparent",
            hover_color="#222931",
            text_color=T.ORANGE,
            command=open_auth_popup
        )
        self.account_btn.grid(row=6, column=0, sticky="ew", padx=20, pady=5)
        sidebar.grid_rowconfigure(6, weight=1)
        off_btn = ctk.CTkButton(
            sidebar,
            text="📷   Tắt Camera",
            height=58,
            corner_radius=7,
            fg_color=T.RED,
            hover_color="#D32F2F",
            text_color=T.TEXT,
            font=ctk.CTkFont(family=T.FONT, size=18, weight="bold"),
            command=lambda: messagebox.showinfo("Camera", "Nút này dùng cho màn hình camera chính."),
        )
        off_btn.grid(row=7, column=0, sticky="ew", padx=20, pady=(15, 38))

    def _clear_page(self):
        # Khi chuyển sang trang khác, tự tắt camera luyện tập để tránh camera chạy ngầm.
        self.stop_practice_camera()

        if self.page_frame is not None:
            self.page_frame.destroy()
        self.page_frame = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self.page_frame.grid(row=0, column=self.content_column, sticky="nsew")
        self.page_frame.grid_columnconfigure(0, weight=1)
        self.page_frame.grid_rowconfigure(0, weight=1)
        return self.page_frame

    def _content(self):
        root = self._clear_page()
        wrapper = ctk.CTkScrollableFrame(root, fg_color=T.BG, corner_radius=0)
        wrapper.grid(row=0, column=0, sticky="nsew", padx=(35, 30), pady=(20, 15))
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(99, weight=1) 
        return wrapper

    def _title(self, parent, title: str, subtitle: str, row: int = 0):
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(family=T.FONT, size=32, weight="bold"), # Giảm từ 43 -> 32
            text_color=T.TEXT,
        ).grid(row=row, column=0, sticky="w")
        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=ctk.CTkFont(family=T.FONT, size=16), # Giảm từ 20 -> 16
            text_color=T.MUTED,
        ).grid(row=row + 1, column=0, sticky="w", pady=(5, 10))
    def show_placeholder(self, title: str, desc: str):
        page = self._content()
        self._title(page, title, desc)
        card = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=18, border_width=1, border_color=T.BORDER)
        card.grid(row=3, column=0, sticky="nsew", pady=20)
        ctk.CTkLabel(card, text="🚧", font=ctk.CTkFont(size=78)).pack(pady=(70, 15))
        ctk.CTkLabel(card, text="Tính năng đang phát triển", font=ctk.CTkFont(family=T.FONT, size=25, weight="bold"), text_color=T.TEXT).pack()
        ctk.CTkButton(card, text="Quay về Góc học tập", height=45, fg_color=T.BLUE, command=self.show_home).pack(pady=30)

    # ---------- DATA HELPERS ----------
    def get_lesson(self, key):
        """Lấy thông tin bài học từ SQL theo label/title/id. Nếu không có thì trả dữ liệu mặc định."""
        text_key = str(key or "").strip()
        lesson = LESSON_DETAILS.get(text_key)
        if lesson:
            return lesson

        # Thử bỏ tiền tố "Chữ " nếu người dùng truyền vào "Chữ A".
        lesson = LESSON_DETAILS.get(text_key.replace("Chữ ", ""))
        if lesson:
            return lesson

        icon, desc = LETTER_HINTS.get(text_key, ("☝", "Giữ tay ổn định trước camera."))
        return {
            "id": text_key,
            "title": f"Chữ {text_key}" if len(text_key) <= 2 else text_key,
            "label": text_key,
            "desc": desc,
            "difficulty": "Dễ",
            "duration": "2 phút",
            "icon": icon,
            "steps": [
                "Thực hiện ký hiệu theo mẫu.",
                "Hướng tay rõ về phía camera.",
                "Giữ tay ổn định trong 2 giây.",
            ],
            "topic_type": "alphabet",
        }

    def lesson_title_text(self, lesson):
        if lesson.get("topic_type") == "alphabet" and not str(lesson.get("title", "")).startswith("Chữ"):
            return f"Chữ {lesson.get('label', '')}"
        return lesson.get("title") or str(lesson.get("label", ""))

    def normalize_lesson_key(self, value):
        """Chuẩn hóa khóa bài học để so sánh: 'Chữ A' -> 'A'."""
        text = str(value or "").strip()
        if text.startswith("Chữ "):
            text = text.replace("Chữ ", "", 1).strip()
        return text.upper()

    def get_current_lesson_key(self, lesson: dict, fallback=None):
        """Lấy khóa bài hiện tại từ dữ liệu SQL/dữ liệu mẫu."""
        for key in ("label", "NhanHienThi", "model_label", "ModelLabel", "title", "TieuDe", "id"):
            value = lesson.get(key)
            if value not in (None, ""):
                return str(value).replace("Chữ ", "", 1).strip()
        return str(fallback or "").replace("Chữ ", "", 1).strip()

    def get_lesson_sequence(self, current_lesson=None):
        """Lấy danh sách thứ tự bài học dựa theo chủ đề đang học."""
        topic_type = current_lesson.get("topic_type", "alphabet") if current_lesson else "alphabet"
        sequence = []

        if topic_type == "conversation":
            # Nếu là câu giao tiếp -> Duyệt trong LESSON_DETAILS và sắp xếp theo số 'order'
            lessons = []
            for key, lesson in LESSON_DETAILS.items():
                if not isinstance(lesson, dict) or lesson.get("topic_type") != "conversation":
                    continue
                value = self.get_current_lesson_key(lesson, key)
                order = lesson.get("order") or lesson.get("ThuTu") or 9999
                try:
                    order = int(order)
                except Exception:
                    order = 9999
                if value:
                    lessons.append((order, value))

            lessons.sort(key=lambda x: x[0])
            for _, value in lessons:
                if self.normalize_lesson_key(value) not in [self.normalize_lesson_key(x) for x in sequence]:
                    sequence.append(value)
        else:
            # Nếu là chữ cái -> Duyệt theo bảng ALPHABET gốc
            for item in ALPHABET:
                if isinstance(item, dict):
                    value = item.get("label") or item.get("NhanHienThi") or item.get("title")
                else:
                    value = item
                value = str(value or "").replace("Chữ ", "", 1).strip()
                if value and self.normalize_lesson_key(value) not in [self.normalize_lesson_key(x) for x in sequence]:
                    sequence.append(value)

        return sequence

    def get_next_lesson_key(self, lesson: dict, fallback=None):
        """Trả về khóa bài kế tiếp cùng chủ đề."""
        sequence = self.get_lesson_sequence(lesson) # Truyền context vào đây
        if not sequence: return None

        current = self.get_current_lesson_key(lesson, fallback)
        current_norm = self.normalize_lesson_key(current)

        for idx, key in enumerate(sequence):
            if self.normalize_lesson_key(key) == current_norm:
                if idx + 1 < len(sequence):
                    return sequence[idx + 1]
                return None
        return sequence[0] if sequence else None

    def get_previous_lesson_key(self, lesson: dict, fallback=None):
        """Trả về khóa bài liền trước cùng chủ đề."""
        sequence = self.get_lesson_sequence(lesson) # Truyền context vào đây
        if not sequence: return None

        current = self.get_current_lesson_key(lesson, fallback)
        current_norm = self.normalize_lesson_key(current)

        for idx, key in enumerate(sequence):
            if self.normalize_lesson_key(key) == current_norm:
                if idx - 1 >= 0:
                    return sequence[idx - 1]
                return None
        return None

    def go_previous_lesson(self, lesson: dict, fallback=None):
        """Đi tới bài liền trước khi nhấn nút 'Bài trước'."""
        previous_key = self.get_previous_lesson_key(lesson, fallback)
        if previous_key:
            self.show_lesson(previous_key)
        else:
            messagebox.showinfo("Góc học tập", "Bạn đang ở bài đầu tiên trong bảng chữ cái.")

    def go_next_lesson(self, lesson: dict, fallback=None):
        """Đi tới bài kế tiếp khi nhấn nút 'Bài tiếp theo'."""
        next_key = self.get_next_lesson_key(lesson, fallback)
        if next_key:
            self.show_lesson(next_key)
        else:
            messagebox.showinfo("Góc học tập", "Bạn đã ở bài cuối cùng trong bảng chữ cái.")


    def _asset_project_root(self):
        """
        Trả về thư mục gốc project C:\\hand_tracking khi file đang nằm ở
        user/goc_hoc_tap/study_ui.py.
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def resolve_asset_path(self, image_path: str):
        """
        Chuyển đường dẫn tương đối lưu trong SQL thành đường dẫn thật trên máy.

        Ví dụ SQL lưu:
            user/assets/signs/alphabet/C.png

        Hàm sẽ đổi thành:
            C:\\hand_tracking\\user\\assets\\signs\\alphabet\\C.png
        """
        if not image_path:
            return None

        image_path = str(image_path).strip()
        if not image_path:
            return None

        if os.path.isabs(image_path):
            return image_path

        return os.path.join(self._asset_project_root(), image_path.replace("/", os.sep))

    def guess_lesson_image_path(self, lesson: dict):
        """
        Nếu SQL chưa có cột DuongDanAnh hoặc study_db.py chưa truyền image,
        tự đoán tên file theo nhãn ký hiệu.
        """
        label = str(
            lesson.get("model_label")
            or lesson.get("ModelLabel")
            or lesson.get("label")
            or lesson.get("NhanHienThi")
            or lesson.get("title")
            or ""
        ).strip()

        title = str(lesson.get("title") or lesson.get("TieuDe") or "").strip()

        # Chuẩn hóa nếu label/title đang có dạng "Chữ C"
        if label.startswith("Chữ "):
            label = label.replace("Chữ ", "", 1).strip()
        if not label and title.startswith("Chữ "):
            label = title.replace("Chữ ", "", 1).strip()

        file_map = {
            # --- ÉP CHỮ CÓ DẤU DÙNG CHUNG ẢNH GỐC Ở NGOÀI THẺ ---
            "A": "A.png", "Ă": "A.png", "Â": "A.png", 
            "B": "B.png", "C": "C.png", "D": "D.png", "Đ": "Dd.png", "DD": "Dd.png",
            "E": "E.png", "Ê": "E.png", "G": "G.png", "H": "H.png", "I": "I.png", "K": "K.png", "L": "L.png",
            "M": "M.png", "N": "N.png", "O": "O.png", "Ô": "O.png", "Ơ": "O.png",
            "P": "P.png", "Q": "Q.png", "R": "R.png",
            "S": "S.png", "T": "T.png", "U": "U.png", "Ư": "U.png", "V": "V.png", "X": "X.png", "Y": "Y.png",
            
            # --- DẤU CÂU ---
            "DAU_MU": "dau_mu.png", 
            "DAU_MOC": "dau_moc.png", 
            "DAU_A": "dau_breve.png", 
            "DAU_HUYEN": "dau_huyen.png",
            "DAU_SAC": "dau_sac.png",
            "DAU_HOI": "dau_hoi.png",
            "DAU_NGA": "dau_nga.png",
            "DAU_NANG": "dau_nang.png",
        }

        key_candidates = [
            label,
            label.upper(),
            title,
            title.upper(),
        ]

        for key in key_candidates:
            if key in file_map:
                return f"user/assets/signs/alphabet/{file_map[key]}"

        return None

    def get_lesson_image_path(self, lesson: dict):
        """
        Lấy đường dẫn ảnh từ dữ liệu SQL/study_db.py.
        Hỗ trợ nhiều tên khóa để tránh lệch tên giữa study_db.py và study_ui.py.
        """
        for key in (
            "image",
            "DuongDanAnh",
            "duong_dan_anh",
            "image_path",
            "path",
            "asset_path",
            "anh",
        ):
            value = lesson.get(key)
            if value:
                return value

        return self.guess_lesson_image_path(lesson)

    def load_lesson_image(self, lesson: dict, size=(330, 280)):
        """
        Load ảnh bàn tay bằng CTkImage. Nếu không có ảnh hoặc sai đường dẫn
        thì trả về None để giao diện tự dùng icon cũ.
        """
        image_path = self.get_lesson_image_path(lesson)
        full_path = self.resolve_asset_path(image_path)

        if not full_path or not os.path.exists(full_path):
            if image_path:
                print("[Góc học tập] Không tìm thấy ảnh:", full_path)
            return None

        try:
            img = Image.open(full_path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            print("[Góc học tập] Không load được ảnh:", full_path, e)
            return None

    def create_lesson_image_label(self, parent, lesson: dict, size=(330, 280), height=330, fallback_font_size=125):
        """
        Tạo label minh họa. Ưu tiên ảnh từ SQL; nếu không có ảnh thì dùng icon cũ.
        """
        lesson_img = self.load_lesson_image(lesson, size=size)
        if lesson_img is not None:
            label = ctk.CTkLabel(
                parent,
                text="",
                image=lesson_img,
                height=height,
                fg_color="#0B1520",
                corner_radius=16
            )
            # Giữ tham chiếu để Tkinter không xóa ảnh khỏi bộ nhớ.
            label.image = lesson_img
            return label

        icon = lesson.get("icon", "☝")
        return ctk.CTkLabel(
            parent,
            text=icon,
            height=height,
            fg_color="#0B1520",
            corner_radius=16,
            font=ctk.CTkFont(size=fallback_font_size),
            text_color=T.TEXT
        )

    # ---------- SMALL COMPONENTS ----------
    def icon_box(self, parent, icon: str, color: str, size=58, font_size=24):
        box = ctk.CTkFrame(parent, width=size, height=size, fg_color=color, corner_radius=12)
        box.grid_propagate(False)
        ctk.CTkLabel(box, text=icon, font=ctk.CTkFont(family=T.FONT, size=font_size, weight="bold"), text_color=T.TEXT).place(relx=0.5, rely=0.5, anchor="center")
        return box

    def top_module_card(self, parent, idx: int, item: dict):
        color = COLOR_MAP[item["color"]]
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=2 if idx == 0 else 1, border_color=T.BLUE if idx == 0 else T.BORDER, corner_radius=16)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0), pady=0)
        
        card.grid_columnconfigure(1, weight=1)
        # BÍ KÍP 1: Ép 2 hàng giãn đều nhau để đẩy cụm text vào giữa
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        
        ib = self.icon_box(card, item["icon"], color if idx else T.BLUE_SOFT, size=60, font_size=25)
        # BÍ KÍP 2: Thêm rowspan=2 để Icon chiếm trọn chiều cao của cả tiêu đề lẫn mô tả
        ib.grid(row=0, column=0, rowspan=2, padx=17, pady=17)
        
        # Đẩy tiêu đề xuống sát mô tả (sticky="sw")
        ctk.CTkLabel(card, text=item["title"], font=ctk.CTkFont(family=T.FONT, size=17, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(0, 2))
        # Đẩy mô tả lên sát tiêu đề (sticky="nw")
        ctk.CTkLabel(card, text=item["desc"], justify="left", font=ctk.CTkFont(family=T.FONT, size=13), text_color=T.MUTED).grid(row=1, column=1, sticky="nw", pady=(2, 0))
        
        card.bind("<Button-1>", lambda _e, t=item["title"]: self._go_module(t))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _e, t=item["title"]: self._go_module(t))
        return card

    def _go_module(self, title: str):
        if "Bảng" in title:
            self.show_alphabet()
        elif "Từ" in title or "Câu" in title or "Giao" in title:
            self.show_conversation()  # Gộp chung gọi 1 hàm
        elif "Ôn" in title:
            self.show_review()

    def section_header(self, parent, row: int, title: str, icon: str = "★", show_all: bool = True, command=None):
        h = ctk.CTkFrame(parent, fg_color="transparent")
        # THÊM LỀ BÊN TRONG (padx, pady) ĐỂ KHÔNG BỊ TRÀN VIỀN CHE MẤT BO GÓC
        h.grid(row=row, column=0, sticky="ew", padx=22, pady=(20, 15))
        h.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(h, text=icon, font=ctk.CTkFont(size=22), text_color=T.BLUE).grid(row=0, column=0, padx=(0, 12))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(family=T.FONT, size=21, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="w")
        
        if show_all:
            # BIẾN LABEL THÀNH CTkButton ĐỂ CLICK ĐƯỢC
            btn = ctk.CTkButton(
                h, 
                text="Xem tất cả  ›", 
                font=ctk.CTkFont(family=T.FONT, size=14), 
                text_color="#37A8FF", 
                fg_color="transparent", 
                hover_color=T.CARD_HOVER, 
                width=0, 
                height=30,
                command=command # Gắn lệnh vào đây
            )
            btn.grid(row=0, column=2, sticky="e")
        return h

    def back_button(self, parent, command=None, text="←  Trở về"):
        """Nút trở về dùng chung cho các trang con trong Góc học tập."""
        return ctk.CTkButton(
            parent,
            text=text,
            height=40,
            width=135,
            corner_radius=14,
            fg_color=T.PANEL,
            hover_color=T.CARD_HOVER,
            border_width=1,
            border_color=T.BORDER,
            text_color=T.TEXT,
            font=ctk.CTkFont(family=T.FONT, size=14, weight="bold"),
            command=command if command is not None else self.show_home,
        )

    def lesson_card(self, parent, idx: int, item: dict):
        card = ctk.CTkFrame(parent, width=230, height=220, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0))
        card.grid_propagate(False)

        # Hàng 1: Số đếm (Neo trên cùng)
        ctk.CTkLabel(card, text=item["no"], width=30, height=30, fg_color=T.BLUE, corner_radius=7, text_color=T.TEXT, font=ctk.CTkFont(weight="bold")).pack(anchor="nw", padx=14, pady=(12, 0))

        # Hàng 2: Nội dung (Xếp ngang hàng, không đè nhau)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=(8, 0))

        hand = ctk.CTkLabel(content, text=item["hand"], width=60, height=60, fg_color="#1A222B", corner_radius=20, font=ctk.CTkFont(size=30))
        hand.pack(side="left", anchor="nw")

        text_box = ctk.CTkFrame(content, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # Logic cắt chữ thông minh (Không cắt ngang từ)
        title_text = item["letter"]
        if len(title_text) > 16: title_text = title_text[:13] + "..."
        
        desc_text = item["desc"]
        if len(desc_text) > 42:
            cut = desc_text.rfind(' ', 0, 39) # Tìm khoảng trắng gần nhất
            if cut == -1: cut = 39
            desc_text = desc_text[:cut] + "..."

        ctk.CTkLabel(text_box, text=title_text, font=ctk.CTkFont(family=T.FONT, size=16, weight="bold"), text_color=T.TEXT, anchor="w", justify="left").pack(fill="x")
        ctk.CTkLabel(text_box, text=desc_text, font=ctk.CTkFont(family=T.FONT, size=12), text_color=T.MUTED, anchor="w", justify="left", wraplength=115).pack(fill="x", pady=(2, 0))

        # Hàng 3: Nút bấm và kẻ ngang (Neo bám chặt xuống đáy)
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=(0, 14), padx=14)

        line = ctk.CTkFrame(bottom, height=1, fg_color=T.LINE)
        line.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(bottom, text="Học ngay  ❯", height=38, fg_color=T.BLUE, hover_color=T.BLUE_DARK, command=lambda: self.show_lesson(item.get("label", item["letter"].replace("Chữ ", "")))).pack(fill="x")
    def topic_card(self, parent, idx: int, item: dict):
        color = COLOR_MAP[item["color"]]
        card = ctk.CTkFrame(parent, width=230, height=180, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0))
        card.grid_propagate(False) 

        # Hàng 1: Icon và Text xếp cạnh nhau
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=(18, 0))

        icon_box = self.icon_box(content, item["icon"], color, size=55, font_size=22)
        icon_box.pack(side="left", anchor="nw")

        text_box = ctk.CTkFrame(content, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # Logic cắt chữ
        title_text = item["title"]
        if len(title_text) > 18: title_text = title_text[:15] + "..."
        
        desc_text = item["desc"]
        if len(desc_text) > 42:
            cut = desc_text.rfind(' ', 0, 39)
            if cut == -1: cut = 39
            desc_text = desc_text[:cut] + "..."

        ctk.CTkLabel(text_box, text=title_text, font=ctk.CTkFont(family=T.FONT, size=16, weight="bold"), text_color=T.TEXT, anchor="w", justify="left").pack(fill="x")
        ctk.CTkLabel(text_box, text=desc_text, font=ctk.CTkFont(family=T.FONT, size=12), text_color=T.MUTED, anchor="w", justify="left", wraplength=120).pack(fill="x", pady=(4, 0))

        # Hàng 2: Thanh tiến độ (Bám chặt xuống đáy)
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=(0, 14), padx=14)

        pb = ctk.CTkProgressBar(bottom, height=5, progress_color=color, fg_color="#29313B")
        pb.pack(fill="x", pady=(0, 10))
        pb.set(item.get("progress", 0.5))

        stat_row = ctk.CTkFrame(bottom, fg_color="transparent")
        stat_row.pack(fill="x")
        ctk.CTkLabel(stat_row, text=item["count"], font=ctk.CTkFont(family=T.FONT, size=13, weight="bold"), text_color=color).pack(side="left")
        ctk.CTkLabel(stat_row, text="›", font=ctk.CTkFont(size=28), text_color=T.MUTED).pack(side="right")
    # ---------- PAGES ----------
    def show_home(self):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)

        top = ctk.CTkFrame(page, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        self._title(top, "GÓC HỌC TẬP", "Học ngôn ngữ ký hiệu từng bước")
        ctk.CTkLabel(top, text="☝  ☝", font=ctk.CTkFont(size=58), text_color=T.BLUE).grid(row=0, column=1, rowspan=2, padx=40)

        modules = ctk.CTkFrame(page, fg_color="transparent")
        modules.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 25))
        for i in range(5):
            modules.grid_columnconfigure(i, weight=1 if i < 4 else 0)
        for i, item in enumerate(TOP_MODULES):
            self.top_module_card(modules, i, item)

        main = ctk.CTkFrame(page, fg_color="transparent")
        main.grid(row=3, column=0, sticky="nsew", padx=(0, 20))
        main.grid_columnconfigure(0, weight=1)

        today_box = ctk.CTkFrame(main, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        today_box.grid(row=0, column=0, sticky="ew", pady=(0, 17))
        today_box.grid_columnconfigure(0, weight=1)
        self.section_header(today_box, 0, "Bài học hôm nay", "▣", command=self.show_alphabet)
        lessons_grid = ctk.CTkFrame(today_box, fg_color="transparent")
        lessons_grid.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        for i in range(3):
            lessons_grid.grid_columnconfigure(i, weight=1)
        for i, item in enumerate(TODAY_LESSONS):
            self.lesson_card(lessons_grid, i, item)

        topic_box = ctk.CTkFrame(main, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        topic_box.grid(row=1, column=0, sticky="ew")
        topic_box.grid_columnconfigure(0, weight=1)
        self.section_header(topic_box, 0, "Chủ đề phổ biến", "★", command=self.show_conversation)
        topics_grid = ctk.CTkFrame(topic_box, fg_color="transparent")
        topics_grid.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        for i in range(3):
            topics_grid.grid_columnconfigure(i, weight=1)
        for i, item in enumerate(POPULAR_TOPICS):
            self.topic_card(topics_grid, i, item)

        right = ctk.CTkFrame(page, fg_color="transparent", width=295)
        right.grid(row=3, column=1, sticky="nsew")
        right.grid_propagate(False)
        self.progress_panel(right)

    def progress_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(card, text="↗  Tiến độ học tập", font=ctk.CTkFont(family=T.FONT, size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=22, pady=(22, 12))
        
        # ==========================================
        # ĐỒNG BỘ DỮ LIỆU THẬT TỪ TÀI KHOẢN
        # ==========================================
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
            # Lấy số lượng bài đã đánh dấu "✓ Đã học"
            user_data = auth_ui.CURRENT_USER or {}
            learned_count = len(auth_ui.LEARNED_LETTERS) if auth_ui.CURRENT_USER else 0
            
            # Lấy dữ liệu thật cho các thống kê, mặc định là 0
            chuoi_ngay = user_data.get("ChuoiNgayHoc", 0)
            do_chinh_xac = user_data.get("DoChinhXacTB", 0)
            thoi_gian_phut = user_data.get("ThoiGianHoc", 0)
        except Exception:
            user_data = {}
            learned_count = 0
            chuoi_ngay = 0
            do_chinh_xac = 0
            thoi_gian_phut = 0
            
        # Tính tổng số chữ cái có trong dữ liệu (mặc định là 29)
        total_letters = len(ALPHABET) if ALPHABET else 29
        # Tính phần trăm để vẽ vòng tròn
        percent = learned_count / total_letters if total_letters > 0 else 0
        
        # Xử lý hiển thị thời gian học (phút -> giờ phút)
        gio = thoi_gian_phut // 60
        phut = thoi_gian_phut % 60
        thoi_gian_str = f"{gio}h {phut}m" if gio > 0 else f"{phut}m"
        # ==========================================

        center = ctk.CTkFrame(card, fg_color="transparent")
        center.pack(fill="x", padx=20)
        
        # GIỮ NGUYÊN VÒNG TRÒN TIẾN ĐỘ NHƯ CŨ, KHÔNG ĐỤNG ĐẾN
        ring = ProgressRing(center, percent, size=120, color=T.BLUE, bg=T.PANEL)
        ring.pack(side="left", padx=(0, 14), pady=5)
        
        info = ctk.CTkFrame(center, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text="Đã học:", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(anchor="w", pady=(16, 0))
        
        # Cập nhật phân số bài học thật
        ctk.CTkLabel(info, text=f"{learned_count}/{total_letters}", font=ctk.CTkFont(size=26, weight="bold"), text_color=T.GREEN).pack(anchor="w")
        
        ctk.CTkLabel(info, text="Bảng chữ cái", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w")
        ctk.CTkFrame(card, height=1, fg_color=T.LINE).pack(fill="x", padx=20, pady=15)
        
        # NẠP DỮ LIỆU THẬT VÀO 3 DÒNG THỐNG KÊ BÊN DƯỚI, GIỮ NGUYÊN HOÀN TOÀN MÀU SẮC GIAO DIỆN CỦA BẠN
        self.stat_row(card, "📅", "Chuỗi ngày học", f"{chuoi_ngay} ngày", T.GREEN, "Cố gắng duy trì mỗi ngày!" if chuoi_ngay > 0 else "Hãy bắt đầu bài học!")
        self.stat_row(card, "🎯", "Độ chính xác TB", f"{do_chinh_xac}%", T.GREEN, "Làm rất tốt! 💪" if do_chinh_xac > 0 else "Chưa có dữ liệu")
        self.stat_row(card, "🕘", "Thời gian học", thoi_gian_str, T.BLUE, "Tổng thời gian học tập")

    def motivation_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.pack(fill="x")
        ctk.CTkLabel(card, text="☆", font=ctk.CTkFont(size=46), text_color=T.BLUE).grid(row=0, column=0, rowspan=2, padx=18, pady=18)
        ctk.CTkLabel(card, text="Bạn đang làm rất tốt!", font=ctk.CTkFont(size=17, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(18, 0))
        ctk.CTkLabel(card, text="Hãy tiếp tục luyện tập để\nnâng cao kỹ năng nhé! 🎉", justify="left", font=ctk.CTkFont(size=13), text_color=T.MUTED).grid(row=1, column=1, sticky="nw", pady=(5, 20))

    def stat_row(self, parent, icon, label, value, color, sub):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 14))
        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=25), text_color=color).pack(side="left", padx=(0, 14))
        texts = ctk.CTkFrame(row, fg_color="transparent")
        texts.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(texts, text=label, font=ctk.CTkFont(size=14, weight="bold"), text_color=T.TEXT).pack(anchor="w")
        ctk.CTkLabel(texts, text=sub, font=ctk.CTkFont(size=12), text_color=T.MUTED).pack(anchor="w")
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(side="right")

    def show_alphabet(self):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        self._title(page, "BẢNG CHỮ CÁI KÝ HIỆU", "Chọn một chữ cái để bắt đầu học")
        self.back_button(page, command=self.show_home, text="←  Trang chính").grid(
            row=0, column=1, rowspan=2, sticky="ne", padx=(15, 0), pady=(5, 0)
        )

        main = ctk.CTkFrame(page, fg_color="transparent")
        main.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0)

        left = ctk.CTkFrame(main, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left.grid_columnconfigure(0, weight=1)

        # ==========================================
        # 1. TẠO THANH TABS CHUYỂN ĐỔI
        # ==========================================
        tabs_frame = ctk.CTkFrame(left, fg_color=T.PANEL, corner_radius=10, border_width=1, border_color=T.BORDER)
        tabs_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        tabs_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.current_alpha_tab = "Chữ cái" # Lưu trạng thái tab hiện tại
        
        def switch_tab(tab_name):
            self.current_alpha_tab = tab_name
            # Hiệu ứng đổi màu khi bấm
            btn_alpha.configure(fg_color=T.BLUE if tab_name == "Chữ cái" else "transparent", text_color=T.TEXT if tab_name == "Chữ cái" else T.MUTED)
            btn_marks.configure(fg_color=T.BLUE if tab_name == "Dấu câu" else "transparent", text_color=T.TEXT if tab_name == "Dấu câu" else T.MUTED)
            filter_alphabet() # Cập nhật lại lưới ngay lập tức
            
        btn_alpha = ctk.CTkButton(tabs_frame, text="Chữ cái", height=40, corner_radius=8, font=ctk.CTkFont(size=14, weight="bold"), fg_color=T.BLUE, command=lambda: switch_tab("Chữ cái"))
        btn_alpha.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        
        btn_marks = ctk.CTkButton(tabs_frame, text="Dấu câu", height=40, corner_radius=8, font=ctk.CTkFont(size=14, weight="bold"), fg_color="transparent", text_color=T.MUTED, hover_color=T.CARD_HOVER, command=lambda: switch_tab("Dấu câu"))
        btn_marks.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        # Thanh tìm kiếm
        search = ctk.CTkEntry(left, placeholder_text="🔍  Tìm kiếm...", height=42, fg_color=T.PANEL, border_color=T.BORDER, text_color=T.TEXT)
        search.grid(row=1, column=0, sticky="ew", pady=(0, 18))

        grid = ctk.CTkFrame(left, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="nsew")
        for c in range(6):
            grid.grid_columnconfigure(c, weight=1)

        # KHUNG CHỨA BẢNG CHI TIẾT BÊN PHẢI
        right_container = ctk.CTkFrame(main, fg_color="transparent")
        right_container.grid(row=0, column=1, sticky="ns", padx=(0, 0))

        current_letter = None
        current_detail_panel = None
        tile_cards = {} 

        def update_right_panel(letter):
            nonlocal current_detail_panel
            if current_detail_panel is not None:
                current_detail_panel.destroy()
                
            if letter is None:
                current_detail_panel = ctk.CTkFrame(right_container, width=310, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
                current_detail_panel.pack_propagate(False) 
                ctk.CTkLabel(current_detail_panel, text="👈", font=ctk.CTkFont(size=70), text_color=T.BLUE).pack(pady=(180, 20))
                ctk.CTkLabel(current_detail_panel, text="Hãy chọn một mục\nđể bắt đầu bài học", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.MUTED, justify="center").pack()
            else:
                current_detail_panel = self.letter_detail(right_container, letter)
                
            current_detail_panel.pack(fill="both", expand=True)

        def on_tile_click(letter):
            nonlocal current_letter
            current_letter = letter
            update_right_panel(letter) 
            
            for l, card in tile_cards.items():
                if l == current_letter:
                    card.configure(border_width=2, border_color=T.BLUE) 
                else:
                    card.configure(border_width=1, border_color=T.BORDER) 

        def filter_alphabet(event=None):
            query = search.get().strip().upper()
            for widget in grid.winfo_children():
                widget.destroy()
            tile_cards.clear() 
            
            # ==========================================
            # 2. XỬ LÝ DỮ LIỆU TỰ ĐỘNG CHIA TAB
            # ==========================================
            # Hệ thống tự mớm sẵn dấu câu nếu SQL của bạn chưa có
            # Dùng ID hệ thống thay vì chữ tiếng Việt
            default_marks = [
                "DAU_A", "DAU_MU", "DAU_MOC", 
                "DAU_SAC", "DAU_HUYEN", "DAU_HOI", "DAU_NGA", "DAU_NANG"
            ]
            # Chuẩn 29 chữ cái Tiếng Việt
            default_alpha = ["A", "Ă", "Â", "B", "C", "D", "Đ", "E", "Ê", "G", "H", "I", "K", "L", "M", "N", "O", "Ô", "Ơ", "P", "Q", "R", "S", "T", "U", "Ư", "V", "X", "Y"]
            
            alpha_list = []
            marks_list = default_marks 
            
            if ALPHABET:
                for item in ALPHABET:
                    val = str(item).upper()
                    # Lấy MỌI chữ cái đơn lẻ (Bao gồm cả Ă, Â, Ê...)
                    if len(val) == 1:
                        alpha_list.append(item)
                        
            # Nếu SQL lỗi không nạp được ALPHABET, dùng danh sách mặc định
            if not alpha_list:
                alpha_list = default_alpha
                
            current_data = alpha_list if self.current_alpha_tab == "Chữ cái" else marks_list
                
            filtered = [char for char in current_data if query in str(char).upper()]
            if not filtered:
                ctk.CTkLabel(grid, text="Không tìm thấy kết quả nào.", text_color=T.MUTED, font=ctk.CTkFont(size=15)).grid(row=0, column=0, columnspan=6, pady=20)
                
            for idx, letter in enumerate(filtered):
                # Tab Chữ cái 6 cột, Tab Dấu câu chỉ 4 cột (Vì thẻ dấu câu bự hơn)
                cols_per_row = 6 if self.current_alpha_tab == "Chữ cái" else 4
                r, c = divmod(idx, cols_per_row)
                
                is_selected = (letter == current_letter)
                card = self.letter_tile(grid, r, c, letter, selected=is_selected, on_click=on_tile_click)
                tile_cards[letter] = card 

        search.bind("<KeyRelease>", filter_alphabet)
        
        # Khởi chạy giao diện lần đầu
        filter_alphabet()
        update_right_panel(current_letter)
    def letter_tile(self, parent, row, col, letter, selected=False, on_click=None):
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        import auth_ui
        
        learned = letter in auth_ui.LEARNED_LETTERS
        lesson = self.get_lesson(letter)
        
        is_mark = len(str(letter)) > 2
        card_width = 165 if is_mark else 120
        font_size = 15 if is_mark else 20
        
        card = ctk.CTkFrame(parent, width=card_width, height=145, fg_color=T.CARD, border_width=2 if selected else 1, border_color=T.BLUE if selected else T.BORDER, corner_radius=12)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)
        
        # BÍ KÍP: Tạo từ điển hiển thị để giao diện trông đẹp mắt
        display_names = {
            "DAU_A": "Dấu Á (Ă)", "DAU_MU": "Dấu Mũ (Â,Ê,Ô)", "DAU_MOC": "Dấu Móc (Ư,Ơ)",
            "DAU_SAC": "Dấu Sắc", "DAU_HUYEN": "Dấu Huyền", "DAU_HOI": "Dấu Hỏi", 
            "DAU_NGA": "Dấu Ngã", "DAU_NANG": "Dấu Nặng"
        }
        display_text = display_names.get(letter, str(letter).title() if is_mark else letter)
        
        ctk.CTkLabel(card, text=display_text, font=ctk.CTkFont(size=font_size, weight="bold"), text_color=T.TEXT).pack(anchor="center", pady=(10, 0))
        
        img_label = self.create_lesson_image_label(card, lesson, size=(65, 65), height=70, fallback_font_size=40)
        img_label.configure(fg_color="transparent", corner_radius=0)
        img_label.pack(pady=(2, 2))
        
        status = "✓ Đã học" if learned else "● Chưa học"
        color = T.GREEN if learned else T.MUTED_2
        ctk.CTkLabel(card, text=status, font=ctk.CTkFont(size=11), text_color=color).pack(pady=(0, 5))
        
        def click_handler(_e, l=letter):
            if on_click: on_click(l)
            
        card.bind("<Button-1>", click_handler)
        for child in card.winfo_children():
            child.bind("<Button-1>", click_handler)
            
        return card  

    def letter_detail(self, parent, letter):
        lesson = self.get_lesson(letter)
        icon = lesson.get("icon", "☝")
        desc = lesson.get("desc", "Dựng ngón trỏ thẳng đứng.")
        steps = lesson.get("steps") or ["Thực hiện ký hiệu theo mẫu.", "Giữ tay ổn định trước camera."]
        card = ctk.CTkFrame(parent, width=310, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=self.lesson_title_text(lesson), font=ctk.CTkFont(size=27, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=20, pady=(22, 8))
        
        # ==========================================
        # BÍ KÍP TÁCH 2 ẢNH CHO CÁC CHỮ CÓ DẤU
        # ==========================================
        composite_map = {
            "Ă": "DAU_A", "Â": "DAU_MU", "Ê": "DAU_MU",
            "Ô": "DAU_MU", "Ơ": "DAU_MOC", "Ư": "DAU_MOC"
        }
        
        val = str(letter).upper().replace("CHỮ ", "").strip()
        
        if val in composite_map:
            # Nếu là chữ có dấu -> Tạo khung ngang chứa 2 ảnh
            img_frame = ctk.CTkFrame(card, fg_color="transparent")
            img_frame.pack(fill="x", padx=20, pady=5)
            img_frame.grid_columnconfigure((0, 1), weight=1)
            
            # 1. Ảnh chữ cái gốc
            base_img = self.create_lesson_image_label(img_frame, lesson, size=(100, 100), height=140, fallback_font_size=60)
            base_img.configure(fg_color="#0E1722", corner_radius=14)
            base_img.grid(row=0, column=0, padx=(0, 5), sticky="ew")
            ctk.CTkLabel(img_frame, text="Ký hiệu gốc", font=ctk.CTkFont(size=12, weight="bold"), text_color=T.MUTED).grid(row=1, column=0, pady=(5,0))
            
            # 2. Ảnh dấu đi kèm
            mark_lesson = {"label": composite_map[val]} # Đánh lừa hệ thống để lấy ảnh dấu
            mark_img = self.create_lesson_image_label(img_frame, mark_lesson, size=(100, 100), height=140, fallback_font_size=60)
            mark_img.configure(fg_color="#0E1722", corner_radius=14)
            mark_img.grid(row=0, column=1, padx=(5, 0), sticky="ew")
            ctk.CTkLabel(img_frame, text="Thêm dấu", font=ctk.CTkFont(size=12, weight="bold"), text_color=T.MUTED).grid(row=1, column=1, pady=(5,0))
        else:
            # Chữ bình thường thì hiện 1 ảnh to như cũ
            detail_image = self.create_lesson_image_label(
                card, lesson, size=(235, 165), height=180, fallback_font_size=82
            )
            detail_image.configure(fg_color="#0E1722", corner_radius=14)
            detail_image.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(card, text="Cách thực hiện", font=ctk.CTkFont(size=17, weight="bold"), text_color=T.BLUE).pack(anchor="w", padx=20, pady=(15, 4))
        for i, step_text in enumerate(steps, 1):
            ctk.CTkLabel(
                card,
                text=f"{i}. {step_text}",
                font=ctk.CTkFont(size=13),
                text_color=T.MUTED,
                justify="left",
                anchor="w",
                wraplength=250
            ).pack(anchor="w", fill="x", padx=22, pady=2)
        ctk.CTkLabel(card, text="💡 Mẹo nhỏ", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.YELLOW).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(card, text=desc, wraplength=250, justify="left", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w", padx=20)
        # Nút chuyển sang màn hình chi tiết bài học (Ảnh thứ 2)
        ctk.CTkButton(card, text="📖  Xem chi tiết bài học", height=44, fg_color=T.BLUE, hover_color=T.BLUE_DARK, command=lambda: self.show_lesson(lesson.get("label", letter))).pack(fill="x", padx=20, pady=(20, 10))
        
        # Nút phụ
        ctk.CTkButton(card, text="📷  Luyện bằng camera", height=40, fg_color="transparent", border_width=1, border_color=T.BORDER, text_color=T.TEXT, hover_color=T.CARD_HOVER, command=lambda: self.show_camera_practice(lesson.get("label", letter))).pack(fill="x", padx=20, pady=(0, 20))
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        import auth_ui, user_db
        
        def mark_done():
            if auth_ui.CURRENT_USER is None:
                messagebox.showinfo("Tài khoản", "Vui lòng đăng nhập để lưu tiến độ học tập!")
                auth_ui.show_auth_window(self.winfo_toplevel(), on_success=mark_done)
                return
                
            if user_db.mark_as_learned(auth_ui.CURRENT_USER["id"], letter):
                auth_ui.LEARNED_LETTERS.append(letter)
                btn_done.configure(text="✓ Đã lưu tiến độ", text_color=T.GREEN, state="disabled")
            else:
                messagebox.showerror("Lỗi DB", "Không thể lưu tiến độ!")

        btn_done = ctk.CTkButton(card, text="✓  Đánh dấu đã học", height=40, fg_color="transparent", border_width=1, border_color=T.BORDER, hover_color=T.CARD_HOVER, command=mark_done)
        btn_done.pack(fill="x", padx=20, pady=(0, 20))
        
        if letter in auth_ui.LEARNED_LETTERS:
            btn_done.configure(text="✓ Đã lưu tiến độ", text_color=T.GREEN, state="disabled")

        return card

    def show_lesson(self, letter="D"):
        lesson = self.get_lesson(letter)
        lesson_title = self.lesson_title_text(lesson)
        topic_type = lesson.get("topic_type", "alphabet")

        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        
        # BÍ KÍP 3: Tiêu đề tự động thay đổi
        title_prefix = "BÀI HỌC: " if topic_type == "alphabet" else "GIAO TIẾP: "
        self._title(page, f"{title_prefix}{lesson_title.upper()}", "Học cách thực hiện ký hiệu đúng")
        
        # BÍ KÍP 4: Nút Back tự nhận diện nơi để về
        back_cmd = self.show_alphabet if topic_type == "alphabet" else self.show_conversation
        back_text = "←  Bảng chữ cái" if topic_type == "alphabet" else "←  Từ vựng & Giao tiếp"
        
        self.back_button(page, command=back_cmd, text=back_text).grid(
            row=0, column=1, rowspan=2, sticky="ne", padx=(15, 0), pady=(5, 0)
        )

        main = ctk.CTkFrame(page, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=18)
        main.grid(row=2, column=0, sticky="nsew", padx=(0, 18))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        icon = lesson.get("icon", "☝")
        desc = lesson.get("desc", "Giữ tay ổn định trước camera.")
        steps = lesson.get("steps") or ["Thực hiện ký hiệu theo mẫu.", "Giữ tay ổn định trước camera."]
        ctk.CTkLabel(main, text="⚙  Minh họa ký hiệu", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.TEXT).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 10))
        demo = self.create_lesson_image_label(
            main,
            lesson,
            size=(430, 310),
            height=330,
            fallback_font_size=125
        )
        demo.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

        guide = ctk.CTkFrame(main, fg_color="transparent")
        guide.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 30), pady=28)
        guide.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            guide,
            text="ⓘ  Hướng dẫn",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=T.TEXT
        ).pack(anchor="w", pady=(0, 15))

        # Các bước hướng dẫn: không khóa chiều cao, cho phép tự xuống dòng.
        # Nếu nội dung dài, text sẽ wrap theo đúng chiều rộng của khung, không bị cắt chữ.
        for i, s in enumerate(steps, 1):
            row = ctk.CTkFrame(
                guide,
                fg_color=T.CARD,
                corner_radius=12,
                border_width=1,
                border_color=T.BORDER
            )
            row.pack(fill="x", expand=True, pady=6)
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row,
                text=str(i),
                width=34,
                height=34,
                fg_color=T.BLUE_SOFT,
                corner_radius=20,
                text_color=T.TEXT,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=0, padx=(14, 12), pady=12, sticky="nw")

            step_label = ctk.CTkLabel(
                row,
                text=s,
                font=ctk.CTkFont(size=16),
                text_color=T.TEXT,
                justify="left",
                anchor="w",
                wraplength=300
            )
            step_label.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=12)

            def _update_step_wrap(event, label=step_label):
                # Trừ phần số thứ tự + padding. Tối thiểu 120px để màn hình nhỏ vẫn không tràn.
                label.configure(wraplength=max(120, event.width - 86))

            row.bind("<Configure>", _update_step_wrap)
        note = ctk.CTkFrame(guide, fg_color=T.CARD, corner_radius=12, border_width=1, border_color=T.BORDER)
        note.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(note, text="⚠  Lưu ý", font=ctk.CTkFont(size=17, weight="bold"), text_color=T.ORANGE).pack(anchor="w", padx=18, pady=(16, 6))
        ctk.CTkLabel(note, text="Giữ tay ổn định, hướng thẳng vào camera\nđể hệ thống nhận diện chính xác hơn.", justify="left", text_color=T.MUTED).pack(anchor="w", padx=18, pady=(0, 16))

        buttons = ctk.CTkFrame(page, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", pady=(18, 0), padx=(0, 18))
        buttons.grid_columnconfigure((0, 1, 2), weight=1)

        current_key = self.get_current_lesson_key(lesson, letter)
        previous_key = self.get_previous_lesson_key(lesson, letter)
        next_key = self.get_next_lesson_key(lesson, letter)

        ctk.CTkButton(
            buttons,
            text="▶  Bắt đầu luyện tập",
            height=55,
            fg_color=T.BLUE,
            command=lambda key=current_key: self.show_camera_practice(key)
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))

        ctk.CTkButton(
            buttons,
            text="←  Bài trước" if previous_key else "✓  Đầu bài",
            height=55,
            fg_color=T.PANEL,
            hover_color=T.CARD_HOVER,
            border_width=1 if previous_key else 0,
            border_color=T.BLUE if previous_key else T.BORDER,
            text_color=T.BLUE if previous_key else T.MUTED,
            command=lambda: self.go_previous_lesson(lesson, letter)
        ).grid(row=0, column=1, sticky="ew", padx=6)

        ctk.CTkButton(
            buttons,
            text="→  Bài tiếp theo" if next_key else "✓  Đã hết bài",
            height=55,
            fg_color="transparent",
            border_width=1,
            border_color=T.BLUE if next_key else T.BORDER,
            text_color=T.BLUE if next_key else T.MUTED,
            hover_color=T.CARD_HOVER,
            command=lambda: self.go_next_lesson(lesson, letter)
        ).grid(row=0, column=2, sticky="ew", padx=(12, 0))

        info = ctk.CTkFrame(page, width=305, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        info.grid(row=2, column=1, sticky="nsew")
        info.grid_propagate(False)
        ctk.CTkLabel(info, text="📘  Thông tin bài học", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.BLUE).pack(anchor="w", padx=20, pady=(22, 15))
        self.info_item(info, "📊", "Mức độ", lesson.get("difficulty", "Dễ"), T.GREEN)
        self.info_item(info, "🕘", "Thời gian", lesson.get("duration", "2 phút"), T.BLUE)
        self.info_item(info, "🏆", "Tiến độ khóa học", "3 / 29", T.PURPLE)
        ctk.CTkProgressBar(info, height=7, progress_color=T.PURPLE, fg_color="#2B3139").pack(fill="x", padx=20, pady=(10, 5))
        ctk.CTkLabel(info, text="10% hoàn thành", text_color=T.MUTED).pack(anchor="w", padx=20)

    def info_item(self, parent, icon, label, value, color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(row, text=icon, width=45, height=45, fg_color="#101B26", corner_radius=22, font=ctk.CTkFont(size=22), text_color=color).pack(side="left", padx=(0, 12))
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=label, text_color=T.MUTED, font=ctk.CTkFont(size=13)).pack(anchor="w")
        ctk.CTkLabel(txt, text=value, text_color=color, font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")

    def stop_practice_camera(self):
        """Tắt camera luyện tập và hủy vòng lặp cập nhật khung hình."""
        if self.practice_after_id is not None:
            try:
                self.after_cancel(self.practice_after_id)
            except Exception:
                pass
            self.practice_after_id = None

        if self.practice_cap is not None:
            try:
                self.practice_cap.release()
            except Exception:
                pass
            self.practice_cap = None

        self.practice_camera_on = False

        if self.practice_status_label is not None:
            try:
                self.practice_status_label.configure(text="● Camera đã tắt", text_color=T.MUTED)
            except Exception:
                pass

        if self.practice_video_label is not None:
            try:
                self.practice_video_label.configure(
                    image=None,
                    text="📷\n\nNhấn Bắt đầu để mở camera luyện tập"
                )
                self.practice_video_label.image = None
            except Exception:
                pass

    def show_camera_practice(self, letter="D"):
        page = self._clear_page()
        
        # BÍ KÍP 1: Lấy trước dữ liệu bài học để lôi ảnh ra
        lesson = self.get_lesson(letter)
        
        wrapper = ctk.CTkFrame(page, fg_color=T.BG)
        wrapper.pack(fill="both", expand=True, padx=30, pady=30)
        
        # --- HEADER ---
        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        self._title(title_box, "LUYỆN TẬP BẰNG CAMERA", f"Thực hành nhận diện ký hiệu: {letter}")
        
        def safe_stop():
            self.practice_camera_on = False
            if self.practice_after_id:
                try: self.after_cancel(self.practice_after_id)
                except: pass
                self.practice_after_id = None
            if self.practice_cap:
                try: self.practice_cap.release()
                except: pass
                self.practice_cap = None

        def go_back():
            safe_stop()
            self.show_lesson(letter)

        self.back_button(header, command=go_back, text="←  Về bài học").pack(side="right", anchor="n", pady=5)

        # --- BODY ---
        body = ctk.CTkFrame(wrapper, fg_color="transparent")
        body.pack(fill="both", expand=True)
        
        # CỘT PHẢI
        right_frame = ctk.CTkFrame(body, fg_color="transparent", width=430)
        right_frame.pack(side="right", fill="y", padx=(25, 0))
        right_frame.pack_propagate(False) 
        
        target_panel = ctk.CTkFrame(right_frame, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        target_panel.pack(fill="x", pady=(0, 15))
        target_panel.grid_columnconfigure((0, 1), weight=1)

        # BÍ KÍP 2: THAY CHỮ BẰNG ẢNH TRONG KHUNG "KÝ HIỆU CẦN LÀM"
        box_req = ctk.CTkFrame(target_panel, fg_color="transparent")
        box_req.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)
        ctk.CTkLabel(box_req, text="Ký hiệu cần làm", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(pady=(0, 8))
        
        img_label = self.create_lesson_image_label(box_req, lesson, size=(90, 90), height=90, fallback_font_size=60)
        img_label.configure(fg_color="transparent")
        img_label.pack()

        ctk.CTkFrame(target_panel, width=1, fg_color=T.BORDER).grid(row=0, column=0, sticky="e", pady=20)

        box_actual = ctk.CTkFrame(target_panel, fg_color="transparent")
        box_actual.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)
        ctk.CTkLabel(box_actual, text="Bạn đang làm", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(pady=(0, 20))
        current_sign_label = ctk.CTkLabel(box_actual, text="--", font=ctk.CTkFont(size=50, weight="bold"), text_color=T.TEXT)
        current_sign_label.pack()

        stats_panel = ctk.CTkFrame(right_frame, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        stats_panel.pack(fill="x", pady=(0, 15))
        
        stat_row_1 = ctk.CTkFrame(stats_panel, fg_color="transparent")
        stat_row_1.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(stat_row_1, text="🎯 Độ chính xác:", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.TEXT).pack(side="left")
        accuracy_value_label = ctk.CTkLabel(stat_row_1, text="0%", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.BLUE)
        accuracy_value_label.pack(side="right")
        
        acc_progress = ctk.CTkProgressBar(stats_panel, height=8, progress_color=T.BLUE, fg_color="#2A2F35")
        acc_progress.pack(fill="x", padx=20, pady=(0, 15))
        acc_progress.set(0)

        stat_row_2 = ctk.CTkFrame(stats_panel, fg_color="transparent")
        stat_row_2.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(stat_row_2, text="✓ Trạng thái:", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.TEXT).pack(side="left")
        status_value_label = ctk.CTkLabel(stat_row_2, text="Đã tắt", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.MUTED)
        status_value_label.pack(side="right")

        feedback_label = ctk.CTkLabel(stats_panel, text="☆ Nhấn 'Bật Camera' để luyện tập.", fg_color="#2A2F35", corner_radius=8, height=45, text_color=T.MUTED, font=ctk.CTkFont(size=13), wraplength=350)
        feedback_label.pack(fill="x", padx=20, pady=(0, 20))

        def toggle_camera():
            if self.practice_camera_on: stop_from_button()
            else: start_practice_camera()

        toggle_btn = ctk.CTkButton(right_frame, text="▶ Bật Camera", height=55, fg_color=T.BLUE, hover_color=T.BLUE_DARK, font=ctk.CTkFont(size=18, weight="bold"), corner_radius=14, command=toggle_camera)
        toggle_btn.pack(fill="x")

        # CỘT TRÁI (CAMERA)
        left_frame = ctk.CTkFrame(body, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        left_frame.pack(side="left", fill="both", expand=True)
        left_frame.grid_propagate(False) 
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        cam_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        cam_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        self.practice_status_label = ctk.CTkLabel(cam_bar, text="● Camera đang tắt", fg_color="#2A2F35", corner_radius=8, text_color=T.MUTED, font=ctk.CTkFont(size=13, weight="bold"), padx=12, pady=6)
        self.practice_status_label.pack(side="left")
        
        camera_view = ctk.CTkFrame(left_frame, fg_color="#080C11", corner_radius=12)
        camera_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        camera_view.grid_propagate(False)
        camera_view.grid_rowconfigure(0, weight=1)
        camera_view.grid_columnconfigure(0, weight=1)

        self.practice_video_label = ctk.CTkLabel(camera_view, text="📷\n\nNhấn 'Bật Camera' để bắt đầu", font=ctk.CTkFont(size=20), text_color=T.MUTED_2)
        self.practice_video_label.grid(row=0, column=0, sticky="nsew")

        # ==========================================
        # LOGIC AI CỐT LÕI
        # ==========================================
        self.sequence_data = []
        self.prev_wx = None
        self.prev_wy = None
        self.mp_hands = None
        self.mp_draw = None
        self.ai_session = None
        self.ai_labels = None
        
        # BÍ KÍP SENIOR: Thêm các biến giám sát thực hành
        self.success_frames = 0
        self.lesson_completed = False
        self.practice_start_time = None

        def load_ai_dependencies():
            if self.mp_hands is None:
                import mediapipe as mp
                self.mp_hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
                self.mp_draw = mp.solutions.drawing_utils
            if self.ai_session is None:
                try:
                    import onnxruntime as ort
                    import numpy as np
                    import os
                    if os.path.exists("model/model.onnx") and os.path.exists("model/labels.npy"):
                        self.ai_session = ort.InferenceSession("model/model.onnx", providers=['CPUExecutionProvider'])
                        self.ai_labels = np.load("model/labels.npy")
                except Exception as e:
                    print("Lỗi load AI model:", e)

        def hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy):
            import numpy as np
            wx, wy = landmarks[0].x, landmarks[0].y
            vector = []
            for i in range(1, 21):
                x = landmarks[i].x - wx
                y = landmarks[i].y - wy
                vector.extend([x, y])
            if prev_wx is None or prev_wy is None:
                delta_x = 0.0; delta_y = 0.0
            else:
                delta_x = wx - prev_wx; delta_y = wy - prev_wy
            if abs(delta_x) < 0.008: delta_x = 0.0
            if abs(delta_y) < 0.008: delta_y = 0.0
            delta_x *= 30; delta_y *= 30    
            vector.extend([hand_type, delta_x, delta_y])
            return np.array(vector), wx, wy

        def record_success(final_accuracy):
            import sys, os, time
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            try:
                import auth_ui, user_db
                
                if auth_ui.CURRENT_USER is None:
                    status_value_label.configure(text="Hoàn thành!", text_color=T.GREEN)
                    feedback_label.configure(text="☆ Tuyệt vời! Hãy đăng nhập để hệ thống lưu lại thành tích này nhé!", fg_color="#17351F", text_color=T.GREEN)
                    return
                
                user_id = auth_ui.CURRENT_USER["id"]
                
                # 1. Đánh dấu chữ cái đã học
                if letter not in auth_ui.LEARNED_LETTERS:
                    user_db.mark_as_learned(user_id, letter)
                    auth_ui.LEARNED_LETTERS.append(letter)
                
                # 2. Tính thời gian học (Tính bằng Phút, ít nhất 1 phút)
                session_time = max(1, int((time.time() - self.practice_start_time) / 60))
                
                # 3. Ghi vào CSDL
                updated_stats = user_db.update_study_stats(user_id, int(final_accuracy * 100), session_time)
                if updated_stats:
                    auth_ui.CURRENT_USER.update(updated_stats) # Ép RAM cập nhật để trang Dashboard nhận ngay lập tức
                    
                status_value_label.configure(text="Đã lưu!", text_color=T.GREEN)
                feedback_label.configure(text="☆ Xuất sắc! Tiến độ, chuỗi ngày và thời gian học đã được cập nhật.", fg_color="#17351F", text_color=T.GREEN)
            except Exception as e:
                print("Lỗi lưu DB:", e)

        def update_practice_frame():
            if not self.practice_camera_on or self.practice_cap is None: return

            try:
                success, frame = self.practice_cap.read()
                if success:
                    import cv2
                    import numpy as np
                    import mediapipe as mp
                    import customtkinter as ctk
                    from PIL import Image

                    frame = cv2.flip(frame, 1)
                    h, w = frame.shape[:2]
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    predicted_char = ""
                    target_confidence = 0.0 
                    hand_detected = False
                    
                    if self.mp_hands is not None:
                        results = self.mp_hands.process(frame_rgb)
                        if results.multi_hand_landmarks:
                            hand_detected = True
                            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                                self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                                label_hand = handedness.classification[0].label
                                hand_type = 0 if label_hand == "Left" else 1
                                vector, self.prev_wx, self.prev_wy = hand_vectorlize(hand_landmarks.landmark, hand_type, self.prev_wx, self.prev_wy)
                                self.sequence_data.append(vector)
                                
                                if len(self.sequence_data) > 30:
                                    self.sequence_data.pop(0)
                                    
                                if len(self.sequence_data) == 30 and self.ai_session is not None:
                                    try:
                                        input_data = np.expand_dims(self.sequence_data, axis=0).astype(np.float32)
                                        input_name = self.ai_session.get_inputs()[0].name
                                        out = self.ai_session.run(None, {input_name: input_data})[0][0]
                                        max_prob, max_index = np.max(out), np.argmax(out)
                                        if max_prob > 0.5:
                                            predicted_char = str(self.ai_labels[max_index]).upper()
                                        for idx, lbl in enumerate(self.ai_labels):
                                            if str(lbl).upper() == letter.upper():
                                                target_confidence = float(out[idx])
                                                break
                                    except: pass
                        else:
                            self.sequence_data.clear()
                            self.prev_wx, self.prev_wy = None, None

                    # THUẬT TOÁN ĐÁNH GIÁ THỰC HÀNH
                    if target_confidence > 0.8:
                        ui_color = T.GREEN
                        bgr_color = (0, 200, 0)
                        
                        if not self.lesson_completed:
                            self.success_frames += 1
                            if self.success_frames > 15: # Giữ tay đúng khoảng 1 giây
                                self.lesson_completed = True
                                record_success(target_confidence)
                    elif target_confidence > 0.4:
                        ui_color = T.YELLOW
                        bgr_color = (0, 215, 255)
                        self.success_frames = 0 # Sai tay là bắt đếm lại từ đầu
                    else:
                        ui_color = T.ORANGE
                        bgr_color = (0, 140, 255)
                        self.success_frames = 0
                        
                    if not hand_detected:
                        ui_color = T.BLUE
                        bgr_color = (255, 144, 30)

                    if hand_detected:
                        cv2.putText(frame, f"Do chinh xac: {int(target_confidence*100)}%", (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.8, bgr_color, 2)

                    if predicted_char:
                        current_sign_label.configure(text=predicted_char, text_color=ui_color if predicted_char == letter else T.ORANGE)
                    else:
                        current_sign_label.configure(text="--", text_color=T.TEXT)
                        
                    if hand_detected:
                        acc_progress.configure(progress_color=ui_color)
                        acc_progress.set(target_confidence)
                        accuracy_value_label.configure(text=f"{int(target_confidence * 100)}%", text_color=ui_color)
                        
                        # Chỉ thay đổi chữ hướng dẫn nếu bài học CHƯA HOÀN THÀNH
                        if not self.lesson_completed:
                            if target_confidence > 0.8:
                                status_value_label.configure(text="Tuyệt vời!", text_color=ui_color)
                                feedback_label.configure(text="☆ Chính xác! Giữ nguyên tay để hệ thống ghi nhớ.", fg_color="#17351F", text_color=ui_color)
                            elif target_confidence > 0.4:
                                status_value_label.configure(text="Gần đúng", text_color=ui_color)
                                feedback_label.configure(text="☆ Bạn đang đi đúng hướng, thử điều chỉnh ngón tay một chút.", fg_color="#332200", text_color=ui_color)
                            else:
                                status_value_label.configure(text="Chưa khớp", text_color=ui_color)
                                feedback_label.configure(text="☆ Vui lòng điều chỉnh lại dáng tay cho giống ảnh mẫu.", fg_color="#332200", text_color=ui_color)
                    else:
                        accuracy_value_label.configure(text="0%", text_color=T.BLUE)
                        acc_progress.configure(progress_color=T.BLUE)
                        acc_progress.set(0)
                        if not self.lesson_completed:
                            status_value_label.configure(text="Đang tìm tay...", text_color=T.BLUE)
                            feedback_label.configure(text="☆ Hãy đưa tay vào camera để bắt đầu.", fg_color="#102034", text_color=T.BLUE)

                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    label_w = camera_view.winfo_width()
                    label_h = camera_view.winfo_height()
                    if label_w < 10: label_w = 480
                    if label_h < 10: label_h = 320
                    
                    scale = min(label_w / w, label_h / h)
                    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                    
                    frame_resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

                    img = Image.fromarray(frame_resized)
                    imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                    
                    self.practice_video_label.configure(image=imgtk, text="")
                    self.practice_video_label.image = imgtk
            except Exception as e:
                print("Lỗi khung hình camera:", e)

            if self.practice_camera_on:
                self.practice_after_id = self.after(10, update_practice_frame)

        def start_practice_camera():
            import cv2
            import os
            import time
            if self.practice_cap is not None:
                self.practice_cap.release()
            
            load_ai_dependencies()
            
            # Reset thông số đo lường mỗi lần bật lại cam
            self.success_frames = 0
            self.lesson_completed = False
            self.practice_start_time = time.time()
            
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
            if not cap.isOpened():
                from tkinter import messagebox
                messagebox.showerror("Lỗi", "Không mở được camera.")
                cap.release()
                return
            self.practice_cap = cap
            self.practice_camera_on = True
            
            self.practice_status_label.configure(text="● Camera đang bật", text_color=T.GREEN, fg_color="#17351F")
            toggle_btn.configure(text="■ Tắt Camera", fg_color=T.RED, hover_color="#D32F2F")
            update_practice_frame()

        def stop_from_button():
            safe_stop()
            self.sequence_data.clear()
            self.prev_wx, self.prev_wy = None, None
            
            toggle_btn.configure(text="▶ Bật Camera", fg_color=T.BLUE, hover_color=T.BLUE_DARK)
            self.practice_status_label.configure(text="● Camera đang tắt", text_color=T.MUTED, fg_color="#2A2F35")
            status_value_label.configure(text="Đã tắt", text_color=T.MUTED)
            accuracy_value_label.configure(text="0%", text_color=T.BLUE)
            acc_progress.set(0)
            current_sign_label.configure(text="--", text_color=T.TEXT)
            feedback_label.configure(text="☆ Camera đã tắt. Nhấn 'Bật Camera' để luyện tập.", fg_color="#2A2F35", text_color=T.MUTED)
            
            from PIL import Image
            blank_img = Image.new('RGB', (10, 10), (8, 12, 17))
            blank_ctk = ctk.CTkImage(light_image=blank_img, dark_image=blank_img, size=(10, 10))
            
            self.practice_video_label.configure(image=blank_ctk, text="📷\n\nNhấn 'Bật Camera' để bắt đầu")
            self.practice_video_label.image = blank_ctk
    def remove_duplicate_topics(self, items):
        """
        Lọc chủ đề bị lặp theo tiêu đề trước khi hiển thị.
        Ví dụ SQL trả về Chào hỏi/Gia đình/Trường học nhiều lần
        thì giao diện chỉ giữ lại mỗi chủ đề một card.
        """
        result = []
        seen = set()

        for item in items or []:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or item.get("TenChuDe") or "").strip()
            if not title:
                continue

            key = title.casefold()
            if key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result

    def show_vocab(self):
        # Hàm này giữ lại để lỡ có nút nào gọi thì chuyển hướng luôn sang trang tổng hợp
        self.show_conversation()

    def show_conversation(self):
        all_topics = (VOCAB_TOPICS or []) + (CONVERSATION_TOPICS or [])
        important_titles = ["Chào hỏi", "Gia đình", "Trường học", "Hỏi đường", "Cảm xúc", "Mua sắm"]
        
        # 1. BẢN ĐỒ DỮ LIỆU: Phân loại bài học vào từng chủ đề
        topic_mapping = {
            "Chào hỏi": ["XIN CHÀO", "CẢM ƠN", "XIN LỖI", "TẠM BIỆT", "TÔI", "TÊN"],
            "Gia đình": ["BỐ", "MẸ"],
            "Trường học": ["GIÁO VIÊN", "HỌC SINH"],
            "Hỏi đường": ["Ở ĐÂU", "ĐI THẲNG"],
            "Cảm xúc": ["VUI", "BUỒN"],
            "Mua sắm": ["TIỀN", "BAO NHIÊU"]
        }

        # 2. Lấy dữ liệu thật từ tài khoản đăng nhập
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
            learned = auth_ui.LEARNED_LETTERS or []
        except Exception:
            learned = []

        combined_topics = []
        for t in all_topics:
            title = t.get("title")
            if title in important_titles:
                # 3. TỰ ĐỘNG TÍNH TIẾN ĐỘ THẬT
                if title in topic_mapping:
                    lessons = topic_mapping[title]
                    t["total"] = len(lessons) # Tổng số bài của chủ đề này
                    t["done"] = len([l for l in lessons if l in learned]) # Số bài user đã học
                    t["first_label"] = lessons[0] if lessons else "D"
                combined_topics.append(t)
                
        # Sắp xếp lại cho đúng thứ tự ưu tiên
        combined_topics.sort(key=lambda x: important_titles.index(x["title"]) if x["title"] in important_titles else 999)

        # Đổi tên Tiêu đề trang thành "TỪ VỰNG & GIAO TIẾP"
        self.topic_page(
            "TỪ VỰNG & GIAO TIẾP", 
            "Học từ vựng và các mẫu câu giao tiếp hằng ngày", 
            combined_topics, 
            right_title="Chủ đề hôm nay", 
            cta="Bắt đầu học", 
            conversation=True
        )

    def topic_page(self, title, subtitle, items, right_title, cta, conversation=False):
        items = self.remove_duplicate_topics(items)

        items = items or [{
            "title": "Chưa có dữ liệu",
            "icon": "?",
            "desc": "Hãy thêm dữ liệu trong SQL Server.",
            "done": 0,
            "total": 1,
            "color": "blue",
            "first_label": "D"
        }]

        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)

        self._title(page, title, subtitle)

        header_right = ctk.CTkFrame(page, fg_color="transparent")
        header_right.grid(row=0, column=1, rowspan=2, sticky="ne", padx=(20, 70), pady=(0, 10))

        self.back_button(
            header_right,
            command=self.show_home,
            text="←  Trang chính"
        ).pack(anchor="e", pady=(0, 8))

        ctk.CTkLabel(
            header_right,
            text="☝  💬",
            font=ctk.CTkFont(size=46),
            text_color=T.BLUE
        ).pack(anchor="e")

        # --- LƯỚI BÀI HỌC BÊN TRÁI ---
        grid = ctk.CTkFrame(page, fg_color="transparent")
        # BÍ KÍP 1: Dùng sticky="new" (North-East-West) để ép khối này bám sát lên mép trên
        grid.grid(row=2, column=0, sticky="new", padx=(0, 25), pady=(20, 0)) 
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)
        for idx, it in enumerate(items):
            r, c = divmod(idx, 3)
            self.big_topic_card(grid, r, c, it)

        # --- THẺ CHỦ ĐỀ HÔM NAY BÊN PHẢI ---
        side = ctk.CTkFrame(page, width=330, fg_color="transparent")
        # BÍ KÍP 2: Bỏ rowspan=2 và dùng sticky="new" để nó nằm ngang hàng tuyệt đối với lưới bên trái
        side.grid(row=2, column=1, sticky="new", pady=(20, 0)) 
        side.grid_propagate(False)
        
        highlight = ctk.CTkFrame(side, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BLUE)
        highlight.pack(fill="x")
        ctk.CTkLabel(highlight, text=f"★  {right_title}", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(20, 14))
        first = items[0]
        color = COLOR_MAP[first["color"]]
        top = ctk.CTkFrame(highlight, fg_color=T.CARD, corner_radius=13, border_width=1, border_color=T.BORDER)
        top.pack(fill="x", padx=18)
        self.icon_box(top, first["icon"], color, size=62, font_size=22).grid(row=0, column=0, padx=16, pady=16, rowspan=2)
        ctk.CTkLabel(top, text=first["title"], font=ctk.CTkFont(size=19, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(18, 0))
        ctk.CTkLabel(top, text="Phổ biến", fg_color="#17351F", corner_radius=6, text_color=T.GREEN, font=ctk.CTkFont(size=12)).grid(row=1, column=1, sticky="nw", pady=(5, 15))
        
        if conversation:
            phrases = ["1  Xin chào", "2  Cảm ơn", "3  Tôi", "4  Tên"]
            for phrase in phrases:
                ctk.CTkLabel(highlight, text=phrase, height=38, fg_color=T.CARD, corner_radius=10, anchor="w", font=ctk.CTkFont(size=14), text_color=T.TEXT).pack(fill="x", padx=18, pady=3)
        else:
            ctk.CTkLabel(highlight, text="Bắt đầu ngày mới với những từ\nthông dụng nhất!", justify="left", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=18, pady=(15, 5))
            pb = ctk.CTkProgressBar(highlight, height=7, progress_color=color, fg_color="#2E333A")
            pb.pack(fill="x", padx=18, pady=(8, 10))
            pb.set(first.get("done", 0) / first.get("total", 1))
            
        ctk.CTkButton(highlight, text=f"▶  {cta}", height=50, fg_color=T.BLUE, command=lambda key=first.get("first_label", "D") if isinstance(first, dict) else "D": self.show_lesson(key)).pack(fill="x", padx=18, pady=(12, 18))

        # --- BÍ KÍP 3: THANH TỔNG QUAN HỌC TẬP (CĂN TRÁI & ÉP NHỎ) ---
        stats_bar = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        # Bóp nhỏ pady=(15, 0) để khung sát lên trên, không gây tràn màn hình (chống cuộn)
        stats_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 25), pady=(15, 0))
        
        # 1. HÀNG 1: Tiêu đề nằm góc trên cùng bên trái
        header_stats = ctk.CTkFrame(stats_bar, fg_color="transparent")
        header_stats.pack(fill="x", padx=20, pady=(12, 6))
        ctk.CTkLabel(header_stats, text="↗", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.BLUE).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header_stats, text="Tổng quan học tập", font=ctk.CTkFont(size=16, weight="bold"), text_color=T.TEXT).pack(side="left")

        # Nét kẻ ngang mỏng phân cách tiêu đề và số liệu
        ctk.CTkFrame(stats_bar, height=1, fg_color="#2A3038").pack(fill="x", padx=20, pady=(0, 10))

        # 2. HÀNG 2: Vùng chứa 3 KPI nằm ngang bên dưới
        kpi_container = ctk.CTkFrame(stats_bar, fg_color="transparent")
        kpi_container.pack(fill="x", expand=True, padx=20, pady=(0, 15))
        kpi_container.grid_columnconfigure((0, 1, 2), weight=1)

        # Lấy dữ liệu thời gian học thật
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
            user_data = auth_ui.CURRENT_USER or {}
            thoi_gian_phut = user_data.get("ThoiGianHoc", 0)
        except Exception:
            thoi_gian_phut = 0
            
        gio = thoi_gian_phut // 60
        phut = thoi_gian_phut % 60
        thoi_gian_str = f"{gio}h {phut}m" if gio > 0 else f"{phut}m"

        total_topics = len(items) if items and items[0].get("title") != "Chưa có dữ liệu" else 0
        # Chủ đề được tính là "Hoàn thành" nếu số bài đã học (done) >= tổng số bài (total)
        completed_topics = sum(1 for it in items if it.get("done", 0) >= it.get("total", 1) and it.get("total", 1) > 0)
        
        # Cộng dồn toàn bộ bài học của trang này
        total_lessons = sum(it.get("total", 1) for it in items) if total_topics > 0 else 0
        done_lessons = sum(it.get("done", 0) for it in items) if total_topics > 0 else 0

        kpis = [
            ("📗", "Chủ đề hoàn thành", f"{completed_topics} / {total_topics}", T.GREEN),
            ("✅", "Mẫu câu hoàn thành" if conversation else "Bài học hoàn thành", f"{done_lessons} / {total_lessons}", T.PURPLE),
            ("🕘", "Thời gian học", thoi_gian_str, T.BLUE)
        ]

        # Đổ dữ liệu thành 3 cột ngang hàng
        for i, (icon, label, value, color) in enumerate(kpis):
            cell = ctk.CTkFrame(kpi_container, fg_color="transparent")
            # Căn giữa các cụm KPI trong cột của nó
            cell.grid(row=0, column=i, sticky="ns") 
            
            ctk.CTkLabel(cell, text=icon, font=ctk.CTkFont(size=26), text_color=color).pack(side="left", padx=(0, 12))
            box = ctk.CTkFrame(cell, fg_color="transparent")
            box.pack(side="left")
            ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(box, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w")
    def big_topic_card(self, parent, row, col, item):
        color = COLOR_MAP[item["color"]]
        
        # Khung ngoài (Khóa cứng chiều cao 180px giống hệt trang chủ)
        card = ctk.CTkFrame(parent, height=180, fg_color=T.CARD, border_width=1, border_color=color if col == 0 and row == 0 else T.BORDER, corner_radius=14)
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 16, 0), pady=(0 if row == 0 else 16, 16))
        card.grid_propagate(False) 

        # Hàng 1: Icon và Text xếp cạnh nhau
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=(18, 0))

        # Icon box thu nhỏ lại size=55 giống trang chủ
        icon_box = self.icon_box(content, item["icon"], color, size=55, font_size=22)
        icon_box.pack(side="left", anchor="nw")

        text_box = ctk.CTkFrame(content, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # Logic cắt chữ thông minh để không bị tràn khung
        title_text = item["title"]
        if len(title_text) > 18: title_text = title_text[:15] + "..."
        
        desc_text = item.get("desc", "")
        if len(desc_text) > 42:
            cut = desc_text.rfind(' ', 0, 39)
            if cut == -1: cut = 39
            desc_text = desc_text[:cut] + "..."

        ctk.CTkLabel(text_box, text=title_text, font=ctk.CTkFont(family=T.FONT, size=16, weight="bold"), text_color=T.TEXT, anchor="w", justify="left").pack(fill="x")
        ctk.CTkLabel(text_box, text=desc_text, font=ctk.CTkFont(family=T.FONT, size=12), text_color=T.MUTED, anchor="w", justify="left", wraplength=120).pack(fill="x", pady=(4, 0))

        # Hàng 2: Thanh tiến độ và Thống kê (Bám chặt xuống đáy)
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=(0, 14), padx=14)

        pb = ctk.CTkProgressBar(bottom, height=5, progress_color=color, fg_color="#29313B")
        pb.pack(fill="x", pady=(0, 10))
        
        done = item.get("done", 0)
        total = item.get("total", 1)
        pb.set(done / total if total > 0 else 0)

        stat_row = ctk.CTkFrame(bottom, fg_color="transparent")
        stat_row.pack(fill="x")
        
        loai_bai = 'câu' if 'Tự' in title_text or title_text in ['Chào hỏi','Hỏi đường','Mua sắm'] else 'bài'
        count_text = f"{done} / {total} {loai_bai}"
        
        ctk.CTkLabel(stat_row, text=count_text, font=ctk.CTkFont(family=T.FONT, size=13, weight="bold"), text_color=color).pack(side="left")
        
        # Bỏ nút bấm vướng víu, thay bằng mũi tên gọn gàng
        ctk.CTkLabel(stat_row, text="›", font=ctk.CTkFont(size=28), text_color=T.MUTED).pack(side="right")
        
        # Bắt sự kiện click cho toàn bộ bề mặt Card
        def on_click(e):
            self.show_lesson(item.get("first_label", "D"))
            
        card.bind("<Button-1>", on_click)
        for child in [content, icon_box, text_box, bottom, stat_row]:
            child.bind("<Button-1>", on_click)
            for subchild in child.winfo_children():
                subchild.bind("<Button-1>", on_click)

    def side_kpi(self, parent, icon, label, value, color):
        row = ctk.CTkFrame(parent, fg_color=T.CARD, corner_radius=10)
        row.pack(fill="x", padx=16, pady=5)
        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=22), text_color=color).pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(side="left")
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=15, weight="bold"), text_color=color).pack(side="right", padx=12)

    def show_review(self):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        self._title(page, "ÔN TẬP", "Luyện tập và củng cố kiến thức đã học")

        header_right = ctk.CTkFrame(page, fg_color="transparent")
        header_right.grid(row=0, column=1, rowspan=2, sticky="ne", padx=(20, 60), pady=(0, 10))

        self.back_button(
            header_right,
            command=self.show_home,
            text="←  Trang chính"
        ).pack(anchor="e", pady=(0, 8))

        ctk.CTkLabel(
            header_right,
            text="☝  ☝",
            font=ctk.CTkFont(size=46),
            text_color=T.BLUE
        ).pack(anchor="e")

        modes = ctk.CTkFrame(page, fg_color="transparent")
        modes.grid(row=2, column=0, sticky="ew", padx=(0, 25), pady=(0, 20))
        modes.grid_columnconfigure((0, 1, 2), weight=1)
        mode_items = [
            ("Flashcard", "Ôn tập từ vựng và\nký hiệu qua thẻ nhớ", "▣", T.BLUE),
            ("Trắc nghiệm", "Kiểm tra kiến thức với\ncâu hỏi trắc nghiệm", "☑", T.PURPLE),
            ("Luyện ký hiệu", "Luyện nhận diện và\nthực hành ký hiệu", "☝", T.GREEN),
        ]
        for i, (name, desc, icon, color) in enumerate(mode_items):
            card = ctk.CTkFrame(modes, fg_color=T.PANEL, corner_radius=16, border_width=2 if i == 0 else 1, border_color=T.BLUE if i == 0 else T.BORDER)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 16, 0))
            card.grid_columnconfigure(1, weight=1)
            self.icon_box(card, icon, color, size=64, font_size=25).grid(row=0, column=0, padx=20, pady=20)
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=19, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(22, 0))
            ctk.CTkLabel(card, text=desc, justify="left", font=ctk.CTkFont(size=14), text_color=T.MUTED).grid(row=1, column=1, sticky="nw", pady=(3, 18))
            ctk.CTkLabel(card, text="›", font=ctk.CTkFont(size=30), text_color=T.MUTED).grid(row=0, column=2, rowspan=2, padx=18)

        suggestions = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        suggestions.grid(row=3, column=0, sticky="ew", padx=(0, 25), pady=(0, 20))
        suggestions.grid_columnconfigure(0, weight=1)
        self.section_header(suggestions, 0, "Gợi ý ôn tập hôm nay", "★", show_all=False)
        grid = ctk.CTkFrame(suggestions, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        for c in range(4):
            grid.grid_columnconfigure(c, weight=1)
        for i, it in enumerate(REVIEW_CARDS):
            self.review_suggestion(grid, i, it)

        stats = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        stats.grid(row=4, column=0, sticky="ew", padx=(0, 25))
        stats.grid_columnconfigure((0, 1, 2), weight=1)
        for i, (icon, label, value, sub, color) in enumerate([
            ("🎯", "Độ chính xác TB", "91%", "Cao hơn 12% so với tuần trước ↗", T.GREEN),
            ("📅", "Chuỗi ngày học", "5 ngày", "Cố gắng duy trì mỗi ngày! 🔥", T.GREEN),
            ("🕘", "Tổng thời gian học", "2h 35m", "Tổng thời gian luyện tập", T.BLUE),
        ]):
            cell = ctk.CTkFrame(stats, fg_color="transparent")
            cell.grid(row=0, column=i, sticky="nsew", padx=20, pady=20)
            ctk.CTkLabel(cell, text=icon, font=ctk.CTkFont(size=32), text_color=color).pack(side="left", padx=(0, 14))
            box = ctk.CTkFrame(cell, fg_color="transparent")
            box.pack(side="left")
            ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=15, weight="bold"), text_color=T.TEXT).pack(anchor="w")
            ctk.CTkLabel(box, text=value, font=ctk.CTkFont(size=27, weight="bold"), text_color=color).pack(anchor="w")
            ctk.CTkLabel(box, text=sub, font=ctk.CTkFont(size=12), text_color=T.MUTED).pack(anchor="w")

        challenge = ctk.CTkFrame(page, width=350, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        challenge.grid(row=2, column=1, rowspan=3, sticky="nsew")
        challenge.grid_propagate(False)
        ctk.CTkLabel(challenge, text="⚡  Thử thách hôm nay", font=ctk.CTkFont(size=19, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=22, pady=(25, 15))
        ctk.CTkLabel(challenge, text="🤏", width=215, height=215, fg_color="#0B1520", corner_radius=110, font=ctk.CTkFont(size=100)).pack(pady=(0, 10))
        ctk.CTkLabel(challenge, text="1 / 10", font=ctk.CTkFont(size=16), text_color=T.BLUE).pack(anchor="w", padx=30)
        ctk.CTkLabel(challenge, text="Ký hiệu này là chữ gì?", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=30, pady=(18, 12))
        for code, ans in [("A", "Chữ C"), ("B", "Chữ O"), ("C", "Chữ G"), ("D", "Chữ Q")]:
            ctk.CTkButton(challenge, text=f"{code}     {ans}", height=48, anchor="w", fg_color=T.CARD, hover_color=T.CARD_HOVER, text_color=T.TEXT, corner_radius=9).pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(challenge, text="▶  Bắt đầu ôn tập", height=55, fg_color=T.BLUE, hover_color=T.BLUE_DARK).pack(fill="x", padx=30, pady=(25, 20))

    def review_suggestion(self, parent, col, it):
        color = COLOR_MAP[it["color"]]
        card = ctk.CTkFrame(parent, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 12, 0))
        ctk.CTkLabel(card, text=it["icon"], width=58, height=58, fg_color=color, corner_radius=30, font=ctk.CTkFont(size=20, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(18, 8))
        ctk.CTkLabel(card, text=it["title"], font=ctk.CTkFont(size=17, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18)
        ctk.CTkLabel(card, text=it["desc"], wraplength=175, justify="left", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w", padx=18, pady=(5, 12))
        ctk.CTkLabel(card, text=it["count"], fg_color="#132033", corner_radius=7, text_color=color, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(0, 18))


def open_study_window(parent=None):
    """Mở giao diện Góc học tập từ app chính."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    if parent is None:
        root = ctk.CTk()
        root.title("VSL Translate - Góc học tập")
        root.geometry("1600x900")
        root.minsize(1280, 760)
        StudyApp(root)
        root.mainloop()
        return root

    win = ctk.CTkToplevel(parent)
    win.title("VSL Translate - Góc học tập")
    win.geometry("1600x900")
    win.minsize(1280, 760)
    win.transient(parent)
    StudyApp(win)
    win.focus()
    return win


def run_app():
    open_study_window(None)
