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
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Dict, Optional

import customtkinter as ctk

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
    def __init__(self, master, show_sidebar: bool = True, on_back: Optional[Callable[[], None]] = None):
        super().__init__(master, fg_color=T.BG, corner_radius=0)
        self.master = master
        self.show_sidebar = show_sidebar
        self.on_back = on_back
        self.content_column = 1 if show_sidebar else 0
        self.active_page = "home"
        self.page_frame: Optional[ctk.CTkFrame] = None
        self.sidebar_buttons: Dict[str, ctk.CTkButton] = {}

        self.pack(fill="both", expand=True)
        if show_sidebar:
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
        else:
            self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if show_sidebar:
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

        side_btn(1, "translate", "🎙   Dịch tự do (1 & 2 Tay)", lambda: messagebox.showinfo("VSL Translate", "Mở lại màn hình dịch tự do trong file ui_user.py."))
        side_btn(2, "study", "📚   Góc học tập", self.show_home, active=True)
        side_btn(3, "game", "🎮   Minigame", lambda: self.show_placeholder("MINIGAME", "Phần minigame có thể phát triển thêm sau."))

        divider = ctk.CTkFrame(sidebar, height=1, fg_color="#4C4C4C")
        divider.grid(row=4, column=0, sticky="ew", padx=25, pady=22)

        side_btn(5, "dict", "📖   Từ điển (Cheat Sheet)", lambda: self.show_placeholder("TỪ ĐIỂN", "Danh sách ký hiệu mẫu và mẹo ghi nhớ."), active=False, color=T.ORANGE)

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
        wrapper.grid(row=0, column=0, sticky="nsew", padx=(35, 30), pady=(35, 30))
        wrapper.grid_columnconfigure(0, weight=1)
        return wrapper

    def _title(self, parent, title: str, subtitle: str, row: int = 0):
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(family=T.FONT, size=43, weight="bold"),
            text_color=T.TEXT,
        ).grid(row=row, column=0, sticky="w")
        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=ctk.CTkFont(family=T.FONT, size=20),
            text_color=T.MUTED,
        ).grid(row=row + 1, column=0, sticky="w", pady=(5, 20))

    def show_placeholder(self, title: str, desc: str):
        page = self._content()
        self._title(page, title, desc)
        card = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=18, border_width=1, border_color=T.BORDER)
        card.grid(row=3, column=0, sticky="nsew", pady=20)
        ctk.CTkLabel(card, text="🚧", font=ctk.CTkFont(size=78)).pack(pady=(70, 15))
        ctk.CTkLabel(card, text="Tính năng đang phát triển", font=ctk.CTkFont(family=T.FONT, size=25, weight="bold"), text_color=T.TEXT).pack()
        ctk.CTkButton(card, text="Quay về Góc học tập", height=45, fg_color=T.BLUE, command=self.show_home).pack(pady=30)

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
        ib = self.icon_box(card, item["icon"], color if idx else T.BLUE_SOFT, size=60, font_size=25)
        ib.grid(row=0, column=0, padx=17, pady=17)
        ctk.CTkLabel(card, text=item["title"], font=ctk.CTkFont(family=T.FONT, size=17, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(18, 0))
        ctk.CTkLabel(card, text=item["desc"], justify="left", font=ctk.CTkFont(family=T.FONT, size=13), text_color=T.MUTED).grid(row=1, column=1, sticky="nw", pady=(2, 12))
        card.bind("<Button-1>", lambda _e, t=item["title"]: self._go_module(t))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _e, t=item["title"]: self._go_module(t))
        return card

    def _go_module(self, title: str):
        if "Bảng" in title:
            self.show_alphabet()
        elif "Từ" in title:
            self.show_vocab()
        elif "Câu" in title:
            self.show_conversation()
        elif "Ôn" in title:
            self.show_review()

    def section_header(self, parent, row: int, title: str, icon: str = "★", show_all: bool = True):
        h = ctk.CTkFrame(parent, fg_color="transparent")
        h.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        h.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(h, text=icon, font=ctk.CTkFont(size=22), text_color=T.BLUE).grid(row=0, column=0, padx=(0, 12))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(family=T.FONT, size=21, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="w")
        if show_all:
            ctk.CTkLabel(h, text="Xem tất cả  ›", font=ctk.CTkFont(family=T.FONT, size=14), text_color="#37A8FF").grid(row=0, column=2, sticky="e")
        return h

    def lesson_card(self, parent, idx: int, item: dict):
        card = ctk.CTkFrame(parent, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0))
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text=item["no"], width=30, height=30, fg_color=T.BLUE, corner_radius=7, text_color=T.TEXT, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=14, pady=(15, 0), sticky="nw")
        hand = ctk.CTkLabel(card, text=item["hand"], width=110, height=90, fg_color="#1A222B", corner_radius=50, font=ctk.CTkFont(size=50))
        hand.grid(row=1, column=0, padx=14, pady=(0, 5))
        ctk.CTkLabel(card, text=item["letter"], font=ctk.CTkFont(family=T.FONT, size=18, weight="bold"), text_color=T.TEXT).grid(row=1, column=1, sticky="nw", pady=(8, 2))
        ctk.CTkLabel(card, text=item["desc"], justify="left", font=ctk.CTkFont(family=T.FONT, size=13), text_color=T.MUTED).grid(row=1, column=1, sticky="w", pady=(35, 0))
        line = ctk.CTkFrame(card, height=1, fg_color=T.LINE)
        line.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 10))
        ctk.CTkButton(card, text="Học ngay  ❯", height=42, fg_color=T.BLUE, hover_color=T.BLUE_DARK, command=lambda: self.show_lesson(item["letter"].replace("Chữ ", ""))).grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 15))

    def topic_card(self, parent, idx: int, item: dict):
        color = COLOR_MAP[item["color"]]
        card = ctk.CTkFrame(parent, fg_color=T.CARD, border_width=1, border_color=T.BORDER, corner_radius=14)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 12, 0))
        card.grid_columnconfigure(1, weight=1)
        self.icon_box(card, item["icon"], color, size=70, font_size=24).grid(row=0, column=0, padx=18, pady=20, rowspan=2)
        ctk.CTkLabel(card, text=item["title"], font=ctk.CTkFont(family=T.FONT, size=18, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(22, 0))
        ctk.CTkLabel(card, text=item["desc"], justify="left", font=ctk.CTkFont(family=T.FONT, size=13), text_color=T.MUTED).grid(row=1, column=1, sticky="nw", pady=(4, 0))
        pb = ctk.CTkProgressBar(card, height=5, progress_color=color, fg_color="#29313B")
        pb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 5))
        pb.set(item.get("progress", 0.5))
        ctk.CTkLabel(card, text=item["count"], font=ctk.CTkFont(family=T.FONT, size=13, weight="bold"), text_color=color).grid(row=3, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 15))
        ctk.CTkLabel(card, text="›", font=ctk.CTkFont(size=32), text_color=T.MUTED).grid(row=1, column=2, padx=(0, 18))

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
        self.section_header(today_box, 0, "Bài học hôm nay", "▣")
        lessons_grid = ctk.CTkFrame(today_box, fg_color="transparent")
        lessons_grid.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        for i in range(3):
            lessons_grid.grid_columnconfigure(i, weight=1)
        for i, item in enumerate(TODAY_LESSONS):
            self.lesson_card(lessons_grid, i, item)

        topic_box = ctk.CTkFrame(main, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        topic_box.grid(row=1, column=0, sticky="ew")
        topic_box.grid_columnconfigure(0, weight=1)
        self.section_header(topic_box, 0, "Chủ đề phổ biến", "★")
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
        self.motivation_panel(right)

    def progress_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(card, text="↗  Tiến độ học tập", font=ctk.CTkFont(family=T.FONT, size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=22, pady=(22, 12))
        center = ctk.CTkFrame(card, fg_color="transparent")
        center.pack(fill="x", padx=20)
        ring = ProgressRing(center, 0.41, size=120, color=T.BLUE, bg=T.PANEL)
        ring.pack(side="left", padx=(0, 14), pady=5)
        info = ctk.CTkFrame(center, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text="Đã học:", font=ctk.CTkFont(size=14), text_color=T.MUTED).pack(anchor="w", pady=(16, 0))
        ctk.CTkLabel(info, text="12/29", font=ctk.CTkFont(size=26, weight="bold"), text_color=T.GREEN).pack(anchor="w")
        ctk.CTkLabel(info, text="Bảng chữ cái", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w")
        ctk.CTkFrame(card, height=1, fg_color=T.LINE).pack(fill="x", padx=20, pady=15)
        self.stat_row(card, "📅", "Chuỗi ngày học", "5 ngày", T.GREEN, "Cố gắng duy trì mỗi ngày!")
        self.stat_row(card, "🎯", "Độ chính xác TB", "91%", T.GREEN, "Làm rất tốt! 💪")
        self.stat_row(card, "🕘", "Thời gian học", "2h 35m", T.BLUE, "Tổng thời gian học tập")

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
        self._title(page, "BẢNG CHỮ CÁI KÝ HIỆU", "Chọn một chữ cái để bắt đầu học")

        main = ctk.CTkFrame(page, fg_color="transparent")
        main.grid(row=2, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0)

        left = ctk.CTkFrame(main, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left.grid_columnconfigure(0, weight=1)

        search = ctk.CTkEntry(left, placeholder_text="🔍  Tìm chữ cái...", height=42, fg_color=T.PANEL, border_color=T.BORDER, text_color=T.TEXT)
        search.grid(row=0, column=0, sticky="ew", pady=(0, 18))

        grid = ctk.CTkFrame(left, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew")
        for c in range(7):
            grid.grid_columnconfigure(c, weight=1)
        for idx, letter in enumerate(ALPHABET):
            r, c = divmod(idx, 7)
            self.letter_tile(grid, r, c, letter)

        detail = self.letter_detail(main, "D")
        detail.grid(row=0, column=1, sticky="ns", padx=(0, 0))

    def letter_tile(self, parent, row, col, letter):
        selected = letter == "D"
        learned = letter in ["A", "Ă", "Â"]
        icon, _ = LETTER_HINTS.get(letter, ("☝", ""))
        card = ctk.CTkFrame(parent, width=118, height=130, fg_color=T.CARD, border_width=2 if selected else 1, border_color=T.BLUE if selected else T.BORDER, corner_radius=12)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=letter, font=ctk.CTkFont(size=24, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=39)).pack(pady=(1, 1))
        status = "✓ Đã học" if learned else ("● Đang học" if selected else "● Chưa học")
        color = T.GREEN if learned else (T.BLUE if selected else T.MUTED_2)
        ctk.CTkLabel(card, text=status, font=ctk.CTkFont(size=12), text_color=color).pack(pady=(0, 8))
        card.bind("<Button-1>", lambda _e, l=letter: self.show_lesson(l))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _e, l=letter: self.show_lesson(l))

    def letter_detail(self, parent, letter):
        icon, desc = LETTER_HINTS.get(letter, ("☝", "Dựng ngón trỏ thẳng đứng."))
        card = ctk.CTkFrame(parent, width=310, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=f"Chữ {letter}", font=ctk.CTkFont(size=27, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=20, pady=(22, 8))
        ctk.CTkLabel(card, text=icon, height=180, fg_color="#0E1722", corner_radius=14, font=ctk.CTkFont(size=82)).pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(card, text="Cách thực hiện", font=ctk.CTkFont(size=17, weight="bold"), text_color=T.BLUE).pack(anchor="w", padx=20, pady=(15, 4))
        steps = ["Dựng ngón trỏ thẳng đứng.", "Các ngón còn lại khép lại.", "Lòng bàn tay hướng về camera.", "Giữ tay ổn định trước ngực."]
        for i, s in enumerate(steps, 1):
            ctk.CTkLabel(card, text=f"{i}. {s}", font=ctk.CTkFont(size=13), text_color=T.MUTED, justify="left").pack(anchor="w", padx=22, pady=2)
        ctk.CTkLabel(card, text="💡 Mẹo nhỏ", font=ctk.CTkFont(size=15, weight="bold"), text_color=T.YELLOW).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(card, text=desc, wraplength=250, justify="left", font=ctk.CTkFont(size=13), text_color=T.MUTED).pack(anchor="w", padx=20)
        ctk.CTkButton(card, text="📷  Luyện bằng camera", height=44, fg_color=T.BLUE, command=lambda: self.show_camera_practice(letter)).pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkButton(card, text="✓  Đánh dấu đã học", height=40, fg_color="transparent", border_width=1, border_color=T.BORDER, hover_color=T.CARD_HOVER).pack(fill="x", padx=20, pady=(0, 20))
        return card

    def show_lesson(self, letter="D"):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        self._title(page, f"BÀI HỌC: CHỮ {letter}", "Học cách thực hiện ký hiệu đúng")

        main = ctk.CTkFrame(page, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=18)
        main.grid(row=2, column=0, sticky="nsew", padx=(0, 18))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        icon, desc = LETTER_HINTS.get(letter, ("☝", "Giữ tay ổn định trước camera."))
        ctk.CTkLabel(main, text="⚙  Minh họa ký hiệu", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.TEXT).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 10))
        demo = ctk.CTkLabel(main, text=icon, height=330, fg_color="#0B1520", corner_radius=16, font=ctk.CTkFont(size=125), text_color=T.TEXT)
        demo.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

        guide = ctk.CTkFrame(main, fg_color="transparent")
        guide.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 30), pady=28)
        ctk.CTkLabel(guide, text="ⓘ  Hướng dẫn", font=ctk.CTkFont(size=20, weight="bold"), text_color=T.TEXT).pack(anchor="w", pady=(0, 15))
        steps = ["Giơ ngón trỏ lên", "Các ngón còn lại khép lại", "Hướng lòng bàn tay về camera", "Giữ tư thế 2 giây"]
        for i, s in enumerate(steps, 1):
            row = ctk.CTkFrame(guide, height=58, fg_color=T.CARD, corner_radius=12, border_width=1, border_color=T.BORDER)
            row.pack(fill="x", pady=6)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=str(i), width=34, height=34, fg_color=T.BLUE_SOFT, corner_radius=20, text_color=T.TEXT, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=14)
            ctk.CTkLabel(row, text=s, font=ctk.CTkFont(size=16), text_color=T.TEXT).pack(side="left")
        note = ctk.CTkFrame(guide, fg_color=T.CARD, corner_radius=12, border_width=1, border_color=T.BORDER)
        note.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(note, text="⚠  Lưu ý", font=ctk.CTkFont(size=17, weight="bold"), text_color=T.ORANGE).pack(anchor="w", padx=18, pady=(16, 6))
        ctk.CTkLabel(note, text="Giữ tay ổn định, hướng thẳng vào camera\nđể hệ thống nhận diện chính xác hơn.", justify="left", text_color=T.MUTED).pack(anchor="w", padx=18, pady=(0, 16))

        buttons = ctk.CTkFrame(page, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", pady=(18, 0), padx=(0, 18))
        buttons.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(buttons, text="▶  Bắt đầu luyện tập", height=55, fg_color=T.BLUE, command=lambda: self.show_camera_practice(letter)).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ctk.CTkButton(buttons, text="⟳  Xem lại", height=55, fg_color=T.PANEL, hover_color=T.CARD_HOVER).grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(buttons, text="→  Bài tiếp theo", height=55, fg_color="transparent", border_width=1, border_color=T.BLUE, text_color=T.BLUE).grid(row=0, column=2, sticky="ew", padx=(12, 0))

        info = ctk.CTkFrame(page, width=305, fg_color=T.PANEL, border_width=1, border_color=T.BORDER, corner_radius=16)
        info.grid(row=2, column=1, sticky="nsew")
        info.grid_propagate(False)
        ctk.CTkLabel(info, text="📘  Thông tin bài học", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.BLUE).pack(anchor="w", padx=20, pady=(22, 15))
        self.info_item(info, "📊", "Mức độ", "Dễ", T.GREEN)
        self.info_item(info, "🕘", "Thời gian", "2 phút", T.BLUE)
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

    def show_camera_practice(self, letter="D"):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        self._title(page, "LUYỆN TẬP BẰNG CAMERA", "Thực hiện ký hiệu theo yêu cầu")
        camera = ctk.CTkFrame(page, fg_color=T.BG, border_width=2, border_color=T.BLUE, corner_radius=16)
        camera.grid(row=2, column=0, sticky="nsew", padx=(0, 25))
        camera.grid_propagate(False)
        ctk.CTkLabel(camera, text="●  Camera đang bật", fg_color="#31363D", corner_radius=8, text_color=T.TEXT, font=ctk.CTkFont(size=14)).place(x=26, y=24)
        ctk.CTkLabel(camera, text="☝", font=ctk.CTkFont(size=170), text_color=T.TEXT).pack(expand=True, pady=60)
        ctk.CTkLabel(camera, text="Khung camera mô phỏng - kết nối OpenCV ở ui_user.py", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(pady=(0, 22))

        right = ctk.CTkFrame(page, fg_color="transparent", width=390)
        right.grid(row=2, column=1, sticky="nsew")
        right.grid_propagate(False)
        panel = ctk.CTkFrame(right, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        panel.pack(fill="x")
        rows = [("🖐", "Ký hiệu cần làm:", letter, T.BLUE), ("🟢", "Bạn đang làm:", letter, T.GREEN), ("🎯", "Độ chính xác:", "96%", T.GREEN), ("✓", "Trạng thái:", "Đúng ✓", T.GREEN)]
        for icon, label, value, color in rows:
            r = ctk.CTkFrame(panel, fg_color="transparent")
            r.pack(fill="x", padx=18, pady=11)
            ctk.CTkLabel(r, text=icon, width=44, height=44, fg_color="#102034", corner_radius=12, font=ctk.CTkFont(size=20)).pack(side="left", padx=(0, 15))
            ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=16, weight="bold"), text_color=T.TEXT).pack(side="left")
            ctk.CTkLabel(r, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=color).pack(side="right")
        ctk.CTkLabel(panel, text="☆  Rất tốt! Giữ tư thế ổn định thêm 1 giây.", fg_color="#17351F", corner_radius=8, height=44, text_color=T.GREEN, font=ctk.CTkFont(size=14)).pack(fill="x", padx=18, pady=(8, 18))

        output = ctk.CTkFrame(right, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        output.pack(fill="x", pady=18)
        ctk.CTkLabel(output, text="VĂN BẢN GHÉP", font=ctk.CTkFont(size=16, weight="bold"), text_color=T.GREEN).pack(anchor="w", padx=18, pady=(18, 8))
        ctk.CTkTextbox(output, height=78, fg_color=T.CARD, border_color=T.BORDER, border_width=1, font=ctk.CTkFont(size=22)).pack(fill="x", padx=18, pady=(0, 18))
        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.pack(fill="x")
        btns.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(btns, text="▶ Bắt đầu", height=45, fg_color=T.BLUE).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(btns, text="⟳ Làm lại", height=45, fg_color=T.PANEL).grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(btns, text="▱ Tắt camera", height=45, fg_color=T.RED).grid(row=0, column=2, sticky="ew", padx=(6, 0))

    def show_vocab(self):
        self.topic_page("TỪ VỰNG THEO CHỦ ĐỀ", "Học từ mới bằng ngôn ngữ ký hiệu", VOCAB_TOPICS, right_title="Chủ đề đề xuất hôm nay", cta="Bắt đầu học")

    def show_conversation(self):
        self.topic_page("CÂU GIAO TIẾP", "Học các mẫu câu giao tiếp hằng ngày bằng ký hiệu", CONVERSATION_TOPICS, right_title="Mẫu câu hôm nay", cta="Bắt đầu học", conversation=True)

    def topic_page(self, title, subtitle, items, right_title, cta, conversation=False):
        page = self._content()
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        self._title(page, title, subtitle)
        ctk.CTkLabel(page, text="☝  💬", font=ctk.CTkFont(size=50), text_color=T.BLUE).grid(row=0, column=1, rowspan=2, padx=(20, 70))
        tabs = ctk.CTkFrame(page, fg_color=T.PANEL, corner_radius=14, border_width=1, border_color=T.BORDER)
        tabs.grid(row=2, column=0, sticky="ew", pady=(0, 20), padx=(0, 25))
        for i, name in enumerate(["▦  Tất cả", "☆  Cơ bản", "🔥  Phổ biến", "✓  Đã học"]):
            tabs.grid_columnconfigure(i, weight=1)
            ctk.CTkButton(tabs, text=name, height=50, fg_color=T.BLUE if i == 0 else "transparent", hover_color=T.BLUE_DARK if i == 0 else T.CARD_HOVER, font=ctk.CTkFont(size=15, weight="bold" if i == 0 else "normal")).grid(row=0, column=i, sticky="ew", padx=10, pady=10)

        grid = ctk.CTkFrame(page, fg_color="transparent")
        grid.grid(row=3, column=0, sticky="nsew", padx=(0, 25))
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)
        for idx, it in enumerate(items):
            r, c = divmod(idx, 3)
            self.big_topic_card(grid, r, c, it)

        side = ctk.CTkFrame(page, width=330, fg_color="transparent")
        side.grid(row=2, column=1, rowspan=2, sticky="ns")
        side.grid_propagate(False)
        highlight = ctk.CTkFrame(side, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BLUE)
        highlight.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(highlight, text=f"★  {right_title}", font=ctk.CTkFont(size=18, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(20, 14))
        first = items[0]
        color = COLOR_MAP[first["color"]]
        top = ctk.CTkFrame(highlight, fg_color=T.CARD, corner_radius=13, border_width=1, border_color=T.BORDER)
        top.pack(fill="x", padx=18)
        self.icon_box(top, first["icon"], color, size=62, font_size=22).grid(row=0, column=0, padx=16, pady=16, rowspan=2)
        ctk.CTkLabel(top, text=first["title"], font=ctk.CTkFont(size=19, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(18, 0))
        ctk.CTkLabel(top, text="Phổ biến", fg_color="#17351F", corner_radius=6, text_color=T.GREEN, font=ctk.CTkFont(size=12)).grid(row=1, column=1, sticky="nw", pady=(5, 15))
        if conversation:
            phrases = ["1  Xin chào", "2  Bạn khỏe không?", "3  Rất vui được gặp bạn"]
            for phrase in phrases:
                ctk.CTkLabel(highlight, text=phrase, height=45, fg_color=T.CARD, corner_radius=10, anchor="w", font=ctk.CTkFont(size=14), text_color=T.TEXT).pack(fill="x", padx=18, pady=4)
        else:
            ctk.CTkLabel(highlight, text="Bắt đầu ngày mới với những từ\nthông dụng nhất!", justify="left", text_color=T.MUTED, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=18, pady=(15, 5))
            pb = ctk.CTkProgressBar(highlight, height=7, progress_color=color, fg_color="#2E333A")
            pb.pack(fill="x", padx=18, pady=(8, 10))
            pb.set(first["done"] / first["total"])
        ctk.CTkButton(highlight, text=f"▶  {cta}", height=50, fg_color=T.BLUE, command=lambda: self.show_lesson("D")).pack(fill="x", padx=18, pady=(12, 18))
        summary = ctk.CTkFrame(side, fg_color=T.PANEL, corner_radius=16, border_width=1, border_color=T.BORDER)
        summary.pack(fill="x")
        ctk.CTkLabel(summary, text="↗  Tổng quan học tập", font=ctk.CTkFont(size=17, weight="bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(18, 12))
        self.side_kpi(summary, "📗", "Chủ đề đã học", "4 / 6", T.GREEN)
        self.side_kpi(summary, "✅", "Bài học hoàn thành" if not conversation else "Mẫu câu hoàn thành", "78 / 118" if not conversation else "27 / 72", T.PURPLE)
        self.side_kpi(summary, "🕘", "Thời gian học", "12h 45m" if not conversation else "5h 24m", T.BLUE)

    def big_topic_card(self, parent, row, col, item):
        color = COLOR_MAP[item["color"]]
        card = ctk.CTkFrame(parent, fg_color=T.CARD, corner_radius=16, border_width=1, border_color=color if col == 0 and row == 0 else T.BORDER)
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 16, 0), pady=(0 if row == 0 else 16, 16))
        card.grid_columnconfigure(1, weight=1)
        self.icon_box(card, item["icon"], color, size=76, font_size=26).grid(row=0, column=0, rowspan=2, padx=18, pady=20)
        ctk.CTkLabel(card, text=item["title"], font=ctk.CTkFont(size=20, weight="bold"), text_color=T.TEXT).grid(row=0, column=1, sticky="sw", pady=(22, 0))
        ctk.CTkLabel(card, text=item["desc"], wraplength=210, justify="left", text_color=T.MUTED, font=ctk.CTkFont(size=14)).grid(row=1, column=1, sticky="nw", pady=(4, 0))
        pb = ctk.CTkProgressBar(card, height=7, progress_color=color, fg_color="#28313A")
        pb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 5))
        pb.set(item["done"] / item["total"])
        ctk.CTkLabel(card, text=f"{item['done']} / {item['total']} {'câu' if 'Tự' in item['title'] or item['title'] in ['Chào hỏi','Hỏi đường','Mua sắm'] else 'bài'}", font=ctk.CTkFont(size=13, weight="bold"), text_color=color).grid(row=3, column=0, sticky="w", padx=18, pady=(0, 16))
        ctk.CTkButton(card, text="Xem bài học   ❯", height=42, fg_color="transparent", border_width=1, border_color=T.BLUE, text_color=T.BLUE, command=lambda: self.show_lesson("D")).grid(row=3, column=1, sticky="ew", padx=(0, 18), pady=(0, 16))

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
        ctk.CTkLabel(page, text="☝  ☝", font=ctk.CTkFont(size=50), text_color=T.BLUE).grid(row=0, column=1, rowspan=2, padx=(20, 60))

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
