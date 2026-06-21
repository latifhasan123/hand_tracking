from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

try:
    from .theme import APP_NAME, COLORS, FONT, FONT_MONO, SIDEBAR_WIDTH, WINDOW_SIZE
    from .data import GAME_MODES, FEATURED_GAMES, ANSWER_HISTORY, REACTION_HISTORY, WORD_BANK, SPIN_SEGMENTS
except ImportError:  # allow running this file directly
    from theme import APP_NAME, COLORS, FONT, FONT_MONO, SIDEBAR_WIDTH, WINDOW_SIZE
    from data import GAME_MODES, FEATURED_GAMES, ANSWER_HISTORY, REACTION_HISTORY, WORD_BANK, SPIN_SEGMENTS


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MinigameFrame(ctk.CTkFrame):
    """Embeddable minigame UI frame."""

    def __init__(self, master, on_back: Optional[Callable[[], None]] = None, show_sidebar: bool = True, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self.on_back = on_back
        self.show_sidebar = show_sidebar
        self.current_screen = "dashboard"
        self.selected_guess_answer = "A"
        self._build_layout()
        self.show_dashboard()

    # ---------- General layout ----------
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)

        if self.show_sidebar:
            self.grid_columnconfigure(0, minsize=SIDEBAR_WIDTH)
            self.grid_columnconfigure(1, weight=1)

            self.sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, fg_color=COLORS["sidebar"], corner_radius=0)
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar.grid_propagate(False)
            self._build_sidebar()
            content_col = 1
        else:
            self.grid_columnconfigure(0, weight=1)
            self.sidebar = None
            content_col = 0

        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.content.grid(row=0, column=content_col, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self):
        self.sidebar.grid_columnconfigure(0, weight=1)
        logo = ctk.CTkLabel(
            self.sidebar,
            text=f"🌐  {APP_NAME}",
            font=(FONT, 22, "bold"),
            text_color=COLORS["blue_2"],
            anchor="w",
        )
        logo.grid(row=0, column=0, sticky="ew", padx=30, pady=(36, 45))

        self._nav_item(1, "✋", "Dịch tự do (1 & 2 Tay)", False, lambda: None)
        self._nav_item(2, "📖", "Góc học tập", False, lambda: None)
        self._nav_item(3, "🎮", "Minigame", True, self.show_dashboard)

        divider = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["stroke_light"])
        divider.grid(row=4, column=0, sticky="ew", padx=22, pady=(24, 24))

        dict_btn = ctk.CTkButton(
            self.sidebar,
            text="📖  Từ điển (Cheat Sheet)",
            height=50,
            corner_radius=8,
            fg_color=COLORS["orange"],
            hover_color="#E88900",
            text_color="white",
            font=(FONT, 15, "bold"),
            command=lambda: None,
        )
        dict_btn.grid(row=5, column=0, padx=22, sticky="ew")

        self.sidebar.grid_rowconfigure(6, weight=1)
        cam_btn = ctk.CTkButton(
            self.sidebar,
            text="▣  Tắt Camera",
            height=56,
            corner_radius=8,
            fg_color=COLORS["red"],
            hover_color="#D9342A",
            text_color="white",
            font=(FONT, 17, "bold"),
        )
        cam_btn.grid(row=7, column=0, sticky="ew", padx=18, pady=(0, 26))

    def _nav_item(self, row: int, icon: str, text: str, selected: bool, command: Callable[[], None]):
        color = COLORS["card"] if selected else "transparent"
        hover = COLORS["card_hover"]
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"{icon}   {text}",
            height=50,
            corner_radius=8,
            fg_color=color,
            hover_color=hover,
            text_color=COLORS["text"],
            anchor="w",
            font=(FONT, 15, "bold" if selected else "normal"),
            command=command,
        )
        btn.grid(row=row, column=0, sticky="ew", padx=18, pady=4)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _page(self):
        page = ctk.CTkFrame(self.content, fg_color=COLORS["bg"], corner_radius=0)
        page.grid(row=0, column=0, sticky="nsew", padx=24, pady=18)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        return page

    def _header(self, parent, title: str, subtitle: str):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=title, font=(FONT, 34, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=subtitle, font=(FONT, 16), text_color=COLORS["muted"]).grid(row=1, column=0, sticky="w", pady=(6, 0))
        deco = ctk.CTkLabel(header, text="✌   👍   🤟   ✋", font=(FONT, 34), text_color=COLORS["blue_2"])
        deco.grid(row=0, column=1, rowspan=2, sticky="e", padx=20)
        return header

    def _panel(self, parent, **grid):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["panel"], border_color=COLORS["stroke"], border_width=1, corner_radius=16)
        frame.grid(**grid)
        return frame

    def _color(self, name: str) -> str:
        return {
            "blue": COLORS["blue"], "green": COLORS["green"], "red": COLORS["red"],
            "orange": COLORS["orange"], "purple": COLORS["purple"], "pink": COLORS["pink"],
            "yellow": COLORS["yellow"], "teal": COLORS["teal"],
        }.get(name, COLORS["blue"])

    def _icon_box(self, parent, text: str, color: str, size: int = 54, font_size: int = 24):
        box = ctk.CTkFrame(parent, width=size, height=size, fg_color=self._color(color), corner_radius=14)
        box.grid_propagate(False)
        ctk.CTkLabel(box, text=text, font=(FONT, font_size, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        return box

    # ---------- Dashboard ----------
    def show_dashboard(self):
        self.current_screen = "dashboard"
        self.clear_content()
        page = self._page()
        self._header(page, "MINIGAME", "Chơi để học ngôn ngữ ký hiệu vui hơn mỗi ngày")

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=280)
        body.grid_rowconfigure(1, weight=1)

        mode_row = ctk.CTkFrame(body, fg_color="transparent")
        mode_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        for i in range(6):
            mode_row.grid_columnconfigure(i, weight=1)
        for i, item in enumerate(GAME_MODES):
            card = self._game_mode_card(mode_row, item, featured=(i == 0))
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0 if i == 5 else 8))

        main = self._panel(body, row=1, column=0, sticky="nsew", padx=(0, 14))
        main.grid_columnconfigure((0, 1, 2), weight=1)
        main.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="★  Game nổi bật hôm nay", font=(FONT, 20, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Xem tất cả  →", font=(FONT, 14), text_color=COLORS["blue_2"]).grid(row=0, column=1, sticky="e")

        for i, game in enumerate(FEATURED_GAMES):
            self._featured_card(main, game).grid(row=1, column=i, sticky="nsew", padx=(18 if i == 0 else 8, 18 if i == 2 else 8), pady=(8, 18))

        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=(0, 14), pady=(16, 0))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=1)
        self._daily_challenge(bottom).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._motivation_card(bottom).grid(row=0, column=1, sticky="ew")

        stats = self._stats_panel(body)
        stats.grid(row=1, column=1, rowspan=2, sticky="nsew")

    def _game_mode_card(self, parent, item, featured=False):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_2"],
            border_color=COLORS["blue"] if featured else COLORS["stroke"],
            border_width=2 if featured else 1,
            corner_radius=14,
            height=150,
        )
        card.grid_propagate(False)
        card.grid_rowconfigure(1, weight=1)
        self._icon_box(card, item["icon"], item["color"], 58, 24).grid(row=0, column=0, padx=18, pady=(18, 6), sticky="w")
        ctk.CTkLabel(card, text=item["title"], font=(FONT, 16, "bold"), text_color=COLORS["text"], justify="left").grid(row=1, column=0, padx=18, sticky="w")
        ctk.CTkLabel(card, text=item["desc"], font=(FONT, 12), text_color=COLORS["muted"], justify="left").grid(row=2, column=0, padx=18, pady=(4, 16), sticky="w")
        card.bind("<Button-1>", lambda e, key=item["key"]: self.open_game(key))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, key=item["key"]: self.open_game(key))
        return card

    def _featured_card(self, parent, game):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=14)
        card.grid_columnconfigure(0, weight=1)
        color = self._color(game["accent"])
        ctk.CTkLabel(card, text=game["icon"], font=(FONT, 54), text_color=color).grid(row=0, column=0, pady=(20, 8))
        ctk.CTkLabel(card, text=game["title"], font=(FONT, 22, "bold"), text_color=COLORS["text"]).grid(row=1, column=0)
        ctk.CTkLabel(card, text=game["desc"], font=(FONT, 14), text_color=COLORS["muted"], justify="center").grid(row=2, column=0, pady=(8, 18))
        ctk.CTkButton(card, text="Chơi ngay", height=42, fg_color=COLORS["blue"], hover_color="#0B62D5", command=lambda: self.open_game(game["key"])).grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 18))
        return card

    def _daily_challenge(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["panel"], border_color=COLORS["stroke"], border_width=1, corner_radius=14, height=90)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text="🎯", font=(FONT, 32), text_color=COLORS["orange"]).grid(row=0, column=0, rowspan=2, padx=22)
        ctk.CTkLabel(card, text="Thử thách hôm nay", font=(FONT, 16, "bold"), text_color=COLORS["text"]).grid(row=0, column=1, sticky="w", pady=(16, 0))
        ctk.CTkLabel(card, text="Hoàn thành 10 câu đoán chữ", font=(FONT, 13), text_color=COLORS["muted"]).grid(row=1, column=1, sticky="w")
        ctk.CTkLabel(card, text="6 / 10", font=(FONT, 18, "bold"), text_color=COLORS["blue_2"]).grid(row=0, column=2, rowspan=2, padx=18)
        ctk.CTkLabel(card, text="🏅 Phần thưởng\n+50 điểm", font=(FONT, 14, "bold"), text_color=COLORS["yellow"]).grid(row=0, column=3, rowspan=2, padx=18)
        return card

    def _motivation_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color="#0B2141", border_color=COLORS["blue"], border_width=1, corner_radius=14, height=90)
        ctk.CTkLabel(card, text="🏆  Bạn đang làm rất tốt!", font=(FONT, 16, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(card, text="Cố gắng thêm một chút nữa\nđể chinh phục mục tiêu nhé!", font=(FONT, 12), text_color=COLORS["muted"], justify="left").pack(anchor="w", padx=18)
        return card

    def _stats_panel(self, parent):
        panel = self._panel(parent, row=0, column=0)  # will be re-gridded by caller
        for w in panel.winfo_children():
            w.destroy()
        ctk.CTkLabel(panel, text="▮  Thành tích của bạn", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=18, pady=(20, 14))
        for icon, title, value, color in [
            ("🏆", "Điểm cao nhất", "320", "yellow"),
            ("◎", "Tỉ lệ đúng", "89%", "green"),
            ("🔥", "Chuỗi thắng", "6", "orange"),
            ("🎮", "Game đã chơi", "18", "blue"),
            ("🎖", "Huy hiệu", "4", "purple"),
        ]:
            self._stat_tile(panel, icon, title, value, color).pack(fill="x", padx=16, pady=7)
        return panel

    def _stat_tile(self, parent, icon: str, title: str, value: str, color: str):
        tile = ctk.CTkFrame(parent, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        tile.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tile, text=icon, font=(FONT, 30), text_color=self._color(color)).grid(row=0, column=0, padx=18, pady=14)
        ctk.CTkLabel(tile, text=title, font=(FONT, 13), text_color=COLORS["muted"]).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tile, text=value, font=(FONT, 28, "bold"), text_color=self._color(color)).grid(row=1, column=1, sticky="w", pady=(0, 12))
        return tile

    # ---------- Navigation ----------
    def open_game(self, key: str):
        {
            "guess": self.show_guess_game,
            "word": self.show_word_game,
            "react": self.show_reaction_game,
            "quiz": self.show_quiz_game,
            "flashcard": self.show_flashcard_game,
            "wheel": self.show_wheel_game,
        }.get(key, self.show_dashboard)()

    # ---------- Mini widgets ----------
    def _side_score_panel(self, parent, title: str, rows):
        panel = self._panel(parent, row=0, column=1, sticky="nsew", padx=(14, 0))
        ctk.CTkLabel(panel, text=f"▮  {title}", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 10))
        for icon, label, value, color in rows:
            self._small_score(panel, icon, label, value, color).pack(fill="x", padx=16, pady=6)
        return panel

    def _small_score(self, parent, icon: str, label: str, value: str, color: str):
        row = ctk.CTkFrame(parent, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=12, height=62)
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row, text=icon, font=(FONT, 24), text_color=self._color(color)).grid(row=0, column=0, rowspan=2, padx=14, pady=10)
        ctk.CTkLabel(row, text=label, font=(FONT, 12), text_color=COLORS["muted"]).grid(row=0, column=1, sticky="w", pady=(10, 0))
        ctk.CTkLabel(row, text=value, font=(FONT, 22, "bold"), text_color=self._color(color)).grid(row=1, column=1, sticky="w", pady=(0, 10))
        return row

    def _hand_canvas(self, parent, kind: str = "B", width=220, height=180):
        canvas = tk.Canvas(parent, width=width, height=height, bd=0, highlightthickness=0, bg=COLORS["panel_2"])
        cx, cy = width // 2, height // 2
        canvas.create_oval(cx - 70, cy - 70, cx + 70, cy + 70, fill="#0D2038", outline="")
        # crude hand drawings to avoid image assets
        skin = "#F6B27A"
        outline = "#C77B4E"
        if kind in ("B", "D"):
            canvas.create_rectangle(cx - 32, cy - 58, cx + 32, cy + 40, fill=skin, outline=outline, width=2)
            for x in [-24, -8, 8, 24]:
                canvas.create_line(cx + x, cy - 55, cx + x, cy + 25, fill=outline, width=1)
            canvas.create_arc(cx - 15, cy - 10, cx + 70, cy + 55, start=110, extent=120, style="arc", outline=outline, width=3)
            canvas.create_rectangle(cx - 28, cy + 38, cx + 28, cy + 75, fill=skin, outline=outline, width=2)
        elif kind == "C":
            canvas.create_arc(cx - 58, cy - 50, cx + 60, cy + 60, start=70, extent=220, style="arc", outline=skin, width=32)
            canvas.create_arc(cx - 58, cy - 50, cx + 60, cy + 60, start=70, extent=220, style="arc", outline=outline, width=2)
            canvas.create_rectangle(cx - 45, cy + 45, cx - 5, cy + 85, fill=skin, outline=outline, width=2)
        elif kind == "V":
            canvas.create_line(cx - 15, cy + 35, cx - 38, cy - 60, fill=skin, width=22)
            canvas.create_line(cx + 15, cy + 35, cx + 38, cy - 60, fill=skin, width=22)
            canvas.create_oval(cx - 38, cy + 10, cx + 38, cy + 70, fill=skin, outline=outline, width=2)
            canvas.create_rectangle(cx - 24, cy + 55, cx + 24, cy + 95, fill=skin, outline=outline, width=2)
        else:
            canvas.create_oval(cx - 45, cy - 45, cx + 45, cy + 45, fill=skin, outline=outline, width=2)
            canvas.create_rectangle(cx - 25, cy + 30, cx + 25, cy + 75, fill=skin, outline=outline, width=2)
        return canvas

    # ---------- Guess game ----------
    def show_guess_game(self):
        self.clear_content()
        page = self._page()
        self._header(page, "ĐOÁN CHỮ CÁI", "Chọn đáp án đúng cho ký hiệu đang hiển thị")
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(game, text="Ký hiệu này là chữ gì?", font=(FONT, 22, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, columnspan=2, pady=(28, 8))
        canvas = self._hand_canvas(game, "B", 260, 210)
        canvas.grid(row=1, column=0, columnspan=2, pady=(4, 18))
        answers = [("A.  Chữ A", "A"), ("B.  Chữ B", "B"), ("C.  Chữ C", "C"), ("D.  Chữ D", "D")]
        for idx, (text, val) in enumerate(answers):
            btn = ctk.CTkButton(
                game, text=text, height=58, corner_radius=10,
                fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                border_color=COLORS["blue"] if val == self.selected_guess_answer else COLORS["stroke"],
                border_width=2 if val == self.selected_guess_answer else 1,
                font=(FONT, 18, "bold"), command=lambda v=val: self._select_answer(v)
            )
            btn.grid(row=2 + idx // 2, column=idx % 2, sticky="ew", padx=18, pady=8)
        hist = self._answer_history(game)
        hist.grid(row=4, column=0, columnspan=2, sticky="ew", padx=18, pady=(22, 16))

        self._side_score_panel(body, "Thông tin trận chơi", [
            ("🏆", "Điểm", "80", "yellow"), ("☰", "Câu", "4 / 10", "blue"),
            ("✓", "Đúng", "3", "green"), ("✕", "Sai", "1", "red"),
            ("◴", "Thời gian", "00:18", "purple"), ("▮", "Level", "Dễ", "green"),
        ])
        self._bottom_controls(body, [
            ("✓  Xác nhận", "blue", lambda: None), ("↻  Chơi lại", "card", self.show_guess_game), ("»  Câu tiếp theo", "green", lambda: None)
        ])

    def _select_answer(self, answer: str):
        self.selected_guess_answer = answer
        self.show_guess_game()

    def _answer_history(self, parent):
        box = ctk.CTkFrame(parent, fg_color=COLORS["panel_2"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        ctk.CTkLabel(box, text="↺  Lịch sử câu trả lời", font=(FONT, 15, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(12, 8))
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 12))
        for n, ans, ok in ANSWER_HISTORY:
            color = COLORS["green"] if ok else (COLORS["blue"] if ok is None and n == "4" else COLORS["stroke_light"])
            chip = ctk.CTkFrame(row, width=54, height=64, fg_color=COLORS["card"], border_color=color, border_width=1, corner_radius=10)
            chip.pack(side="left", padx=5)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=n, font=(FONT_MONO, 10), text_color=COLORS["muted"]).pack(pady=(4, 0))
            ctk.CTkLabel(chip, text=ans, font=(FONT, 17, "bold"), text_color=COLORS["text"]).pack()
            ctk.CTkLabel(chip, text="✓" if ok else "—", font=(FONT, 12, "bold"), text_color=color).pack()
        return box

    # ---------- Word game ----------
    def show_word_game(self):
        self.clear_content()
        page = self._page()
        self._header(page, "GHÉP TỪ", "Ghép các ký hiệu để tạo thành từ đúng")
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(game, text="💡  Gợi ý: Thành viên trong gia đình", font=(FONT, 17, "bold"), text_color=COLORS["text"], fg_color="#102238", corner_radius=8, width=430, height=45).grid(row=0, column=0, pady=(20, 12))
        sign_row = ctk.CTkFrame(game, fg_color="transparent")
        sign_row.grid(row=1, column=0)
        for letter, kind, color in [("M", "D", "blue"), ("Ẹ", "C", "purple")]:
            card = ctk.CTkFrame(sign_row, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=12, width=190, height=165)
            card.pack(side="left", padx=10)
            card.pack_propagate(False)
            self._hand_canvas(card, kind, 160, 110).pack(pady=(8, 0))
            ctk.CTkLabel(card, text=letter, font=(FONT, 18, "bold"), text_color="white", fg_color=self._color(color), corner_radius=20, width=42, height=34).pack()
        slots = ctk.CTkFrame(game, fg_color="transparent")
        slots.grid(row=2, column=0, pady=18)
        for _ in range(2):
            slot = ctk.CTkFrame(slots, width=140, height=90, fg_color=COLORS["panel_2"], border_color=COLORS["blue_2"], border_width=2, corner_radius=14)
            slot.pack(side="left", padx=12)
        bank = ctk.CTkFrame(game, fg_color="transparent")
        bank.grid(row=3, column=0, pady=8)
        for letter in WORD_BANK:
            ctk.CTkButton(bank, text=letter, width=48, height=42, fg_color=COLORS["card"], hover_color=COLORS["card_hover"], font=(FONT, 16, "bold")).pack(side="left", padx=4)
        self._word_history(game).grid(row=4, column=0, sticky="ew", padx=20, pady=(24, 14))
        self._side_score_panel(body, "Thông tin trận chơi", [
            ("🟡", "Điểm", "65", "yellow"), ("📖", "Từ", "3 / 8", "blue"),
            ("✓", "Đúng", "2", "green"), ("✕", "Sai", "1", "red"), ("◴", "Thời gian", "00:27", "purple"),
        ])
        self._bottom_controls(body, [("⌕  Kiểm tra", "blue", lambda: None), ("»  Bỏ qua", "purple", lambda: None), ("💡  Gợi ý", "green", lambda: None)])

    def _word_history(self, parent):
        box = ctk.CTkFrame(parent, fg_color=COLORS["panel_2"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        ctk.CTkLabel(box, text="Từ đã ghép", font=(FONT, 14, "bold"), text_color=COLORS["text"]).pack(side="left", padx=20, pady=16)
        for word, ok in [("BA", True), ("AN", True), ("CA", False), ("3", None), ("4", None), ("5", None), ("6", None), ("7", None), ("8", None)]:
            color = COLORS["green"] if ok else (COLORS["red"] if ok is False else COLORS["stroke_light"])
            ctk.CTkLabel(box, text=("✓  " if ok else "✕  " if ok is False else "") + word, font=(FONT, 13, "bold"), text_color=COLORS["text"], fg_color=COLORS["card"], corner_radius=9, width=70, height=34).pack(side="left", padx=6)
        return box

    # ---------- Reaction game ----------
    def show_reaction_game(self):
        self.clear_content()
        page = self._page()
        self._header(page, "PHẢN XẠ NHANH", "Làm đúng ký hiệu trước khi hết thời gian")
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(game, text="Yêu cầu: Hãy làm ký hiệu chữ  B", font=(FONT, 18, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 8))
        camera = ctk.CTkFrame(game, fg_color="#101725", border_color=COLORS["purple"], border_width=2, corner_radius=10, height=420)
        camera.grid(row=1, column=0, sticky="nsew", padx=24)
        camera.grid_propagate(False)
        ctk.CTkLabel(camera, text="CAMERA PREVIEW", font=(FONT, 18, "bold"), text_color=COLORS["muted"]).place(relx=0.5, rely=0.18, anchor="center")
        self._hand_canvas(camera, "B", 300, 240).place(relx=0.5, rely=0.55, anchor="center")
        ctk.CTkLabel(camera, text="●  Camera đang hoạt động", fg_color="#00000080", text_color=COLORS["text"], corner_radius=8, width=190, height=30).place(x=24, rely=0.9, anchor="w")
        self._reaction_history(game).grid(row=2, column=0, sticky="ew", padx=24, pady=18)
        self._side_score_panel(body, "", [
            ("⏱", "Thời gian còn lại", "03", "purple"), ("★", "Điểm", "95", "yellow"),
            ("🔥", "Combo", "3", "orange"), ("B", "Bạn đang làm", "B", "purple"),
            ("◎", "Độ chính xác", "96%", "blue"), ("✓", "Trạng thái", "Đúng", "green"),
        ])
        self._bottom_controls(body, [("▶  Bắt đầu", "green", lambda: None), ("↻  Làm lại", "blue", self.show_reaction_game), ("»  Câu tiếp theo", "purple", lambda: None)])

    def _reaction_history(self, parent):
        box = ctk.CTkFrame(parent, fg_color=COLORS["panel_2"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        ctk.CTkLabel(box, text="↺  Lịch sử lượt chơi", font=(FONT, 15, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(12, 8))
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 12))
        for n, letter, pct, ok in REACTION_HISTORY:
            color = COLORS["green"] if ok else COLORS["red"]
            chip = ctk.CTkFrame(row, fg_color=COLORS["card"], border_color=COLORS["purple"] if letter == "B" else COLORS["stroke"], border_width=1, corner_radius=10)
            chip.pack(side="left", padx=5)
            ctk.CTkLabel(chip, text=f"{n}   {letter}", font=(FONT, 14, "bold"), text_color=self._color("purple")).pack(padx=14, pady=(8, 0))
            ctk.CTkLabel(chip, text=f"{pct}  {'✓' if ok else '✕'}", font=(FONT, 11), text_color=color).pack(padx=14, pady=(0, 8))
        return box

    # ---------- Quiz game ----------
    def show_quiz_game(self):
        self.clear_content()
        page = self._page()
        self._header(page, "QUIZ KIẾN THỨC", "Trả lời câu hỏi về bảng chữ cái, từ vựng và câu giao tiếp")
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure((0, 1, 2, 3), weight=1)
        progress = ctk.CTkFrame(game, fg_color=COLORS["panel_2"], corner_radius=12)
        progress.grid(row=0, column=0, columnspan=4, sticky="ew", padx=22, pady=(18, 14))
        ctk.CTkLabel(progress, text="Câu 5 / 10", font=(FONT, 18, "bold"), text_color=COLORS["blue_2"]).pack(side="left", padx=20, pady=14)
        ctk.CTkProgressBar(progress, height=12, progress_color=COLORS["blue"]).pack(side="left", fill="x", expand=True, padx=18)
        ctk.CTkLabel(game, text="?  Câu hỏi", font=(FONT, 16, "bold"), text_color=COLORS["purple"]).grid(row=1, column=0, columnspan=4, sticky="w", padx=28, pady=(8, 0))
        ctk.CTkLabel(game, text="Ký hiệu nào là chữ C?", font=(FONT, 24, "bold"), text_color=COLORS["text"]).grid(row=2, column=0, columnspan=4, sticky="w", padx=28, pady=(8, 8))
        self._hand_canvas(game, "C", 270, 170).grid(row=3, column=0, columnspan=4, pady=(0, 14))
        for idx, (letter, kind, label, color, selected) in enumerate([("A", "V", "V", "blue", False), ("B", "O", "O", "purple", False), ("C", "C", "C", "green", True), ("D", "B", "B", "yellow", False)]):
            card = ctk.CTkFrame(game, fg_color=COLORS["card"], border_color=self._color(color) if selected else COLORS["stroke"], border_width=2 if selected else 1, corner_radius=14)
            card.grid(row=4, column=idx, sticky="nsew", padx=(22 if idx == 0 else 8, 22 if idx == 3 else 8), pady=(8, 18))
            ctk.CTkLabel(card, text=letter, font=(FONT, 16, "bold"), fg_color=self._color(color), corner_radius=20, width=36, height=32, text_color="white").pack(anchor="nw", padx=14, pady=12)
            self._hand_canvas(card, kind, 160, 110).pack()
            ctk.CTkLabel(card, text=label, font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(pady=(0, 12))
        self._side_score_panel(body, "Bảng điểm", [("🏆", "Điểm hiện tại", "120", "yellow"), ("✓", "Đúng", "4", "green"), ("✕", "Sai", "1", "red"), ("◷", "Thời gian còn lại", "01:15", "blue"), ("📖", "Chủ đề", "Tổng hợp", "blue")])
        self._bottom_controls(body, [("✓  Xác nhận", "blue", lambda: None), ("»  Bỏ qua", "card", lambda: None), ("✕  Kết thúc", "red", self.show_dashboard)])

    # ---------- Flashcard game ----------
    def show_flashcard_game(self):
        self.clear_content()
        page = self._page()
        self._header(page, "FLASHCARD", "Lật thẻ và ghép đúng chữ với ký hiệu")
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for r in range(3):
            for c in range(4):
                card = ctk.CTkFrame(game, width=160, height=115, fg_color="#161E5A", border_color=COLORS["purple"], border_width=1, corner_radius=12)
                card.grid(row=r, column=c, sticky="nsew", padx=12, pady=12)
                card.grid_propagate(False)
                if (r, c) in [(2, 0), (2, 1)]:
                    card.configure(fg_color="#0C3A1B", border_color=COLORS["green"], border_width=2)
                    ctk.CTkLabel(card, text="A", font=(FONT, 44, "bold"), text_color="#B6FF9F").place(relx=0.5, rely=0.48, anchor="center")
                    ctk.CTkLabel(card, text="✓", font=(FONT, 20, "bold"), text_color="white", fg_color=COLORS["green"], corner_radius=16, width=30, height=30).place(relx=0.85, rely=0.82, anchor="center")
                elif (r, c) == (0, 1):
                    card.configure(fg_color="#0C2344", border_color=COLORS["blue_2"], border_width=2)
                    ctk.CTkLabel(card, text="B", font=(FONT, 46, "bold"), text_color=COLORS["text"]).place(relx=0.5, rely=0.5, anchor="center")
                elif (r, c) == (1, 2):
                    card.configure(fg_color="#0C2344", border_color=COLORS["blue_2"], border_width=2)
                    self._hand_canvas(card, "V", 140, 100).place(relx=0.5, rely=0.55, anchor="center")
                else:
                    ctk.CTkLabel(card, text="✋  🌐  ✌", font=(FONT, 18), text_color="#31448F").place(relx=0.5, rely=0.5, anchor="center")
        self._side_score_panel(body, "Thông tin lượt chơi", [("▣", "Lượt mở", "8", "blue"), ("◎", "Cặp đúng", "3/6", "green"), ("◴", "Thời gian", "00:42", "orange"), ("🏆", "Điểm", "70", "yellow")])
        self._bottom_controls(body, [("↻  Chơi lại", "blue", self.show_flashcard_game), ("💡  Gợi ý   3", "purple", lambda: None), ("→  Tiếp tục", "green", lambda: None)])

    # ---------- Wheel game ----------
    def show_wheel_game(self):
        self.clear_content()
        page = self._page()
        self._header(page, "VÒNG QUAY THỬ THÁCH", "Quay để nhận thử thách ký hiệu bất ngờ")
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure(0, weight=1)
        wheel = tk.Canvas(game, width=520, height=470, bg=COLORS["panel"], bd=0, highlightthickness=0)
        wheel.grid(row=0, column=0, pady=(14, 0))
        self._draw_wheel(wheel, 260, 235, 200)
        stats = ctk.CTkFrame(game, fg_color=COLORS["panel_2"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        stats.grid(row=1, column=0, sticky="ew", padx=24, pady=14)
        for label, value, color in [("Số lượt quay", "3", "blue"), ("Điểm nhận được", "45", "yellow"), ("Thử thách hoàn thành", "2", "green")]:
            ctk.CTkLabel(stats, text=f"{label}\n{value}", font=(FONT, 16, "bold"), text_color=self._color(color), justify="center").pack(side="left", expand=True, fill="x", padx=20, pady=14)
        result = self._panel(body, row=0, column=1, sticky="nsew", padx=(14, 0))
        result.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(result, text="⭐  Thử thách nhận được", font=(FONT, 20, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, pady=(28, 12))
        ctk.CTkLabel(result, text="〽", font=(FONT, 68), text_color=COLORS["blue_2"]).grid(row=1, column=0)
        ctk.CTkLabel(result, text="Làm ký hiệu chữ M", font=(FONT, 24, "bold"), text_color=COLORS["text"]).grid(row=2, column=0, pady=(8, 4))
        ctk.CTkLabel(result, text="Phần thưởng  🟡  +20 điểm", font=(FONT, 17, "bold"), text_color=COLORS["yellow"], fg_color=COLORS["card"], corner_radius=10, width=280, height=54).grid(row=3, column=0, pady=12)
        ctk.CTkButton(result, text="🎡  Quay ngay", height=56, font=(FONT, 20, "bold"), fg_color=COLORS["blue"], command=lambda: None).grid(row=4, column=0, sticky="ew", padx=60, pady=(10, 4))
        ctk.CTkLabel(result, text="Số lượt quay hôm nay: 3/5", text_color=COLORS["muted"], font=(FONT, 13)).grid(row=5, column=0)
        ctk.CTkLabel(result, text="🎁  Phần thưởng hôm nay", font=(FONT, 18, "bold"), text_color=COLORS["text"]).grid(row=6, column=0, pady=(30, 10))
        reward = ctk.CTkFrame(result, fg_color="transparent")
        reward.grid(row=7, column=0, sticky="ew", padx=20)
        for t, c in [("10 điểm\nĐạt 1 lượt quay", "purple"), ("20 điểm\nĐạt 3 thử thách", "blue"), ("50 điểm\nĐạt 5 thử thách", "yellow")]:
            ctk.CTkLabel(reward, text=f"🛡\n{t}", font=(FONT, 13, "bold"), text_color=self._color(c), fg_color=COLORS["card"], corner_radius=12, width=130, height=90).pack(side="left", expand=True, padx=8)
        self._bottom_controls(body, [("←  Quay lại", "card", self.show_dashboard), ("📜  Lịch sử vòng quay", "blue", lambda: None), ("✓  Hoàn thành", "green", lambda: None)])

    def _draw_wheel(self, canvas, cx, cy, r):
        start = 90
        for i, (name, icon, color) in enumerate(SPIN_SEGMENTS):
            extent = 360 / len(SPIN_SEGMENTS)
            canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=start+i*extent, extent=extent, fill=color, outline="#111827", width=3)
            mid = math.radians(start + i*extent + extent / 2)
            tx = cx + math.cos(mid) * r * 0.55
            ty = cy - math.sin(mid) * r * 0.55
            canvas.create_text(tx, ty-12, text=icon, fill="white", font=(FONT, 26, "bold"))
            canvas.create_text(tx, ty+22, text=name, fill="white", font=(FONT, 14, "bold"), justify="center")
        canvas.create_oval(cx-55, cy-55, cx+55, cy+55, fill="#0B1220", outline="#334155", width=3)
        canvas.create_polygon(cx-28, cy-r-8, cx+28, cy-r-8, cx, cy-r+45, fill=COLORS["orange"], outline=COLORS["yellow"], width=3)

    # ---------- Shared body/control ----------
    def _game_body(self, page):
        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=340)
        body.grid_rowconfigure(0, weight=1)
        return body

    def _bottom_controls(self, parent, buttons):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        for idx, (text, color, cmd) in enumerate(buttons):
            fg = COLORS["card"] if color == "card" else self._color(color)
            ctk.CTkButton(box, text=text, height=54, corner_radius=10, fg_color=fg, hover_color=COLORS["card_hover"] if color == "card" else fg, font=(FONT, 17, "bold"), command=cmd).pack(side="left", expand=True, fill="x", padx=8)
        ctk.CTkButton(box, text="🏠  Menu", height=54, width=120, corner_radius=10, fg_color=COLORS["panel"], hover_color=COLORS["card_hover"], font=(FONT, 15, "bold"), command=self.show_dashboard).pack(side="left", padx=8)


class MinigameWindow(ctk.CTk):
    """Standalone app window."""

    def __init__(self):
        super().__init__()
        self.title("VSL Translate - Minigame")
        self.geometry(WINDOW_SIZE)
        self.minsize(1200, 720)
        self.configure(fg_color=COLORS["bg"])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        MinigameFrame(self).grid(row=0, column=0, sticky="nsew")


def open_minigame_window(parent=None):
    """Open the minigame UI from another Tk/CustomTkinter window."""
    if parent is None:
        app = MinigameWindow()
        app.mainloop()
        return app

    win = ctk.CTkToplevel(parent)
    win.title("VSL Translate - Minigame")
    win.geometry(WINDOW_SIZE)
    win.minsize(1200, 720)
    win.configure(fg_color=COLORS["bg"])
    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=1)
    MinigameFrame(win).grid(row=0, column=0, sticky="nsew")
    win.focus()
    return win
