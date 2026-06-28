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
        LESSON_DETAILS,
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
        LESSON_DETAILS,
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
# DỮ LIỆU THẬT: CÁC CẶP KÝ HIỆU HAY NHẦM LẪN
# (Dựa trên sự tương đồng về hình dáng tay)
# ==========================================
CONFUSED_PAIRS_DATA = [
    ("D", "Đ", "Chữ D dựng thẳng ngón trỏ, chữ Đ có thêm chuyển động gập ngón trỏ hai lần."),
    ("K", "H", "Chữ K dựng đứng 2 ngón tách ra, chữ H nằm ngang và khép sát 2 ngón lại."),
    ("K", "P", "Hình dáng tay y hệt nhau, nhưng chữ K hướng lên, chữ P chúi mũi ngón tay xuống."),
    ("A", "S", "Chữ A ngón cái để dọc bên mép tay, chữ S ngón cái gập ngang ôm khóa các ngón khác."),
    ("R", "V", "Chữ V hai ngón trỏ và giữa tách hình chữ V, chữ R hai ngón này đan chéo lên nhau."),
    ("I", "Y", "Chữ I chỉ dựng đứng mỗi ngón út, chữ Y dựng ngón út và chĩa thêm ngón cái ra ngoài.")
]
# ==========================================
# NẠP DỮ LIỆU THẬT TỪ SQL SERVER
# ==========================================
# Nếu SQL lỗi hoặc chưa có bảng, giao diện vẫn chạy bằng dữ liệu mẫu trong data.py.
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
        
    # BÍ KÍP 2: XÓA VIỆC GÁN TỪ ĐIỂN RỖNG VÀ DÙNG .update() ĐỂ BẢO TOÀN DATA
    if _sql_data.get("LESSON_DETAILS"):
        LESSON_DETAILS.update(_sql_data["LESSON_DETAILS"])
        
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
        self.lesson_cap = None
        self.lesson_video_after_id = None
        # CẤY 2 BỘ NÃO VÀO BỘ NHỚ LƯU TRỮ CỦA APP
        self.lstm_model_1 = None
        self.action_labels_1 = []
        self.lstm_model_2 = None
        self.action_labels_2 = []

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
        # Luồng mới: Cả Sidebar và các nút bên trong đều dùng chung một Panel
        def handle_sidebar_auth():
            import sys, os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            try:
                import auth_ui
                if auth_ui.CURRENT_USER is not None:
                    messagebox.showinfo("Tài khoản", f"Bạn đang đăng nhập với tài khoản: {auth_ui.CURRENT_USER['username']}")
                    return
            except Exception: pass
            
            # Gọi màn hình đăng nhập nội tuyến, đăng nhập xong quay về Trang chủ
            self.show_auth_panel(return_page=self.show_home)

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
            command=handle_sidebar_auth
        )
        self.account_btn.grid(row=6, column=0, sticky="ew", padx=20, pady=5)
        self.refresh_account_button()
        self.account_btn.grid(row=6, column=0, sticky="ew", padx=20, pady=5)
        self.refresh_account_button()
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
        if hasattr(self, 'stop_lesson_video'):
            self.stop_lesson_video()
        if self.page_frame is not None:
            self.page_frame.destroy()
        self.page_frame = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self.page_frame.grid(row=0, column=self.content_column, sticky="nsew")
        self.page_frame.grid_columnconfigure(0, weight=1)
        self.page_frame.grid_rowconfigure(0, weight=1)
        return self.page_frame

    def _content(self):
        root = self._clear_page()
        
        # ==========================================
        # BÍ KÍP 1: ĐỌC NGỮ CẢNH ĐỂ QUYẾT ĐỊNH BẬT/TẮT THANH CUỘN
        # ==========================================
        import inspect
        try:
            caller_name = inspect.stack()[1].function
            # Chỉ Bảng chữ cái, Trang chủ, và Từ vựng mới có thanh cuộn (Scroll)
            needs_scroll = caller_name in ["show_alphabet", "show_home", "show_conversation"]
        except Exception:
            needs_scroll = False
            
        if needs_scroll:
            wrapper = ctk.CTkScrollableFrame(root, fg_color=T.BG, corner_radius=0)
        else:
            # Các trang tĩnh (Bài học, Ôn tập) sẽ không có thanh cuộn
            wrapper = ctk.CTkFrame(root, fg_color=T.BG, corner_radius=0)
            
        wrapper.grid(row=0, column=0, sticky="nsew", padx=(35, 30), pady=(20, 15))
        wrapper.grid_columnconfigure(0, weight=1)
        
        if not needs_scroll:
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
            lessons = []
            try:
                for key, lesson in LESSON_DETAILS.items():
                    if not isinstance(lesson, dict) or lesson.get("topic_type") != "conversation":
                        continue
                    value = self.get_current_lesson_key(lesson, key)
                    order = lesson.get("order") or lesson.get("ThuTu") or 9999
                    try: order = int(order)
                    except: order = 9999
                    if value: lessons.append((order, value))
                lessons.sort(key=lambda x: x[0])
                for _, value in lessons:
                    if self.normalize_lesson_key(value) not in [self.normalize_lesson_key(x) for x in sequence]:
                        sequence.append(value)
            except Exception: pass
        else:
            # ==========================================
            # BÍ KÍP 2: PHÂN LUỒNG RẠCH RÒI "DẤU CÂU" VÀ "CHỮ CÁI"
            # ==========================================
            current_key = str(self.get_current_lesson_key(current_lesson)).upper()
            is_mark = current_key.startswith("DAU_") or "DẤU" in current_key

            try:
                for item in ALPHABET:
                    value = item.get("label") or item.get("NhanHienThi") or item.get("title") if isinstance(item, dict) else item
                    value_str = str(value or "").replace("Chữ ", "", 1).strip().upper()
                    
                    if not value_str: continue
                    item_is_mark = value_str.startswith("DAU_") or "DẤU" in value_str
                    
                    # Nếu đang học Dấu thì chỉ load mảng Dấu, đang học Chữ thì load mảng Chữ
                    if is_mark == item_is_mark:
                        if self.normalize_lesson_key(value_str) not in [self.normalize_lesson_key(x) for x in sequence]:
                            sequence.append(value_str)
            except Exception: pass
            
            # Cứu cánh (Fallback): Lỡ trong ALPHABET không có sẵn mảng dấu câu
            if is_mark and not sequence:
                sequence = ["DAU_A", "DAU_MU", "DAU_MOC", "DAU_SAC", "DAU_HUYEN", "DAU_HOI", "DAU_NGA", "DAU_NANG"]
                if current_key not in sequence:
                    sequence.insert(0, current_key)

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

    def decompose_target_sign(self, char_str):
        """
        Phân tích 1 chữ cái thành: (Chữ_gốc, Mã_dấu_đi_kèm, Có_phải_chữ_kép_không)
        Ví dụ: 'Â' -> ('A', 'DAU_MU', True)
               'B' -> ('B', None, False)
        """
        import sys, os
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if project_root not in sys.path:
            sys.path.append(project_root)
            
        try:
            from core.vietnamese_utils import VIETNAMESE_MAP
        except Exception:
            # Bọc lót an toàn nhỡ import lỗi
            VIETNAMESE_MAP = {
                "DAU_MU": {'A': 'Â', 'E': 'Ê', 'O': 'Ô'},
                "DAU_MOC": {'O': 'Ơ', 'U': 'Ư'},
                "DAU_A": {'A': 'Ă'}
            }

        val = str(char_str).replace("Chữ ", "").strip().upper()
        for mark_code, char_dict in VIETNAMESE_MAP.items():
            for base_c, result_c in char_dict.items():
                if result_c.upper() == val:
                    return (base_c, mark_code, True)
        return (val, None, False)

    def get_mark_display_name(self, mark_code):
        names = {
            "DAU_A": "Dấu Á",
            "DAU_MU": "Dấu Mũ",
            "DAU_MOC": "Dấu Móc",
            "DAU_SAC": "Dấu Sắc",
            "DAU_HUYEN": "Dấu Huyền",
            "DAU_HOI": "Dấu Hỏi",
            "DAU_NGA": "Dấu Ngã",
            "DAU_NANG": "Dấu Nặng"
        }
        return names.get(str(mark_code), "Dấu câu")
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
        Load ảnh bàn tay bằng CTkImage CÓ CACHING để tăng tốc độ UI.
        """
        # BÍ KÍP 2: Tạo bộ nhớ đệm (Cache) để không phải đọc lại ổ cứng nhiều lần
        if not hasattr(self, 'image_cache'):
            self.image_cache = {}
            
        image_path = self.get_lesson_image_path(lesson)
        full_path = self.resolve_asset_path(image_path)

        if not full_path or not os.path.exists(full_path):
            return None

        # Kiểm tra xem ảnh này đã có trong RAM chưa?
        cache_key = f"{full_path}_{size[0]}x{size[1]}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        try:
            from PIL import Image
            img = Image.open(full_path)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            
            # Lưu vào Cache cho các lần load sau
            self.image_cache[cache_key] = ctk_img
            return ctk_img
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
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=0, corner_radius=16)
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
    def refresh_account_button(self, user=None):
        """
        Cập nhật nút tài khoản ở góc trái sidebar.
        Nếu đã đăng nhập thì hiện tên user.
        Nếu chưa đăng nhập thì hiện Đăng nhập / Đăng ký.
        """
        # ==========================================
        # BÍ KÍP CHỐNG XUNG ĐỘT: Báo cho Giao diện Cha (ui_user.py) cập nhật
        # ==========================================
        toplevel = self.winfo_toplevel()
        if hasattr(toplevel, "refresh_sidebar_auth"):
            toplevel.refresh_sidebar_auth()
            
        if not hasattr(self, "account_btn"):
            return

        # (Phần code cũ bên dưới của bạn giữ nguyên, không cần sửa)
        # Nếu chưa truyền user vào thì mới tự tìm trong auth_ui...

        # Nếu chưa truyền user vào thì mới tự tìm trong auth_ui
        if user is None:
            import sys
            import os
            import importlib

            auth_ui = None

            # Ưu tiên lấy module auth_ui đang có CURRENT_USER trong bộ nhớ
            for name, module in list(sys.modules.items()):
                if name == "auth_ui" or name.endswith(".auth_ui"):
                    if getattr(module, "CURRENT_USER", None):
                        auth_ui = module
                        break

            # Nếu chưa tìm thấy thì import như bình thường
            if auth_ui is None:
                user_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                if user_dir not in sys.path:
                    sys.path.insert(0, user_dir)

                try:
                    auth_ui = importlib.import_module("auth_ui")
                except Exception as e:
                    print("Không import được auth_ui trong refresh_account_button:", e)
                    return

            user = getattr(auth_ui, "CURRENT_USER", None)

        if user:
            username = (
                user.get("username")
                or user.get("Username")
                or user.get("TenDangNhap")
                or user.get("ten_dang_nhap")
                or user.get("HoTen")
                or user.get("name")
                or "User"
            )

            self.account_btn.configure(
                text=f"👤   Chào, {username}",
                text_color=T.GREEN,
                fg_color="#17351F",
                hover_color="#1F4A2A"
            )

            try:
                self.account_btn.update_idletasks()
            except Exception:
                pass

        else:
            self.account_btn.configure(
                text="👤   Đăng nhập / Đăng ký",
                text_color=T.ORANGE,
                fg_color="transparent",
                hover_color="#222931"
            )
    def show_auth_panel(self, return_page=None):
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không tải được module đăng nhập: {e}")
            return

        # Nếu đã đăng nhập, tự động đồng bộ UI và quay về
        if getattr(auth_ui, "CURRENT_USER", None) is not None:
            self.refresh_account_button(auth_ui.CURRENT_USER)
            if callable(return_page): return_page()
            else: self.show_home()
            return

        # Vẽ trang Đăng nhập nội tuyến (Inline Panel)
        page = self._clear_page()
        page.configure(fg_color=T.BG)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)

        auth_area = ctk.CTkFrame(page, fg_color=T.BG, corner_radius=0)
        auth_area.grid(row=0, column=0, sticky="nsew")
        auth_area.grid_columnconfigure(0, weight=1)
        auth_area.grid_rowconfigure(0, weight=1)

        # Gắn nút "Trở về" nổi lên trên cùng góc phải
        back_holder = ctk.CTkFrame(page, fg_color="transparent")
        back_holder.place(relx=1.0, y=32, x=-55, anchor="ne")
        self.back_button(
            back_holder,
            command=return_page if callable(return_page) else self.show_home,
            text="←  Trở về"
        ).pack()
        back_holder.lift()

        def after_login_success():
            # 1. Đổi ngay nút Sidebar thành "👤 Chào, [Tên]"
            self.refresh_account_button(getattr(auth_ui, "CURRENT_USER", None))
            
            # 2. Điều hướng chính xác về nơi người dùng vừa gọi
            if callable(return_page): 
                self.after(100, return_page)
            else: 
                self.after(100, self.show_home)

        # Nhúng Form đăng nhập vào Panel
        auth_frame = auth_ui.AuthFrame(auth_area, on_success=after_login_success)
        auth_frame.grid(row=0, column=0, sticky="nsew")
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

        ctk.CTkButton(
            bottom, 
            text="Học ngay  ❯", 
            height=38, 
            fg_color=T.BLUE, 
            hover_color=T.BLUE_DARK, 
            command=lambda: self.show_lesson(
                item.get("label", item["letter"].replace("Chữ ", "")),
                custom_back_cmd=self.show_home,        # <--- Bơm địa chỉ Home vào
                custom_back_text="←  Trang chính"      # <--- Đổi tên nút cho đẹp
            )
        ).pack(fill="x")
    def topic_card(self, parent, idx: int, item: dict):
        color = COLOR_MAP.get(item.get("color", "blue"), T.BLUE)
        
        # BÍ KÍP 2: Xóa viền (border_width=0) theo chuẩn Flat Design hiện đại
        card = ctk.CTkFrame(parent, width=230, height=180, fg_color=T.CARD, border_width=0, corner_radius=14)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0))
        card.grid_propagate(False) 

        # Hàng 1: Icon và Text xếp cạnh nhau
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=14, pady=(18, 0))

        icon_box = self.icon_box(content, item["icon"], color, size=55, font_size=22)
        icon_box.pack(side="left", anchor="nw")

        text_box = ctk.CTkFrame(content, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # Logic cắt chữ chống tràn UI
        title_text = item["title"]
        if len(title_text) > 18: title_text = title_text[:15] + "..."
        
        desc_text = item.get("desc", "")
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
        pb.set(item.get("progress", 0))

        stat_row = ctk.CTkFrame(bottom, fg_color="transparent")
        stat_row.pack(fill="x")
        ctk.CTkLabel(stat_row, text=item.get("count", "0 bài học"), font=ctk.CTkFont(family=T.FONT, size=13, weight="bold"), text_color=color).pack(side="left")
        ctk.CTkLabel(stat_row, text="›", font=ctk.CTkFont(size=28), text_color=T.MUTED).pack(side="right")
        
        # BÍ KÍP 3: Gắn sự kiện click để nhảy vào thẳng bài học giống trang Giao tiếp
        def on_click(e):
            self.show_lesson(
                item.get("first_label", "D"),
                custom_back_cmd=self.show_home,        # <--- Bơm địa chỉ Home vào
                custom_back_text="←  Trang chính"
            )
            
        card.bind("<Button-1>", on_click)
        for child in [content, icon_box, text_box, bottom, stat_row]:
            child.bind("<Button-1>", on_click)
            for subchild in child.winfo_children():
                subchild.bind("<Button-1>", on_click)
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
            
        # ==========================================
        # BÍ KÍP 1: KẾT NỐI DỮ LIỆU THẬT CHO CHỦ ĐỀ PHỔ BIẾN
        # ==========================================
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
            learned = auth_ui.LEARNED_LETTERS or []
        except Exception:
            learned = []

        # Bản đồ khóa chính để đếm
        topic_mapping = {
            "Chào hỏi": ["XIN CHÀO", "CẢM ƠN", "XIN LỖI", "TẠM BIỆT", "TÔI", "TÊN"],
            "Gia đình": ["BỐ", "MẸ"],
            "Trường học": ["GIÁO VIÊN", "HỌC SINH"]
        }

        for i, item in enumerate(POPULAR_TOPICS):
            title = item.get("title")
            if title in topic_mapping:
                lessons = topic_mapping[title]
                total = len(lessons)
                done = len([l for l in lessons if l in learned])
                
                # Cập nhật số liệu vào dictionary trước khi ném cho thẻ vẽ
                item["progress"] = done / total if total > 0 else 0
                item["count"] = f"{done} / {total} câu" if title == "Chào hỏi" else f"{done} / {total} bài"
                item["first_label"] = lessons[0] if lessons else "D"
                
            self.topic_card(topics_grid, i, item)

        right = ctk.CTkFrame(page, fg_color="transparent", width=295)
        right.grid(row=3, column=1, sticky="nsew")
        right.grid_propagate(False)
        self.progress_panel(right)

    def progress_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(card, text="↗  Tiến độ học tập", font=ctk.CTkFont(family=T.FONT, size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=22, pady=(22, 12))
        
        # ==========================================================
        # BÍ KÍP VÀNG: KẾT NỐI DB THẬT & LỌC CHỮ CÁI THUẦN TÚY (CORE 29)
        # ==========================================================
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui, user_db
            
            # 1. LẤY DỮ LIỆU THẬT TỪ DATABASE CHỨ KHÔNG NHÌN VÀO RAM NỮA
            user_data = auth_ui.CURRENT_USER or {}
            user_id = user_data.get("id")
            
            if user_id:
                # Gọi thẳng xuống SQL Server bốc dữ liệu mới nhất
                raw_learned_list = user_db.get_learned_letters(user_id)
                # Lấy luôn 3 chỉ số "sống"
                stats_row = user_db.get_user_minigame_stats(user_id) or {}
                do_chinh_xac = stats_row.get("DoChinhXacTB", 0)
                chuoi_ngay = stats_row.get("ChuoiNgayHoc", 0)
                
                # Truy vấn riêng ThoiGianHoc từ TaiKhoan
                conn = user_db.get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT ISNULL(ThoiGianHoc, 0) FROM TaiKhoan WHERE ID = ?", (user_id,))
                thoi_gian_phut = cursor.fetchone()[0]
            else:
                raw_learned_list = auth_ui.LEARNED_LETTERS or []
                do_chinh_xac, chuoi_ngay, thoi_gian_phut = 0, 0, 0
                
            # 2. ÁP DỤNG BỘ LỌC DLC: Chỉ đếm những chữ cái thuộc Core 29
            pure_learned = [char for char in raw_learned_list if self.is_pure_alphabet_letter(char)]
            learned_count = len(pure_learned)
            
        except Exception as e:
            print("[Progress Panel] Lỗi móc nối DB:", e)
            learned_count, do_chinh_xac, chuoi_ngay, thoi_gian_phut = 0, 0, 0, 0

        # Khóa cứng mẫu số là 29 (Bảng chữ cái VSL chuẩn)
        total_letters = 29
        percent = min(1.0, learned_count / total_letters)

        # Xử lý hiển thị thời gian học (phút -> giờ phút)
        gio = thoi_gian_phut // 60
        phut = thoi_gian_phut % 60
        thoi_gian_str = f"{gio}h {phut}m" if gio > 0 else f"{phut}m"

        center = ctk.CTkFrame(card, fg_color="transparent")
        center.pack(fill="x", padx=20)
        
        ring = ProgressRing(center, percent, size=120, color=T.BLUE, bg=T.PANEL)
        ring.pack(side="left", padx=(0, 14), pady=5)
        
        info = ctk.CTkFrame(center, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text="Đã học:", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(anchor="w", pady=(16, 0))
        
        # Hiển thị đúng: Ví dụ 15/29
        ctk.CTkLabel(info, text=f"{learned_count}/{total_letters}", font=ctk.CTkFont(size=26, weight="bold"), text_color=T.GREEN).pack(anchor="w")
        
        ctk.CTkLabel(info, text="Bảng chữ cái", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w")
        ctk.CTkFrame(card, height=1, fg_color=T.LINE).pack(fill="x", padx=20, pady=15)
        
        # IN 3 CHỈ SỐ "SỐNG" RA GIAO DIỆN VỚI CÂU CHÚ THÍCH THÔNG MINH
        self.stat_row(card, "📅", "Chuỗi ngày học", f"{chuoi_ngay} ngày", T.GREEN, "Cố gắng duy trì mỗi ngày!" if chuoi_ngay > 0 else "Hãy bắt đầu bài học!")
        self.stat_row(card, "🎯", "Độ chính xác TB", f"{do_chinh_xac}%", T.GREEN, "Làm rất tốt! 💪" if do_chinh_xac > 0 else "Chưa có dữ liệu")
        self.stat_row(card, "🕘", "Thời gian học", thoi_gian_str, T.BLUE, "Tổng thời gian thực hành")

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
                def on_tile_state_flipped(marked_letter):
                    if marked_letter in tile_cards:
                        target_card = tile_cards[marked_letter]
                        
                        # 1. Đổi dòng chữ nhỏ thành "✓ Đã học" màu xanh
                        target_card.status_label.configure(text="✓ Đã học", text_color=T.GREEN)
                        
                        # 2. Bonus UX: Đổi luôn viền của cái thẻ đó sang màu Xanh lá cho rực rỡ!
                        target_card.configure(border_color=T.GREEN)

                # Bơm tổng đài vào Bảng chi tiết
                current_detail_panel = self.letter_detail(
                    right_container, 
                    letter,
                    on_marked_learned=on_tile_state_flipped  # <--- Cắm dây kết nối
                )
                
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
            
            default_marks = [
                "DAU_A", "DAU_MU", "DAU_MOC", 
                "DAU_SAC", "DAU_HUYEN", "DAU_HOI", "DAU_NGA", "DAU_NANG"
            ]
            default_alpha = ["A", "Ă", "Â", "B", "C", "D", "Đ", "E", "Ê", "G", "H", "I", "K", "L", "M", "N", "O", "Ô", "Ơ", "P", "Q", "R", "S", "T", "U", "Ư", "V", "X", "Y"]
            
            alpha_list = []
            marks_list = default_marks 
            
            if ALPHABET:
                for item in ALPHABET:
                    val = str(item).upper()
                    if len(val) == 1:
                        alpha_list.append(item)
                        
            if not alpha_list:
                alpha_list = default_alpha
                
            current_data = alpha_list if self.current_alpha_tab == "Chữ cái" else marks_list
            
            # ==========================================
            # SIÊU TỪ ĐIỂN TÌM KIẾM (SEARCH INDEX)
            # ==========================================
            mark_search_index = {
                "DAU_A": "DẤU Á (Ă) DAU A",
                "DAU_MU": "DẤU MŨ (Â, Ê, Ô) DAU MU",
                "DAU_MOC": "DẤU MÓC (Ư, Ơ) DAU MOC",
                "DAU_SAC": "DẤU SẮC DAU SAC",
                "DAU_HUYEN": "DẤU HUYỀN DAU HUYEN",
                "DAU_HOI": "DẤU HỎI DAU HOI",
                "DAU_NGA": "DẤU NGÃ DAU NGA",
                "DAU_NANG": "DẤU NẶNG DAU NANG"
            }
                
            filtered = []
            for char in current_data:
                # Trỏ sang siêu từ điển, nếu không có thì lấy str gốc
                target_str = mark_search_index.get(str(char), str(char)).upper()
                if query in target_str or query in str(char).upper():
                    filtered.append(char)

            if not filtered:
                ctk.CTkLabel(grid, text="Không tìm thấy kết quả nào.", text_color=T.MUTED, font=ctk.CTkFont(size=15)).grid(row=0, column=0, columnspan=6, pady=20)
                
            for idx, letter in enumerate(filtered):
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
        status_lbl = ctk.CTkLabel(card, text=status, font=ctk.CTkFont(size=11), text_color=color)
        status_lbl.pack(pady=(0, 5))
        
        card.status_label = status_lbl
        
        def click_handler(_e, l=letter):
            if on_click: on_click(l)
            
        card.bind("<Button-1>", click_handler)
        for child in card.winfo_children():
            child.bind("<Button-1>", click_handler)
            
        return card  

    def letter_detail(self, parent, letter, on_marked_learned=None):
        lesson = self.get_lesson(letter)
        icon = lesson.get("icon", "☝")
        desc = lesson.get("desc", "Dựng ngón trỏ thẳng đứng.")
        steps = lesson.get("steps") or ["Thực hiện ký hiệu theo mẫu.", "Giữ tay ổn định trước camera."]
        card = ctk.CTkFrame(parent, width=310, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=self.lesson_title_text(lesson), font=ctk.CTkFont(size=27, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=20, pady=(22, 8))
        
        # ĐÃ XÓA UNICODE - DÙNG LOGIC NGUYÊN THỦY
        val = str(letter).upper().replace("CHỮ ", "").strip()
        
        composite_map = {
            "Ă": "DAU_A", "Â": "DAU_MU", "Ê": "DAU_MU",
            "Ô": "DAU_MU", "Ơ": "DAU_MOC", "Ư": "DAU_MOC"
        }
        # Bản đồ lấy ảnh chữ gốc chuẩn xác
        base_letter_map = {
            "Ă": "A", "Â": "A", "Ê": "E",
            "Ô": "O", "Ơ": "O", "Ư": "U"
        }
        
        if val in composite_map:
            # TẠO KHUNG NGANG CHỨA 2 ẢNH
            img_frame = ctk.CTkFrame(card, fg_color="transparent")
            img_frame.pack(fill="x", padx=20, pady=5)
            img_frame.grid_columnconfigure((0, 1), weight=1)
            
            base_char = base_letter_map[val]
            base_lesson = self.get_lesson(base_char)
            base_img = self.create_lesson_image_label(img_frame, base_lesson, size=(100, 100), height=140, fallback_font_size=60)
            base_img.configure(fg_color="#0E1722", corner_radius=14)
            base_img.grid(row=0, column=0, padx=(0, 5), sticky="ew")
            ctk.CTkLabel(img_frame, text="Ký hiệu gốc", font=ctk.CTkFont(size=12, weight="bold"), text_color=T.MUTED).grid(row=1, column=0, pady=(5,0))
            
            mark_char = composite_map[val]
            mark_lesson = {"label": mark_char} 
            mark_img = self.create_lesson_image_label(img_frame, mark_lesson, size=(100, 100), height=140, fallback_font_size=60)
            mark_img.configure(fg_color="#0E1722", corner_radius=14)
            mark_img.grid(row=0, column=1, padx=(5, 0), sticky="ew")
            ctk.CTkLabel(img_frame, text="Thêm dấu", font=ctk.CTkFont(size=12, weight="bold"), text_color=T.MUTED).grid(row=1, column=1, pady=(5,0))
        else:
            # ẢNH BÌNH THƯỜNG
            media_border = ctk.CTkFrame(card, fg_color="#0B1520", border_width=2, border_color=T.BORDER, corner_radius=16)
            media_border.pack(fill="x", padx=20, pady=5)
            
            detail_image = self.create_lesson_image_label(
                media_border, lesson, size=(235, 165), height=180, fallback_font_size=82
            )
            detail_image.configure(fg_color="transparent", corner_radius=14)
            detail_image.pack(fill="both", expand=True, padx=2, pady=2)
            
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
                if letter not in auth_ui.LEARNED_LETTERS:
                    auth_ui.LEARNED_LETTERS.append(letter)
                btn_done.configure(text="✓ Đã lưu tiến độ", text_color=T.GREEN, state="disabled")
                
                # ==========================================================
                # BẮN TÍN HIỆU LÀM XANH THẺ GRID (KHÔNG CẦN RESET)
                # ==========================================================
                if on_marked_learned:
                    on_marked_learned(letter)
            else:
                messagebox.showerror("Lỗi DB", "Không thể lưu tiến độ!")

        btn_done = ctk.CTkButton(card, text="✓  Đánh dấu đã học", height=40, fg_color="transparent", border_width=1, border_color=T.BORDER, hover_color=T.CARD_HOVER, command=mark_done)
        btn_done.pack(fill="x", padx=20, pady=(0, 20))
        
        if letter in auth_ui.LEARNED_LETTERS:
            btn_done.configure(text="✓ Đã lưu tiến độ", text_color=T.GREEN, state="disabled")

        return card
    # ==========================================
    # CỖ MÁY VIDEO PLAYER (MP4) CHO BÀI HỌC
    # ==========================================
    # ==========================================
    # CỖ MÁY VIDEO PLAYER (MP4) CHO BÀI HỌC
    # ==========================================
    def get_lesson_video_path(self, lesson_key):
        """Truy tìm đường dẫn file .mp4: TỐI ƯU TỐC ĐỘ (Đã gỡ bỏ Unicode)"""
        import os
        
        val = str(lesson_key).strip().upper()
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        folder_path = os.path.join(base_dir, "user", "assets", "signs", "NNKH")
        
        if not os.path.exists(folder_path):
            folder_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'signs', 'NNKH')
            
        if os.path.exists(folder_path):
            direct_file = os.path.join(folder_path, f"{val}.mp4")
            if os.path.exists(direct_file):
                return direct_file
                
            for file in os.listdir(folder_path):
                if file.upper() == f"{val}.MP4":
                    return os.path.join(folder_path, file)
        return None

    def stop_lesson_video(self):
        """Dọn dẹp luồng phát video một cách an toàn"""
        if self.lesson_video_after_id is not None:
            try: self.after_cancel(self.lesson_video_after_id)
            except Exception: pass
            self.lesson_video_after_id = None
            
        if self.lesson_cap is not None:
            try: self.lesson_cap.release()
            except Exception: pass
            self.lesson_cap = None

    def play_lesson_video(self, video_label, video_path, target_w=430, target_h=310):
        """Phát video MP4 và tự động lặp lại (Loop)"""
        import cv2
        from PIL import Image
        import customtkinter as ctk
        
        self.stop_lesson_video() 
        self.lesson_cap = cv2.VideoCapture(video_path)
        
        def update_frame():
            if not self.lesson_cap or not self.lesson_cap.isOpened():
                return
                
            success, frame = self.lesson_cap.read()
            if not success:
                self.lesson_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, frame = self.lesson_cap.read()
                
            if success:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = frame_rgb.shape[:2]
                
                # Render video đúng kích thước tùy chỉnh được truyền vào
                scale = min(target_w / w, target_h / h)
                new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                
                frame_resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
                img = Image.fromarray(frame_resized)
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                
                video_label.configure(image=imgtk, text="")
                video_label.image = imgtk
                
            self.lesson_video_after_id = self.after(33, update_frame)
            
        update_frame()

    # TÌM TRONG HÀM show_lesson() ĐỂ CHÉP ĐÈ ĐOẠN KHUNG ẢNH:
    def show_lesson(self, letter="D", custom_back_cmd=None, custom_back_text=None):
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
        if custom_back_cmd:
            back_cmd = custom_back_cmd
            back_text = custom_back_text or "←  Trở về"
        else:
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
        
        media_border = ctk.CTkFrame(main, fg_color="#0B1520", border_width=2, border_color=T.BORDER, corner_radius=18)
        media_border.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        media_border.grid_rowconfigure(0, weight=1)
        
        target_key = lesson.get("label", letter)
        video_path = self.get_lesson_video_path(target_key)
        
        val = str(letter).upper().replace("CHỮ ", "").strip()
        composite_map = {
            "Ă": "DAU_A", "Â": "DAU_MU", "Ê": "DAU_MU",
            "Ô": "DAU_MU", "Ơ": "DAU_MOC", "Ư": "DAU_MOC"
        }
        base_letter_map = {
            "Ă": "A", "Â": "A", "Ê": "E",
            "Ô": "O", "Ơ": "O", "Ư": "U"
        }
        
        if video_path:
            # ƯU TIÊN PHÁT VIDEO NẾU CÓ
            media_border.grid_columnconfigure(0, weight=1)
            demo = ctk.CTkLabel(media_border, text="Đang tải video...", font=ctk.CTkFont(size=16), text_color=T.MUTED)
            demo.grid(row=0, column=0, sticky="nsew", padx=2, pady=2) 
            self.play_lesson_video(demo, video_path)
        elif val in composite_map:
            # BÍ KÍP MỚI: TÁCH 2 ẢNH NGAY TRONG TRANG BÀI HỌC
            media_border.grid_columnconfigure((0, 1), weight=1)
            
            # Ảnh chữ cái gốc
            base_char = base_letter_map[val]
            base_lesson = self.get_lesson(base_char)
            base_img = self.create_lesson_image_label(media_border, base_lesson, size=(180, 180), height=330, fallback_font_size=100)
            base_img.configure(fg_color="transparent", corner_radius=16)
            base_img.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            
            # Ảnh dấu câu
            mark_char = composite_map[val]
            mark_lesson = self.get_lesson(mark_char)
            mark_img = self.create_lesson_image_label(media_border, mark_lesson, size=(180, 180), height=330, fallback_font_size=100)
            mark_img.configure(fg_color="transparent", corner_radius=16)
            mark_img.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        else:
            # HIỆN 1 ẢNH NHƯ BÌNH THƯỜNG
            media_border.grid_columnconfigure(0, weight=1)
            demo = self.create_lesson_image_label(
                media_border,
                lesson,
                size=(430, 310),
                height=330,
                fallback_font_size=125
            )
            demo.configure(fg_color="transparent", corner_radius=16)
            demo.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        guide = ctk.CTkFrame(main, fg_color="transparent")
        guide.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 30), pady=28)
        guide.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            guide,
            text="ⓘ  Hướng dẫn",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=T.TEXT
        ).pack(anchor="w", pady=(0, 15))

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
            command=lambda k=current_key, bc=back_cmd, bt=back_text: self.show_camera_practice(
                k, 
                back_cmd=lambda: self.show_lesson(k, custom_back_cmd=bc, custom_back_text=bt)
            )
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
        
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
            learned = auth_ui.LEARNED_LETTERS or []
        except Exception:
            learned = []

        sequence = self.get_lesson_sequence(lesson)
        total_items = len(sequence) if sequence else 1
        done_items = len([k for k in sequence if k in learned])
        percent = done_items / total_items
        
        progress_label = "Mẫu câu hoàn thành" if topic_type == "conversation" else "Tiến độ bảng chữ cái"
        
        self.info_item(info, "🏆", progress_label, f"{done_items} / {total_items}", T.PURPLE)
        
        pb = ctk.CTkProgressBar(info, height=7, progress_color=T.PURPLE, fg_color="#2B3139")
        pb.pack(fill="x", padx=20, pady=(10, 5))
        pb.set(percent)
        
        ctk.CTkLabel(info, text=f"{int(percent * 100)}% hoàn thành", text_color=T.MUTED).pack(anchor="w", padx=20)
    def is_pure_alphabet_letter(self, letter_code):
        """
        Bộ lọc chuẩn 29 chữ cái Tiếng Việt.
        Chỉ vứt bỏ các DẤU CÂU độc lập (DAU_MU, DAU_SAC, Dấu Á...).
        Các chữ cái Tiếng Việt (Ă, Â, Ê, Ô, Ơ, Ư) được phục hồi nhân phẩm.
        """
        code_str = str(letter_code).replace("Chữ ", "").strip().upper()
        
        # 1. Nếu là các mã Dấu câu backend hoặc chứa chữ "DẤU" -> Vứt!
        if code_str.startswith("DAU_") or "DẤU" in code_str:
            return False
            
        # 2. Danh sách định danh chính xác 100% của 29 chữ cái Tiếng Việt chuẩn
        # (Bao gồm cả 'DD' là định danh của chữ 'Đ' trong một số Database)
        bang_chu_cai_chuom_29 = [
            "A", "Ă", "Â", "B", "C", "D", "Đ", "DD", "E", "Ê", 
            "G", "H", "I", "K", "L", "M", "N", "O", "Ô", "Ơ", 
            "P", "Q", "R", "S", "T", "U", "Ư", "V", "X", "Y"
        ]
        
        return code_str in bang_chu_cai_chuom_29
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

    # THÊM BIẾN practice_mode=None VÀO ĐẦU HÀM
    def show_camera_practice(self, letter="D", pair_list=None, back_cmd=None, practice_mode=None):
        page = self._clear_page()
        
        self.practice_targets = pair_list if pair_list else [letter]
        self.current_target_idx = 0
        
        def get_current_target():
            return self.practice_targets[self.current_target_idx]
            
        initial_letter = get_current_target()
        lesson = self.get_lesson(initial_letter)
        
        wrapper = ctk.CTkFrame(page, fg_color=T.BG)
        wrapper.pack(fill="both", expand=True, padx=30, pady=30)
        
        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        
        if practice_mode == "weak_signs":
            self._title(title_box, "KÝ HIỆU CẦN CHÚ Ý", f"Thực hành {len(self.practice_targets)} ký hiệu bạn làm sai nhiều nhất")
        elif pair_list:
            if len(pair_list) > 2: self._title(title_box, "ÔN TẬP TỪ VỰNG", f"Thực hành liên hoàn {len(pair_list)} ký hiệu bạn đã học")
            else: self._title(title_box, "LUYỆN TẬP PHÂN BIỆT", f"Thực hành liên hoàn cặp ký hiệu: {pair_list[0]} ↔ {pair_list[1]}")
        else:
            self._title(title_box, "LUYỆN TẬP BẰNG CAMERA", f"Thực hành nhận diện ký hiệu: {initial_letter}")
        
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
            if back_cmd: back_cmd()
            elif pair_list: self.show_confused_letters()
            else: self.show_lesson(initial_letter)

        self.back_button(header, command=go_back, text="←  Trở về").pack(side="right", anchor="n", pady=5)

        body = ctk.CTkFrame(wrapper, fg_color="transparent")
        body.pack(fill="both", expand=True)
        
        right_frame = ctk.CTkFrame(body, fg_color="transparent", width=430)
        right_frame.pack(side="right", fill="y", padx=(25, 0))
        right_frame.pack_propagate(False) 
        
        target_panel = ctk.CTkFrame(right_frame, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        target_panel.pack(fill="x", pady=(0, 15))

        box_req = ctk.CTkFrame(target_panel, fg_color="transparent")
        box_req.pack(fill="x", padx=10, pady=(15, 5))
        
        header_req = ctk.CTkFrame(box_req, fg_color="transparent")
        header_req.pack(fill="x", padx=10)
        ctk.CTkLabel(header_req, text="Ký hiệu cần làm:", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(side="left")
        self.target_name_label = ctk.CTkLabel(header_req, text=f"{get_current_target()}", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.BLUE)
        self.target_name_label.pack(side="right")

        media_border = ctk.CTkFrame(box_req, fg_color="#0B1520", border_width=2, border_color=T.BORDER, corner_radius=14)
        media_border.pack(pady=(10, 5))
        self.practice_req_media = ctk.CTkLabel(media_border, text="", fg_color="transparent")
        self.practice_req_media.pack(padx=2, pady=2)
        ctk.CTkFrame(target_panel, height=1, fg_color=T.BORDER).pack(fill="x", padx=20, pady=5)
        
        box_actual = ctk.CTkFrame(target_panel, fg_color="transparent")
        box_actual.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(box_actual, text="Bạn đang làm:", font=ctk.CTkFont(size=15), text_color=T.MUTED).pack(side="left")
        current_sign_label = ctk.CTkLabel(box_actual, text="--", font=ctk.CTkFont(size=32, weight="bold"), text_color=T.TEXT)
        current_sign_label.pack(side="right")

        def load_practice_media(target_letter):
            target_lesson = self.get_lesson(target_letter)
            target_key = target_lesson.get("label", target_letter)
            video_path = self.get_lesson_video_path(target_key)
            
            if video_path:
                # VỊ TRÍ 1: Thay image="" thành image=None
                self.practice_req_media.configure(text="Đang tải video...", image=None)
                self.play_lesson_video(self.practice_req_media, video_path, target_w=280, target_h=180)
            else:
                self.stop_lesson_video()
                img = self.load_lesson_image(target_lesson, size=(280, 180))
                if img:
                    self.practice_req_media.configure(image=img, text="")
                    self.practice_req_media.image = img
                else:
                    # VỊ TRÍ 2: Thay image="" thành image=None
                    self.practice_req_media.configure(image=None, text=target_lesson.get("icon", "☝"), font=ctk.CTkFont(size=60))

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

        # =================================================================
        # BỘ ĐIỀU KHIỂN NHIỆM VỤ 2 BƯỚC (CHỮ GỐC + DẤU CÂU)
        # =================================================================
        self.composite_sub_step = 0  # 0: Chữ thường, 1: Đang làm chữ gốc, 2: Đang quẹt dấu
        self.current_base_char = None
        self.current_mark_code = None

        def setup_current_target_ui():
            target_raw = get_current_target()
            base_c, mark_c, is_comp = self.decompose_target_sign(target_raw)
            
            if is_comp:
                self.composite_sub_step = 1
                self.current_base_char = base_c
                self.current_mark_code = mark_c
                
                self.target_name_label.configure(text=f"{target_raw}  (Bước 1/2: Chữ {base_c})")
                load_practice_media(base_c) # Load ảnh chữ A trước
                feedback_label.configure(text=f"☆ Học chữ {target_raw}: Hãy giơ tay tạo dáng chữ [{base_c}] trước.", fg_color="#102034", text_color=T.BLUE)
            else:
                self.composite_sub_step = 0
                self.current_base_char = target_raw
                self.current_mark_code = None
                
                self.target_name_label.configure(text=f"{target_raw}")
                load_practice_media(target_raw)
                feedback_label.configure(text=f"☆ Hãy thực hiện ký hiệu: {target_raw}", fg_color="#102034", text_color=T.BLUE)
                
            self.lesson_completed = False
            self.success_frames = 0

        # Khởi tạo giao diện câu đầu tiên
        setup_current_target_ui()

        def toggle_camera():
            if self.practice_camera_on: stop_from_button()
            else: start_practice_camera()

        toggle_btn = ctk.CTkButton(right_frame, text="▶ Bật Camera", height=55, fg_color=T.BLUE, hover_color=T.BLUE_DARK, font=ctk.CTkFont(size=18, weight="bold"), corner_radius=14, command=toggle_camera)
        toggle_btn.pack(fill="x")

        left_frame = ctk.CTkFrame(body, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        left_frame.pack(side="left", fill="both", expand=True)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        cam_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        cam_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        self.practice_status_label = ctk.CTkLabel(cam_bar, text="● Camera đang tắt", fg_color="#2A2F35", corner_radius=8, text_color=T.MUTED, font=ctk.CTkFont(size=13, weight="bold"), padx=12, pady=6)
        self.practice_status_label.pack(side="left")
        
        REACTION_CAMERA_W, REACTION_CAMERA_H = 720, 430
        camera_view = ctk.CTkFrame(left_frame, width=REACTION_CAMERA_W, height=REACTION_CAMERA_H, fg_color="#080C11", corner_radius=12)
        camera_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        camera_view.grid_propagate(False)
        camera_view.grid_rowconfigure(0, weight=1); camera_view.grid_columnconfigure(0, weight=1)

        self.practice_video_label = ctk.CTkLabel(camera_view, text="📷\n\nNhấn 'Bật Camera' để bắt đầu", font=ctk.CTkFont(size=20), text_color=T.MUTED_2)
        self.practice_video_label.grid(row=0, column=0, sticky="nsew")

        self.sequence_data = []
        self.prev_wx = self.prev_wy = None
        self.mp_hands = self.mp_draw = self.ai_session = self.ai_labels = None
        self.success_frames = 0
        self.lesson_completed = False

        # ==========================================
        # VỊ TRÍ 2: TỰ ĐỘNG BUNG KHÓA QUÉT 2 TAY CHO GIAO TIẾP
        # ==========================================
        # ==========================================
        # VỊ TRÍ 1: SỬA HÀM NẠP AI (THÊM RETURN TRUE)
        # ==========================================
        def load_ai_dependencies():
            import sys, os
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            if root_dir not in sys.path: sys.path.append(root_dir)
            
            if self.mp_hands is None:
                import mediapipe as mp
                self.mp_hands = mp.solutions.hands.Hands(
                    static_image_mode=False, 
                    max_num_hands=2,  # Luôn mở khóa quét tối đa 2 tay
                    min_detection_confidence=0.7
                )
                self.mp_draw = mp.solutions.drawing_utils

            # NẠP 2 SIÊU NÃO TỪ CORE (Chỉ nạp đúng 1 lần cho nhẹ RAM)
            try:
                from core.translate_window import load_lstm_model, load_lstm_model_both
                if self.lstm_model_1 is None:
                    self.lstm_model_1, self.action_labels_1 = load_lstm_model()
                if self.lstm_model_2 is None:
                    self.lstm_model_2, self.action_labels_2 = load_lstm_model_both()
            except Exception as e:
                print("[AI Study] Lỗi nạp siêu não LSTM:", e)
                return False # Báo lỗi nếu nạp hỏng
                
            return True # <--- BÍ KÍP LÀ ĐÂY: Báo cáo đã nạp AI thành công!

        def hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy):
            import numpy as np
            wx, wy = landmarks[0].x, landmarks[0].y
            vector = []
            for i in range(1, 21): vector.extend([landmarks[i].x - wx, landmarks[i].y - wy])
            delta_x = 0.0 if prev_wx is None else (wx - prev_wx) * 30
            delta_y = 0.0 if prev_wy is None else (wy - prev_wy) * 30
            if abs(delta_x) < 0.24: delta_x = 0.0
            if abs(delta_y) < 0.24: delta_y = 0.0
            vector.extend([hand_type, delta_x, delta_y])
            return np.array(vector), wx, wy

        def switch_to_next_target():
            self.current_target_idx += 1
            setup_current_target_ui()
            feedback_label.configure(text=f"☆ Đã chuyển tiếp! Vui lòng thực hiện ký hiệu {get_current_target()}.", fg_color="#102034", text_color=T.BLUE)

        def show_victory():
            safe_stop()
            toggle_btn.pack_forget() 
            overlay = ctk.CTkFrame(camera_view, fg_color="#080C11", corner_radius=12)
            overlay.place(relwidth=1, relheight=1)
            
            ctk.CTkLabel(overlay, text="🎉", font=ctk.CTkFont(size=90)).pack(pady=(60, 10))
            ctk.CTkLabel(overlay, text="HOÀN THÀNH XUẤT SẮC", font=ctk.CTkFont(size=24, weight="bold"), text_color=T.GREEN).pack(pady=(0, 10))
            ctk.CTkLabel(overlay, text=f"Tuyệt vời! Bạn đã thực hiện thành công\nký hiệu {initial_letter}!", font=ctk.CTkFont(size=16), text_color=T.TEXT).pack(pady=(0, 30))
            
            btns = ctk.CTkFrame(overlay, fg_color="transparent")
            btns.pack()
            def practice_again():
                overlay.destroy(); toggle_btn.pack(fill="x")
                toggle_btn.configure(text="▶ Bật Camera", fg_color=T.BLUE, hover_color=T.BLUE_DARK)
                self.practice_status_label.configure(text="● Camera đang tắt", text_color=T.MUTED, fg_color="#2A2F35")
                status_value_label.configure(text="Đã tắt", text_color=T.MUTED); accuracy_value_label.configure(text="0%", text_color=T.BLUE)
                acc_progress.set(0); current_sign_label.configure(text="--", text_color=T.TEXT)
                setup_current_target_ui()
                feedback_label.configure(text=f"☆ Đã khởi động lại. Nhấn 'Bật Camera' để bắt đầu.", fg_color="#2A2F35", text_color=T.MUTED)

            ctk.CTkButton(btns, text="⟳ Luyện tập lại", font=ctk.CTkFont(weight="bold"), height=45, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, command=practice_again).pack(side="left", padx=10)
            ctk.CTkButton(btns, text="← Trở về", font=ctk.CTkFont(weight="bold"), height=45, fg_color=T.BLUE, command=go_back).pack(side="left", padx=10)

        def record_success(final_accuracy):
            import sys, os, time
            try:
                import auth_ui, user_db
                if auth_ui.CURRENT_USER is not None:
                    user_id = auth_ui.CURRENT_USER["id"]
                    curr_t = get_current_target()
                    if curr_t not in auth_ui.LEARNED_LETTERS:
                        user_db.mark_as_learned(user_id, curr_t)
                        auth_ui.LEARNED_LETTERS.append(curr_t)
                        
                    # ==========================================================
                    # BÍ KÍP VÀNG: TỰ ĐỘNG CHỐT GIỜ & PHÂN LUỒNG KHI HOÀN THÀNH
                    # ==========================================================
                    # 1. Tính số phút đã đứng trước camera (ít nhất là cộng 1 phút)
                    start_t = getattr(self, "practice_start_time", time.time())
                    elapsed_mins = max(1, int((time.time() - start_t) / 60))
                    
                    # 2. Phân loại xem bài này là Giao tiếp hay Bảng chữ cái
                    check_val = str(initial_letter).strip().upper()
                    is_conv = lesson.get("topic_type") == "conversation" or (len(check_val) > 2 and not check_val.startswith("DAU_"))
                    target_type = "conversation" if is_conv else "alphabet"
                    
                    # 3. Gửi hỏa tốc xuống DB
                    updated = user_db.update_study_stats(
                        user_id, 
                        int(final_accuracy * 100), 
                        time_minutes=elapsed_mins, 
                        topic_type=target_type
                    )
                    if updated:
                        auth_ui.CURRENT_USER.update(updated)
            except Exception as e: 
                print("Lỗi chốt giờ camera:", e)

            if self.current_target_idx < len(self.practice_targets) - 1:
                status_value_label.configure(text="Tốt lắm!", text_color=T.GREEN)
                self.after(1500, switch_to_next_target) 
            else:
                status_value_label.configure(text="Hoàn thành!", text_color=T.GREEN)
                feedback_label.configure(text="☆ Xuất sắc! Bạn đã làm đúng hoàn toàn.", fg_color="#17351F", text_color=T.GREEN)
                self.after(1200, show_victory)

        def update_practice_frame():
            if not self.practice_camera_on or self.practice_cap is None: return

            try:
                success, frame = self.practice_cap.read()
                if success:
                    self.practice_frame_counter += 1
                    
                    import cv2, numpy as np, mediapipe as mp, PIL.Image
                    frame = cv2.flip(frame, 1); h, w = frame.shape[:2]
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    hand_detected = False
                    
                    if self.composite_sub_step == 1: current_eval_letter = self.current_base_char
                    elif self.composite_sub_step == 2: current_eval_letter = self.current_mark_code
                    else: current_eval_letter = get_current_target()

                    is_dynamic_mark = current_eval_letter.startswith("DAU_") or "DẤU" in current_eval_letter.upper()
                    required_frames = 7 if is_dynamic_mark else 15
                    
                    if self.mp_hands is not None:
                        results = self.mp_hands.process(frame_rgb)
                        hands_detected = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
                        
                        if hands_detected > 0:
                            hand_detected = True
                            # Vẽ xương tay
                            for hl in results.multi_hand_landmarks:
                                self.mp_draw.draw_landmarks(frame, hl, mp.solutions.hands.HAND_CONNECTIONS)
                                
                            try:
                                # Nhập cỗ máy trích xuất feature từ core giống hệt ui_user.py
                                from core.train_window import hand_vectorlize
                                from core.train_window_both import extract_86_features
                                from core.translate_window import predict_sign
                            except Exception: pass

                            # ==========================================
                            # LUỒNG 1: SUY LUẬN MÔ HÌNH 1 TAY (43 Dims)
                            # ==========================================
                            if hands_detected == 1 and self.lstm_model_1 is not None:
                                self.seq_2_hands.clear() # Xóa tàn dư 2 tay
                                
                                handedness = results.multi_handedness[0]
                                hand_landmarks = results.multi_hand_landmarks[0]
                                hand_type = 0 if handedness.classification[0].label == "Left" else 1
                                
                                vec_43, self.prev_wx_l, self.prev_wy_l = hand_vectorlize(
                                    hand_landmarks.landmark, hand_type, self.prev_wx_l, self.prev_wy_l
                                )
                                
                                self.seq_1_hand.append(vec_43)
                                if len(self.seq_1_hand) > 30: self.seq_1_hand.pop(0)
                                
                                # Throttling: 5 frame chấm AI 1 lần
                                if len(self.seq_1_hand) == 30 and (self.practice_frame_counter % 5 == 0):
                                    pred_txt, prob = predict_sign(self.lstm_model_1, self.action_labels_1, self.seq_1_hand)
                                    self.cached_predicted_char = pred_txt
                                    
                                    # Chấm điểm: Nếu AI đọc ra đúng chữ đang học thì ghi nhận %
                                    if pred_txt.upper() == current_eval_letter.upper():
                                        self.cached_target_confidence = prob
                                    else:
                                        self.cached_target_confidence = 0.0 if prob > 0.5 else self.cached_target_confidence

                            # ==========================================
                            # LUỒNG 2: SUY LUẬN MÔ HÌNH 2 TAY (86 Dims)
                            # ==========================================
                            elif hands_detected == 2 and self.lstm_model_2 is not None:
                                self.seq_1_hand.clear() # Xóa tàn dư 1 tay
                                
                                vec_86, self.prev_wx_l, self.prev_wy_l, self.prev_wx_r, self.prev_wy_r = extract_86_features(
                                    results, self.prev_wx_l, self.prev_wy_l, self.prev_wx_r, self.prev_wy_r
                                )
                                
                                if vec_86 is not None:
                                    self.seq_2_hands.append(vec_86)
                                    if len(self.seq_2_hands) > 30: self.seq_2_hands.pop(0)
                                    
                                    if len(self.seq_2_hands) == 30 and (self.practice_frame_counter % 5 == 0):
                                        pred_txt, prob = predict_sign(self.lstm_model_2, self.action_labels_2, self.seq_2_hands)
                                        self.cached_predicted_char = pred_txt
                                        
                                        if pred_txt.upper() == current_eval_letter.upper():
                                            self.cached_target_confidence = prob
                                        else:
                                            self.cached_target_confidence = 0.0 if prob > 0.5 else self.cached_target_confidence

                    # --- XUẤT KẾT QUẢ TỪ CACHE RA GIAO DIỆN ---
                    predicted_char = self.cached_predicted_char
                    target_confidence = self.cached_target_confidence

                    if target_confidence > 0.8:
                        ui_color = T.GREEN
                        if not self.lesson_completed:
                            self.success_frames += 1
                            if self.success_frames >= required_frames: 
                                if self.composite_sub_step == 1:
                                    self.composite_sub_step = 2
                                    self.success_frames = 0
                                    self.seq_1_hand.clear(); self.seq_2_hands.clear()
                                    self.prev_wx_l = self.prev_wy_l = self.prev_wx_r = self.prev_wy_r = None
                                    self.cached_predicted_char = ""; self.cached_target_confidence = 0.0

                                    mark_disp = self.get_mark_display_name(self.current_mark_code)
                                    self.target_name_label.configure(text=f"{get_current_target()}  (Bước 2/2: {mark_disp})")
                                    load_practice_media(self.current_mark_code) 
                                    feedback_label.configure(text=f"☆ Chuẩn dáng chữ! Giữ tay và thực hiện [{mark_disp}] nào!", fg_color="#17351F", text_color=T.GREEN)
                                else:
                                    self.lesson_completed = True
                                    record_success(target_confidence)
                    elif target_confidence > 0.4: ui_color = T.YELLOW; self.success_frames = 0 
                    else: ui_color = T.ORANGE; self.success_frames = 0
                    if not hand_detected: ui_color = T.BLUE

                    if predicted_char:
                        display_text = predicted_char
                        if display_text.startswith("DAU_"): display_text = self.get_mark_display_name(display_text).upper()
                        current_sign_label.configure(text=display_text, text_color=ui_color if predicted_char == current_eval_letter else T.ORANGE)
                    else: current_sign_label.configure(text="--", text_color=T.TEXT)
                        
                    if hand_detected:
                        acc_progress.configure(progress_color=ui_color); acc_progress.set(target_confidence)
                        accuracy_value_label.configure(text=f"{int(target_confidence * 100)}%", text_color=ui_color)
                        if not self.lesson_completed and self.composite_sub_step != 2:
                            if target_confidence > 0.8: status_value_label.configure(text="Tuyệt vời!", text_color=ui_color)
                            elif target_confidence > 0.4: status_value_label.configure(text="Gần đúng", text_color=ui_color)
                            else: status_value_label.configure(text="Chưa khớp", text_color=ui_color)
                    else:
                        accuracy_value_label.configure(text="0%", text_color=T.BLUE); acc_progress.set(0)
                        if not self.lesson_completed: status_value_label.configure(text="Đang tìm tay...", text_color=T.BLUE)

                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    scale = min(REACTION_CAMERA_W / w, REACTION_CAMERA_H / h)
                    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                    img = PIL.Image.fromarray(cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA))
                    imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                    self.practice_video_label.configure(image=imgtk, text=""); self.practice_video_label.image = imgtk
            except Exception as e: print("Lỗi khung hình camera:", e)

            if self.practice_camera_on: self.practice_after_id = self.after(15, update_practice_frame)

        def start_practice_camera():
            import cv2, time, threading
            import os
            
            if self.practice_cap: 
                self.practice_cap.release()
                
            # 1. Đổi trạng thái UI ngay lập tức để người dùng không bấm nhiều lần
            toggle_btn.configure(text="⏳ Đang mở...", state="disabled", fg_color=T.MUTED)
            self.practice_status_label.configure(text="● Đang khởi động AI & Camera...", text_color=T.ORANGE)

            # 2. Tách các tác vụ nặng (Nạp AI + Bật Cam) sang luồng phụ để chống đơ UI
            def init_task():
                load_ai_dependencies()
                import cv2
                
                # THUẬT TOÁN TỰ ĐỘNG DÒ TÌM CAMERA (AUTO-FALLBACK)
                cap = None
                for cam_idx in [0, 1, 2]: # Quét các cổng camera 0, 1, 2
                    cap = cv2.VideoCapture(cam_idx) # Thử mở chuẩn cơ bản trước
                    if cap is not None and cap.isOpened(): 
                        break
                    
                    if os.name == "nt": # Nếu thất bại, thử dùng DirectShow trên Windows
                        cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
                        if cap is not None and cap.isOpened(): 
                            break

                if cap is not None and cap.isOpened():
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Gọi lại luồng chính (UI Thread) để cập nhật giao diện sau khi xong
                self.after(0, finish_init, cap, time.time())

            # 3. Hàm hoàn tất, khởi tạo các biến và chạy khung hình
            def finish_init(cap, start_t):
                if not cap.isOpened(): 
                    self.practice_status_label.configure(text="● Lỗi mở camera", text_color=T.RED)
                    toggle_btn.configure(text="▶ Bật Camera", state="normal", fg_color=T.BLUE)
                    return
                
                setup_current_target_ui()
                self.practice_start_time = start_t
                
                # Khởi tạo 2 luồng bám đuổi vector độc lập cho 1 tay và 2 tay
                self.seq_1_hand = []
                self.seq_2_hands = []
                self.prev_wx_l = self.prev_wy_l = None
                self.prev_wx_r = self.prev_wy_r = None
                
                self.practice_frame_counter = 0
                self.cached_predicted_char = ""
                self.cached_target_confidence = 0.0

                self.practice_cap = cap
                self.practice_camera_on = True
                
                self.practice_status_label.configure(text="● Camera đang bật", text_color=T.GREEN)
                toggle_btn.configure(text="■ Tắt Camera", state="normal", fg_color=T.RED)
                update_practice_frame()

            # Chạy luồng phụ
            threading.Thread(target=init_task, daemon=True).start()

        def stop_from_button():
            safe_stop()
            self.seq_1_hand.clear(); self.seq_2_hands.clear()
            self.prev_wx_l = self.prev_wy_l = self.prev_wx_r = self.prev_wy_r = None
            self.cached_predicted_char = ""; self.cached_target_confidence = 0.0

            self.current_target_idx = 0; setup_current_target_ui()
            toggle_btn.configure(text="▶ Bật Camera", fg_color=T.BLUE)
            self.practice_status_label.configure(text="● Camera đang tắt", text_color=T.MUTED)
            status_value_label.configure(text="Đã tắt", text_color=T.MUTED); accuracy_value_label.configure(text="0%", text_color=T.BLUE)
            acc_progress.set(0); current_sign_label.configure(text="--", text_color=T.TEXT)
            from PIL import Image
            blank_img = Image.new('RGB', (10, 10), (8, 12, 17))
            blank_ctk = ctk.CTkImage(light_image=blank_img, dark_image=blank_img, size=(10, 10))
            self.practice_video_label.configure(image=blank_ctk, text="📷\n\nNhấn 'Bật Camera' để bắt đầu"); self.practice_video_label.image = blank_ctk
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
            right_title="Chủ đề phổ biến",
            cta="Bắt đầu học", 
            conversation=True
        )

    def topic_page(self, title, subtitle, items, right_title, cta, conversation=False):
        import math
        
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

        ctk.CTkLabel(header_right, text="☝  💬", font=ctk.CTkFont(size=46), text_color=T.BLUE).pack(anchor="e")

        # --- LƯỚI BÀI HỌC BÊN TRÁI ---
        grid = ctk.CTkFrame(page, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="nsew", padx=(0, 25), pady=(20, 0)) 
        
        page.grid_rowconfigure(2, weight=1)
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)
        for r in range(math.ceil(len(items) / 3)):
            grid.grid_rowconfigure(r, weight=1)

        for idx, it in enumerate(items):
            r, c = divmod(idx, 3)
            self.big_topic_card(grid, r, c, it)

        # --- THẺ CHỦ ĐỀ HÔM NAY BÊN PHẢI ---
        side = ctk.CTkFrame(page, width=330, fg_color="transparent")
        side.grid(row=2, column=1, sticky="nsew", pady=(20, 0)) 
        side.grid_propagate(False)
        
        highlight = ctk.CTkFrame(side, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BLUE)
        highlight.pack(fill="both", expand=True) 
        ctk.CTkLabel(highlight, text=f"★  {right_title}", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(20, 14))
        
        first = items[0]
        color = COLOR_MAP[first.get("color", "blue")]
        top = ctk.CTkFrame(highlight, fg_color=T.CARD, corner_radius=13, border_width=0)
        top.pack(fill="x", padx=18)
        
        self.icon_box(top, first.get("icon", "?"), color, size=62, font_size=22).grid(row=0, column=0, padx=16, pady=16)
        ctk.CTkLabel(top, text=first.get("title", ""), font=ctk.CTkFont(size=19, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="w", pady=0)
        
        if conversation:
            phrases = ["1  Xin chào", "2  Cảm ơn", "3  Tôi", "4  Tên"]
            for phrase in phrases:
                ctk.CTkLabel(highlight, text=phrase, height=38, fg_color=T.CARD, corner_radius=10, anchor="w", font=ctk.CTkFont(size=14), text_color=T.TEXT).pack(fill="x", padx=18, pady=3)
        else:
            ctk.CTkLabel(highlight, text="Bắt đầu ngày mới với những từ\nthông dụng nhất!", justify="left", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=18, pady=(15, 5))
            pb = ctk.CTkProgressBar(highlight, height=7, progress_color=color, fg_color="#2E333A")
            pb.pack(fill="x", padx=18, pady=(8, 10))
            pb.set(first.get("done", 0) / first.get("total", 1))
            
        first_lbl = first.get("first_label", "D") if isinstance(first, dict) else "D"
        ctk.CTkButton(highlight, text=f"▶  {cta}", height=50, fg_color=T.BLUE, command=lambda key=first_lbl: self.show_lesson(key)).pack(side="bottom", fill="x", padx=18, pady=18)

        # --- THANH TỔNG QUAN HỌC TẬP (BÊN TRÁI Ở DƯỚI) ---
        stats_bar = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        stats_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 25), pady=(15, 0))
        
        header_stats = ctk.CTkFrame(stats_bar, fg_color="transparent")
        header_stats.pack(fill="x", padx=20, pady=(12, 6))
        ctk.CTkLabel(header_stats, text="↗", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.BLUE).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(header_stats, text="Tổng quan học tập", font=ctk.CTkFont(size=16, weight="bold"), text_color=T.TEXT).pack(side="left")

        ctk.CTkFrame(stats_bar, height=1, fg_color="#2A3038").pack(fill="x", padx=20, pady=(0, 10))

        kpi_container = ctk.CTkFrame(stats_bar, fg_color="transparent")
        kpi_container.pack(fill="x", expand=True, padx=20, pady=(0, 15))
        kpi_container.grid_columnconfigure((0, 1, 2), weight=1)

        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui, user_db
            user_data = auth_ui.CURRENT_USER or {}
            user_id = user_data.get("id")
            
            if user_id:
                conn = user_db.get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT ISNULL(ThoiGianGiaoTiep, 0) FROM TaiKhoan WHERE ID = ?", (user_id,))
                thoi_gian_phut = cursor.fetchone()[0]
            else:
                thoi_gian_phut = 0
        except Exception:
            thoi_gian_phut = 0
            
        gio = thoi_gian_phut // 60
        phut = thoi_gian_phut % 60
        thoi_gian_str = f"{gio}h {phut}m" if gio > 0 else f"{phut}m"

        total_topics = len(items) if items and items[0].get("title") != "Chưa có dữ liệu" else 0
        completed_topics = sum(1 for it in items if it.get("done", 0) >= it.get("total", 1) and it.get("total", 1) > 0)
        
        # ==========================================================
        # 2 DÒNG BỊ MẤT TÍCH ĐÃ ĐƯỢC PHỤC HỒI:
        # ==========================================================
        total_lessons = sum(it.get("total", 1) for it in items) if total_topics > 0 else 0
        done_lessons = sum(it.get("done", 0) for it in items) if total_topics > 0 else 0

        kpis = [
            ("📗", "Chủ đề hoàn thành", f"{completed_topics} / {total_topics}", T.GREEN),
            ("✅", "Mẫu câu hoàn thành" if conversation else "Bài học hoàn thành", f"{done_lessons} / {total_lessons}", T.PURPLE),
            ("🕘", "Thời gian học", thoi_gian_str, T.BLUE)
        ]

        for i, (icon, label, value, color) in enumerate(kpis):
            cell = ctk.CTkFrame(kpi_container, fg_color="transparent")
            cell.grid(row=0, column=i, sticky="ns") 
            
            ctk.CTkLabel(cell, text=icon, font=ctk.CTkFont(size=26), text_color=color).pack(side="left", padx=(0, 12))
            box = ctk.CTkFrame(cell, fg_color="transparent")
            box.pack(side="left")
            ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(box, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w")

    def big_topic_card(self, parent, row, col, item):
        color = COLOR_MAP[item.get("color", "blue")]
        
        card = ctk.CTkFrame(parent, fg_color=T.CARD, border_width=0, corner_radius=14)
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 16, 0), pady=(0 if row == 0 else 16, 0))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=(18, 0))

        icon_box = self.icon_box(content, item.get("icon", "?"), color, size=55, font_size=22)
        icon_box.pack(side="left", anchor="nw")

        text_box = ctk.CTkFrame(content, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True, padx=(12, 0))

        title_text = item.get("title", "")
        if len(title_text) > 18: title_text = title_text[:15] + "..."
        
        desc_text = item.get("desc", "")
        if len(desc_text) > 42:
            cut = desc_text.rfind(' ', 0, 39)
            if cut == -1: 
                cut = 39
            desc_text = desc_text[:cut] + "..."

        ctk.CTkLabel(text_box, text=title_text, font=ctk.CTkFont(family=T.FONT, size=16, weight="bold"), text_color=T.TEXT, anchor="w", justify="left").pack(fill="x")
        ctk.CTkLabel(text_box, text=desc_text, font=ctk.CTkFont(family=T.FONT, size=12), text_color=T.MUTED, anchor="w", justify="left", wraplength=120).pack(fill="x", pady=(4, 0))

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
        ctk.CTkLabel(stat_row, text="›", font=ctk.CTkFont(size=28), text_color=T.MUTED).pack(side="right")
        
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
        header_right.grid(row=0, column=1, sticky="ne", padx=(20, 60), pady=(0, 10))

        self.back_button(
            header_right,
            command=self.show_home,
            text="←  Trang chính"
        ).pack(anchor="e", pady=(0, 8))

        ctk.CTkLabel(header_right, text="☝  💬", font=ctk.CTkFont(size=46), text_color=T.BLUE).pack(anchor="e")

        # --- GỢI Ý ÔN TẬP ---
        suggestions = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        suggestions.grid(row=1, column=0, sticky="new", padx=(0, 25), pady=(15, 20))
        suggestions.grid_columnconfigure(0, weight=1)
        self.section_header(suggestions, 0, "Gợi ý ôn tập hôm nay", "★", show_all=False)
        
        grid = ctk.CTkFrame(suggestions, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        for c in range(2): 
            grid.grid_columnconfigure(c, weight=1)
            
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui
            learned_count = len(auth_ui.LEARNED_LETTERS) if auth_ui.CURRENT_USER else 0
        except Exception:
            learned_count = 0

        # ==========================================
        # BÍ KÍP 1: TÁCH BẢN SAO DỮ LIỆU VÀ "HÔ BIẾN" THẺ BỊ TRÙNG LẶP
        # ==========================================
        import copy
        display_cards = copy.deepcopy(REVIEW_CARDS)

        for i, it in enumerate(display_cards):
            r, c = divmod(i, 2)
            if it.get("title") == "Các chữ hay nhầm":
                it["count"] = f"{len(CONFUSED_PAIRS_DATA)} cặp chữ"
            elif it.get("title") == "Từ đã học gần đây":
                it["count"] = f"{learned_count} từ"
            elif "phản xạ" in it.get("title", "").lower():
                total_reaction = learned_count if learned_count > 0 else len(ALPHABET or [])
                it["count"] = f"{min(10, max(1, total_reaction))} lượt"
            # Chặn đứng sự dư thừa: Đổi thẻ "Kiểm tra nhanh" thành "Ký hiệu cần chú ý"
            elif "kiểm tra" in it.get("title", "").lower():
                it["title"] = "Ký hiệu cần chú ý"
                it["desc"] = "Khắc phục các ký hiệu bạn làm sai nhiều nhất"
                it["icon"] = "🎯"
                it["color"] = "red"  # Đổi sang màu đỏ cảnh báo
                it["count"] = "Phân tích AI"
                
            self.review_suggestion(grid, r, c, it)

        # --- KHUNG CHỨA CỘT PHẢI ---
        # --- KHUNG CHỨA CỘT PHẢI ---
        right_container = ctk.CTkFrame(page, width=330, fg_color="transparent")
        # BÍ KÍP 1: Dùng sticky="nsew" và pady=(15, 20) để khung này có chiều cao bằng đúng khung bên trái
        right_container.grid(row=1, column=1, sticky="nsew", pady=(15, 20))
        
        # (ĐÃ XÓA KHUNG "PHÂN TÍCH TỪ AI HỆ THỐNG" ĐỂ TRÁNH DƯ THỪA)

        challenge = ctk.CTkFrame(right_container, width=330, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        # BÍ KÍP 2: Dùng fill="both", expand=True để Bài Test giãn ra lấp đầy toàn bộ cột phải
        challenge.pack(fill="both", expand=True)
        
        ctk.CTkLabel(challenge, text="⚡  Bài test hôm nay", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=22, pady=(20, 5))
        
        center_box = ctk.CTkFrame(challenge, fg_color="transparent")
        # Căn giữa nội dung bên trong bề mặt đã được kéo giãn
        center_box.pack(fill="both", expand=True)
        
        # Tăng một chút padding (pady) để nội dung đẩy ra giữa đẹp mắt hơn
        ctk.CTkLabel(center_box, text="🏆", font=ctk.CTkFont(size=85)).pack(pady=(45, 15))
        ctk.CTkLabel(center_box, text="Kiểm tra năng lực", font=ctk.CTkFont(size=19, weight="bold"), text_color=T.BLUE).pack()
        ctk.CTkLabel(center_box, text="Hệ thống sẽ chọn ngẫu nhiên 10 câu\ntừ các chủ đề để đánh giá trình độ.", text_color=T.MUTED, font=ctk.CTkFont(size=14), justify="center", wraplength=280).pack(pady=(10, 20))
        
        ctk.CTkButton(challenge, text="▶  Bắt đầu thi", height=48, font=ctk.CTkFont(size=14, weight="bold"), fg_color=T.BLUE, hover_color=T.BLUE_DARK, command=self.show_quick_quiz).pack(fill="x", padx=20, pady=(0, 20))

        # (Tìm đoạn này ở phần cuối của show_review)
        try:
            import auth_ui, user_db
            user_data = auth_ui.CURRENT_USER or {}
            user_id = user_data.get("id")
            
            if user_id:
                stats_row = user_db.get_user_minigame_stats(user_id) or {}
                do_chinh_xac = stats_row.get("DoChinhXacTB", 0)
                chuoi_ngay = stats_row.get("ChuoiNgayHoc", 0)
                
                conn = user_db.get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT ISNULL(ThoiGianGiaoTiep, 0) FROM TaiKhoan WHERE ID = ?", (user_id,))
                thoi_gian_phut = cursor.fetchone()[0]
            else:
                do_chinh_xac, chuoi_ngay, thoi_gian_phut = 0, 0, 0
        except Exception:
            do_chinh_xac, chuoi_ngay, thoi_gian_phut = 0, 0, 0
            
        gio = thoi_gian_phut // 60
        phut = thoi_gian_phut % 60
        thoi_gian_str = f"{gio}h {phut}m" if gio > 0 else f"{phut}m"

        # --- BẢNG THỐNG KÊ TRÀN VIỀN ---
        stats = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        stats.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 0), pady=(0, 20))
        stats.grid_columnconfigure((0, 1, 2), weight=1)
        
        for i, (icon, label, value, sub, color) in enumerate([
            ("🎯", "Độ chính xác TB", f"{do_chinh_xac}%", "Trung bình các bài luyện tập", T.GREEN),
            ("📅", "Chuỗi ngày học", f"{chuoi_ngay} ngày", "Cố gắng duy trì mỗi ngày! 🔥" if chuoi_ngay > 0 else "Hãy bắt đầu ngay!", T.GREEN),
            ("🕘", "Tổng thời gian học", thoi_gian_str, "Tổng thời gian thực hành", T.BLUE),
        ]):
            cell = ctk.CTkFrame(stats, fg_color="transparent")
            cell.grid(row=0, column=i, sticky="nsew", padx=20, pady=20)
            ctk.CTkLabel(cell, text=icon, font=ctk.CTkFont(size=32), text_color=color).pack(side="left", padx=(0, 14))
            box = ctk.CTkFrame(cell, fg_color="transparent")
            box.pack(side="left")
            ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=15, weight="bold"), text_color=T.TEXT).pack(anchor="w")
            ctk.CTkLabel(box, text=value, font=ctk.CTkFont(size=27, weight="bold"), text_color=color).pack(anchor="w")
            ctk.CTkLabel(box, text=sub, font=ctk.CTkFont(size=12), text_color=T.MUTED).pack(anchor="w")
    def review_suggestion(self, parent, row, col, it):
        color = COLOR_MAP[it["color"]]
        card = ctk.CTkFrame(parent, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        pad_x = (0 if col == 0 else 14, 0)
        pad_y = (0 if row == 0 else 14, 0)
        card.grid(row=row, column=col, sticky="nsew", padx=pad_x, pady=pad_y)
        
        ctk.CTkLabel(card, text=it["icon"], width=50, height=50, fg_color=color, corner_radius=25, font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(18, 8))
        ctk.CTkLabel(card, text=it["title"], font=ctk.CTkFont(size=16, weight="bold"), text_color=T.TEXT, wraplength=220, justify="left").pack(anchor="w", padx=18)
        ctk.CTkLabel(card, text=it["desc"], wraplength=220, justify="left", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w", padx=18, pady=(5, 12))
        ctk.CTkLabel(card, text=it["count"], fg_color="#132033", corner_radius=7, text_color=color, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=18, pady=(0, 18))

        def on_click(e):
            if it["title"] == "Các chữ hay nhầm":
                self.show_confused_letters()
            elif it["title"] == "Từ đã học gần đây":
                self.show_recent_words()
            # ==========================================
            # BÍ KÍP 3: GỌI HÀM XỬ LÝ GIAO DIỆN TRUNG GIAN
            # ==========================================
            elif it["title"] == "Ký hiệu cần chú ý":
                self.show_weak_signs()
            elif "phản xạ" in it["title"].lower():
                self.show_reaction_training()
            elif "kiểm tra" in it["title"].lower():
                self.show_quick_quiz()
            else:
                messagebox.showinfo("Đang phát triển", f"Tính năng {it['title']} sẽ được cập nhật ở phiên bản sau.")
                
        card.bind("<Button-1>", on_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)
    def show_confused_letters(self):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        
        self._title(page, "CÁC CHỮ HAY NHẦM", "Phân biệt các cặp ký hiệu có hình dáng tương đồng")

        header_right = ctk.CTkFrame(page, fg_color="transparent")
        header_right.grid(row=0, column=1, sticky="ne", padx=(20, 60), pady=(0, 10))
        self.back_button(header_right, command=self.show_review, text="←  Trở về").pack(anchor="e", pady=(0, 8))

        # Khung chứa danh sách lưới
        main = ctk.CTkFrame(page, fg_color="transparent")
        main.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 25), pady=(20, 0))
        for c in range(2): 
            main.grid_columnconfigure(c, weight=1)

        # Dữ liệu Mock mô phỏng các chữ hay nhầm
        confused_pairs = [
            ("A", "Ă", "Khác biệt ở chuyển động vẫy cổ tay nhẹ."),
            ("C", "G", "Độ mở của ngón cái và ngón trỏ khác nhau."),
            ("D", "Đ", "Chữ Đ có thêm chuyển động gập ngón trỏ hai lần."),
            ("U", "Ư", "Chữ Ư có thêm ngón cái chĩa ra tạo dấu móc."),
            ("O", "Ô", "Khác biệt ở thao tác vẽ thêm dấu mũ (di chuyển xuống)."),
            ("E", "Ê", "Giữ nguyên hình tay, chỉ vẽ thêm dấu mũ.")
        ]

        # Quét trực tiếp từ nguồn dữ liệu thật thay vì tạo mới
        for i, (l1, l2, desc) in enumerate(CONFUSED_PAIRS_DATA):
            r, c = divmod(i, 2)
            self.confused_pair_card(main, r, c, l1, l2, desc)

    def confused_pair_card(self, parent, row, col, l1, l2, desc):
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        # Giữ khoảng cách chuẩn: cách đều nhau 20px
        pad_x = (0 if col == 0 else 20, 0)
        card.grid(row=row, column=col, sticky="nsew", padx=pad_x, pady=(0, 20))
        
        # Tiêu đề card
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text=f"Phân biệt {l1} và {l2}", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(side="left")
        
        # Khung chứa 2 ảnh đặt cạnh nhau
        img_container = ctk.CTkFrame(card, fg_color="transparent")
        img_container.pack(fill="x", padx=20, pady=(5, 10))
        img_container.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Ảnh 1 (Bên trái)
        l1_lesson = self.get_lesson(l1)
        left_img = self.create_lesson_image_label(img_container, l1_lesson, size=(100, 100), height=130, fallback_font_size=60)
        left_img.configure(fg_color="#0E1722", corner_radius=12)
        left_img.grid(row=0, column=0, sticky="ew")
        
        # Chữ VS ở giữa
        ctk.CTkLabel(img_container, text="↔", font=ctk.CTkFont(size=32, weight="bold"), text_color=T.MUTED).grid(row=0, column=1)
        
        # Ảnh 2 (Bên phải)
        l2_lesson = self.get_lesson(l2)
        right_img = self.create_lesson_image_label(img_container, l2_lesson, size=(100, 100), height=130, fallback_font_size=60)
        right_img.configure(fg_color="#0E1722", corner_radius=12)
        right_img.grid(row=0, column=2, sticky="ew")
        
        # Chú thích điểm khác biệt
        ctk.CTkLabel(card, text=desc, text_color=T.MUTED, font=ctk.CTkFont(size=14), wraplength=280, justify="left").pack(anchor="w", padx=20, pady=(5, 15))
        
        # Nút hành động
        # Nút hành động
        btn = ctk.CTkButton(card, text="▶ Luyện tập cặp này", font=ctk.CTkFont(size=14, weight="bold"), fg_color=T.BLUE, hover_color=T.BLUE_DARK, height=44)
        
        # BÍ KÍP 1: Truyền hẳn 1 danh sách (list) chứa 2 chữ cái vào tham số pair_list
        btn.configure(command=lambda: self.show_camera_practice(pair_list=[l1, l2])) 
        
        btn.pack(fill="x", padx=20, pady=(0, 20))
    def show_recent_words(self):
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        # ==========================================
        # BÍ KÍP FIX LỖI 1: Tự động dùng thuật toán thông minh nhất để cập nhật Sidebar
        # ==========================================
        self.refresh_account_button()
        
        is_logged_in = False
        learned = []
        
        # ==========================================
        # BÍ KÍP FIX LỖI 2: Truy tìm đúng module auth_ui đang giữ thông tin người dùng
        # ==========================================
        auth_module = None
        for name, module in list(sys.modules.items()):
            if name == "auth_ui" or name.endswith(".auth_ui"):
                if getattr(module, "CURRENT_USER", None):
                    auth_module = module
                    break
                    
        # Nếu chưa có thì fallback về import thông thường
        if auth_module is None:
            try:
                import auth_ui
                auth_module = auth_ui
            except Exception:
                pass

        # Lấy dữ liệu thật
        if auth_module and getattr(auth_module, "CURRENT_USER", None):
            is_logged_in = True
            learned = getattr(auth_module, "LEARNED_LETTERS", [])

        # --- GIAO DIỆN CHÍNH ---
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        
        self._title(page, "TỪ ĐÃ HỌC GẦN ĐÂY", "Ôn tập lại các ký hiệu bạn vừa hoàn thành")

        header_right = ctk.CTkFrame(page, fg_color="transparent")
        header_right.grid(row=0, column=1, sticky="ne", padx=(20, 60), pady=(0, 10))
        self.back_button(header_right, command=self.show_review, text="←  Trở về").pack(anchor="e", pady=(0, 8))

        main = ctk.CTkFrame(page, fg_color="transparent")
        main.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 25), pady=(20, 0))
        
        # BÍ KÍP 3: Xử lý giao diện cho trạng thái CHƯA ĐĂNG NHẬP
        # BÍ KÍP 3: Xử lý giao diện cho trạng thái CHƯA ĐĂNG NHẬP
        if not is_logged_in:
            empty_panel = ctk.CTkFrame(
                main,
                fg_color=T.PANEL,
                corner_radius=16,
                border_width=1,
                border_color=T.BORDER
            )
            empty_panel.pack(fill="x", pady=20)

            ctk.CTkLabel(
                empty_panel,
                text="🔒",
                font=ctk.CTkFont(size=70)
            ).pack(pady=(50, 15))

            ctk.CTkLabel(
                empty_panel,
                text="Vui lòng đăng nhập",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=T.TEXT
            ).pack()

            ctk.CTkLabel(
                empty_panel,
                text="Hệ thống cần xác thực tài khoản để lấy dữ liệu lịch sử học tập của bạn.",
                text_color=T.MUTED,
                font=ctk.CTkFont(size=14)
            ).pack(pady=(10, 25))

            def do_login():
                self.show_auth_panel(return_page=self.show_recent_words)

            ctk.CTkButton(
                empty_panel,
                text="Đăng nhập ngay",
                font=ctk.CTkFont(size=15, weight="bold"),
                fg_color=T.BLUE,
                hover_color=T.BLUE_DARK,
                height=45,
                command=do_login
            ).pack(pady=(0, 50))

            return

        # BÍ KÍP 4: Xử lý giao diện cho trạng thái CHƯA HỌC TỪ NÀO
        if not learned:
            empty_panel = ctk.CTkFrame(main, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
            empty_panel.pack(fill="x", pady=20)
            ctk.CTkLabel(empty_panel, text="📭", font=ctk.CTkFont(size=70)).pack(pady=(50, 15))
            ctk.CTkLabel(empty_panel, text="Chưa có dữ liệu", font=ctk.CTkFont(size=22, weight="bold"), text_color=T.TEXT).pack()
            ctk.CTkLabel(empty_panel, text="Bạn chưa hoàn thành bài học nào. Hãy quay lại Bảng chữ cái để bắt đầu nhé!", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(pady=(10, 25))
            ctk.CTkButton(empty_panel, text="Đến Bảng chữ cái", font=ctk.CTkFont(size=15, weight="bold"), fg_color=T.BLUE, height=45, command=self.show_alphabet).pack(pady=(0, 50))
            return

        # Xử lý Logic Hiển thị danh sách từ đã học
        recent_words = learned.copy()
        recent_words.reverse() # Lật ngược mảng để từ mới học nằm trên cùng
        
        # Thanh Công cụ (Action Bar)
        action_bar = ctk.CTkFrame(main, fg_color="transparent")
        action_bar.pack(fill="x", pady=(0, 25))
        
        top_5 = recent_words[:5]
        btn_text = f"▶ Ôn tập {len(top_5)} từ gần nhất"
        
        # BÍ KÍP 3: Bơm định tuyến (back_cmd) cho luồng học liên hoàn
        ctk.CTkButton(action_bar, text=btn_text, font=ctk.CTkFont(size=15, weight="bold"), height=45, fg_color=T.BLUE, hover_color=T.BLUE_DARK, command=lambda: self.show_camera_practice(pair_list=top_5, back_cmd=self.show_recent_words)).pack(side="left")
        
        ctk.CTkLabel(action_bar, text=f"Tổng cộng: {len(recent_words)} từ đã học", font=ctk.CTkFont(size=14, weight="bold"), text_color=T.GREEN).pack(side="right", pady=10)

        # Vẽ lưới (Grid) 4 cột để chứa thẻ từ vựng
        grid = ctk.CTkFrame(main, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        for c in range(4):
            grid.grid_columnconfigure(c, weight=1)

        for i, letter in enumerate(recent_words):
            r, c = divmod(i, 4)
            self.recent_word_card(grid, r, c, letter)

    def recent_word_card(self, parent, row, col, letter):
        lesson = self.get_lesson(letter)
        card = ctk.CTkFrame(parent, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 16, 0), pady=(0 if row == 0 else 16, 0))
        
        img_container = ctk.CTkFrame(card, fg_color="transparent")
        img_container.pack(fill="x", padx=16, pady=(16, 5))
        
        img_label = self.create_lesson_image_label(img_container, lesson, size=(120, 120), height=130, fallback_font_size=60)
        img_label.configure(fg_color="#0B1520", corner_radius=12)
        img_label.pack(fill="x")
        
        title_text = self.lesson_title_text(lesson)
        ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(size=17, weight="bold"), text_color=T.TEXT).pack(pady=(10, 0))
        
        # BÍ KÍP 4: Bơm định tuyến (back_cmd) cho luồng học từ đơn lẻ
        btn = ctk.CTkButton(card, text="▶ Ôn lại", font=ctk.CTkFont(weight="bold"), height=38, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, hover_color=T.CARD_HOVER, text_color=T.BLUE, command=lambda: self.show_camera_practice(letter, back_cmd=self.show_recent_words))
        btn.pack(fill="x", padx=16, pady=(12, 16))
    def show_reaction_training(self):
        """Luyện phản xạ: Đập đi xây lại - Đồng bộ, Ổn định và An toàn tuyệt đối."""
        import os
        import random
        import sys
        import time
        from tkinter import messagebox
        import customtkinter as ctk

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        self.refresh_account_button()

        # ---------- 1) NẠP DỮ LIỆU TÀI KHOẢN ----------
        auth_module = None
        for name, module in list(sys.modules.items()):
            if name == "auth_ui" or name.endswith(".auth_ui"):
                auth_module = module
                break

        if auth_module is None:
            try:
                import auth_ui
                auth_module = auth_ui
            except Exception:
                auth_module = None

        is_logged_in = bool(auth_module and getattr(auth_module, "CURRENT_USER", None))
        learned = list(getattr(auth_module, "LEARNED_LETTERS", []) or []) if auth_module else []

        # Chuẩn bị kho dữ liệu (Pool)
        all_signs = []
        for item in ALPHABET or []:
            val = item.get("label") or item.get("title") if isinstance(item, dict) else item
            val = str(val or "").replace("Chữ ", "", 1).strip().upper()
            if val and val not in all_signs and not val.startswith("DAU_"):
                all_signs.append(val)

        if not all_signs:
            all_signs = ["A", "B", "C", "D", "Đ", "E", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "X", "Y"]

        clean_learned = [str(v or "").replace("Chữ ", "", 1).strip().upper() for v in learned if not str(v).startswith("DAU_")]
        pool = clean_learned[:] if clean_learned else all_signs[:]
        random.shuffle(pool)

        if len(pool) < 10:
            extra = [x for x in all_signs if x not in pool]
            random.shuffle(extra)
            pool.extend(extra[:10 - len(pool)])

        targets = pool[:min(10, len(pool))]

        if not targets:
            messagebox.showinfo("Luyện phản xạ", "Chưa có dữ liệu ký hiệu để luyện tập.")
            return

        # ---------- 2) KHAI BÁO BIẾN TRẠNG THÁI ----------
        self.reaction_targets = targets
        self.reaction_results = []
        self.reaction_index = 0
        self.reaction_round_started = False
        self.reaction_round_start = None
        self.reaction_session_start = time.time()
        self.reaction_time_limit = 4.0
        self.reaction_success_frames = 0
        self.reaction_best_confidence = 0.0

        self.sequence_data = []
        self.seq_1_hand = []
        self.seq_2_hands = []
        self.prev_wx_l = self.prev_wy_l = self.prev_wx_r = self.prev_wy_r = None
        
        self.practice_frame_counter = 0
        self.cached_predicted_char = ""
        self.cached_target_confidence = 0.0

        # ---------- 3) DỰNG GIAO DIỆN (UI) ----------
        page = self._clear_page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(page, fg_color=T.BG)
        wrapper.pack(fill="both", expand=True, padx=30, pady=30)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        self._title(title_box, "LUYỆN PHẢN XẠ", f"Thực hiện nhanh {len(targets)} ký hiệu trước camera")

        def safe_stop():
            self.practice_camera_on = False
            if hasattr(self, 'practice_after_id') and self.practice_after_id:
                try: self.after_cancel(self.practice_after_id)
                except Exception: pass
                self.practice_after_id = None
            if hasattr(self, 'practice_cap') and self.practice_cap:
                try: self.practice_cap.release()
                except Exception: pass
                self.practice_cap = None

        def go_back():
            safe_stop()
            self.show_review()

        self.back_button(header, command=go_back, text="←  Trở về").pack(side="right", anchor="n", pady=6)

        body = ctk.CTkFrame(wrapper, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # -- KHU VỰC CAMERA --
        left_frame = ctk.CTkFrame(body, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        left_frame.pack(side="left", fill="both", expand=True)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        cam_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        cam_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=15)

        self.practice_status_label = ctk.CTkLabel(cam_bar, text="● Camera đang tắt", fg_color="#2A2F35", corner_radius=8, text_color=T.MUTED, font=ctk.CTkFont(size=13, weight="bold"), padx=12, pady=6)
        self.practice_status_label.pack(side="left")

        ctk.CTkLabel(cam_bar, text="Mẹo: đưa tay vào khung, làm đúng và giữ ổn định thật nhanh.", text_color=T.MUTED, font=ctk.CTkFont(size=13)).pack(side="right")

        camera_view = ctk.CTkFrame(left_frame, width=720, height=430, fg_color="#080C11", corner_radius=12)
        camera_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        camera_view.grid_propagate(False)
        camera_view.grid_rowconfigure(0, weight=1); camera_view.grid_columnconfigure(0, weight=1)

        self.practice_video_label = ctk.CTkLabel(camera_view, text="⚡\n\nNhấn 'Bắt đầu phản xạ' để mở camera", font=ctk.CTkFont(size=22, weight="bold"), text_color=T.MUTED_2)
        self.practice_video_label.grid(row=0, column=0, sticky="nsew")

        # -- KHU VỰC THỬ THÁCH (BÊN PHẢI) --
        right_frame = ctk.CTkFrame(body, fg_color="transparent", width=430)
        right_frame.pack(side="right", fill="y", padx=(25, 0))
        right_frame.pack_propagate(False)

        target_panel = ctk.CTkFrame(right_frame, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        target_panel.pack(fill="x", pady=(0, 15))

        top_row = ctk.CTkFrame(target_panel, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(18, 8))

        self.reaction_question_label = ctk.CTkLabel(top_row, text=f"0 / {len(targets)}", font=ctk.CTkFont(size=14, weight="bold"), text_color=T.MUTED)
        self.reaction_question_label.pack(side="left")

        self.reaction_score_label = ctk.CTkLabel(top_row, text="Đúng: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=T.GREEN)
        self.reaction_score_label.pack(side="right")

        ctk.CTkLabel(target_panel, text="Ký hiệu cần làm", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(pady=(4, 2))
        self.reaction_target_label = ctk.CTkLabel(target_panel, text="Sẵn sàng", font=ctk.CTkFont(size=28, weight="bold"), text_color=T.MUTED)
        self.reaction_target_label.pack(pady=(0, 10))

        self.reaction_img_box = ctk.CTkFrame(target_panel, fg_color="transparent")
        self.reaction_img_box.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(self.reaction_img_box, text="⚡\nChờ bắt đầu", height=130, fg_color="#0E1722", corner_radius=14, font=ctk.CTkFont(size=18, weight="bold"), text_color=T.MUTED).pack(fill="x")

        self.reaction_timer_label = ctk.CTkLabel(target_panel, text="--", font=ctk.CTkFont(size=22, weight="bold"), text_color=T.MUTED)
        self.reaction_timer_label.pack(pady=(0, 8))

        self.reaction_timer_bar = ctk.CTkProgressBar(target_panel, height=9, progress_color=T.BLUE, fg_color="#2A3038")
        self.reaction_timer_bar.pack(fill="x", padx=20, pady=(0, 20))
        self.reaction_timer_bar.set(0)

        feedback_panel = ctk.CTkFrame(right_frame, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        feedback_panel.pack(fill="x", pady=(0, 15))

        row_pred = ctk.CTkFrame(feedback_panel, fg_color="transparent")
        row_pred.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(row_pred, text="Bạn đang làm:", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.TEXT).pack(side="left")
        self.reaction_pred_label = ctk.CTkLabel(row_pred, text="--", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.TEXT)
        self.reaction_pred_label.pack(side="right")

        row_conf = ctk.CTkFrame(feedback_panel, fg_color="transparent")
        row_conf.pack(fill="x", padx=20, pady=(4, 8))
        ctk.CTkLabel(row_conf, text="Độ khớp:", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.TEXT).pack(side="left")
        self.reaction_conf_label = ctk.CTkLabel(row_conf, text="0%", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.BLUE)
        self.reaction_conf_label.pack(side="right")

        self.reaction_conf_bar = ctk.CTkProgressBar(feedback_panel, height=8, progress_color=T.BLUE, fg_color="#2A3038")
        self.reaction_conf_bar.pack(fill="x", padx=20, pady=(0, 14))
        self.reaction_conf_bar.set(0)

        self.reaction_feedback_label = ctk.CTkLabel(feedback_panel, text="☆ Sẵn sàng chưa? Nhấn bắt đầu để luyện phản xạ.", fg_color="#2A2F35", corner_radius=8, height=45, text_color=T.MUTED, font=ctk.CTkFont(size=13), wraplength=350)
        self.reaction_feedback_label.pack(fill="x", padx=20, pady=(0, 18))

        control_bar = ctk.CTkFrame(wrapper, fg_color=T.PANEL, corner_radius=18, border_width=1, border_color=T.BORDER)
        control_bar.pack(side="bottom", fill="x", pady=(18, 0))
        control_bar.grid_columnconfigure(0, weight=1); control_bar.grid_columnconfigure(1, weight=0)

        control_left = ctk.CTkFrame(control_bar, fg_color="transparent")
        control_left.grid(row=0, column=0, sticky="ew", padx=22, pady=16)
        ctk.CTkLabel(control_left, text="⚡  Sẵn sàng luyện phản xạ?", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w")
        ctk.CTkLabel(control_left, text="Bấm bắt đầu → đếm ngược 3 giây → hiện ký hiệu bất ngờ. Cần làm đúng trước khi hết 4 giây.", font=ctk.CTkFont(size=13), text_color=T.MUTED, wraplength=760, justify="left").pack(anchor="w", pady=(5, 0))

        start_btn = ctk.CTkButton(control_bar, text="▶  Bắt đầu phản xạ", width=230, height=58, fg_color=T.ORANGE, hover_color="#D98200", font=ctk.CTkFont(size=18, weight="bold"), corner_radius=16)
        start_btn.grid(row=0, column=1, sticky="e", padx=22, pady=16)

        # ---------- 4) CÁC HÀM CẬP NHẬT UI TRUNG GIAN ----------
        def set_waiting_target_ui(message="Chờ bắt đầu"):
            for child in self.reaction_img_box.winfo_children(): child.destroy()
            ctk.CTkLabel(self.reaction_img_box, text=f"⚡\n{message}", height=105, fg_color="#0E1722", corner_radius=14, font=ctk.CTkFont(size=18, weight="bold"), text_color=T.MUTED).pack(fill="x")
            self.reaction_target_label.configure(text="Sẵn sàng", text_color=T.MUTED)
            self.reaction_timer_label.configure(text="--", text_color=T.MUTED)
            self.reaction_timer_bar.configure(progress_color=T.BLUE); self.reaction_timer_bar.set(0)
            self.reaction_pred_label.configure(text="--", text_color=T.TEXT)
            self.reaction_conf_label.configure(text="0%", text_color=T.BLUE)
            self.reaction_conf_bar.configure(progress_color=T.BLUE); self.reaction_conf_bar.set(0)

        def reset_ui_to_idle():
            safe_stop()
            start_btn.configure(text="▶  Bắt đầu phản xạ", state="normal", fg_color=T.ORANGE, hover_color="#D98200")
            self.practice_status_label.configure(text="● Camera đang tắt", text_color=T.MUTED, fg_color="#2A2F35")
            set_waiting_target_ui("Chờ bắt đầu")

        def stop_reaction_training():
            reset_ui_to_idle()
            self.reaction_round_started = False
            self.reaction_results.clear()
            self.reaction_index = 0
            from PIL import Image
            blank_img = Image.new('RGB', (10, 10), (8, 12, 17))
            blank_ctk = ctk.CTkImage(light_image=blank_img, dark_image=blank_img, size=(10, 10))
            self.practice_video_label.configure(image=blank_ctk, text="⚡\n\nNhấn 'Bắt đầu phản xạ' để mở camera")
            self.practice_video_label.image = blank_ctk

        def render_target_preview():
            for child in self.reaction_img_box.winfo_children(): child.destroy()
            target = self.reaction_targets[self.reaction_index]
            composite_map = {"Ă": "DAU_A", "Â": "DAU_MU", "Ê": "DAU_MU", "Ô": "DAU_MU", "Ơ": "DAU_MOC", "Ư": "DAU_MOC"}

            if target in composite_map:
                row = ctk.CTkFrame(self.reaction_img_box, fg_color="transparent")
                row.pack(anchor="center")
                base = self.create_lesson_image_label(row, self.get_lesson(target), size=(95, 95), height=105, fallback_font_size=52)
                base.configure(fg_color="#0E1722", corner_radius=12); base.pack(side="left", padx=6)
                mark = self.create_lesson_image_label(row, {"label": composite_map[target]}, size=(95, 95), height=105, fallback_font_size=52)
                mark.configure(fg_color="#0E1722", corner_radius=12); mark.pack(side="left", padx=6)
            else:
                img = self.create_lesson_image_label(self.reaction_img_box, self.get_lesson(target), size=(95, 95), height=130, fallback_font_size=70)
                img.configure(fg_color="#0E1722", corner_radius=14); img.pack(fill="x")

        def begin_start_countdown(number=3):
            if not self.practice_camera_on: return
            if number <= 0:
                start_round()
                return
            for child in self.reaction_img_box.winfo_children(): child.destroy()
            ctk.CTkLabel(self.reaction_img_box, text=str(number), height=105, fg_color="#0E1722", corner_radius=14, font=ctk.CTkFont(size=60, weight="bold"), text_color=T.ORANGE).pack(fill="x")
            self.reaction_target_label.configure(text="Chuẩn bị", text_color=T.ORANGE)
            self.reaction_timer_label.configure(text=str(number), text_color=T.ORANGE)
            self.reaction_timer_bar.configure(progress_color=T.ORANGE); self.reaction_timer_bar.set(number / 3)
            self.reaction_feedback_label.configure(text="☆ Chuẩn bị nhìn ký hiệu và làm thật nhanh!", fg_color="#332200", text_color=T.ORANGE)
            self.after(1000, lambda: begin_start_countdown(number - 1))

        # ---------- 5) CORE LOGIC CỦA GAME (AI & VÒNG LẶP) ----------
        def hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy):
            import numpy as np
            wx, wy = landmarks[0].x, landmarks[0].y
            vector = []
            for i in range(1, 21): vector.extend([landmarks[i].x - wx, landmarks[i].y - wy])
            delta_x = 0.0 if prev_wx is None else (wx - prev_wx) * 30
            delta_y = 0.0 if prev_wy is None else (wy - prev_wy) * 30
            if abs(delta_x) < 0.24: delta_x = 0.0
            if abs(delta_y) < 0.24: delta_y = 0.0
            vector.extend([hand_type, delta_x, delta_y])
            return np.array(vector), wx, wy

        def update_reaction_frame():
            if not self.practice_camera_on or self.practice_cap is None: return

            try:
                success, frame = self.practice_cap.read()
                if success:
                    self.practice_frame_counter += 1
                    import cv2, numpy as np, mediapipe as mp, PIL.Image
                    frame = cv2.flip(frame, 1); h, w = frame.shape[:2]
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    hand_detected = False
                    current_target = self.reaction_targets[self.reaction_index] if self.reaction_index < len(self.reaction_targets) else ""

                    if getattr(self, 'mp_hands', None) is not None:
                        results = self.mp_hands.process(frame_rgb)
                        hands_detected = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0

                        if hands_detected > 0:
                            hand_detected = True
                            for hl in results.multi_hand_landmarks:
                                self.mp_draw.draw_landmarks(frame, hl, mp.solutions.hands.HAND_CONNECTIONS)
                            
                            try:
                                from core.train_window_both import extract_86_features
                                from core.translate_window import predict_sign
                            except Exception: pass

                            # LUỒNG 1 TAY
                            if hands_detected == 1 and getattr(self, 'lstm_model_1', None):
                                self.seq_2_hands.clear()
                                handedness = results.multi_handedness[0]
                                hand_type = 0 if handedness.classification[0].label == "Left" else 1
                                vec_43, self.prev_wx_l, self.prev_wy_l = hand_vectorlize(results.multi_hand_landmarks[0].landmark, hand_type, self.prev_wx_l, self.prev_wy_l)
                                self.seq_1_hand.append(vec_43)
                                if len(self.seq_1_hand) > 30: self.seq_1_hand.pop(0)
                                if len(self.seq_1_hand) == 30 and (self.practice_frame_counter % 3 == 0):
                                    pred_txt, prob = predict_sign(self.lstm_model_1, self.action_labels_1, self.seq_1_hand)
                                    self.cached_predicted_char = pred_txt
                                    self.cached_target_confidence = prob if pred_txt.upper() == current_target.upper() else (0.0 if prob > 0.5 else self.cached_target_confidence)

                            # LUỒNG 2 TAY
                            elif hands_detected == 2 and getattr(self, 'lstm_model_2', None):
                                self.seq_1_hand.clear()
                                vec_86, self.prev_wx_l, self.prev_wy_l, self.prev_wx_r, self.prev_wy_r = extract_86_features(results, self.prev_wx_l, self.prev_wy_l, self.prev_wx_r, self.prev_wy_r)
                                if vec_86 is not None:
                                    self.seq_2_hands.append(vec_86)
                                    if len(self.seq_2_hands) > 30: self.seq_2_hands.pop(0)
                                    if len(self.seq_2_hands) == 30 and (self.practice_frame_counter % 3 == 0):
                                        pred_txt, prob = predict_sign(self.lstm_model_2, self.action_labels_2, self.seq_2_hands)
                                        self.cached_predicted_char = pred_txt
                                        self.cached_target_confidence = prob if pred_txt.upper() == current_target.upper() else (0.0 if prob > 0.5 else self.cached_target_confidence)
                        else:
                            self.seq_1_hand.clear(); self.seq_2_hands.clear()
                            self.prev_wx_l = self.prev_wy_l = self.prev_wx_r = self.prev_wy_r = None

                    # KIỂM TRA ĐIỀU KIỆN THẮNG/THUA TRONG VÒNG LẶP
                    if not self.reaction_round_started:
                        self.cached_target_confidence = 0.0
                        self.cached_predicted_char = ""
                        self.reaction_success_frames = 0
                    else:
                        if self.cached_target_confidence > self.reaction_best_confidence:
                            self.reaction_best_confidence = self.cached_target_confidence

                    if hand_detected:
                        if self.cached_target_confidence >= 0.8: ui_color = T.GREEN; bgr_color = (0, 200, 0); self.reaction_success_frames += 1
                        elif self.cached_target_confidence >= 0.4: ui_color = T.YELLOW; bgr_color = (0, 215, 255); self.reaction_success_frames = 0
                        else: ui_color = T.ORANGE; bgr_color = (0, 140, 255); self.reaction_success_frames = 0

                        self.reaction_conf_bar.configure(progress_color=ui_color); self.reaction_conf_bar.set(self.cached_target_confidence)
                        self.reaction_conf_label.configure(text=f"{int(self.cached_target_confidence * 100)}%", text_color=ui_color)
                        self.reaction_pred_label.configure(text=self.cached_predicted_char or "--", text_color=ui_color if self.cached_predicted_char == current_target else T.ORANGE)
                    else:
                        self.reaction_success_frames = 0
                        self.reaction_conf_bar.configure(progress_color=T.BLUE); self.reaction_conf_bar.set(0)
                        self.reaction_conf_label.configure(text="0%", text_color=T.BLUE); self.reaction_pred_label.configure(text="--", text_color=T.TEXT)

                    if self.reaction_round_started:
                        elapsed = time.time() - self.reaction_round_start
                        remain = max(0.0, self.reaction_time_limit - elapsed)
                        ratio = remain / self.reaction_time_limit
                        timer_color = T.GREEN if ratio > 0.55 else T.YELLOW if ratio > 0.25 else T.RED
                        
                        self.reaction_timer_bar.configure(progress_color=timer_color); self.reaction_timer_bar.set(ratio)
                        self.reaction_timer_label.configure(text=f"{remain:04.1f}s", text_color=timer_color)

                        # Chốt điểm
                        if self.reaction_success_frames >= 7: finish_round(True, self.cached_target_confidence)
                        elif remain <= 0: finish_round(False, self.reaction_best_confidence)

                    # RENDER CAMERA
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    scale = min(720 / w, 430 / h)
                    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                    frame_resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    img = PIL.Image.fromarray(frame_resized)
                    imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                    self.practice_video_label.configure(image=imgtk, text=""); self.practice_video_label.image = imgtk

            except Exception as e: print("[Luyện phản xạ] Lỗi khung hình:", e)
            if self.practice_camera_on: self.practice_after_id = self.after(33, update_reaction_frame)

        def start_round():
            if self.reaction_index >= len(self.reaction_targets):
                show_result_page(); return

            target = self.reaction_targets[self.reaction_index]
            self.reaction_round_started = True
            self.reaction_round_start = time.time()
            self.reaction_success_frames = 0
            self.reaction_best_confidence = 0.0

            self.seq_1_hand.clear(); self.seq_2_hands.clear()
            self.prev_wx_l = self.prev_wy_l = self.prev_wx_r = self.prev_wy_r = None

            self.reaction_target_label.configure(text=f"Chữ {target}")
            self.reaction_pred_label.configure(text="--", text_color=T.TEXT)
            self.reaction_conf_label.configure(text="0%", text_color=T.BLUE)
            self.reaction_conf_bar.configure(progress_color=T.BLUE); self.reaction_conf_bar.set(0)
            self.reaction_timer_bar.configure(progress_color=T.BLUE); self.reaction_timer_bar.set(1)
            self.reaction_timer_label.configure(text="04.0s", text_color=T.BLUE)
            self.reaction_feedback_label.configure(text="☆ Làm ký hiệu này càng nhanh càng tốt!", fg_color="#102034", text_color=T.BLUE)

            render_target_preview()
            correct = sum(1 for r in self.reaction_results if r["correct"])
            self.reaction_score_label.configure(text=f"Đúng: {correct}")
            self.reaction_question_label.configure(text=f"Câu {self.reaction_index + 1} / {len(self.reaction_targets)}")

        def finish_round(ok, confidence):
            if not self.reaction_round_started: return
            target = self.reaction_targets[self.reaction_index]
            reaction_time = time.time() - self.reaction_round_start if ok else None

            self.reaction_results.append({"target": target, "correct": bool(ok), "reaction_time": reaction_time, "confidence": confidence})
            
            correct = sum(1 for r in self.reaction_results if r["correct"])
            self.reaction_score_label.configure(text=f"Đúng: {correct}")

            self.reaction_round_started = False
            self.reaction_success_frames = 0
            self.seq_1_hand.clear(); self.seq_2_hands.clear()
            self.prev_wx_l = self.prev_wy_l = self.prev_wx_r = self.prev_wy_r = None

            if ok: self.reaction_feedback_label.configure(text="☆ Chính xác! Chuyển sang ký hiệu tiếp theo...", fg_color="#17351F", text_color=T.GREEN)
            else: self.reaction_feedback_label.configure(text=f"☆ Quá giờ! Đáp án là chữ {target}.", fg_color="#451A1F", text_color=T.RED)

            self.reaction_index += 1
            if self.reaction_index >= len(self.reaction_targets): self.after(1000, show_result_page)
            else: self.after(900, start_round)

        def show_result_page():
            safe_stop()
            total = len(self.reaction_results) or len(self.reaction_targets)
            correct = sum(1 for r in self.reaction_results if r["correct"])
            accuracy = int((correct / total) * 100) if total else 0
            correct_times = [r["reaction_time"] for r in self.reaction_results if r["correct"] and r["reaction_time"] is not None]
            avg_time = sum(correct_times) / len(correct_times) if correct_times else 0
            session_minutes = max(1, int((time.time() - self.reaction_session_start) / 60))

            try:
                import user_db
                if is_logged_in and auth_module and getattr(auth_module, "CURRENT_USER", None):
                    updated = user_db.update_study_stats(auth_module.CURRENT_USER["id"], accuracy, session_time_minutes=session_minutes)
                    if updated: auth_module.CURRENT_USER.update(updated)
            except Exception as e: print("[Luyện phản xạ] Không lưu được thống kê:", e)

            result_page = self._clear_page()
            result_page.grid_columnconfigure(0, weight=1); result_page.grid_rowconfigure(0, weight=1)

            card = ctk.CTkFrame(result_page, fg_color=T.PANEL, corner_radius=20, border_width=1, border_color=T.BORDER)
            card.grid(row=0, column=0, sticky="nsew", padx=150, pady=70); card.grid_columnconfigure(0, weight=1)

            icon = "⚡" if accuracy >= 70 else "💪"
            color = T.GREEN if accuracy >= 80 else T.BLUE if accuracy >= 50 else T.ORANGE
            title = "PHẢN XẠ RẤT TỐT!" if accuracy >= 80 else "KHÁ ỔN RỒI!" if accuracy >= 50 else "CẦN LUYỆN THÊM!"

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=110)).pack(pady=(45, 15))
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=31, weight="bold"), text_color=color).pack(pady=(0, 10))
            ctk.CTkLabel(card, text=f"Bạn làm đúng {correct} / {total} ký hiệu.", font=ctk.CTkFont(size=18), text_color=T.MUTED).pack(pady=(0, 25))

            stats = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
            stats.pack(pady=(0, 28), padx=50, fill="x"); stats.grid_columnconfigure((0, 1, 2), weight=1)

            for i, (label, value, c) in enumerate([("Độ chính xác", f"{accuracy}%", color), ("Phản xạ TB", f"{avg_time:.2f}s" if avg_time else "--", T.ORANGE), ("Thời gian học", f"{session_minutes} phút", T.BLUE)]):
                cell = ctk.CTkFrame(stats, fg_color="transparent")
                cell.grid(row=0, column=i, sticky="nsew", padx=15, pady=18)
                ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=14), text_color=T.MUTED).pack()
                ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=30, weight="bold"), text_color=c).pack(pady=(4, 0))

            mistakes = [r["target"] for r in self.reaction_results if not r["correct"]]
            note = "✓ Kết quả đã được ghi nhận và tính vào Độ chính xác TB." if is_logged_in else "⚠ Vui lòng đăng nhập để lưu kết quả!"
            note_color = T.GREEN if is_logged_in else T.ORANGE
            if mistakes: note += "\nKý hiệu nên ôn lại: " + ", ".join(mistakes[:6])

            ctk.CTkLabel(card, text=note, font=ctk.CTkFont(size=15, weight="bold"), text_color=note_color, justify="center", wraplength=650).pack(pady=(0, 28))

            btns = ctk.CTkFrame(card, fg_color="transparent"); btns.pack()
            ctk.CTkButton(btns, text="⟳ Luyện lại", height=50, width=180, fg_color=T.CARD, hover_color=T.CARD_HOVER, border_width=1, border_color=T.BORDER, font=ctk.CTkFont(size=16, weight="bold"), command=self.show_reaction_training).pack(side="left", padx=10)
            ctk.CTkButton(btns, text="← Trở về Ôn tập", height=50, width=180, fg_color=T.BLUE, hover_color=T.BLUE_DARK, font=ctk.CTkFont(size=16, weight="bold"), command=self.show_review).pack(side="left", padx=10)

        # ---------- 6) ĐỘNG CƠ KHỞI ĐỘNG (HOẠT ĐỘNG ĐỒNG BỘ 100%) ----------
        def start_training():
            import cv2
            
            # Khóa nút ngay lập tức để người dùng không bấm liên tục
            start_btn.configure(text="⏳ Đang tải AI & Camera...", state="disabled", fg_color=T.MUTED)
            self.practice_status_label.configure(text="● Đang khởi động...", text_color=T.ORANGE)
            set_waiting_target_ui("Đang nạp AI...")
            self.update_idletasks() # Ép giao diện vẽ lại ngay lập tức

            # 1. NẠP AI ĐỒNG BỘ (An toàn tuyệt đối cho Tkinter)
            try:
                import mediapipe as mp
                self.mp_hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
                self.mp_draw = mp.solutions.drawing_utils
                from core.translate_window import load_lstm_model, load_lstm_model_both
                if not getattr(self, 'lstm_model_1', None): self.lstm_model_1, self.action_labels_1 = load_lstm_model()
                if not getattr(self, 'lstm_model_2', None): self.lstm_model_2, self.action_labels_2 = load_lstm_model_both()
            except Exception as e:
                messagebox.showerror("Lỗi AI", f"Không nạp được mô hình AI: {e}")
                reset_ui_to_idle()
                return

            # 2. DÒ TÌM CAMERA ĐỒNG BỘ
            cap = None
            for cam_idx in [0, 1, 2]:
                cap = cv2.VideoCapture(cam_idx)
                if cap and cap.isOpened(): break
                if os.name == "nt":
                    cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
                    if cap and cap.isOpened(): break

            if cap is None or not cap.isOpened():
                if cap: cap.release()
                messagebox.showerror("Lỗi Camera", "Không mở được camera!\n1. Vui lòng tắt camera ở màn hình 'Dịch tự do'.\n2. Tắt Zoom, Zalo Call.")
                reset_ui_to_idle()
                return

            # 3. SET UP HOÀN TẤT VÀ CHẠY
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)

            self.practice_cap = cap
            self.practice_camera_on = True
            self.reaction_results.clear()
            self.reaction_index = 0
            self.reaction_session_start = time.time()
            self.seq_1_hand.clear(); self.seq_2_hands.clear()

            start_btn.configure(text="■  Dừng luyện", state="normal", fg_color=T.RED, hover_color="#D32F2F", command=stop_reaction_training)
            self.practice_status_label.configure(text="● Camera đang bật", text_color=T.GREEN, fg_color="#17351F")

            set_waiting_target_ui("Sắp bắt đầu...")
            begin_start_countdown(3)
            update_reaction_frame()

        start_btn.configure(command=start_training)
    # ==========================================
    # KHỐI LOGIC: CỖ MÁY BÀI KIỂM TRA NHANH
    # ==========================================
    def show_quick_quiz(self):
        import random
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        learned = []
        try:
            import auth_ui
            if auth_ui.CURRENT_USER:
                learned = auth_ui.LEARNED_LETTERS or []
        except Exception: pass

        # 1. Trích xuất danh sách mọi ký hiệu để làm đáp án nhiễu
        all_letters = []
        for item in ALPHABET:
            val = item.get("label") or item.get("title") if isinstance(item, dict) else item
            val = str(val).replace("Chữ ", "").strip().upper()
            if val and val not in all_letters:
                all_letters.append(val)
        if not all_letters:
            all_letters = ["A", "B", "C", "D", "E", "G", "H", "I", "K", "L"]

        # 2. Thuật toán chọn 10 câu hỏi (Ưu tiên từ đã học)
        pool = learned.copy()
        random.shuffle(pool)
        if len(pool) < 10:
            extra = [l for l in all_letters if l not in pool]
            random.shuffle(extra)
            pool.extend(extra[:10 - len(pool)])
            
        target_list = pool[:10]
        if not target_list: return

        # 3. Trộn đáp án (1 Đúng - 3 Sai)
        self.quiz_data = []
        for target in target_list:
            distractors = [l for l in all_letters if l != target]
            random.shuffle(distractors)
            choices = distractors[:3] + [target]
            random.shuffle(choices)
            self.quiz_data.append({"target": target, "choices": choices})

        self.quiz_score = 0
        self.current_q_idx = 0

        # --- DỰNG GIAO DIỆN PHÒNG THI ---
        page = self._clear_page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        # Thanh Header điều hướng
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)
        self.back_button(header, command=self.show_review, text="←  Thoát").grid(row=0, column=0, sticky="w")
        
        prog_frame = ctk.CTkFrame(header, fg_color="transparent")
        prog_frame.grid(row=0, column=1, sticky="ew", padx=40)
        self.quiz_prog = ctk.CTkProgressBar(prog_frame, height=10, progress_color=T.BLUE, fg_color="#2A3038", corner_radius=5)
        self.quiz_prog.pack(fill="x", pady=(15, 5))
        
        self.quiz_lbl_count = ctk.CTkLabel(header, text="Câu 1 / 10", font=ctk.CTkFont(size=16, weight="bold"), text_color=T.TEXT)
        self.quiz_lbl_count.grid(row=0, column=2, sticky="e")

        # Nội dung chính (Khu vực hình ảnh)
        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 20))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=0)

        self.quiz_img_card = ctk.CTkFrame(body, fg_color=T.PANEL, corner_radius=20, border_width=1, border_color=T.BORDER)
        self.quiz_img_card.grid(row=0, column=0, sticky="nsew", pady=(10, 20))
        self.quiz_img_card.pack_propagate(False)
        ctk.CTkLabel(self.quiz_img_card, text="Ký hiệu tay này là chữ gì?", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.MUTED).pack(pady=(25, 10))
        self.quiz_img_container = ctk.CTkFrame(self.quiz_img_card, fg_color="transparent")
        self.quiz_img_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Lưới 4 nút đáp án (2x2)
        ans_frame = ctk.CTkFrame(body, fg_color="transparent")
        ans_frame.grid(row=1, column=0, sticky="ew")
        ans_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.quiz_btns = []
        for i in range(4):
            r, c = divmod(i, 2)
            btn = ctk.CTkButton(ans_frame, text="", height=65, font=ctk.CTkFont(size=22, weight="bold"), corner_radius=14, fg_color=T.PANEL, hover_color=T.CARD_HOVER, border_width=2, border_color=T.BORDER, text_color=T.TEXT)
            btn.grid(row=r, column=c, sticky="ew", padx=10, pady=10)
            self.quiz_btns.append(btn)

        self.load_quiz_question()

    def load_quiz_question(self):
        if self.current_q_idx >= len(self.quiz_data):
            self.show_quiz_result()
            return
            
        q_data = self.quiz_data[self.current_q_idx]
        target = q_data["target"]
        choices = q_data["choices"]
        
        self.quiz_lbl_count.configure(text=f"Câu {self.current_q_idx + 1} / {len(self.quiz_data)}")
        self.quiz_prog.set((self.current_q_idx) / len(self.quiz_data))
        
        for child in self.quiz_img_container.winfo_children():
            child.destroy()
            
        # ==========================================
        # BÍ KÍP 1: TÁCH 2 ẢNH CHO CHỮ CÓ DẤU TRONG BÀI TEST
        # ==========================================
        composite_map = {
            "Ă": "DAU_A", "Â": "DAU_MU", "Ê": "DAU_MU",
            "Ô": "DAU_MU", "Ơ": "DAU_MOC", "Ư": "DAU_MOC"
        }
        val = str(target).upper().strip()
        
        if val in composite_map:
            # Tạo khung ngang chứa 2 ảnh
            img_frame = ctk.CTkFrame(self.quiz_img_container, fg_color="transparent")
            img_frame.pack(expand=True)
            
            # Ảnh chữ cái gốc
            base_lesson = self.get_lesson(val) 
            base_img = self.create_lesson_image_label(img_frame, base_lesson, size=(130, 130), height=150, fallback_font_size=70)
            base_img.configure(fg_color="#080C11", corner_radius=16)
            base_img.pack(side="left", padx=8)
            
            # Ảnh dấu đi kèm
            mark_lesson = {"label": composite_map[val]}
            mark_img = self.create_lesson_image_label(img_frame, mark_lesson, size=(130, 130), height=150, fallback_font_size=70)
            mark_img.configure(fg_color="#080C11", corner_radius=16)
            mark_img.pack(side="left", padx=8)
        else:
            # Chữ bình thường thì hiện 1 ảnh to
            lesson = self.get_lesson(target)
            img_lbl = self.create_lesson_image_label(self.quiz_img_container, lesson, size=(220, 220), height=240, fallback_font_size=100)
            img_lbl.configure(fg_color="#080C11", corner_radius=16)
            img_lbl.pack(expand=True)
        # ==========================================
        
        for i, btn in enumerate(self.quiz_btns):
            choice_val = choices[i]
            btn.configure(text=f"Chữ {choice_val}", fg_color=T.PANEL, border_color=T.BORDER, text_color=T.TEXT, state="normal")
            btn.configure(command=lambda b=btn, c=choice_val, t=target: self.check_quiz_answer(b, c, t))
    def check_quiz_answer(self, btn, selected, target):
        for b in self.quiz_btns:
            b.configure(state="disabled") # Khóa toàn bộ nút
            
        if selected == target: # Chọn đúng
            self.quiz_score += 1
            btn.configure(fg_color="#17351F", border_color=T.GREEN, text_color=T.GREEN)
            delay = 800
        else: # Chọn sai
            btn.configure(fg_color="#451A1F", border_color=T.RED, text_color=T.RED)
            for b in self.quiz_btns:
                if b.cget("text") == f"Chữ {target}":
                    b.configure(fg_color="#17351F", border_color=T.GREEN, text_color=T.GREEN)
            delay = 1500 # Sai thì phạt đợi lâu hơn 1 chút để nhìn đáp án
            
        self.current_q_idx += 1
        self.after(delay, self.load_quiz_question) # Chuyển câu mượt mà

    def show_quiz_result(self):
        page = self._clear_page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        # Tính độ chính xác %
        accuracy = int((self.quiz_score / len(self.quiz_data)) * 100) if self.quiz_data else 0
        
        # LƯU ĐỘ CHÍNH XÁC VÀO DATABASE THẬT (KHÔNG CỘNG ĐIỂM)
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import auth_ui, user_db
            if auth_ui.CURRENT_USER:
                updated = user_db.update_study_stats(auth_ui.CURRENT_USER["id"], accuracy, session_time_minutes=1)
                if updated:
                    auth_ui.CURRENT_USER.update(updated)
        except Exception: pass
        
        card = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=20, border_width=1, border_color=T.BORDER)
        card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text="🏆", font=ctk.CTkFont(size=120)).pack(pady=(60, 20))
        
        if self.quiz_score >= 8: msg, color = "XUẤT SẮC!", T.GREEN
        elif self.quiz_score >= 5: msg, color = "KHÁ LẮM!", T.BLUE
        else: msg, color = "CẦN CỐ GẮNG HƠN!", T.ORANGE
            
        ctk.CTkLabel(card, text=msg, font=ctk.CTkFont(size=32, weight="bold"), text_color=color).pack(pady=(0, 10))
        ctk.CTkLabel(card, text=f"Bạn đã trả lời đúng {self.quiz_score} trên {len(self.quiz_data)} câu hỏi.", font=ctk.CTkFont(size=18), text_color=T.MUTED).pack(pady=(0, 30))
        
        # ==========================================
        # BÍ KÍP 2: THAY "ĐIỂM SỐ" THÀNH "ĐỘ CHÍNH XÁC %"
        # ==========================================
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(0, 40))
        ctk.CTkLabel(score_box, text="Độ chính xác", font=ctk.CTkFont(size=15), text_color=T.MUTED).pack(pady=(15, 0))
        ctk.CTkLabel(score_box, text=f"{accuracy}%", font=ctk.CTkFont(size=45, weight="bold"), text_color=color).pack(padx=60, pady=(0, 15))
        # ==========================================
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="⟳ Làm lại bài test", font=ctk.CTkFont(size=16, weight="bold"), height=50, width=180, fg_color=T.CARD, hover_color=T.CARD_HOVER, border_width=1, border_color=T.BORDER, command=self.show_quick_quiz).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="← Trở về Ôn tập", font=ctk.CTkFont(size=16, weight="bold"), height=50, width=180, fg_color=T.BLUE, hover_color=T.BLUE_DARK, command=self.show_review).pack(side="left", padx=10)
    def show_weak_signs(self):
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        self.refresh_account_button()
        
        is_logged_in = False
        learned = []
        
        auth_module = None
        for name, module in list(sys.modules.items()):
            if name == "auth_ui" or name.endswith(".auth_ui"):
                if getattr(module, "CURRENT_USER", None):
                    auth_module = module
                    break
                    
        if auth_module is None:
            try:
                import auth_ui
                auth_module = auth_ui
            except Exception: pass

        if auth_module and getattr(auth_module, "CURRENT_USER", None):
            is_logged_in = True
            learned = getattr(auth_module, "LEARNED_LETTERS", [])

        # KỊCH BẢN 1: Đã đăng nhập và có dữ liệu -> Bật Camera luôn
        if is_logged_in and learned:
            import random
            weak_words = random.sample(learned, min(3, len(learned)))
            self.show_camera_practice(pair_list=weak_words, back_cmd=self.show_review, practice_mode="weak_signs")
            return

        # KỊCH BẢN 2: Chưa đăng nhập hoặc chưa có dữ liệu -> Hiện trang thông báo khóa
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        
        self._title(page, "KÝ HIỆU CẦN CHÚ Ý", "Khắc phục các ký hiệu bạn làm sai nhiều nhất")

        header_right = ctk.CTkFrame(page, fg_color="transparent")
        header_right.grid(row=0, column=1, sticky="ne", padx=(20, 60), pady=(0, 10))
        self.back_button(header_right, command=self.show_review, text="←  Trở về").pack(anchor="e", pady=(0, 8))

        main = ctk.CTkFrame(page, fg_color="transparent")
        main.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 25), pady=(20, 0))
        
        if not is_logged_in:
            empty_panel = ctk.CTkFrame(main, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
            empty_panel.pack(fill="x", pady=20)
            ctk.CTkLabel(empty_panel, text="🔒", font=ctk.CTkFont(size=70)).pack(pady=(50, 15))
            ctk.CTkLabel(empty_panel, text="Vui lòng đăng nhập", font=ctk.CTkFont(size=22, weight="bold"), text_color=T.TEXT).pack()
            ctk.CTkLabel(empty_panel, text="Hệ thống cần xác thực tài khoản để AI có thể phân tích lỗi sai của bạn.", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(pady=(10, 25))
            
            def do_login():
                self.show_auth_panel(return_page=self.show_weak_signs)
                
            ctk.CTkButton(empty_panel, text="Đăng nhập ngay", font=ctk.CTkFont(size=15, weight="bold"), fg_color=T.BLUE, hover_color=T.BLUE_DARK, height=45, command=do_login).pack(pady=(0, 50))
            return

        if not learned:
            empty_panel = ctk.CTkFrame(main, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
            empty_panel.pack(fill="x", pady=20)
            ctk.CTkLabel(empty_panel, text="📭", font=ctk.CTkFont(size=70)).pack(pady=(50, 15))
            ctk.CTkLabel(empty_panel, text="Chưa có dữ liệu", font=ctk.CTkFont(size=22, weight="bold"), text_color=T.TEXT).pack()
            ctk.CTkLabel(empty_panel, text="Bạn chưa hoàn thành bài học nào. Hãy học thêm từ mới để hệ thống có thể phân tích!", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(pady=(10, 25))
            ctk.CTkButton(empty_panel, text="Đến Bảng chữ cái", font=ctk.CTkFont(size=15, weight="bold"), fg_color=T.BLUE, height=45, command=self.show_alphabet).pack(pady=(0, 50))
            return
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
