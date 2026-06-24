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
    # ---------- Navigation ----------
    def open_game(self, key: str):
        # Dọn dẹp đồng hồ nếu đang chạy dở
        if hasattr(self, '_stop_word_timer'): self._stop_word_timer()
        if hasattr(self, '_stop_reaction_timer'): self._stop_reaction_timer()
        
        {
            "guess": getattr(self, "show_sign_rain_game", self.show_dashboard),
            "word": getattr(self, "start_word_game", self.show_dashboard),
            "react": getattr(self, "start_reaction_game", self.show_dashboard),
            "quiz": getattr(self, "show_safecracker_game", self.show_dashboard), # ĐÃ SỬA DÒNG NÀY
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

    # =========================================================================
    # CỖ MÁY MINIGAME 1: MƯA KÝ HIỆU (SIGN RAIN / DEFENDER)
    # =========================================================================
    # =========================================================================
    # CỖ MÁY MINIGAME 1: MƯA KÝ HIỆU (SIGN RAIN / DEFENDER)
    # =========================================================================
    def show_sign_rain_game(self):
        """Giao diện & Logic cho game Mưa Ký Hiệu (Sign Rain)"""
        # Dọn dẹp các timer cũ nếu có
        if hasattr(self, '_stop_word_timer'): self._stop_word_timer()
        if hasattr(self, '_stop_reaction_timer'): self._stop_reaction_timer()
        
        self.current_screen = "sign_rain"
        self.clear_content()
        page = self._page()
        
        # --- CẤU TRÚC DỮ LIỆU GAME (STATE) ---
        self.sr_is_playing = False
        self.sr_score = 0
        self.sr_lives = 3
        self.sr_active_targets = []  
        self.sr_spawn_counter = 0
        self.sr_speed_multiplier = 1.0
        self.sr_cap = None
        self.sr_camera_after_id = None
        self.sr_game_after_id = None
        
        # Bộ biến AI
        self.sequence_data = []
        self.prev_wx = None
        self.prev_wy = None
        self.mp_hands = None
        self.mp_draw = None
        self.ai_session = None
        self.ai_labels = None

        # --- GIAO DIỆN CHÍNH ---
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="MƯA KÝ HIỆU 🌧️", font=(FONT, 30, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        
        def go_back():
            self.sr_is_playing = False
            if self.sr_cap: self.sr_cap.release()
            if self.sr_camera_after_id: self.after_cancel(self.sr_camera_after_id)
            if self.sr_game_after_id: self.after_cancel(self.sr_game_after_id)
            self.show_dashboard()
            
        ctk.CTkButton(header, text="← Trở về", font=(FONT, 15, "bold"), fg_color=COLORS["panel"], hover_color=COLORS["stroke"], height=40, command=go_back).grid(row=0, column=1, sticky="e", padx=20)

        body = self._game_body(page)

        # --- CỘT TRÁI: KHU VỰC GAME (CANVAS) ---
        game_board = ctk.CTkFrame(body, fg_color=COLORS["panel_2"], border_color=COLORS["stroke"], border_width=2, corner_radius=16)
        game_board.grid(row=0, column=0, sticky="nsew")
        
        import tkinter as tk
        self.sr_canvas = tk.Canvas(game_board, bg="#080C11", highlightthickness=0)
        self.sr_canvas.pack(fill="both", expand=True, padx=15, pady=15)
        
        # --- CỘT PHẢI: CAMERA & BẢNG ĐIỂM ---
        right_panel = self._panel(body, row=0, column=1, sticky="nsew", padx=(14, 0))
        
        stats_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["card"], corner_radius=16)
        stats_frame.pack(fill="x", padx=16, pady=16)
        
        score_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        score_row.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(score_row, text="Điểm số:", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(side="left")
        self.lbl_score = ctk.CTkLabel(score_row, text="0", font=(FONT, 28, "bold"), text_color=COLORS["yellow"])
        self.lbl_score.pack(side="right")
        
        lives_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        lives_row.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkLabel(lives_row, text="Mạng:", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(side="left")
        self.lbl_lives = ctk.CTkLabel(lives_row, text="❤️ ❤️ ❤️", font=(FONT, 22), text_color=COLORS["red"])
        self.lbl_lives.pack(side="right")
        
        cam_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["panel_2"], corner_radius=16)
        cam_frame.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(cam_frame, text="Camera AI", font=(FONT, 16, "bold"), text_color=COLORS["blue_2"]).pack(pady=(15, 5))
        
        self.sr_video_label = ctk.CTkLabel(cam_frame, text="📷 Đang chờ...", height=200, fg_color="#05080D", corner_radius=12)
        self.sr_video_label.pack(fill="x", padx=15, pady=(0, 15))
        
        self.lbl_ai_detect = ctk.CTkLabel(cam_frame, text="AI Đang thấy: --", font=(FONT, 16, "bold"), text_color=COLORS["green"])
        self.lbl_ai_detect.pack(pady=(0, 15))
        
        self.btn_sr_start = ctk.CTkButton(right_panel, text="▶ BẮT ĐẦU CHƠI", font=(FONT, 18, "bold"), height=60, corner_radius=16, fg_color=COLORS["blue"], hover_color="#0B62D5")
        self.btn_sr_start.pack(fill="x", side="bottom", padx=16, pady=16)

        # ==================================================
        # CORE LOGIC: CÁC HÀM XỬ LÝ (NESTED FUNCTIONS)
        # ==================================================
        def load_ai():
            """Nạp Model AI và Mediapipe"""
            import mediapipe as mp
            import numpy as np
            import onnxruntime as ort
            import os
            
            if not self.mp_hands:
                self.mp_hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
                self.mp_draw = mp.solutions.drawing_utils
                
            if not self.ai_session:
                try:
                    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'model.onnx'))
                    label_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'labels.npy'))
                    if not os.path.exists(model_path): model_path = "model/model.onnx"
                    if not os.path.exists(label_path): label_path = "model/labels.npy"
                    
                    self.ai_session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                    self.ai_labels = np.load(label_path)
                    return True
                except Exception as e:
                    print("Lỗi load AI:", e)
                    return False
            return True

        def hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy):
            import numpy as np
            wx, wy = landmarks[0].x, landmarks[0].y
            vector = []
            for i in range(1, 21):
                vector.extend([landmarks[i].x - wx, landmarks[i].y - wy])
            delta_x = (wx - prev_wx)*30 if prev_wx else 0.0
            delta_y = (wy - prev_wy)*30 if prev_wy else 0.0
            vector.extend([hand_type, delta_x, delta_y])
            return np.array(vector), wx, wy

        def login_and_save(score):
            """Hàm tạm lưu điểm và gọi màn hình đăng nhập"""
            self.pending_save_score = score
            self._trigger_login_flow()

        def game_over():
            self.sr_is_playing = False
            
            # 1. CHỐNG LAG: Phải giải phóng (Release) Camera ngay lập tức
            if self.sr_cap:
                self.sr_cap.release()
                self.sr_cap = None
            if hasattr(self, 'sr_video_label') and self.sr_video_label.winfo_exists():
                self.sr_video_label.configure(image="", text="Đã tắt Camera")

            self.sr_canvas.delete("all")
            self.sr_canvas.create_text(self.sr_canvas.winfo_width()/2, self.sr_canvas.winfo_height()/2 - 40, text="GAME OVER", font=(FONT, 50, "bold"), fill=COLORS["red"])
            self.sr_canvas.create_text(self.sr_canvas.winfo_width()/2, self.sr_canvas.winfo_height()/2 + 10, text=f"Điểm của bạn: {self.sr_score}", font=(FONT, 25), fill=COLORS["text"])
            self.btn_sr_start.configure(text="⟳ CHƠI LẠI", state="normal", fg_color=COLORS["orange"], hover_color="#CC7A00")
            
            # 2. XỬ LÝ LƯU DATABASE & GỢI Ý ĐĂNG NHẬP
            if self.current_user_id:
                try:
                    db = self._get_db()
                    if db and hasattr(db, 'get_conn'):
                        conn = db.get_conn()
                        cursor = conn.cursor()
                        # Cập nhật điểm số và tăng số lần chơi
                        cursor.execute("UPDATE TaiKhoan SET DiemSo = ISNULL(DiemSo, 0) + ? WHERE ID = ?", (self.sr_score, self.current_user_id))
                        cursor.execute("UPDATE TaiKhoan SET TongSoLanTap = ISNULL(TongSoLanTap, 0) + 1 WHERE ID = ?", (self.current_user_id,))
                        conn.commit()
                        self.sr_canvas.create_text(self.sr_canvas.winfo_width()/2, self.sr_canvas.winfo_height()/2 + 60, text="✅ Đã lưu kết quả vào hệ thống!", font=(FONT, 16), fill=COLORS["green"])
                except Exception as e:
                    print("Lỗi lưu điểm:", e)
            else:
                self.sr_canvas.create_text(self.sr_canvas.winfo_width()/2, self.sr_canvas.winfo_height()/2 + 60, text="🔒 Bạn chưa đăng nhập. Điểm này chưa được lưu!", font=(FONT, 16), fill=COLORS["orange"])
                # Bật popup nút bấm ngay giữa màn hình
                self.btn_sr_login = ctk.CTkButton(self.sr_canvas.master, text="👤 Đăng nhập để lưu điểm", font=(FONT, 16, "bold"), fg_color=COLORS["blue"], command=lambda: login_and_save(self.sr_score))
                self.btn_sr_login.place(relx=0.5, rely=0.85, anchor="center")

        def game_loop():
            if not self.sr_is_playing: return
            
            w = self.sr_canvas.winfo_width()
            h = self.sr_canvas.winfo_height()
            
            to_remove = []
            for target in self.sr_active_targets:
                self.sr_canvas.move(target['id'], 0, target['speed'] * self.sr_speed_multiplier)
                coords = self.sr_canvas.coords(target['id'])
                if coords and coords[1] > h:
                    to_remove.append(target)
            
            for target in to_remove:
                self.sr_canvas.delete(target['id'])
                if target in self.sr_active_targets:
                    self.sr_active_targets.remove(target)
                self.sr_lives -= 1
                self.lbl_lives.configure(text=" ".join(["❤️"] * max(0, self.sr_lives)))
                
                self.sr_canvas.config(bg="#330000")
                self.after(100, lambda: self.sr_canvas.config(bg="#080C11") if self.sr_is_playing else None)
                
                if self.sr_lives <= 0:
                    game_over()
                    return
            
            self.sr_spawn_counter += 1
            spawn_rate = max(20, 60 - int(self.sr_score / 50)) 
            
            if self.sr_spawn_counter >= spawn_rate:
                self.sr_spawn_counter = 0
                import random
                char = random.choice(['A','B','C','D','E','G','H','I','K','L','M','N','O','P','Q','R','S','T','U','V','X','Y'])
                x_pos = random.randint(50, max(100, w - 50))
                
                text_id = self.sr_canvas.create_text(x_pos, 0, text=char, font=(FONT, 45, "bold"), fill=COLORS["blue_2"])
                self.sr_active_targets.append({'char': char, 'id': text_id, 'speed': random.uniform(2.5, 4.0)})
                self.sr_speed_multiplier += 0.01

            self.sr_game_after_id = self.after(30, game_loop)

        def camera_loop():
            if not self.sr_is_playing or not self.sr_cap: return
            import cv2
            import numpy as np
            from PIL import Image
            import mediapipe as mp

            success, frame = self.sr_cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                predicted_char = ""
                confidence = 0.0

                if self.mp_hands:
                    results = self.mp_hands.process(frame_rgb)
                    if results.multi_hand_landmarks:
                        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                            self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                            hand_type = 0 if handedness.classification[0].label == "Left" else 1
                            vector, self.prev_wx, self.prev_wy = hand_vectorlize(hand_landmarks.landmark, hand_type, self.prev_wx, self.prev_wy)
                            self.sequence_data.append(vector)
                            
                            if len(self.sequence_data) > 30: self.sequence_data.pop(0)
                            
                            if len(self.sequence_data) == 30 and self.ai_session:
                                try:
                                    input_data = np.expand_dims(self.sequence_data, axis=0).astype(np.float32)
                                    out = self.ai_session.run(None, {self.ai_session.get_inputs()[0].name: input_data})[0][0]
                                    max_idx = np.argmax(out)
                                    confidence = float(out[max_idx])
                                    if confidence > 0.65:
                                        predicted_char = str(self.ai_labels[max_idx]).upper()
                                except: pass
                    else:
                        self.sequence_data.clear()
                        self.prev_wx = self.prev_wy = None

                if predicted_char:
                    self.lbl_ai_detect.configure(text=f"AI Đang thấy: {predicted_char}", text_color=COLORS["green"])
                else:
                    self.lbl_ai_detect.configure(text="AI Đang thấy: --", text_color=COLORS["muted"])

                if predicted_char and confidence > 0.65:
                    for target in self.sr_active_targets:
                        if target['char'] == predicted_char:
                            self.sr_canvas.delete(target['id'])
                            coords = self.sr_canvas.coords(target['id'])
                            if coords:
                                boom_id = self.sr_canvas.create_text(coords[0], coords[1], text="💥 BÙM", font=(FONT, 20, "bold"), fill=COLORS["orange"])
                                self.after(300, lambda i=boom_id: self.sr_canvas.delete(i))
                            
                            self.sr_active_targets.remove(target)
                            self.sr_score += 10
                            self.lbl_score.configure(text=str(self.sr_score))
                            self.sequence_data.clear()
                            break

                h, w = frame.shape[:2]
                scale = min(320/w, 200/h)
                new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
                frame_res = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (new_w, new_h), interpolation=cv2.INTER_AREA)
                
                imgtk = ctk.CTkImage(light_image=Image.fromarray(frame_res), dark_image=Image.fromarray(frame_res), size=(new_w, new_h))
                self.sr_video_label.configure(image=imgtk, text="")
                self.sr_video_label.image = imgtk

            self.sr_camera_after_id = self.after(15, camera_loop)

        def start_game():
            # Dọn dẹp nút "Đăng nhập" nếu nó đang hiện từ ván trước
            if hasattr(self, 'btn_sr_login') and self.btn_sr_login.winfo_exists():
                self.btn_sr_login.destroy()
                
            import cv2
            if not load_ai():
                self.lbl_ai_detect.configure(text="Lỗi nạp Model AI!", text_color=COLORS["red"])
                return
            
            self.sr_is_playing = True
            self.sr_score = 0
            self.sr_lives = 3
            self.sr_speed_multiplier = 1.0
            self.sr_spawn_counter = 0
            self.sr_active_targets.clear()
            self.sr_canvas.delete("all")
            
            self.lbl_score.configure(text="0")
            self.lbl_lives.configure(text="❤️ ❤️ ❤️")
            self.btn_sr_start.configure(state="disabled", text="ĐANG CHƠI...", fg_color=COLORS["stroke"])
            self.sr_canvas.config(bg="#080C11")
            
            if not self.sr_cap:
                import os
                self.sr_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
                self.sr_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.sr_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            game_loop()
            camera_loop()

        self.btn_sr_start.configure(command=start_game)
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
        
        ctk.CTkLabel(card, text="⏰", font=(FONT, 100)).pack(pady=(40, 10)) # Đã tinh chỉnh lại padding cho cân đối
        ctk.CTkLabel(card, text="HẾT GIỜ!", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
        
        correct_count = len([x for x in self.word_history if x[1]])
        ctk.CTkLabel(card, text=f"Bạn đã chiến đấu kiên cường và ghép đúng {correct_count} từ.", font=(FONT, 18), text_color=COLORS["muted"]).pack(pady=(0, 20))
        
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(0, 20))
        ctk.CTkLabel(score_box, text="Tổng Điểm Kỷ Lục", font=(FONT, 16), text_color=COLORS["muted"]).pack(pady=(20, 0))
        ctk.CTkLabel(score_box, text=f"🏆 {self.word_score}", font=(FONT, 48, "bold"), text_color=COLORS["yellow"]).pack(padx=60, pady=(0, 20))
        
        # ==========================================================
        # XỬ LÝ LƯU DATABASE & GỢI Ý ĐĂNG NHẬP 
        # ==========================================================
        def login_and_save(score):
            """Hành vi tạm lưu điểm vào RAM và gọi form Đăng nhập"""
            self.pending_save_score = score
            self._trigger_login_flow()

        db_frame = ctk.CTkFrame(card, fg_color="transparent")
        db_frame.pack(pady=(0, 30))

        if self.current_user_id:
            try:
                db = self._get_db()
                if db and hasattr(db, 'get_conn'):
                    conn = db.get_conn()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE TaiKhoan SET DiemSo = ISNULL(DiemSo, 0) + ? WHERE ID = ?", (self.word_score, self.current_user_id))
                    cursor.execute("UPDATE TaiKhoan SET TongSoLanTap = ISNULL(TongSoLanTap, 0) + 1 WHERE ID = ?", (self.current_user_id,))
                    conn.commit()
                    ctk.CTkLabel(db_frame, text="✅ Đã lưu kết quả vào hệ thống!", font=(FONT, 16, "bold"), text_color=COLORS["green"]).pack()
            except Exception as e:
                print("Lỗi lưu điểm game ghép từ:", e)
        else:
            ctk.CTkLabel(db_frame, text="🔒 Bạn chưa đăng nhập. Điểm này chưa được lưu!", font=(FONT, 15), text_color=COLORS["orange"]).pack(pady=(0, 12))
            ctk.CTkButton(db_frame, text="👤 Đăng nhập để lưu điểm", font=(FONT, 15, "bold"), fg_color=COLORS["blue"], hover_color="#0B62D5", height=40, command=lambda: login_and_save(self.word_score)).pack()
        # ==========================================================

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
        ctk.CTkLabel(status_bar, text="❤️ " * max(0, self.react_lives), font=(FONT, 24), text_color=COLORS["red"]).pack(side="left")
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
        
        ctk.CTkLabel(card, text="💥", font=(FONT, 100)).pack(pady=(40, 10))
        ctk.CTkLabel(card, text="GAME OVER", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
        
        ctk.CTkLabel(card, text="Tốc độ phản xạ của bạn thật đáng kinh ngạc!", font=(FONT, 18), text_color=COLORS["muted"]).pack(pady=(0, 20))
        
        score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
        score_box.pack(pady=(0, 20))
        ctk.CTkLabel(score_box, text="Điểm Phản Xạ Kỷ Lục", font=(FONT, 16), text_color=COLORS["muted"]).pack(pady=(20, 0))
        ctk.CTkLabel(score_box, text=f"💰 {self.react_score}", font=(FONT, 48, "bold"), text_color=COLORS["orange"]).pack(padx=60, pady=(0, 20))
        
        # ==========================================================
        # XỬ LÝ LƯU DATABASE & GỢI Ý ĐĂNG NHẬP 
        # ==========================================================
        def login_and_save(score):
            """Hành vi tạm lưu điểm vào RAM và gọi form Đăng nhập"""
            self.pending_save_score = score
            self._trigger_login_flow()

        db_frame = ctk.CTkFrame(card, fg_color="transparent")
        db_frame.pack(pady=(0, 30))

        if self.current_user_id:
            try:
                db = self._get_db()
                if db and hasattr(db, 'get_conn'):
                    conn = db.get_conn()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE TaiKhoan SET DiemSo = ISNULL(DiemSo, 0) + ? WHERE ID = ?", (self.react_score, self.current_user_id))
                    cursor.execute("UPDATE TaiKhoan SET TongSoLanTap = ISNULL(TongSoLanTap, 0) + 1 WHERE ID = ?", (self.current_user_id,))
                    conn.commit()
                    ctk.CTkLabel(db_frame, text="✅ Đã lưu kết quả vào hệ thống!", font=(FONT, 16, "bold"), text_color=COLORS["green"]).pack()
            except Exception as e:
                print("Lỗi lưu điểm game phản xạ:", e)
        else:
            ctk.CTkLabel(db_frame, text="🔒 Bạn chưa đăng nhập. Điểm này chưa được lưu!", font=(FONT, 15), text_color=COLORS["orange"]).pack(pady=(0, 12))
            ctk.CTkButton(db_frame, text="👤 Đăng nhập để lưu điểm", font=(FONT, 15, "bold"), fg_color=COLORS["blue"], hover_color="#0B62D5", height=40, command=lambda: login_and_save(self.react_score)).pack()
        # ==========================================================
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="⟳ Chơi lại", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["blue"], command=self.start_reaction_game).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🏠 Menu", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["card"], command=self.show_dashboard).pack(side="left", padx=10)

    # =========================================================================
    # CỖ MÁY MINIGAME 4: GIẢI MÃ KÉT SẮT (ESCAPE ROOM / PUZZLE)
    # =========================================================================
    def show_safecracker_game(self):
        # 1. Dọn dẹp timer
        if hasattr(self, '_stop_word_timer'): self._stop_word_timer()
        if hasattr(self, '_stop_reaction_timer'): self._stop_reaction_timer()
        
        # 2. Setup state
        self.sc_is_playing = False
        self.sc_score = 0
        self.sc_time_left = 60 # 60 giây sinh tử để giải càng nhiều két càng tốt
        self.sc_current_word = ""
        self.sc_current_hint = ""
        self.sc_unlocked_chars = []
        self.sc_cap = None
        self.sc_camera_after_id = None
        self.sc_game_after_id = None
        
        # Biến AI
        self.sequence_data = []
        self.prev_wx = None
        self.prev_wy = None
        self.mp_hands = None
        self.mp_draw = None
        self.ai_session = None
        self.ai_labels = None
        
        # Kho câu đố (Viết không dấu để AI nhận diện bộ chữ VSL cơ bản)
        self.sc_word_pool = [
            ("Trái nghĩa với ĐEN", "TRANG"),
            ("Thủ đô của Việt Nam", "HANOI"),
            ("Động vật kêu meo meo", "MEO"),
            ("Màu của bầu trời", "XANH"),
            ("Môn thể thao Vua", "BONGDA"),
            ("Nơi chứa nhiều sách", "THUVIEN"),
            ("Hành tinh chúng ta đang sống", "TRAIDAT"),
            ("Loài hoa biểu tượng của Hà Lan", "TULIP"),
            ("Mùa nóng nhất trong năm", "MUAHE"),
            ("Người sinh ra bạn (Nữ)", "ME")
        ]
        
        # 3. Dựng Giao Diện
        self.current_screen = "safecracker"
        self.clear_content()
        page = self._page()
        
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="GIẢI MÃ KÉT SẮT 🔐", font=(FONT, 30, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        
        def go_back():
            self.sc_is_playing = False
            if self.sc_cap: self.sc_cap.release()
            if self.sc_camera_after_id: self.after_cancel(self.sc_camera_after_id)
            if self.sc_game_after_id: self.after_cancel(self.sc_game_after_id)
            self.show_dashboard()
            
        ctk.CTkButton(header, text="← Trở về", font=(FONT, 15, "bold"), fg_color=COLORS["panel"], hover_color=COLORS["stroke"], height=40, command=go_back).grid(row=0, column=1, sticky="e", padx=20)

        body = self._game_body(page)
        
        # --- CỘT TRÁI - GIAO DIỆN KÉT SẮT ---
        game_board = ctk.CTkFrame(body, fg_color="#0A1118", border_color=COLORS["stroke"], border_width=2, corner_radius=16)
        game_board.grid(row=0, column=0, sticky="nsew")
        game_board.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(game_board, text="Mật mã Két Sắt", font=(FONT, 20, "bold"), text_color=COLORS["muted"]).pack(pady=(30, 5))
        self.lbl_sc_hint = ctk.CTkLabel(game_board, text="Gợi ý: ...", font=(FONT, 24, "bold"), text_color=COLORS["blue_2"], wraplength=400, justify="center")
        self.lbl_sc_hint.pack(pady=(0, 20))
        
        # BÍ KÍP: HIỆU ỨNG BOM NỔ CHẬM
        self.sc_timer_bar = ctk.CTkProgressBar(game_board, height=10, progress_color=COLORS["green"], fg_color="#2A3038", corner_radius=5)
        self.sc_timer_bar.pack(fill="x", padx=80, pady=(0, 20))
        self.sc_timer_bar.set(1.0)
        
        self.sc_slots_frame = ctk.CTkFrame(game_board, fg_color="transparent")
        self.sc_slots_frame.pack(pady=10)
        
        self.lbl_sc_status = ctk.CTkLabel(game_board, text="Hãy làm ký hiệu để nhập từng chữ cái!", font=(FONT, 16), text_color=COLORS["orange"])
        self.lbl_sc_status.pack(pady=10)
        
        # BÍ KÍP: CỬA HÀNG HACKER
        shop_frame = ctk.CTkFrame(game_board, fg_color="transparent")
        shop_frame.pack(side="bottom", fill="x", pady=25)
        
        ctk.CTkLabel(shop_frame, text="🛒 Cửa hàng Hacker (Dùng Tiền Thưởng)", font=(FONT, 14, "bold"), text_color=COLORS["muted"]).pack(pady=(0, 10))
        shop_btns = ctk.CTkFrame(shop_frame, fg_color="transparent")
        shop_btns.pack()

        # --- CỘT PHẢI - CAMERA & THỐNG KÊ ---
        right_panel = self._panel(body, row=0, column=1, sticky="nsew", padx=(14, 0))
        
        stats_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["card"], corner_radius=16)
        stats_frame.pack(fill="x", padx=16, pady=16)
        
        score_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        score_row.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(score_row, text="Tiền thưởng:", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(side="left")
        self.lbl_sc_score = ctk.CTkLabel(score_row, text="0", font=(FONT, 28, "bold"), text_color=COLORS["yellow"])
        self.lbl_sc_score.pack(side="right")
        
        time_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        time_row.pack(fill="x", padx=20, pady=(5, 20))
        ctk.CTkLabel(time_row, text="Thời gian:", font=(FONT, 18, "bold"), text_color=COLORS["text"]).pack(side="left")
        self.lbl_sc_time = ctk.CTkLabel(time_row, text="00:00", font=(FONT, 22, "bold"), text_color=COLORS["purple"])
        self.lbl_sc_time.pack(side="right")
        
        cam_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["panel_2"], corner_radius=16)
        cam_frame.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(cam_frame, text="Camera AI", font=(FONT, 16, "bold"), text_color=COLORS["blue_2"]).pack(pady=(15, 5))
        
        self.sc_video_label = ctk.CTkLabel(cam_frame, text="📷 Đang chờ...", height=200, fg_color="#05080D", corner_radius=12)
        self.sc_video_label.pack(fill="x", padx=15, pady=(0, 15))
        
        self.lbl_sc_detect = ctk.CTkLabel(cam_frame, text="AI Đang thấy: --", font=(FONT, 16, "bold"), text_color=COLORS["green"])
        self.lbl_sc_detect.pack(pady=(0, 15))
        
        self.btn_sc_start = ctk.CTkButton(right_panel, text="▶ BẮT ĐẦU GIẢI MÃ", font=(FONT, 18, "bold"), height=60, corner_radius=16, fg_color=COLORS["blue"], hover_color="#0B62D5")
        self.btn_sc_start.pack(fill="x", side="bottom", padx=16, pady=16)
        
        # ==========================================
        # CÁC HÀM LOGIC XỬ LÝ BÊN TRONG
        # ==========================================
        def load_ai():
            import mediapipe as mp
            import numpy as np
            import onnxruntime as ort
            import os
            
            if not self.mp_hands:
                self.mp_hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
                self.mp_draw = mp.solutions.drawing_utils
                
            if not self.ai_session:
                try:
                    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'model.onnx'))
                    label_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'labels.npy'))
                    if not os.path.exists(model_path): model_path = "model/model.onnx"
                    if not os.path.exists(label_path): label_path = "model/labels.npy"
                    
                    self.ai_session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                    self.ai_labels = np.load(label_path)
                    return True
                except: return False
            return True

        def hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy):
            import numpy as np
            wx, wy = landmarks[0].x, landmarks[0].y
            vector = []
            for i in range(1, 21): vector.extend([landmarks[i].x - wx, landmarks[i].y - wy])
            vector.extend([hand_type, (wx - prev_wx)*30 if prev_wx else 0.0, (wy - prev_wy)*30 if prev_wy else 0.0])
            return np.array(vector), wx, wy
            
        def render_slots():
            for w in self.sc_slots_frame.winfo_children(): w.destroy()
            for i, char in enumerate(self.sc_current_word):
                if i < len(self.sc_unlocked_chars):
                    slot = ctk.CTkFrame(self.sc_slots_frame, width=60, height=70, fg_color=COLORS["green"], corner_radius=8)
                    slot.pack(side="left", padx=5)
                    slot.pack_propagate(False)
                    ctk.CTkLabel(slot, text=char, font=(FONT, 32, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
                elif i == len(self.sc_unlocked_chars):
                    slot = ctk.CTkFrame(self.sc_slots_frame, width=60, height=70, fg_color=COLORS["panel"], border_color=COLORS["orange"], border_width=2, corner_radius=8)
                    slot.pack(side="left", padx=5)
                    slot.pack_propagate(False)
                    ctk.CTkLabel(slot, text="_", font=(FONT, 32, "bold"), text_color=COLORS["orange"]).place(relx=0.5, rely=0.5, anchor="center")
                else:
                    slot = ctk.CTkFrame(self.sc_slots_frame, width=60, height=70, fg_color=COLORS["panel"], border_color=COLORS["stroke"], border_width=1, corner_radius=8)
                    slot.pack(side="left", padx=5)
                    slot.pack_propagate(False)
                    ctk.CTkLabel(slot, text="", font=(FONT, 32, "bold"), text_color=COLORS["muted"]).place(relx=0.5, rely=0.5, anchor="center")

        def resume_after_success():
            self.sc_is_playing = True
            load_next_puzzle()
            camera_loop()

        def check_win_condition():
            if len(self.sc_unlocked_chars) == len(self.sc_current_word):
                self.sc_score += 50
                self.sc_time_left += 15 # Tặng thêm 15 giây
                self.lbl_sc_score.configure(text=str(self.sc_score))
                self.lbl_sc_status.configure(text="🎉 MỞ KÉT THÀNH CÔNG! +50 Xu, +15s", text_color=COLORS["green"])
                
                self.sc_is_playing = False
                self.after(1500, resume_after_success)
            else:
                next_char = self.sc_current_word[len(self.sc_unlocked_chars)]
                self.lbl_sc_status.configure(text=f"Tuyệt! Giơ tiếp chữ cái: {next_char}", text_color=COLORS["blue_2"])

        def load_next_puzzle():
            import random
            puzzle = random.choice(self.sc_word_pool)
            self.sc_current_hint = puzzle[0]
            self.sc_current_word = puzzle[1]
            
            # --- BÍ KÍP 1: KHỞI ĐẦU NHÂN ĐẠO ---
            self.sc_unlocked_chars = [self.sc_current_word[0]] 
            
            self.lbl_sc_hint.configure(text=f"💡 {self.sc_current_hint}")
            if len(self.sc_unlocked_chars) < len(self.sc_current_word):
                next_char = self.sc_current_word[len(self.sc_unlocked_chars)]
                self.lbl_sc_status.configure(text=f"Hãy giơ tay làm ký hiệu chữ cái: {next_char}", text_color=COLORS["orange"])
            render_slots()

        # --- LOGIC CỬA HÀNG HACKER ---
        def buy_hint():
            if not self.sc_is_playing: return
            if self.sc_score >= 20:
                self.sc_score -= 20
                self.lbl_sc_score.configure(text=str(self.sc_score))
                target_idx = len(self.sc_unlocked_chars)
                if target_idx < len(self.sc_current_word):
                    self.sc_unlocked_chars.append(self.sc_current_word[target_idx])
                    self.sequence_data.clear()
                    render_slots()
                    check_win_condition()
            else:
                from tkinter import messagebox
                messagebox.showwarning("Thiếu Xu", "Bạn không đủ 20 xu để mua tính năng này!")

        def buy_time():
            if not self.sc_is_playing: return
            if self.sc_score >= 30:
                self.sc_score -= 30
                self.lbl_sc_score.configure(text=str(self.sc_score))
                self.sc_time_left += 15
            else:
                from tkinter import messagebox
                messagebox.showwarning("Thiếu Xu", "Bạn không đủ 30 xu để mua tính năng này!")

        def buy_skip():
            if not self.sc_is_playing: return
            if self.sc_score >= 15:
                self.sc_score -= 15
                self.lbl_sc_score.configure(text=str(self.sc_score))
                load_next_puzzle()
            else:
                from tkinter import messagebox
                messagebox.showwarning("Thiếu Xu", "Bạn không đủ 15 xu để mua tính năng này!")

        # Gắn nút cửa hàng
        ctk.CTkButton(shop_btns, text="💡 Lật 1 chữ\n-20 Xu", font=(FONT, 14, "bold"), height=50, fg_color="#122A4F", hover_color="#1A3B6E", border_width=1, border_color=COLORS["blue"], command=buy_hint).pack(side="left", padx=8)
        ctk.CTkButton(shop_btns, text="⏳ +15 Giây\n-30 Xu", font=(FONT, 14, "bold"), height=50, fg_color="#451A1F", hover_color="#63252C", border_width=1, border_color=COLORS["red"], command=buy_time).pack(side="left", padx=8)
        ctk.CTkButton(shop_btns, text="🔄 Đổi Két\n-15 Xu", font=(FONT, 14, "bold"), height=50, fg_color="#332200", hover_color="#4D3300", border_width=1, border_color=COLORS["orange"], command=buy_skip).pack(side="left", padx=8)

        def login_and_save(score):
            self.pending_save_score = score
            self._trigger_login_flow()

        def game_over():
            self.sc_is_playing = False
            if self.sc_cap:
                self.sc_cap.release()
                self.sc_cap = None
            if hasattr(self, 'sc_video_label') and self.sc_video_label.winfo_exists():
                self.sc_video_label.configure(image="", text="Đã tắt Camera")
                
            self.current_screen = "safecracker_game_over"
            self.clear_content()
            page = self._page()
            page.grid_columnconfigure(0, weight=1)
            page.grid_rowconfigure(0, weight=1)
            
            card = ctk.CTkFrame(page, fg_color=COLORS["panel"], corner_radius=20, border_color=COLORS["stroke"], border_width=1)
            card.grid(row=0, column=0, sticky="nsew", padx=150, pady=80)
            card.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(card, text="🔐", font=(FONT, 100)).pack(pady=(40, 10))
            ctk.CTkLabel(card, text="HẾT GIỜ", font=(FONT, 36, "bold"), text_color=COLORS["red"]).pack(pady=(0, 10))
            ctk.CTkLabel(card, text="Két sắt đã bị khóa chặt. Bạn đã thu thập được:", font=(FONT, 18), text_color=COLORS["muted"]).pack(pady=(0, 20))
            
            score_box = ctk.CTkFrame(card, fg_color="#080C11", corner_radius=16)
            score_box.pack(pady=(0, 20))
            ctk.CTkLabel(score_box, text="Tiền thưởng Kỷ Lục", font=(FONT, 16), text_color=COLORS["muted"]).pack(pady=(20, 0))
            ctk.CTkLabel(score_box, text=f"💰 {self.sc_score} Xu", font=(FONT, 48, "bold"), text_color=COLORS["yellow"]).pack(padx=60, pady=(0, 20))
            
            # XỬ LÝ DATABASE & ĐĂNG NHẬP
            db_frame = ctk.CTkFrame(card, fg_color="transparent")
            db_frame.pack(pady=(0, 30))

            if self.current_user_id:
                try:
                    db = self._get_db()
                    if db and hasattr(db, 'get_conn'):
                        conn = db.get_conn()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE TaiKhoan SET DiemSo = ISNULL(DiemSo, 0) + ? WHERE ID = ?", (self.sc_score, self.current_user_id))
                        cursor.execute("UPDATE TaiKhoan SET TongSoLanTap = ISNULL(TongSoLanTap, 0) + 1 WHERE ID = ?", (self.current_user_id,))
                        conn.commit()
                        ctk.CTkLabel(db_frame, text="✅ Đã lưu kết quả vào hệ thống!", font=(FONT, 16, "bold"), text_color=COLORS["green"]).pack()
                except Exception as e: print("Lỗi lưu điểm game két sắt:", e)
            else:
                ctk.CTkLabel(db_frame, text="🔒 Bạn chưa đăng nhập. Điểm này chưa được lưu!", font=(FONT, 15), text_color=COLORS["orange"]).pack(pady=(0, 12))
                ctk.CTkButton(db_frame, text="👤 Đăng nhập để lưu điểm", font=(FONT, 15, "bold"), fg_color=COLORS["blue"], hover_color="#0B62D5", height=40, command=lambda: login_and_save(self.sc_score)).pack()

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack()
            ctk.CTkButton(btn_frame, text="⟳ Chơi lại", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["blue"], command=self.show_safecracker_game).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text="🏠 Về Menu", font=(FONT, 18, "bold"), height=54, width=180, fg_color=COLORS["card"], hover_color=COLORS["card_hover"], command=self.show_dashboard).pack(side="left", padx=10)


        def timer_loop():
            if not self.sc_is_playing: return
            if self.sc_time_left > 0:
                self.sc_time_left -= 1
                if hasattr(self, 'lbl_sc_time') and self.lbl_sc_time.winfo_exists():
                    self.lbl_sc_time.configure(text=f"00:{self.sc_time_left:02d}")
                    
                    # --- BÍ KÍP 2: UPDATE MÀU SẮC DỰA TRÊN ĐỒNG HỒ ---
                    ratio = min(1.0, self.sc_time_left / 60.0)
                    self.sc_timer_bar.set(ratio)
                    
                    if self.sc_time_left > 30: color = COLORS["green"]
                    elif self.sc_time_left > 10: color = COLORS["orange"]
                    else: color = COLORS["red"]
                        
                    self.lbl_sc_time.configure(text_color=color)
                    self.sc_timer_bar.configure(progress_color=color)
                    
                self.sc_game_after_id = self.after(1000, timer_loop)
            else:
                game_over()

        def camera_loop():
            if not self.sc_is_playing or not self.sc_cap: return
            import cv2
            from PIL import Image
            import numpy as np
            import mediapipe as mp

            success, frame = self.sc_cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                predicted_char = ""
                confidence = 0.0

                if self.mp_hands:
                    results = self.mp_hands.process(frame_rgb)
                    if results.multi_hand_landmarks:
                        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                            self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                            hand_type = 0 if handedness.classification[0].label == "Left" else 1
                            vector, self.prev_wx, self.prev_wy = hand_vectorlize(hand_landmarks.landmark, hand_type, self.prev_wx, self.prev_wy)
                            self.sequence_data.append(vector)
                            
                            if len(self.sequence_data) > 30: self.sequence_data.pop(0)
                            if len(self.sequence_data) == 30 and self.ai_session:
                                try:
                                    input_data = np.expand_dims(self.sequence_data, axis=0).astype(np.float32)
                                    out = self.ai_session.run(None, {self.ai_session.get_inputs()[0].name: input_data})[0][0]
                                    max_idx = np.argmax(out)
                                    confidence = float(out[max_idx])
                                    if confidence > 0.70:
                                        predicted_char = str(self.ai_labels[max_idx]).upper()
                                except: pass
                    else:
                        self.sequence_data.clear()
                        self.prev_wx = self.prev_wy = None

                if predicted_char:
                    self.lbl_sc_detect.configure(text=f"AI Đang thấy: {predicted_char} ({int(confidence*100)}%)", text_color=COLORS["green"])
                else:
                    self.lbl_sc_detect.configure(text="AI Đang thấy: --", text_color=COLORS["muted"])

                # KIỂM TRA MẬT MÃ
                if predicted_char and confidence > 0.75:
                    target_char_idx = len(self.sc_unlocked_chars)
                    if target_char_idx < len(self.sc_current_word):
                        needed_char = self.sc_current_word[target_char_idx]
                        
                        if predicted_char == needed_char:
                            self.sc_unlocked_chars.append(needed_char)
                            self.sequence_data.clear()
                            render_slots()
                            check_win_condition() # Tái sử dụng logic kiểm tra Win

                h, w = frame.shape[:2]
                scale = min(320/w, 200/h)
                new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
                frame_res = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (new_w, new_h), interpolation=cv2.INTER_AREA)
                
                imgtk = ctk.CTkImage(light_image=Image.fromarray(frame_res), dark_image=Image.fromarray(frame_res), size=(new_w, new_h))
                self.sc_video_label.configure(image=imgtk, text="")
                self.sc_video_label.image = imgtk

            if self.sc_is_playing:
                self.sc_camera_after_id = self.after(15, camera_loop)

        def start_game():
            if hasattr(self, 'btn_sc_login') and self.btn_sc_login.winfo_exists():
                self.btn_sc_login.destroy()
                
            import cv2
            if not load_ai():
                self.lbl_sc_detect.configure(text="Lỗi nạp Model AI!", text_color=COLORS["red"])
                return
            
            self.sc_is_playing = True
            self.sc_score = 0
            self.sc_time_left = 60
            
            self.lbl_sc_score.configure(text="0")
            self.lbl_sc_time.configure(text="00:60", text_color=COLORS["green"])
            self.btn_sc_start.configure(state="disabled", text="ĐANG GIẢI MÃ...", fg_color=COLORS["stroke"])
            
            load_next_puzzle()
            
            if not self.sc_cap:
                import os
                self.sc_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
                self.sc_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.sc_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            timer_loop()
            camera_loop()

        self.btn_sc_start.configure(command=start_game)
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
        
        # --- BÍ KÍP: CỘNG ĐIỂM BÙ NẾU CHƠI XONG MỚI ĐĂNG NHẬP ---
        if hasattr(self, 'pending_save_score') and self.pending_save_score > 0 and self.current_user_id:
            try:
                db = self._get_db()
                if db and hasattr(db, 'get_conn'):
                    conn = db.get_conn()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE TaiKhoan SET DiemSo = ISNULL(DiemSo, 0) + ? WHERE ID = ?", (self.pending_save_score, self.current_user_id))
                    cursor.execute("UPDATE TaiKhoan SET TongSoLanTap = ISNULL(TongSoLanTap, 0) + 1 WHERE ID = ?", (self.current_user_id,))
                    conn.commit()
                    print(f"-> Đã cộng bù {self.pending_save_score} điểm vào DB!")
                    self.pending_save_score = 0 # Đặt lại sau khi lưu
            except Exception as e:
                print("Lỗi lưu điểm bù sau đăng nhập:", e)
        # --------------------------------------------------------
        
        # 2. Render lại UI Dashboard
        self.show_dashboard()
        
        # 3. ĐỒNG BỘ GIAO DIỆN SIDEBAR CỦA UI_USER
        try:
            toplevel = self.winfo_toplevel()
            if hasattr(toplevel, "refresh_sidebar_auth"):
                toplevel.refresh_sidebar_auth()
                print("-> Đã đồng bộ Sidebar App Tổng qua hàm: refresh_sidebar_auth")
            else:
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
