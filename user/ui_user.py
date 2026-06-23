import sys
import os
import time  # Thư viện đo FPS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

try:
    from goc_hoc_tap.study_ui import StudyApp
except Exception as e:
    StudyApp = None
    _study_import_error = e

try:
    from minigame.minigame_ui import MinigameFrame
except Exception as e:
    MinigameFrame = None
    _minigame_import_error = e

# Nhập 2 cỗ máy hút dữ liệu từ 2 Ngăn
from core.train_window import hand_vectorlize
from core.train_window_both import extract_86_features, hands, mp_draw, mp_hands

# Nhập 2 bộ não AI
from core.translate_window import load_lstm_model, load_lstm_model_both, predict_sign
from core.vietnamese_utils import apply_vietnamese_sign, LIST_DAU

def create_user_menu(root):
    root.title("Hand Sign Translator - Pro Edition (Dual Model)")
    window_width = 1300
    window_height = 750 # Nới rộng một chút cho thoải mái
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{int((screen_width / 2) - (window_width / 2))}+{int((screen_height / 2) - (window_height / 2))}")

    # TẢI CÙNG LÚC 2 BỘ NÃO
    lstm_model_1, action_labels_1 = load_lstm_model()
    lstm_model_2, action_labels_2 = load_lstm_model_both()

    cap = None
    is_camera_on = False
    history_list = []
    last_detected = ""
    current_sentence = "" 
    
    # BIẾN NHỚ ĐỘC LẬP CHO 2 NGĂN VÀ TỐI ƯU FPS
    test_sequence_1 = []
    test_sequence_2 = []
    prev_wx_l, prev_wy_l = None, None
    prev_wx_r, prev_wy_r = None, None
    
    frame_counter = 0
    prev_time = 0
    
    # Biến nhớ đệm AI (Giảm tải lag)
    cached_raw_text = ""
    cached_prob = 0.0

    # ==========================================
    # CẤU HÌNH GIẢM DELAY CAMERA
    # ==========================================
    # Giảm độ phân giải đầu vào giúp MediaPipe + AI xử lý nhanh hơn.
    # Nếu máy mạnh, bạn có thể đổi lại 640 x 480.
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30

    # AI_INTERVAL càng lớn thì khung hình càng mượt, nhưng kết quả nhận diện cập nhật chậm hơn.
    # Gợi ý: máy yếu = 8 hoặc 10, máy mạnh = 5.
    AI_INTERVAL = 8

    # Giới hạn kích thước ảnh hiển thị để giảm tải resize khi giao diện quá lớn.
    DISPLAY_MAX_WIDTH = 900
    DISPLAY_MAX_HEIGHT = 650

    # ==========================================
    # GIAO DIỆN DỊCH TỰ DO HIỆN ĐẠI
    # ==========================================
    COLORS = {
        "bg": "#0B1020",
        "sidebar": "#111827",
        "sidebar_card": "#182033",
        "card": "#171C2B",
        "card2": "#1E2538",
        "camera": "#050914",
        "blue": "#1E90FF",
        "blue2": "#00A6FF",
        "green": "#32D583",
        "orange": "#FFB020",
        "red": "#FF4B55",
        "purple": "#8B5CF6",
        "text": "#FFFFFF",
        "muted": "#A7B0C0",
        "border": "#27324A",
    }

    ctk.set_appearance_mode("dark")
    root.configure(fg_color=COLORS["bg"])

    # ==========================================
    # CỘT 1: SIDEBAR BÊN TRÁI
    # ==========================================
    sidebar = ctk.CTkFrame(root, width=280, fg_color=COLORS["sidebar"], corner_radius=0)
    sidebar.pack_propagate(False)
    sidebar.pack(side="left", fill="y")

    logo_box = ctk.CTkFrame(sidebar, fg_color="transparent")
    logo_box.pack(fill="x", padx=18, pady=(26, 22))

    ctk.CTkLabel(
        logo_box,
        text="🌐 VSL",
        font=ctk.CTkFont(size=26, weight="bold"),
        text_color=COLORS["blue2"]
    ).pack(anchor="w")

    ctk.CTkLabel(
        logo_box,
        text="TRANSLATE",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=COLORS["text"]
    ).pack(anchor="w", pady=(0, 2))

    ctk.CTkLabel(
        logo_box,
        text="Học và dịch ngôn ngữ ký hiệu",
        font=ctk.CTkFont(size=12),
        text_color=COLORS["muted"]
    ).pack(anchor="w")
    def nav_button(text, active=False, command=None):
        return ctk.CTkButton(
            sidebar,
            text=text,
            font=ctk.CTkFont(size=15, weight="bold" if active else "normal"),
            fg_color=COLORS["blue"] if active else "transparent",
            hover_color="#1473CC" if active else COLORS["card2"],
            text_color=COLORS["text"],
            anchor="w",
            height=44,
            corner_radius=14,
            command=command if command is not None else (lambda: None)
        )

    translate_nav_btn = nav_button("🎙️  Dịch tự do", active=True, command=lambda: show_translate_panel())
    translate_nav_btn.pack(fill="x", padx=15, pady=5)

    study_nav_btn = nav_button("📚  Góc học tập", command=lambda: show_study_panel())
    study_nav_btn.pack(fill="x", padx=15, pady=5)

    minigame_nav_btn = nav_button("🎮  Minigame", command=lambda: show_minigame_panel())
    minigame_nav_btn.pack(fill="x", padx=15, pady=5)

    
    sidebar_tip = ctk.CTkFrame(sidebar, fg_color=COLORS["sidebar_card"], corner_radius=18)
    sidebar_tip.pack(fill="x", padx=15, pady=(22, 10))

    ctk.CTkLabel(
        sidebar_tip,
        text="💡 Mẹo sử dụng",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=COLORS["blue2"]
    ).pack(anchor="w", padx=14, pady=(14, 4))

    ctk.CTkLabel(
        sidebar_tip,
        text="Đưa tay vào khung hình,\ngiữ ổn định 1–2 giây để\nAI nhận diện chính xác hơn.",
        font=ctk.CTkFont(size=12),
        text_color=COLORS["muted"],
        justify="left"
    ).pack(anchor="w", padx=14, pady=(0, 14))

    # ==========================================
    # KHUNG CHỨA CÁC NÚT Ở ĐÁY SIDEBAR
    # ==========================================
    bottom_sidebar = ctk.CTkFrame(sidebar, fg_color="transparent")
    bottom_sidebar.pack(side="bottom", fill="x", pady=20)

    try:
        import auth_ui
    except ImportError:
        pass

    # 1. NÚT BẬT CAMERA (Tạo và pack đầu tiên để nó nằm trên cùng)
    cam_btn = ctk.CTkButton(
        bottom_sidebar,
        text="▶  Bật Camera",
        font=ctk.CTkFont(size=16, weight="bold"),
        fg_color=COLORS["green"],
        hover_color="#24B874",
        text_color="#08111F",
        height=48,
        corner_radius=16
    )
    # Khoảng cách phía dưới (pady=15) để đẩy nút đăng nhập xuống một chút
    cam_btn.pack(side="top", fill="x", padx=15, pady=(0, 15))

    # 2. NÚT ĐĂNG NHẬP (Nằm ngay dưới Camera)
    account_btn = ctk.CTkButton(
        bottom_sidebar,
        text="👤  Đăng nhập / Đăng ký",
        height=48,
        corner_radius=14,
        anchor="w",
        font=ctk.CTkFont(size=15, weight="bold"),
        fg_color=COLORS["card2"],
        hover_color="#2A323B",
        text_color="white",
        command=lambda: show_auth_panel()
    )
    account_btn.pack(side="top", fill="x", padx=15)

    # 3. NÚT ĐĂNG XUẤT (Nằm dưới cùng, mặc định ẩn)
    def perform_logout():
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất khỏi tài khoản này?"):
            if 'auth_ui' in sys.modules:
                auth_ui.CURRENT_USER = None
                auth_ui.LEARNED_LETTERS = []
            
            # Trả lại trạng thái mặc định
            account_btn.configure(text="👤  Đăng nhập / Đăng ký", fg_color=COLORS["card2"], text_color="white")
            logout_btn.pack_forget()
            show_study_panel()       

    logout_btn = ctk.CTkButton(
        bottom_sidebar,
        text="🚪  Đăng xuất",
        height=44,
        corner_radius=14,
        anchor="w",
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="#451A1F",
        hover_color="#5C2329",
        text_color="white",
        command=perform_logout
    )
    # ==========================================
    # KHUNG NỘI DUNG CHÍNH: các mục Dịch tự do / Góc học tập / Minigame
    # sẽ được đổi ngay trong khung này, không mở cửa sổ mới.
    # ==========================================
    content_container = ctk.CTkFrame(root, fg_color=COLORS["bg"], corner_radius=0)
    content_container.pack(side="left", fill="both", expand=True)

    translate_panel = ctk.CTkFrame(content_container, fg_color=COLORS["bg"], corner_radius=0)
    translate_panel.pack(fill="both", expand=True)

    # ==========================================
    # CỘT 3: BẢNG KẾT QUẢ BÊN PHẢI
    # ==========================================
    right_panel = ctk.CTkFrame(translate_panel, width=280, fg_color=COLORS["bg"], corner_radius=0)
    right_panel.pack_propagate(False)
    right_panel.pack(side="right", fill="y", padx=(0, 20), pady=20)

    result_card = ctk.CTkFrame(
        right_panel,
        fg_color=COLORS["card"],
        corner_radius=24,
        border_width=1,
        border_color=COLORS["border"]
    )
    result_card.pack(fill="x", pady=(0, 16))

    ctk.CTkLabel(
        result_card,
        text="Kết quả nhận diện",
        font=ctk.CTkFont(size=21, weight="bold"),
        text_color=COLORS["text"]
    ).pack(anchor="w", padx=20, pady=(20, 8))

    result_box = ctk.CTkFrame(result_card, fg_color="#0F1422", corner_radius=18)
    result_box.pack(fill="x", padx=20, pady=(6, 12))

    result_label = ctk.CTkLabel(
        result_box,
        text="...",
        font=ctk.CTkFont(size=60, weight="bold"),
        text_color=COLORS["blue2"]
    )
    result_label.pack(pady=(18, 0))

    accuracy_label = ctk.CTkLabel(
        result_box,
        text="Sẵn sàng quét...",
        font=ctk.CTkFont(size=14),
        text_color=COLORS["muted"]
    )
    accuracy_label.pack(pady=(0, 16))

    progress_bar = ctk.CTkProgressBar(
        result_card,
        width=220,
        height=12,
        corner_radius=10,
        progress_color=COLORS["blue"],
        fg_color="#0F1422"
    )
    progress_bar.set(0)
    progress_bar.pack(pady=(0, 18))

    mode_rows = [
        ("AI", "Đang sẵn sàng", COLORS["green"]),
        ("Ngưỡng xác nhận", "80%", COLORS["green"]),
    ]

    for label, value, color in mode_rows:
        row = ctk.CTkFrame(result_card, fg_color=COLORS["card2"], corner_radius=14)
        row.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["muted"]
        ).pack(side="left", padx=14, pady=10)

        ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color
        ).pack(side="right", padx=14)

    text_card = ctk.CTkFrame(
        right_panel,
        fg_color=COLORS["card"],
        corner_radius=24,
        border_width=1,
        border_color=COLORS["border"]
    )
    text_card.pack(fill="both", expand=True)

    ctk.CTkLabel(
        text_card,
        text="Văn bản đã ghép",
        font=ctk.CTkFont(size=21, weight="bold"),
        text_color=COLORS["text"]
    ).pack(anchor="w", padx=20, pady=(20, 8))

    sentence_box = ctk.CTkTextbox(
        text_card,
        height=160,
        font=ctk.CTkFont(size=20),
        wrap="word",
        fg_color="#0F1422",
        text_color=COLORS["text"],
        border_width=1,
        border_color=COLORS["border"],
        corner_radius=16
    )
    sentence_box.pack(fill="both", expand=True, padx=20, pady=(6, 12))
    sentence_box.insert("0.0", "")
    sentence_box.configure(state="disabled")

    # Cụm phím chức năng
    def update_box_ui():
        sentence_box.configure(state="normal")
        sentence_box.delete("0.0", "end")
        sentence_box.insert("0.0", current_sentence)
        sentence_box.configure(state="disabled")

    def action_backspace():
        nonlocal current_sentence
        if len(current_sentence) > 0:
            current_sentence = current_sentence[:-1]
            update_box_ui()

    def action_copy():
        root.clipboard_clear()
        root.clipboard_append(current_sentence)
        messagebox.showinfo("Thành công", "Đã sao chép văn bản vào bộ nhớ tạm!")

    def action_clear_all():
        nonlocal current_sentence
        current_sentence = ""
        update_box_ui()

    # Cụm 3 nút chức năng: dùng grid + giảm padding để 3 nút hiển thị đều nhau
    # Lưu ý: không dùng pack(side=left/right) ở đây vì dễ làm nút thứ 3 bị tràn.
    btn_frame = ctk.CTkFrame(text_card, fg_color="transparent")
    btn_frame.pack(fill="x", padx=12, pady=(0, 20))
    btn_frame.grid_columnconfigure(0, weight=1, uniform="action_buttons")
    btn_frame.grid_columnconfigure(1, weight=1, uniform="action_buttons")
    btn_frame.grid_columnconfigure(2, weight=1, uniform="action_buttons")

    button_style = {
        "height": 38,
        "width": 70,
        "corner_radius": 13,
        "font": ctk.CTkFont(size=12, weight="bold"),
    }

    ctk.CTkButton(
        btn_frame,
        text="⌫ Xóa",
        fg_color=COLORS["orange"],
        hover_color="#E99A00",
        text_color="#111827",
        command=action_backspace,
        **button_style
    ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

    ctk.CTkButton(
        btn_frame,
        text="📋 Copy",
        fg_color=COLORS["blue"],
        hover_color="#1473CC",
        text_color="white",
        command=action_copy,
        **button_style
    ).grid(row=0, column=1, sticky="ew", padx=4)

    ctk.CTkButton(
        btn_frame,
        text="🗑 Xóa hết",
        fg_color=COLORS["red"],
        hover_color="#D73745",
        text_color="white",
        command=action_clear_all,
        **button_style
    ).grid(row=0, column=2, sticky="ew", padx=(4, 0))

    # ==========================================
    # CỘT 2: CAMERA Ở GIỮA
    # ==========================================
    middle_panel = ctk.CTkFrame(translate_panel, fg_color=COLORS["bg"], corner_radius=0)
    middle_panel.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    header = ctk.CTkFrame(middle_panel, fg_color="transparent")
    header.pack(fill="x", pady=(0, 14))

    title_box = ctk.CTkFrame(header, fg_color="transparent")
    title_box.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        title_box,
        text="DỊCH TỰ DO",
        font=ctk.CTkFont(size=34, weight="bold"),
        text_color=COLORS["text"]
    ).pack(anchor="w")

    ctk.CTkLabel(
        title_box,
        text="Nhận diện ngôn ngữ ký hiệu bằng camera theo thời gian thực",
        font=ctk.CTkFont(size=15),
        text_color=COLORS["muted"]
    ).pack(anchor="w", pady=(2, 0))

    camera_card = ctk.CTkFrame(
        middle_panel,
        fg_color=COLORS["card"],
        corner_radius=24,
        border_width=1,
        border_color=COLORS["border"]
    )
    camera_card.pack(fill="both", expand=True)

    cam_header = ctk.CTkFrame(camera_card, fg_color="transparent")
    cam_header.pack(fill="x", padx=22, pady=(18, 8))

    ctk.CTkLabel(
        cam_header,
        text="📷 Camera nhận diện",
        font=ctk.CTkFont(size=21, weight="bold"),
        text_color=COLORS["text"]
    ).pack(side="left")

    radar_label = ctk.CTkLabel(
        cam_header,
        text="🔴 Đang tắt camera",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=COLORS["muted"]
    )
    radar_label.pack(side="right")

    camera_border = ctk.CTkFrame(
        camera_card,
        fg_color=COLORS["camera"],
        border_color=COLORS["blue"],
        border_width=2,
        corner_radius=22
    )
    camera_border.pack(fill="both", expand=True, padx=22, pady=(8, 18))

    video_label = ctk.CTkLabel(
        camera_border,
        text="🖐️\n\nNhấn Bật Camera để bắt đầu dịch",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=COLORS["muted"]
    )
    video_label.pack(fill="both", expand=True, padx=10, pady=10)

    history_frame = ctk.CTkFrame(camera_card, fg_color="#0F1422", corner_radius=16)
    history_label = ctk.CTkLabel(
        history_frame,
        text="Lịch sử: ",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=COLORS["green"]
    )

    # ==========================================
    # LOGIC NGƯỜI GÁC CỔNG AI
    # ==========================================
    def toggle_camera():
        nonlocal cap, is_camera_on, last_detected, history_list, current_sentence
        nonlocal test_sequence_1, test_sequence_2, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
        nonlocal cached_raw_text, cached_prob
        
        if not is_camera_on:
            # Dùng CAP_DSHOW trên Windows để mở camera nhanh hơn và giảm độ trễ buffer.
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
            
            # ÉP ĐỘ PHÂN GIẢI THẤP HƠN ĐỂ GIẢM DELAY KHUNG HÌNH
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            
            is_camera_on = True
            cam_btn.configure(text="■  Tắt Camera", fg_color=COLORS["red"], hover_color="#D73745", text_color=COLORS["text"])
            video_label.configure(text="")
            camera_border.pack(fill="both", expand=True, padx=22, pady=(8, 18))
            history_frame.pack(fill="x", padx=22, pady=(0, 18), side="bottom")
            history_label.pack(padx=18, pady=12, anchor="w")
            update_frame()
        else:
            is_camera_on = False
            if cap: cap.release()
            video_label.configure(image="", text="🖐️\n\nNhấn Bật Camera để bắt đầu dịch")
            video_label.image = None
            history_frame.pack_forget()
            cam_btn.configure(text="▶  Bật Camera", fg_color=COLORS["green"], hover_color="#24B874", text_color="#08111F")
            radar_label.configure(text="🔴 Đang tắt camera", text_color=COLORS["muted"])
            
            result_label.configure(text="...")
            accuracy_label.configure(text="Sẵn sàng quét...")
            progress_bar.set(0)
            history_list.clear()
            last_detected = ""
            test_sequence_1.clear()
            test_sequence_2.clear()
            cached_raw_text, cached_prob = "", 0.0
            prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = None, None, None, None

    cam_btn.configure(command=toggle_camera)

    # ==========================================
    # CHUYỂN PANEL TRONG FRAME CHÍNH
    # ==========================================
    def set_active_nav(active_name: str):
        nav_config = {
            "translate": translate_nav_btn,
            "study": study_nav_btn,
            "minigame": minigame_nav_btn,
        }
        for name, btn in nav_config.items():
            is_active = name == active_name
            btn.configure(
                fg_color=COLORS["blue"] if is_active else "transparent",
                hover_color="#1473CC" if is_active else COLORS["card2"],
                font=ctk.CTkFont(size=15, weight="bold" if is_active else "normal"),
            )

    def clear_embedded_panels():
        for child in content_container.winfo_children():
            if child is not translate_panel:
                child.destroy()

    def stop_camera_before_switch():
        # Nếu đang bật camera mà chuyển qua Góc học tập/Minigame thì tắt trước
        # để tránh camera vẫn chạy nền gây lag.
        if is_camera_on:
            toggle_camera()

    def show_translate_panel():
        clear_embedded_panels()
        for child in content_container.winfo_children():
            child.pack_forget()
        translate_panel.pack(fill="both", expand=True)
        set_active_nav("translate")
        
        # Đã sửa lại khoảng cách (pady) để nó bung ra đúng vị trí trên nút đăng nhập
        cam_btn.pack(before=account_btn, side="top", fill="x", padx=15, pady=(0, 15))

    def show_study_panel():
        stop_camera_before_switch()
        clear_embedded_panels()
        translate_panel.pack_forget()
        cam_btn.pack_forget()

        panel = ctk.CTkFrame(content_container, fg_color=COLORS["bg"], corner_radius=0)
        panel.pack(fill="both", expand=True)

        if StudyApp is None:
            ctk.CTkLabel(
                panel,
                text=f"Chưa mở được Góc học tập.\nChi tiết: {_study_import_error}",
                text_color=COLORS["red"],
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(expand=True)
        else:
            # show_sidebar=False để không hiện sidebar phụ bên trong.
            StudyApp(panel, show_sidebar=False, on_back=show_translate_panel)

        set_active_nav("study")

    def show_minigame_panel():
        stop_camera_before_switch()
        clear_embedded_panels()
        translate_panel.pack_forget()
        cam_btn.pack_forget()

        panel = ctk.CTkFrame(content_container, fg_color=COLORS["bg"], corner_radius=0)
        panel.pack(fill="both", expand=True)

        if MinigameFrame is None:
            ctk.CTkLabel(
                panel,
                text=f"Chưa mở được Minigame.\nChi tiết: {_minigame_import_error}",
                text_color=COLORS["red"],
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(expand=True)
        else:
            # show_sidebar=False để Minigame dùng sidebar chính của app.
            MinigameFrame(panel, on_back=show_translate_panel, show_sidebar=False).pack(fill="both", expand=True)

        set_active_nav("minigame")
    def show_auth_panel():
        stop_camera_before_switch()
        clear_embedded_panels()
        translate_panel.pack_forget()
        cam_btn.pack_forget()

        # Bỏ Active (làm mờ) tất cả các nút điều hướng bên trái
        translate_nav_btn.configure(fg_color="transparent", font=ctk.CTkFont(size=15, weight="normal"))
        study_nav_btn.configure(fg_color="transparent", font=ctk.CTkFont(size=15, weight="normal"))
        minigame_nav_btn.configure(fg_color="transparent", font=ctk.CTkFont(size=15, weight="normal"))

        try:
            import auth_ui
            
            # Nếu đã đăng nhập rồi thì không cho vô màn hình đăng nhập nữa
            if auth_ui.CURRENT_USER is not None:
                messagebox.showinfo("Tài khoản", f"Bạn đang đăng nhập với tài khoản: {auth_ui.CURRENT_USER['username']}")
                show_study_panel()
                return

            def on_login_success():
                # Cập nhật chữ, đổi nền sang xanh rêu và giữ chữ trắng
                account_btn.configure(
                    text=f"🟢  Chào, {auth_ui.CURRENT_USER['username']}", 
                    fg_color="#17351F", 
                    text_color="white"
                )
                
                # Hiện nút đăng xuất với khoảng cách (pady) đều hơn
                logout_btn.pack(after=account_btn, side="top", fill="x", padx=15, pady=(8, 0))
                
                show_study_panel()

            # Triệu hồi AuthFrame và thả vào khung nội dung chính
            auth_frame = auth_ui.AuthFrame(content_container, on_success=on_login_success)
            auth_frame.pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải giao diện đăng nhập: {e}")
    def update_frame():
        nonlocal last_detected, history_list, current_sentence, frame_counter, prev_time
        nonlocal test_sequence_1, test_sequence_2, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
        nonlocal cached_raw_text, cached_prob
        
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame_counter += 1
                curr_time = time.time()
                fps = 1 / (curr_time - prev_time) if prev_time > 0 else 30
                prev_time = curr_time
                
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                hands_detected = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
                
                raw_text, prob = "", 0.0
                is_ready = False

                # Cập nhật Radar
                if hands_detected == 1:
                    radar_label.configure(text="🟢 Đang nhận diện: 1 Tay", text_color="#4CAF50")
                elif hands_detected == 2:
                    radar_label.configure(text="🔵 Đang nhận diện: 2 Tay", text_color="#2196F3")
                else:
                    radar_label.configure(text="🔴 Không thấy tay", text_color="#F44336")

                # 🌟 TÍNH NĂNG MỚI 4: VẼ KHUNG HƯỚNG DẪN KHI TRỐNG TRƠN
                if hands_detected == 0:
                    cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (150, 150, 150), 2)
                    cv2.putText(frame, "DUA TAY VAO KHUNG HINH", (w//4 - 20, h//4 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)

                # Hiển thị FPS
                cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                if hands_detected > 0:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    if hands_detected == 1:
                        test_sequence_2.clear() 
                        handedness = results.multi_handedness[0]
                        hand_landmarks = results.multi_hand_landmarks[0]
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        current_vector, prev_wx_l, prev_wy_l = hand_vectorlize(hand_landmarks.landmark, hand_type, prev_wx_l, prev_wy_l)
                        
                        if lstm_model_1 is not None:
                            test_sequence_1.append(current_vector)
                            test_sequence_1 = test_sequence_1[-30:]
                            if len(test_sequence_1) == 30:
                                # Tối ưu: không gọi AI ở mọi frame để giảm giật/độ trễ camera
                                if frame_counter % AI_INTERVAL == 0:
                                    cached_raw_text, cached_prob = predict_sign(lstm_model_1, action_labels_1, test_sequence_1)
                                raw_text, prob = cached_raw_text, cached_prob
                                is_ready = True
                                
                    elif hands_detected == 2:
                        test_sequence_1.clear() 
                        current_vector, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = extract_86_features(
                            results, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
                        )
                        
                        if current_vector is not None and lstm_model_2 is not None:
                            test_sequence_2.append(current_vector)
                            test_sequence_2 = test_sequence_2[-30:]
                            if len(test_sequence_2) == 30:
                                if frame_counter % AI_INTERVAL == 0:
                                    cached_raw_text, cached_prob = predict_sign(lstm_model_2, action_labels_2, test_sequence_2)
                                raw_text, prob = cached_raw_text, cached_prob
                                is_ready = True

                else:
                    prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = None, None, None, None
                    test_sequence_1.clear()
                    test_sequence_2.clear()
                    cached_raw_text, cached_prob = "", 0.0
                    last_detected = ""

                # --- BỘ LỌC 80% CHUNG & HIỂN THỊ UI ---
                if is_ready:
                    accuracy_pct = int(prob * 100)
                    
                    SIGN_DISPLAY_MAP = {
                        "DAU_MU": "^", "DAU_MOC": "˘", "DAU_SAC": "´", 
                        "DAU_HUYEN": "`", "DAU_HOI": "?", "DAU_NGA": "~", "DAU_NANG": "."
                    }
                    
                    visual_text = SIGN_DISPLAY_MAP.get(raw_text, raw_text)
                    hover_text = visual_text if raw_text != "KHONG_XAC_DINH" else "Chưa rõ"
                    
                    # Cập nhật thanh tiến độ màu sắc
                    progress_bar.set(prob)
                    if prob < 0.5:
                        progress_bar.configure(progress_color="#F44336")
                        color_code = "#F44336"
                        status_text = f"Không hợp lệ: {hover_text} ({accuracy_pct}%)"
                        display_text = "..." 
                    elif prob < 0.8:
                        progress_bar.configure(progress_color="#FF9800")
                        color_code = "#FF9800"
                        status_text = f"Đang phân tích: {hover_text} ({accuracy_pct}%)"
                        display_text = "..." 
                    else:
                        progress_bar.configure(progress_color="#4CAF50")
                        color_code = "#4CAF50"
                        status_text = f"Đã xác nhận: {hover_text} ({accuracy_pct}%)"
                        display_text = raw_text  
                            
                    result_label.configure(text=visual_text if display_text != "..." else "...")
                    accuracy_label.configure(text=status_text, text_color=color_code)
                    
                    # LOGIC GÕ VĂN BẢN
                    if frame_counter % AI_INTERVAL == 0:
                        if display_text != last_detected:
                            if display_text != "...":
                                history_list.append(visual_text) 
                                if len(history_list) > 6:
                                    history_list.pop(0)
                                history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                
                                if display_text == "SPACE": current_sentence += " "
                                elif display_text == "DEL": current_sentence = current_sentence[:-1]
                                elif display_text == "CLEAR": current_sentence = ""
                                elif display_text in LIST_DAU: 
                                    current_sentence = apply_vietnamese_sign(current_sentence, display_text)
                                elif len(display_text) == 1: current_sentence += display_text 
                                else:
                                    if len(current_sentence) > 0 and current_sentence[-1] != " ":
                                        current_sentence += " "
                                    current_sentence += display_text + " "

                                update_box_ui()

                            last_detected = display_text
                else:
                    progress_bar.set(0)

                # Xử lý hình ảnh xuất ra
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                target_w = min(camera_border.winfo_width() - 20, DISPLAY_MAX_WIDTH)
                target_h = min(camera_border.winfo_height() - 20, DISPLAY_MAX_HEIGHT)
                if target_w > 10 and target_h > 10:
                    scale = min(target_w / w, target_h / h)
                    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                    frame_rgb = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.configure(image=imgtk, text="")
                video_label.image = imgtk

            root.after(5, update_frame)

    def on_close():
        if cap: cap.release()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
