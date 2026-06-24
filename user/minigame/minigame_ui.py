from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk
# --- Thêm vào phần đầu file minigame_ui.py ---
try:
    import auth_ui
    import user_db
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import auth_ui
    import user_db
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

    # --- Cập nhật lại hàm __init__ của class MinigameFrame ---
    def __init__(self, master, on_back: Optional[Callable[[], None]] = None, show_sidebar: bool = True, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self.on_back = on_back
        self.show_sidebar = show_sidebar
        self.current_screen = "dashboard"
        self.selected_guess_answer = "A"
        
        # Lấy ID trực tiếp từ Single Source of Truth (auth_ui)
        self.current_user_id = auth_ui.CURRENT_USER["id"] if auth_ui.CURRENT_USER else None
        
        self._build_layout()
        self.show_dashboard()
    def _get_auth(self):
        """Trích xuất module auth_ui một cách an toàn nhất"""
        import sys
        if 'auth_ui' in sys.modules: return sys.modules['auth_ui']
        if 'user.auth_ui' in sys.modules: return sys.modules['user.auth_ui']
        try:
            import auth_ui
            return auth_ui
        except Exception: 
            return None

    def _get_db(self):
        """Trích xuất module user_db một cách an toàn nhất"""
        import sys
        if 'user_db' in sys.modules: return sys.modules['user_db']
        if 'user.user_db' in sys.modules: return sys.modules['user.user_db']
        try:
            import user_db
            return user_db
        except Exception: 
            return None

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
        if hasattr(self, '_stop_word_timer'): self._stop_word_timer()
        if hasattr(self, '_stop_reaction_timer'): self._stop_reaction_timer()
        self.current_screen = "dashboard"
        self.clear_content()
        page = self._page()
        self._header(page, "MINIGAME", "Chơi để học ngôn ngữ ký hiệu vui hơn mỗi ngày")

        # Refresh lại ID người dùng mỗi lần vào Dashboard
        auth = self._get_auth()
        self.current_user = auth.CURRENT_USER if (auth and hasattr(auth, "CURRENT_USER")) else None
        self.current_user_id = self.current_user["id"] if self.current_user else None

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=300)
        body.grid_rowconfigure(1, weight=1)

        # 1. DẢI MENU GAME
        mode_row = ctk.CTkFrame(body, fg_color="transparent")
        mode_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        active_modes = [m for m in GAME_MODES if m.get("key") not in ("flashcard", "wheel")]
        for i in range(len(active_modes)): mode_row.grid_columnconfigure(i, weight=1)
        for i, item in enumerate(active_modes):
            card = self._game_mode_card(mode_row, item, featured=(i == 0))
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0 if i == len(active_modes) - 1 else 8))

        # 2. KHU VỰC TRUNG TÂM: BẢNG XẾP HẠNG
        main = self._panel(body, row=1, column=0, sticky="nsew", padx=(0, 14))
        main.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="🏆  Bảng xếp hạng tuần", font=(FONT, 20, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        
        if self.current_user_id:
            ctk.CTkLabel(header, text="Xem tất cả  →", font=(FONT, 14), text_color=COLORS["blue_2"], cursor="hand2").grid(row=0, column=1, sticky="e")
            ranks_frame = ctk.CTkFrame(main, fg_color="transparent")
            ranks_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
            
            leaderboard_data = []
            db = self._get_db()
            if db and hasattr(db, "get_leaderboard"):
                try:
                    db_ranks = db.get_leaderboard(5)
                    for idx, row in enumerate(db_ranks):
                        leaderboard_data.append((str(idx+1), ["🥇", "🥈", "🥉"][idx] if idx < 3 else "▪", row[0], str(row[1])))
                except Exception as e: print("Lỗi lấy DB BXH:", e)

            for idx, (rank, icon, name, score) in enumerate(leaderboard_data):
                is_me = (self.current_user and name == self.current_user.get("username"))
                row_bg = "#122A4F" if is_me else COLORS["card"]
                border = COLORS["blue"] if is_me else COLORS["stroke"]
                
                row = ctk.CTkFrame(ranks_frame, fg_color=row_bg, border_color=border, border_width=1, corner_radius=10, height=56)
                row.pack(fill="x", pady=6)
                row.pack_propagate(False)
                ctk.CTkLabel(row, text=icon, font=(FONT, 22)).pack(side="left", padx=(18, 14))
                ctk.CTkLabel(row, text=name, font=(FONT, 16, "bold" if is_me else "normal"), text_color=COLORS["text"]).pack(side="left")
                ctk.CTkLabel(row, text=f"{score} pt", font=(FONT, 16, "bold"), text_color=COLORS["yellow"] if idx < 3 else COLORS["muted"]).pack(side="right", padx=18)
        else:
            lock_card = ctk.CTkFrame(main, fg_color="transparent")
            lock_card.grid(row=1, column=0, sticky="nsew", pady=40)
            lock_card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(lock_card, text="🔒", font=(FONT, 46)).pack(pady=5)
            ctk.CTkLabel(lock_card, text="Tính năng yêu cầu Đăng nhập", font=(FONT, 16, "bold"), text_color=COLORS["text"]).pack(pady=2)
            ctk.CTkLabel(lock_card, text="Đăng nhập để xem vị trí của bạn trên bảng xếp hạng tuần\nvà tranh tài cùng mọi người nhé!", font=(FONT, 13), text_color=COLORS["muted"], justify="center", wraplength=400).pack(pady=4)
            ctk.CTkButton(lock_card, text="👤  Đăng nhập ngay", font=(FONT, 14, "bold"), height=42, width=170, corner_radius=10, fg_color=COLORS["blue"], hover_color="#0B62D5", command=self._trigger_login_flow).pack(pady=12)

        # 3. BOTTOM CONTROLS
        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=(0, 14), pady=(16, 0))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        self._daily_challenge(bottom).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._motivation_card(bottom).grid(row=0, column=1, sticky="ew")

        # 4. BẢNG THÀNH TÍCH 
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
        
        # Sửa lỗi tràn viền: Thêm wraplength=160 để ép xuống dòng nếu chữ quá dài
        ctk.CTkLabel(card, text=item["desc"], font=(FONT, 12), text_color=COLORS["muted"], justify="left", wraplength=160).grid(row=2, column=0, padx=18, pady=(4, 16), sticky="w")
        
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
        # BỎ FIX CỨNG HEIGHT: Để khung tự động giãn vừa với text
        card = ctk.CTkFrame(parent, fg_color=COLORS["panel"], border_color=COLORS["stroke"], border_width=1, corner_radius=14)
        card.grid_columnconfigure(1, weight=1)
        
        # Thêm pady=18 cho icon để tạo độ cao tự nhiên cho cả block
        ctk.CTkLabel(card, text="🎯", font=(FONT, 32), text_color=COLORS["orange"]).grid(row=0, column=0, rowspan=2, padx=20, pady=18)
        
        # Chỉnh sticky="sw" (đẩy xuống đáy) cho title và "nw" (đẩy lên đỉnh) cho mô tả để chữ không bị đè
        ctk.CTkLabel(card, text="Thử thách hôm nay", font=(FONT, 16, "bold"), text_color=COLORS["text"]).grid(row=0, column=1, sticky="sw", pady=(18, 2))
        ctk.CTkLabel(card, text="Hoàn thành 10 câu đoán chữ", font=(FONT, 13), text_color=COLORS["muted"]).grid(row=1, column=1, sticky="nw", pady=(0, 18))
        
        ctk.CTkLabel(card, text="6 / 10", font=(FONT, 18, "bold"), text_color=COLORS["blue_2"]).grid(row=0, column=2, rowspan=2, padx=16)
        
        # Rút gọn chữ "Phần thưởng" thành "Thưởng" cho đỡ chật
        ctk.CTkLabel(card, text="🏅 Thưởng\n+50 điểm", font=(FONT, 14, "bold"), text_color=COLORS["yellow"], justify="center").grid(row=0, column=3, rowspan=2, padx=(0, 20))
        return card

    def _motivation_card(self, parent):
        # BỎ FIX CỨNG HEIGHT
        card = ctk.CTkFrame(parent, fg_color="#0B2141", border_color=COLORS["blue"], border_width=1, corner_radius=14)
        
        # Bọc nội dung vào một frame trong suốt để quản lý padding dễ hơn
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=18, pady=18) # pady=18 sẽ tự chống viền cho text
        
        ctk.CTkLabel(content, text="🏆 Bạn đang làm rất tốt!", font=(FONT, 16, "bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        
        # Rút gọn chữ một chút và bọc wraplength=180 để tự động xuống dòng đẹp mắt
        ctk.CTkLabel(content, text="Cố gắng chút nữa để đạt mục tiêu nhé!", font=(FONT, 13), text_color=COLORS["muted"], justify="left", wraplength=180).pack(anchor="w")
        return card

    def _stats_panel(self, parent):
        panel = self._panel(parent, row=0, column=0) 
        for w in panel.winfo_children(): w.destroy()
            
        ctk.CTkLabel(panel, text="▮  Thành tích", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 16))
        
        if self.current_user_id:
            stats_data = []
            db = self._get_db()
            if db and hasattr(db, "get_user_minigame_stats"):
                try:
                    real_stats = db.get_user_minigame_stats(self.current_user_id)
                    if real_stats:
                        stats_data = [
                            ("🏆", "Điểm cao nhất", str(real_stats.get("DiemSo", 0)), "yellow"),
                            ("◎", "Tỉ lệ đúng", f"{real_stats.get('DoChinhXacTB', 0)}%", "green"),
                            ("🔥", "Chuỗi ngày học", str(real_stats.get("ChuoiNgayHoc", 0)), "orange"),
                            ("🎮", "Số lần tập", str(real_stats.get("TongSoLanTap", 0)), "blue"),
                            ("🎖", "Huy hiệu", str(max(1, real_stats.get("DiemSo", 0) // 100)), "purple"),
                        ]
                except Exception as e: print("Lỗi lấy DB Thành tích:", e)
            
            if not stats_data:
                stats_data = [("🏆", "Điểm cao nhất", "0", "yellow"), ("◎", "Tỉ lệ đúng", "0%", "green"), ("🔥", "Chuỗi ngày học", "0", "orange"), ("🎮", "Số lần tập", "0", "blue"), ("🎖", "Huy hiệu", "1", "purple")]

            for icon, title, value, color in stats_data:
                self._stat_tile(panel, icon, title, value, color).pack(fill="x", padx=18, pady=(0, 10))
        else:
            holder = ctk.CTkFrame(panel, fg_color="transparent")
            holder.pack(fill="both", expand=True, padx=20, pady=50)
            ctk.CTkLabel(holder, text="📊", font=(FONT, 40)).pack(pady=6)
            ctk.CTkLabel(holder, text="Chưa có dữ liệu", font=(FONT, 15, "bold"), text_color=COLORS["muted"]).pack(pady=2)
            ctk.CTkLabel(holder, text="Hãy kết nối tài khoản để theo dõi và cập nhật chuỗi tiến độ học tập cá nhân.", font=(FONT, 12), text_color=COLORS["muted"], justify="center", wraplength=220).pack(pady=4)
            
        return panel

    def _stat_tile(self, parent, icon: str, title: str, value: str, color: str):
        # GỠ BỎ: height=68 và tile.grid_propagate(False)
        tile = ctk.CTkFrame(parent, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        tile.grid_columnconfigure(1, weight=1)
        
        # Chỉnh lại pady ở trên và dưới để khung tự động lấy được chiều cao chuẩn
        ctk.CTkLabel(tile, text=icon, font=(FONT, 28), text_color=self._color(color)).grid(row=0, column=0, rowspan=2, padx=16, pady=12)
        ctk.CTkLabel(tile, text=title, font=(FONT, 13), text_color=COLORS["muted"]).grid(row=0, column=1, sticky="w", pady=(12, 0))
        ctk.CTkLabel(tile, text=value, font=(FONT, 22, "bold"), text_color=self._color(color)).grid(row=1, column=1, sticky="w", pady=(0, 12))
        return tile

    # ---------- Navigation ----------
    def open_game(self, key: str):
        # Dọn dẹp đồng hồ nếu đang chạy dở
        if hasattr(self, '_stop_word_timer'): self._stop_word_timer()
        if hasattr(self, '_stop_reaction_timer'): self._stop_reaction_timer()
        
        {
            "guess": getattr(self, "start_guess_game", self.show_dashboard),
            "word": getattr(self, "start_word_game", self.show_dashboard),
            # BÍ KÍP 1: Bật định tuyến cho 2 siêu phẩm mới
            "react": getattr(self, "start_reaction_game", self.show_dashboard),
            "quiz": getattr(self, "start_quiz_game", self.show_dashboard),
            "flashcard": getattr(self, "show_flashcard_game", self.show_dashboard),
            "wheel": getattr(self, "show_wheel_game", self.show_dashboard),
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

    # ---------- CỖ MÁY MINIGAME: ĐOÁN CHỮ (SURVIVAL MODE) ----------
    def _get_real_image(self, letter, size=(180, 180)):
        """Hàm lấy ảnh thật từ hệ thống thay vì vẽ Canvas"""
        import os
        from PIL import Image
        import customtkinter as ctk
        
        file_map = {
            "A": "A.png", "Ă": "A.png", "Â": "A.png", "B": "B.png", "C": "C.png", "D": "D.png", "Đ": "Dd.png",
            "E": "E.png", "Ê": "E.png", "G": "G.png", "H": "H.png", "I": "I.png", "K": "K.png", "L": "L.png",
            "M": "M.png", "N": "N.png", "O": "O.png", "Ô": "O.png", "Ơ": "O.png", "P": "P.png", "Q": "Q.png",
            "R": "R.png", "S": "S.png", "T": "T.png", "U": "U.png", "Ư": "U.png", "V": "V.png", "X": "X.png", "Y": "Y.png"
        }
        val = str(letter).upper().strip()
        file_name = file_map.get(val, f"{val}.png")
        
        # Truy tìm đường dẫn tuyệt đối của thư mục assets
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        path = os.path.join(base_dir, "user", "assets", "signs", "alphabet", file_name)
        
        if not os.path.exists(path):
            path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'signs', 'alphabet', file_name)
            
        if os.path.exists(path):
            try:
                img = Image.open(path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            except: pass
        return None

    def start_guess_game(self):
        # Khởi tạo chỉ số sinh tồn
        self.guess_hearts = 3
        self.guess_score = 0
        self.guess_combo = 0
        self.guess_history = []
        
        # Trích xuất danh sách chữ cái từ Dữ liệu gốc
        import random
        try:
            from .data import ALPHABET
            self.guess_pool = []
            for item in ALPHABET:
                val = item.get("label") or item.get("title") if isinstance(item, dict) else item
                val = str(val).replace("Chữ ", "").strip().upper()
                if len(val) == 1 and val not in self.guess_pool: # Chỉ lấy chữ cái đơn
                    self.guess_pool.append(val)
        except:
            self.guess_pool = ["A", "B", "C", "D", "E", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "X", "Y"]
            
        self._load_next_guess_question()

    def _load_next_guess_question(self):
        # Kiểm tra điều kiện Tử Vong (Game Over)
        if self.guess_hearts <= 0:
            self.show_guess_game_over()
            return
            
        import random
        self.guess_target = random.choice(self.guess_pool)
        distractors = [l for l in self.guess_pool if l != self.guess_target]
        random.shuffle(distractors)
        self.guess_choices = distractors[:3] + [self.guess_target]
        random.shuffle(self.guess_choices)
        
        self.show_guess_game()

    def show_guess_game(self):
        if not hasattr(self, 'guess_hearts'):
            self.start_guess_game()
            return
            
        self.clear_content()
        page = self._page()
        self._header(page, "ĐOÁN CHỮ CÁI", "Chế độ Sinh tồn: Sai 3 lần là Game Over!")
        body = self._game_body(page)
        
        # --- KHU VỰC TRUNG TÂM (GAME PLAY) ---
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure((0, 1), weight=1)
        
        # Thanh trạng thái (Mạng & Xu)
        status_bar = ctk.CTkFrame(game, fg_color="transparent")
        status_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 0))
        ctk.CTkLabel(status_bar, text="❤️ " * self.guess_hearts + "🖤 " * (3 - self.guess_hearts), font=(FONT, 24), text_color=COLORS["red"]).pack(side="left")
        ctk.CTkLabel(status_bar, text=f"💰 {self.guess_score} Xu", font=(FONT, 24, "bold"), text_color=COLORS["yellow"]).pack(side="right")
        
        ctk.CTkLabel(game, text="Ký hiệu tay này là chữ gì?", font=(FONT, 22, "bold"), text_color=COLORS["text"]).grid(row=1, column=0, columnspan=2, pady=(10, 8))
        
        # Nạp ảnh thật từ hệ thống
        img_box = ctk.CTkFrame(game, fg_color="#0D1424", corner_radius=16)
        img_box.grid(row=2, column=0, columnspan=2, pady=(4, 18))
        real_img = self._get_real_image(self.guess_target, size=(200, 200))
        
        if real_img:
            ctk.CTkLabel(img_box, text="", image=real_img).pack(padx=30, pady=30)
        else:
            self._hand_canvas(img_box, "B", 260, 210).pack(padx=20, pady=20) # Dự phòng

        # 4 Nút đáp án tương tác trực tiếp
        self.guess_buttons = []
        for idx, val in enumerate(self.guess_choices):
            btn = ctk.CTkButton(
                game, text=f"{chr(65+idx)}.  Chữ {val}", height=58, corner_radius=10,
                fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                border_color=COLORS["stroke"], border_width=1,
                font=(FONT, 18, "bold"), text_color=COLORS["text"]
            )
            btn.grid(row=3 + idx // 2, column=idx % 2, sticky="ew", padx=18, pady=8)
            btn.configure(command=lambda b=btn, v=val: self._check_guess_answer(b, v))
            self.guess_buttons.append(btn)

        # --- KHU VỰC BÊN PHẢI (POWER-UPS) ---
        side_panel = self._panel(body, row=0, column=1, sticky="nsew", padx=(14, 0))
        ctk.CTkLabel(side_panel, text="▮  Vật phẩm hỗ trợ", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Cơ chế Cửa hàng Vật phẩm
        def use_powerup(ptype):
            from tkinter import messagebox
            if ptype == "5050":
                if self.guess_score >= 50:
                    self.guess_score -= 50
                    wrong_answers = [b for b in self.guess_buttons if b.cget("text").split("Chữ ")[-1] != self.guess_target]
                    import random
                    for b in random.sample(wrong_answers, 2):
                        b.configure(text="", state="disabled", fg_color="#121826", border_color="#121826")
                    self.show_guess_game() # Reload UI để trừ tiền hiển thị
                else: messagebox.showinfo("Cửa hàng", "Bạn không đủ 50 Xu để dùng!")
            elif ptype == "heal":
                if self.guess_score >= 100:
                    if self.guess_hearts < 3:
                        self.guess_score -= 100
                        self.guess_hearts += 1
                        self.show_guess_game()
                    else: messagebox.showinfo("Đầy máu", "Bạn đang đầy máu, không cần dùng đâu!")
                else: messagebox.showinfo("Cửa hàng", "Bạn không đủ 100 Xu để dùng!")

        # Thẻ mua 50/50
        p1 = ctk.CTkFrame(side_panel, fg_color=COLORS["card"], border_color=COLORS["purple"], border_width=1, corner_radius=12)
        p1.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(p1, text="🃏", font=(FONT, 26)).pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(p1, text="Trợ giúp 50/50\nXóa 2 đáp án sai", justify="left", font=(FONT, 12)).pack(side="left")
        ctk.CTkButton(p1, text="-50 Xu", width=60, fg_color=COLORS["purple"], font=(FONT, 12, "bold"), command=lambda: use_powerup("5050")).pack(side="right", padx=14)

        # Thẻ mua Hồi sinh
        p2 = ctk.CTkFrame(side_panel, fg_color=COLORS["card"], border_color=COLORS["green"], border_width=1, corner_radius=12)
        p2.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(p2, text="💖", font=(FONT, 26)).pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(p2, text="Hồi sinh\nCộng 1 Trái tim", justify="left", font=(FONT, 12)).pack(side="left")
        ctk.CTkButton(p2, text="-100 Xu", width=60, fg_color=COLORS["green"], font=(FONT, 12, "bold"), command=lambda: use_powerup("heal")).pack(side="right", padx=14)
        
        # Thống kê hiện tại
        ctk.CTkFrame(side_panel, height=1, fg_color=COLORS["stroke_light"]).pack(fill="x", padx=20, pady=15)
        self._small_score(side_panel, "🔥", "Combo liên tiếp", str(self.guess_combo), "orange").pack(fill="x", padx=16, pady=6)
        self._small_score(side_panel, "🎯", "Số câu đã qua", str(len(self.guess_history)), "blue").pack(fill="x", padx=16, pady=6)

        self._bottom_controls(body, [("✕  Đầu hàng & Thoát", "red", self.show_dashboard)])

    def _check_guess_answer(self, btn, selected_val):
        for b in self.guess_buttons:
            b.configure(state="disabled") # Ngăn người chơi bấm spam
            
        if selected_val == self.guess_target:
            self.guess_combo += 1
            reward = 10 + (self.guess_combo * 2) # Combo càng cao, Vàng càng nhiều
            self.guess_score += reward
            self.guess_history.append((selected_val, True))
            btn.configure(fg_color="#17351F", border_color=COLORS["green"], text_color=COLORS["green"])
            self.after(500, self._load_next_guess_question) # Nhảy câu cực nhanh nếu đúng
        else:
            self.guess_hearts -= 1
            self.guess_combo = 0
            self.guess_history.append((selected_val, False))
            btn.configure(fg_color="#451A1F", border_color=COLORS["red"], text_color=COLORS["red"])
            
            # Hiện đáp án đúng màu xanh để học hỏi
            for b in self.guess_buttons:
                if b.cget("text").split("Chữ ")[-1] == self.guess_target:
                    b.configure(fg_color="#17351F", border_color=COLORS["green"], text_color=COLORS["green"])
            
            self.after(1500, self._load_next_guess_question) # Giữ lại 1.5s để người chơi thấy lỗi sai

    def show_guess_game_over(self):
        self.clear_content()
        page = self._page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        card = ctk.CTkFrame(page, fg_color=COLORS["panel"], corner_radius=20, border_color=COLORS["stroke"], border_width=1)
        card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text="💀", font=(FONT, 100)).pack(pady=(60, 20))
        ctk.CTkLabel(card, text="GAME OVER", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
        ctk.CTkLabel(card, text=f"Bạn đã sống sót qua {len(self.guess_history)} câu hỏi.", font=(FONT, 18), text_color=COLORS["muted"]).pack(pady=(0, 30))
        
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(0, 40))
        ctk.CTkLabel(score_box, text="Tổng Xu thu thập được", font=(FONT, 16), text_color=COLORS["muted"]).pack(pady=(20, 0))
        ctk.CTkLabel(score_box, text=f"💰 {self.guess_score}", font=(FONT, 48, "bold"), text_color=COLORS["yellow"]).pack(padx=60, pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="⟳ Chơi lại", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["blue"], command=self.start_guess_game).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🏠 Về Bảng điều khiển", font=(FONT, 18, "bold"), height=54, width=220, fg_color=COLORS["card"], hover_color=COLORS["card_hover"], command=self.show_dashboard).pack(side="left", padx=10)

    # ---------- Word game ----------
    # ---------- CỖ MÁY MINIGAME: GHÉP TỪ (TIME ATTACK) ----------
    def _stop_word_timer(self):
        if hasattr(self, 'word_timer_id') and self.word_timer_id:
            try: self.after_cancel(self.word_timer_id)
            except: pass
            self.word_timer_id = None

    def start_word_game(self):
        self._stop_word_timer()
        self.word_score = 0
        self.word_time_left = 60 # Bắt đầu với 60 giây sinh tử
        self.word_history = []
        
        # Ngân hàng dữ liệu từ vựng (Dùng từ không dấu để người chơi thao tác phím ảo nhanh nhất)
        self.word_pool = {
            "BA": "Người sinh ra mình (Nam)",
            "ME": "Người sinh ra mình (Nữ)",
            "ANH": "Con trai lớn trong nhà",
            "CHI": "Con gái lớn trong nhà",
            "EM": "Người nhỏ tuổi hơn mình",
            "HOC": "Hành động thu nhận kiến thức",
            "VUI": "Cảm xúc tích cực, hay cười",
            "BUON": "Cảm xúc tiêu cực, muốn khóc",
            "TEN": "Danh xưng dùng để gọi nhau",
            "BAN": "Người đang chơi game cùng tôi",
            "TOI": "Từ để chỉ bản thân mình",
            "CHAO": "Hành động khi gặp mặt nhau"
        }
        self._load_next_word_question()
        self._run_word_timer()

    def _load_next_word_question(self):
        import random
        if self.word_time_left <= 0:
            self.show_word_game_over()
            return
            
        self.word_target = random.choice(list(self.word_pool.keys()))
        self.word_hint = self.word_pool[self.word_target]
        self.word_user_input = [] # Xóa các phím người dùng đã nhập
        
        # Thuật toán tạo Bàn phím: Ký tự đúng + Ký tự nhiễu ngẫu nhiên
        target_chars = list(self.word_target)
        all_chars = "A B C D E G H I K L M N O P Q R S T U V X Y".split()
        distractors = [c for c in all_chars if c not in target_chars]
        random.shuffle(distractors)
        
        bank_size = 10
        needed = bank_size - len(target_chars)
        self.word_bank = target_chars + distractors[:needed]
        random.shuffle(self.word_bank)
        
        self.show_word_game()

    def _run_word_timer(self):
        if getattr(self, 'current_screen', '') != "word_game":
            return
            
        if self.word_time_left > 0:
            self.word_time_left -= 1
            # Kỹ thuật cập nhật Label an toàn, chống crash (Exception Tkinter)
            if hasattr(self, 'word_timer_label') and self.word_timer_label.winfo_exists():
                self.word_timer_label.configure(text=f"00:{self.word_time_left:02d}")
                color = COLORS["red"] if self.word_time_left <= 10 else COLORS["purple"]
                self.word_timer_label.configure(text_color=color)
            self.word_timer_id = self.after(1000, self._run_word_timer)
        else:
            self.show_word_game_over()

    def show_word_game(self):
        if not hasattr(self, 'word_time_left'):
            self.start_word_game()
            return
            
        self.current_screen = "word_game"
        self.clear_content()
        page = self._page()
        self._header(page, "GHÉP TỪ (TIME ATTACK)", "Đua với thời gian: Ghép đúng +5s, Sai/Bỏ qua -8s!")
        body = self._game_body(page)
        
        # --- KHU VỰC TRUNG TÂM ---
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure(0, weight=1)
        
        # Gợi ý
        ctk.CTkLabel(game, text=f"💡 Gợi ý: {self.word_hint}", font=(FONT, 17, "bold"), text_color=COLORS["text"], fg_color="#102238", corner_radius=8, height=45).grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 12))
        
        # Hiển thị dãy Ký hiệu tay (Chỉ hiện ảnh, giấu chữ đi để test trình độ)
        sign_row = ctk.CTkFrame(game, fg_color="transparent")
        sign_row.grid(row=1, column=0, pady=10)
        
        for char in self.word_target:
            card = ctk.CTkFrame(sign_row, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=12, width=130, height=130)
            card.pack(side="left", padx=6)
            card.pack_propagate(False)
            
            # Tái sử dụng Cỗ máy quét ảnh thật từ bước trước
            real_img = getattr(self, '_get_real_image', lambda c, s: None)(char, size=(100, 100))
            if real_img:
                ctk.CTkLabel(card, text="", image=real_img).pack(pady=(15, 0))
            else:
                ctk.CTkLabel(card, text="?", font=(FONT, 40, "bold"), text_color=COLORS["blue"]).pack(pady=40)
        
        # Ô trống chứa ký tự người dùng gõ
        slots = ctk.CTkFrame(game, fg_color="transparent")
        slots.grid(row=2, column=0, pady=18)
        for i in range(len(self.word_target)):
            char = self.word_user_input[i] if i < len(self.word_user_input) else ""
            slot = ctk.CTkFrame(slots, width=65, height=65, fg_color=COLORS["panel_2"], border_color=COLORS["green"] if char else COLORS["blue_2"], border_width=2, corner_radius=10)
            slot.pack(side="left", padx=8)
            slot.pack_propagate(False)
            ctk.CTkLabel(slot, text=char, font=(FONT, 28, "bold"), text_color=COLORS["text"]).place(relx=0.5, rely=0.5, anchor="center")
            
        # Bàn phím ảo
        bank = ctk.CTkFrame(game, fg_color="transparent")
        bank.grid(row=3, column=0, pady=8)
        for char in self.word_bank:
            btn = ctk.CTkButton(bank, text=char, width=54, height=54, fg_color=COLORS["card"], hover_color=COLORS["card_hover"], font=(FONT, 20, "bold"), command=lambda c=char: self._click_word_letter(c))
            btn.pack(side="left", padx=4)
            
        # Lịch sử
        self._real_word_history(game).grid(row=4, column=0, sticky="ew", padx=20, pady=(24, 14))
        
        # --- BẢNG ĐIỂM CỘT PHẢI ---
        self._build_word_score_panel(body)
        
        # Thanh điều khiển
        self._bottom_controls(body, [
            ("⌫  Xóa chữ", "orange", self._delete_word_letter), 
            ("✓  Kiểm tra", "blue", self._check_word_answer), 
            ("»  Bỏ qua (-8s)", "red", self._skip_word)
        ])

    def _click_word_letter(self, char):
        if len(self.word_user_input) < len(self.word_target):
            self.word_user_input.append(char)
            self.show_word_game()

    def _delete_word_letter(self):
        if self.word_user_input:
            self.word_user_input.pop()
            self.show_word_game()

    def _check_word_answer(self):
        if len(self.word_user_input) < len(self.word_target):
            from tkinter import messagebox
            messagebox.showwarning("Chưa xong", "Hãy điền đầy đủ các ô trống!")
            return
            
        user_word = "".join(self.word_user_input)
        if user_word == self.word_target:
            self.word_score += 15
            self.word_time_left += 5 # Thưởng
            self.word_history.append((self.word_target, True))
        else:
            self.word_time_left -= 8 # Phạt
            self.word_history.append((user_word, False))
            
        self._load_next_word_question()

    def _skip_word(self):
        self.word_time_left -= 8 # Bỏ qua cũng bị phạt thời gian
        self.word_history.append((self.word_target, False))
        self._load_next_word_question()
        
    def _real_word_history(self, parent):
        box = ctk.CTkFrame(parent, fg_color=COLORS["panel_2"], border_color=COLORS["stroke"], border_width=1, corner_radius=12)
        ctk.CTkLabel(box, text="Từ vừa ghép", font=(FONT, 14, "bold"), text_color=COLORS["text"]).pack(side="left", padx=20, pady=16)
        for word, ok in self.word_history[-5:]:
            color = COLORS["green"] if ok else COLORS["red"]
            ctk.CTkLabel(box, text=("✓ " if ok else "✕ ") + word, font=(FONT, 13, "bold"), text_color=COLORS["text"], fg_color=color, corner_radius=9, height=34).pack(side="left", padx=6, ipadx=10)
        return box

    def _build_word_score_panel(self, parent):
        panel = self._panel(parent, row=0, column=1, sticky="nsew", padx=(14, 0))
        ctk.CTkLabel(panel, text="▮  Time Attack", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 10))
        
        self._small_score(panel, "🏆", "Điểm số", str(self.word_score), "yellow").pack(fill="x", padx=16, pady=6)
        correct_count = len([x for x in self.word_history if x[1]])
        self._small_score(panel, "✅", "Đã đúng", str(correct_count), "green").pack(fill="x", padx=16, pady=6)
        
        # BÍ KÍP 2: Khung Đồng hồ tự động cập nhật
        timer_row = ctk.CTkFrame(panel, fg_color=COLORS["card"], border_color=COLORS["stroke"], border_width=1, corner_radius=12, height=62)
        timer_row.pack(fill="x", padx=16, pady=6)
        timer_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(timer_row, text="◴", font=(FONT, 24), text_color=COLORS["purple"]).grid(row=0, column=0, rowspan=2, padx=14, pady=10)
        ctk.CTkLabel(timer_row, text="Thời gian", font=(FONT, 12), text_color=COLORS["muted"]).grid(row=0, column=1, sticky="w", pady=(10, 0))
        
        timer_color = COLORS["red"] if self.word_time_left <= 10 else COLORS["purple"]
        self.word_timer_label = ctk.CTkLabel(timer_row, text=f"00:{max(0, self.word_time_left):02d}", font=(FONT, 22, "bold"), text_color=timer_color)
        self.word_timer_label.grid(row=1, column=1, sticky="w", pady=(0, 10))

    def show_word_game_over(self):
        self._stop_word_timer()
        self.current_screen = "word_game_over"
        self.clear_content()
        page = self._page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        card = ctk.CTkFrame(page, fg_color=COLORS["panel"], corner_radius=20, border_color=COLORS["stroke"], border_width=1)
        card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text="⏰", font=(FONT, 100)).pack(pady=(60, 20))
        ctk.CTkLabel(card, text="HẾT GIỜ!", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
        
        correct_count = len([x for x in self.word_history if x[1]])
        ctk.CTkLabel(card, text=f"Bạn đã chiến đấu kiên cường và ghép đúng {correct_count} từ.", font=(FONT, 18), text_color=COLORS["muted"]).pack(pady=(0, 30))
        
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(0, 40))
        ctk.CTkLabel(score_box, text="Tổng Điểm Kỷ Lục", font=(FONT, 16), text_color=COLORS["muted"]).pack(pady=(20, 0))
        ctk.CTkLabel(score_box, text=f"🏆 {self.word_score}", font=(FONT, 48, "bold"), text_color=COLORS["yellow"]).pack(padx=60, pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="⟳ Chơi lại", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["blue"], command=self.start_word_game).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🏠 Về Menu", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["card"], hover_color=COLORS["card_hover"], command=self.show_dashboard).pack(side="left", padx=10)

    # =========================================================================
    # CỖ MÁY MINIGAME 3: PHẢN XẠ NHANH (COMBO & FRENZY MODE)
    # =========================================================================
    def _stop_reaction_timer(self):
        if hasattr(self, 'react_timer_id') and self.react_timer_id:
            try: self.after_cancel(self.react_timer_id)
            except: pass
            self.react_timer_id = None

    def start_reaction_game(self):
        self._stop_reaction_timer()
        self.react_score = 0
        self.react_combo = 0
        self.react_lives = 3
        self.react_frenzy = False
        
        try:
            from .data import ALPHABET
            self.react_pool = [str(item.get("label", item)).replace("Chữ ", "").strip().upper() for item in ALPHABET if len(str(item.get("label", item)).replace("Chữ ", "").strip()) == 1]
        except:
            self.react_pool = ["A", "B", "C", "D", "E", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "X", "Y"]
            
        self._load_next_reaction()

    def _load_next_reaction(self):
        if self.react_lives <= 0:
            self.show_reaction_game_over()
            return
            
        import random
        self.react_target = random.choice(self.react_pool)
        distractors = random.sample([x for x in self.react_pool if x != self.react_target], 3)
        self.react_choices = distractors + [self.react_target]
        random.shuffle(self.react_choices)
        
        # Nhịp độ sinh tử: Frenzy Mode chỉ có 1.5s, Bình thường có 3s
        self.react_max_time = 1.5 if self.react_frenzy else 3.0
        self.react_time_left = self.react_max_time
        
        self.show_reaction_game()
        self._run_reaction_timer()

    def _run_reaction_timer(self):
        if getattr(self, 'current_screen', '') != "react_game": return
            
        if self.react_time_left > 0:
            self.react_time_left -= 0.1
            if hasattr(self, 'react_prog') and self.react_prog.winfo_exists():
                self.react_prog.set(max(0, self.react_time_left / self.react_max_time))
                if self.react_time_left < 1.0 and not self.react_frenzy:
                    self.react_prog.configure(progress_color=COLORS["red"])
            self.react_timer_id = self.after(100, self._run_reaction_timer)
        else:
            self._check_reaction_answer(None, "TIMEOUT")

    def show_reaction_game(self):
        self.current_screen = "react_game"
        self.clear_content()
        page = self._page()
        
        title = "🔥 FRENZY MODE 🔥" if self.react_frenzy else "PHẢN XẠ NHANH"
        sub = "ĐIỂM x5! TỐC ĐỘ BÀN THỜ!" if self.react_frenzy else "Combo & Frenzy: Tốc độ quyết định tất cả!"
        self._header(page, title, sub)
        
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure((0, 1), weight=1)
        
        if self.react_frenzy: # Đổi màu UI khi đang Cuồng Nộ
            game.configure(border_color=COLORS["orange"], border_width=2)
            
        status_bar = ctk.CTkFrame(game, fg_color="transparent")
        status_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 0))
        ctk.CTkLabel(status_bar, text="❤️ " * self.react_lives + "🖤 " * (3 - self.react_lives), font=(FONT, 24), text_color=COLORS["red"]).pack(side="left")
        ctk.CTkLabel(status_bar, text=f"💰 {self.react_score} Xu", font=(FONT, 24, "bold"), text_color=COLORS["yellow"]).pack(side="right")
        
        prog_color = COLORS["orange"] if self.react_frenzy else COLORS["blue"]
        self.react_prog = ctk.CTkProgressBar(game, height=14, corner_radius=7, progress_color=prog_color, fg_color=COLORS["panel_2"])
        self.react_prog.grid(row=1, column=0, columnspan=2, sticky="ew", padx=30, pady=(15, 5))
        self.react_prog.set(1.0)
        
        img_box = ctk.CTkFrame(game, fg_color="#0D1424", corner_radius=16)
        img_box.grid(row=2, column=0, columnspan=2, pady=10)
        real_img = getattr(self, '_get_real_image', lambda c, s: None)(self.react_target, size=(180, 180))
        if real_img: ctk.CTkLabel(img_box, text="", image=real_img).pack(padx=20, pady=20)
        else: ctk.CTkLabel(img_box, text="?", font=(FONT, 60)).pack(padx=60, pady=60)
            
        self.react_buttons = []
        for idx, val in enumerate(self.react_choices):
            btn = ctk.CTkButton(
                game, text=f"Chữ {val}", height=55, corner_radius=12,
                fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                border_color=COLORS["stroke"], border_width=1, font=(FONT, 20, "bold"), text_color=COLORS["text"]
            )
            btn.grid(row=3 + idx // 2, column=idx % 2, sticky="ew", padx=15, pady=8)
            btn.configure(command=lambda b=btn, v=val: self._check_reaction_answer(b, v))
            self.react_buttons.append(btn)
            
        side_panel = self._panel(body, row=0, column=1, sticky="nsew", padx=(14, 0))
        ctk.CTkLabel(side_panel, text="▮  Chỉ số", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 10))
        self._small_score(side_panel, "🔥", "COMBO", f"x{self.react_combo}", "orange" if self.react_combo > 0 else "muted").pack(fill="x", padx=16, pady=6)
        
        frenzy_box = ctk.CTkFrame(side_panel, fg_color=COLORS["card"], corner_radius=12)
        frenzy_box.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(frenzy_box, text="Thanh Cuồng Nộ", font=(FONT, 14, "bold"), text_color=COLORS["orange"]).pack(pady=(10, 5))
        f_prog = ctk.CTkProgressBar(frenzy_box, height=10, progress_color=COLORS["orange"], fg_color=COLORS["panel_2"])
        f_prog.pack(fill="x", padx=20, pady=(0, 15))
        f_prog.set(min(1.0, self.react_combo / 5.0))
        
        self._bottom_controls(body, [("✕  Đầu hàng", "red", self.show_dashboard)])

    def _check_reaction_answer(self, btn, selected_val):
        self._stop_reaction_timer()
        for b in self.react_buttons: b.configure(state="disabled")
            
        if selected_val == self.react_target:
            self.react_combo += 1
            multiplier = 5 if self.react_frenzy else (1 + self.react_combo * 0.2)
            self.react_score += int(10 * multiplier)
            
            if self.react_combo >= 5 and not self.react_frenzy:
                self.react_frenzy = True # KÍCH HOẠT FRENZY!
                
            if btn: btn.configure(fg_color="#17351F", border_color=COLORS["green"])
            self.after(200, self._load_next_reaction) # Siêu nhanh
        else:
            self.react_lives -= 1
            self.react_combo = 0
            self.react_frenzy = False
            
            if btn: btn.configure(fg_color="#451A1F", border_color=COLORS["red"])
            for b in self.react_buttons:
                if b.cget("text") == f"Chữ {self.react_target}":
                    b.configure(fg_color="#17351F", border_color=COLORS["green"])
            self.after(1000, self._load_next_reaction)

    def show_reaction_game_over(self):
        self._stop_reaction_timer()
        self.current_screen = "react_game_over"
        self.clear_content()
        page = self._page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        card = ctk.CTkFrame(page, fg_color=COLORS["panel"], corner_radius=20, border_color=COLORS["stroke"], border_width=1)
        card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text="💥", font=(FONT, 100)).pack(pady=(60, 20))
        ctk.CTkLabel(card, text="GAME OVER", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
        
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(20, 40))
        ctk.CTkLabel(score_box, text="Điểm Phản Xạ Kỷ Lục", font=(FONT, 16), text_color=COLORS["muted"]).pack(pady=(20, 0))
        ctk.CTkLabel(score_box, text=f"💰 {self.react_score}", font=(FONT, 48, "bold"), text_color=COLORS["orange"]).pack(padx=60, pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="⟳ Chơi lại", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["blue"], command=self.start_reaction_game).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🏠 Menu", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["card"], command=self.show_dashboard).pack(side="left", padx=10)

    # =========================================================================
    # CỖ MÁY MINIGAME 4: TRẮC NGHIỆM KIẾN THỨC (HIGH STAKES / BETTING)
    # =========================================================================
    def start_quiz_game(self):
        self.quiz_bank = 100 # Cho sẵn vốn khởi nghiệp
        self.quiz_round = 1
        
        import random
        try:
            from .data import ALPHABET
            self.quiz_pool = [str(item.get("label", item)).replace("Chữ ", "").strip().upper() for item in ALPHABET if len(str(item.get("label", item)).replace("Chữ ", "").strip()) == 1]
        except:
            self.quiz_pool = list("ABCDEGHIJKLMNOPQRSTUVXY")
            
        self.show_quiz_betting()

    def show_quiz_betting(self):
        if self.quiz_bank <= 0:
            self.show_quiz_game_over()
            return
            
        self.current_screen = "quiz_bet"
        self.clear_content()
        page = self._page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        card = ctk.CTkFrame(page, fg_color=COLORS["panel"], corner_radius=20, border_color=COLORS["stroke"], border_width=1)
        card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text="⚖️ VÒNG " + str(self.quiz_round), font=(FONT, 28, "bold"), text_color=COLORS["blue"]).pack(pady=(40, 10))
        ctk.CTkLabel(card, text="Đấu Trường Triệu Phú", font=(FONT, 16), text_color=COLORS["muted"]).pack()
        
        ctk.CTkLabel(card, text=f"Tài sản: 💰 {self.quiz_bank} Xu", font=(FONT, 36, "bold"), text_color=COLORS["yellow"]).pack(pady=(30, 20))
        ctk.CTkLabel(card, text="Bạn muốn cược bao nhiêu Xu cho câu hỏi tiếp theo?", font=(FONT, 18), text_color=COLORS["text"]).pack(pady=(0, 20))
        
        bet_frame = ctk.CTkFrame(card, fg_color="transparent")
        bet_frame.pack()
        
        # Mệnh giá cược
        bets = [10, 25, 50, self.quiz_bank]
        for b in bets:
            if b <= self.quiz_bank:
                txt = f"Cược {b}" if b < self.quiz_bank else "🎲 ALL IN!"
                color = COLORS["blue"] if b < self.quiz_bank else COLORS["red"]
                ctk.CTkButton(bet_frame, text=txt, font=(FONT, 18, "bold"), height=54, fg_color=color, hover_color=COLORS["card_hover"], command=lambda bet=b: self._start_quiz_question(bet)).pack(side="left", padx=10)
                
        ctk.CTkButton(card, text="Chốt lời & Nghỉ chơi", font=(FONT, 16, "bold"), fg_color="transparent", text_color=COLORS["muted"], hover_color=COLORS["card"], command=self.show_quiz_game_over).pack(pady=(40, 0))

    def _start_quiz_question(self, bet_amount):
        self.current_bet = bet_amount
        import random
        self.quiz_target = random.choice(self.quiz_pool)
        distractors = random.sample([x for x in self.quiz_pool if x != self.quiz_target], 3)
        self.quiz_choices = distractors + [self.quiz_target]
        random.shuffle(self.quiz_choices)
        self.show_quiz_game()

    def show_quiz_game(self):
        self.current_screen = "quiz_game"
        self.clear_content()
        page = self._page()
        self._header(page, "TRẮC NGHIỆM (HIGH STAKES)", f"Tiền cược: 💰 {self.current_bet} Xu. Đúng ăn gấp đôi, Sai mất trắng!")
        
        body = self._game_body(page)
        game = self._panel(body, row=0, column=0, sticky="nsew")
        game.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(game, text="Ký hiệu này là chữ gì?", font=(FONT, 24, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        
        img_box = ctk.CTkFrame(game, fg_color="#0D1424", corner_radius=16)
        img_box.grid(row=1, column=0, columnspan=2, pady=10)
        real_img = getattr(self, '_get_real_image', lambda c, s: None)(self.quiz_target, size=(200, 200))
        if real_img: ctk.CTkLabel(img_box, text="", image=real_img).pack(padx=30, pady=30)
        else: ctk.CTkLabel(img_box, text="?", font=(FONT, 60)).pack(padx=60, pady=60)
            
        self.quiz_buttons = []
        for idx, val in enumerate(self.quiz_choices):
            btn = ctk.CTkButton(
                game, text=f"Chữ {val}", height=60, corner_radius=12,
                fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                font=(FONT, 20, "bold"), text_color=COLORS["text"]
            )
            btn.grid(row=2 + idx // 2, column=idx % 2, sticky="ew", padx=15, pady=10)
            btn.configure(command=lambda b=btn, v=val: self._check_quiz_answer(b, v))
            self.quiz_buttons.append(btn)
            
        side_panel = self._panel(body, row=0, column=1, sticky="nsew", padx=(14, 0))
        self._small_score(side_panel, "🏦", "Vốn hiện tại", str(self.quiz_bank), "green").pack(fill="x", padx=16, pady=20)
        self._small_score(side_panel, "🎲", "Đang cược", str(self.current_bet), "orange").pack(fill="x", padx=16, pady=6)
        
        self._bottom_controls(body, [("✕  Bỏ chạy (Mất tiền cược)", "red", self.show_quiz_betting)])

    def _check_quiz_answer(self, btn, selected_val):
        for b in self.quiz_buttons: b.configure(state="disabled")
        
        if selected_val == self.quiz_target:
            self.quiz_bank += self.current_bet # Thắng cược
            btn.configure(fg_color="#17351F", border_color=COLORS["green"])
            self.quiz_round += 1
            self.after(1000, self.show_quiz_betting)
        else:
            self.quiz_bank -= self.current_bet # Thua cược
            btn.configure(fg_color="#451A1F", border_color=COLORS["red"])
            for b in self.quiz_buttons:
                if b.cget("text") == f"Chữ {self.quiz_target}":
                    b.configure(fg_color="#17351F", border_color=COLORS["green"])
            self.quiz_round += 1
            self.after(1500, self.show_quiz_betting)

    def show_quiz_game_over(self):
        self.current_screen = "quiz_game_over"
        self.clear_content()
        page = self._page()
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        card = ctk.CTkFrame(page, fg_color=COLORS["panel"], corner_radius=20, border_color=COLORS["stroke"], border_width=1)
        card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
        card.grid_columnconfigure(0, weight=1)
        
        if self.quiz_bank <= 0:
            ctk.CTkLabel(card, text="💸", font=(FONT, 100)).pack(pady=(60, 20))
            ctk.CTkLabel(card, text="PHÁ SẢN!", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
        else:
            ctk.CTkLabel(card, text="👑", font=(FONT, 100)).pack(pady=(60, 20))
            ctk.CTkLabel(card, text="CHỐT LỜI THÀNH CÔNG", font=(FONT, 36, "bold"), text_color=COLORS["green"]).pack(pady=(0, 10))
            
        ctk.CTkLabel(card, text=f"Bạn đã rời khỏi sàn đấu với tài sản:", font=(FONT, 18), text_color=COLORS["muted"]).pack(pady=(0, 30))
        
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(0, 40))
        ctk.CTkLabel(score_box, text=f"💰 {self.quiz_bank} Xu", font=(FONT, 54, "bold"), text_color=COLORS["yellow"]).pack(padx=80, pady=20)
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="⟳ Khởi nghiệp lại", font=(FONT, 18, "bold"), height=54, width=200, fg_color=COLORS["blue"], command=self.start_quiz_game).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🏠 Về Menu", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["card"], command=self.show_dashboard).pack(side="left", padx=10)
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
    def _trigger_login_flow(self):
        """Kích hoạt màn hình Đăng nhập NHÚNG TRỰC TIẾP vào Minigame (Không dùng Pop-up)"""
        try:
            auth = self._get_auth()
            if auth and hasattr(auth, 'AuthFrame'):
                # 1. Dọn dẹp sạch sẽ giao diện Dashboard hiện tại
                self.clear_content()
                
                # 2. Tạo một Container mới để chứa Form Đăng nhập
                auth_container = ctk.CTkFrame(self.content, fg_color="transparent")
                auth_container.pack(fill="both", expand=True)
                
                # 3. Tạo thanh điều hướng trên cùng (Nút Back bảo vệ UX)
                top_bar = ctk.CTkFrame(auth_container, fg_color="transparent", height=60)
                top_bar.pack(fill="x", padx=30, pady=(20, 0))
                
                back_btn = ctk.CTkButton(
                    top_bar, 
                    text="←  Quay lại Minigame", 
                    font=(FONT, 15, "bold"), 
                    fg_color="transparent", 
                    text_color=COLORS["muted"], 
                    hover_color=COLORS["card"],
                    width=180,
                    height=40,
                    command=self.show_dashboard  # Bấm vào sẽ tự động render lại Dashboard
                )
                back_btn.pack(side="left")
                
                # 4. Nhúng thẳng AuthFrame (Form Đăng nhập/Đăng ký) vào giữa màn hình
                form_wrapper = ctk.CTkFrame(auth_container, fg_color="transparent")
                form_wrapper.pack(fill="both", expand=True, pady=20)
                
                # Khởi tạo panel từ auth_ui.py và móc nối hàm callback
                login_panel = auth.AuthFrame(form_wrapper, on_success=self._on_login_success_callback)
                login_panel.pack(expand=True, fill="both")
                
            else:
                print("Lỗi hệ thống: Không tìm thấy class AuthFrame trong module auth_ui!")
        except Exception as e:
            print("Lỗi nhúng panel xác thực:", e)

    def _on_login_success_callback(self):
        """Hàm Callback Kích hoạt ngay khi Đăng nhập Thành công"""
        # 1. Cập nhật lại thông tin User ID ngay lập tức
        auth = self._get_auth()
        self.current_user = auth.CURRENT_USER if (auth and hasattr(auth, "CURRENT_USER")) else None
        self.current_user_id = self.current_user["id"] if self.current_user else None
        
        # 2. Render lại UI Dashboard (Thuật toán sẽ tự xóa form Login và load DB thật)
        self.show_dashboard()
        
        # 3. ĐỒNG BỘ GIAO DIỆN SIDEBAR CỦA UI_USER (Chuẩn xác như study_ui)
        try:
            toplevel = self.winfo_toplevel()
            # Tìm chính xác hàm refresh_sidebar_auth mà bạn đã khai báo trong ui_user.py
            if hasattr(toplevel, "refresh_sidebar_auth"):
                toplevel.refresh_sidebar_auth()
                print("-> Đã đồng bộ Sidebar App Tổng qua hàm: refresh_sidebar_auth")
            else:
                # Dự phòng nếu mở file main_minigame.py chạy độc lập không có ui_user
                print("Đang chạy độc lập, không có sidebar để cập nhật.")
        except Exception as e:
            print("Cảnh báo: Không thể đồng bộ Sidebar App tổng:", e)

class MinigameWindow(ctk.CTk):
    """Standalone app window."""

    def __init__(self, master, on_back: Optional[Callable[[], None]] = None, show_sidebar: bool = True, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], **kwargs)
        self.on_back = on_back
        self.show_sidebar = show_sidebar
        self.current_screen = "dashboard"
        self.selected_guess_answer = "A"
        
        # Gọi an toàn, nếu lỗi thì tự động gán None để UI vẫn chạy tiếp
        self.current_user = None
        auth = self._get_auth()
        if auth and hasattr(auth, "CURRENT_USER") and auth.CURRENT_USER:
            self.current_user = auth.CURRENT_USER
            
        self.current_user_id = self.current_user["id"] if self.current_user else None
        
        self._build_layout()
        self.show_dashboard()



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
