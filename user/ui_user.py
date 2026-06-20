import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Nhập 2 cỗ máy hút dữ liệu từ 2 Ngăn
from core.train_window import hand_vectorlize
from core.train_window_both import extract_86_features, hands, mp_draw, mp_hands

# Nhập 2 bộ não AI
from core.translate_window import load_lstm_model, load_lstm_model_both, predict_sign
from core.vietnamese_utils import apply_vietnamese_sign, LIST_DAU
def create_user_menu(root):
    root.title("Hand Sign Translator - Pro Edition (Dual Model)")
    window_width = 1300
    window_height = 700
    
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
    
    # BIẾN NHỚ ĐỘC LẬP CHO 2 NGĂN
    test_sequence_1 = [] # Sổ tay 43 số
    test_sequence_2 = [] # Sổ tay 86 số
    prev_wx_l, prev_wy_l = None, None
    prev_wx_r, prev_wy_r = None, None
    frame_counter = 0

    # ==========================================
    # CỘT 1: SIDEBAR BÊN TRÁI 
    # ==========================================
    sidebar = ctk.CTkFrame(root, width=300, fg_color="#1E1E1E", corner_radius=0)
    sidebar.pack_propagate(False) 
    sidebar.pack(side="left", fill="y")

    ctk.CTkLabel(sidebar, text="🌐 VSL TRANSLATE", font=ctk.CTkFont(size=20, weight="bold"), text_color="#2196F3").pack(pady=(30, 30))

    def dummy_action(mode_name):
        messagebox.showinfo("Tính năng đang phát triển", f"Tính năng '{mode_name}' sẽ sớm ra mắt!")

    ctk.CTkButton(sidebar, text="🎙️ Dịch tự do (1 & 2 Tay)", font=ctk.CTkFont(size=15), fg_color="#2B2B2B", hover_color="#383838", anchor="w", height=40).pack(fill="x", padx=15, pady=5)
    ctk.CTkButton(sidebar, text="📚 Góc học tập", font=ctk.CTkFont(size=15), fg_color="transparent", hover_color="#383838", anchor="w", height=40, command=lambda: dummy_action("Góc học tập")).pack(fill="x", padx=15, pady=5)
    ctk.CTkButton(sidebar, text="🎮 Minigame", font=ctk.CTkFont(size=15), fg_color="transparent", hover_color="#383838", anchor="w", height=40, command=lambda: dummy_action("Minigame")).pack(fill="x", padx=15, pady=5)
    
    ctk.CTkFrame(sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=20)
    ctk.CTkButton(sidebar, text="📖 Từ điển (Cheat Sheet)", font=ctk.CTkFont(size=14, weight="bold"), fg_color="#FF9800", hover_color="#F57C00", height=40, command=lambda: dummy_action("Từ điển")).pack(fill="x", padx=15, pady=5)

    cam_btn = ctk.CTkButton(sidebar, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"), fg_color="#4CAF50", hover_color="#388E3C", height=45)
    cam_btn.pack(side="bottom", fill="x", padx=15, pady=20)

    # ==========================================
    # CỘT 3: BẢNG KẾT QUẢ BÊN PHẢI
    # ==========================================
    right_panel = ctk.CTkFrame(root, width=300, fg_color="#2B2B2B", corner_radius=0)
    right_panel.pack_propagate(False)
    right_panel.pack(side="right", fill="y")

    ctk.CTkLabel(right_panel, text="KẾT QUẢ DỊCH", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 0))
    result_label = ctk.CTkLabel(right_panel, text="...", font=ctk.CTkFont(size=60, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=(10, 0))
    accuracy_label = ctk.CTkLabel(right_panel, text="Sẵn sàng quét...", font=ctk.CTkFont(size=14), text_color="gray70")
    accuracy_label.pack(pady=(0, 20))

    ctk.CTkLabel(right_panel, text="VĂN BẢN ĐÃ GHÉP", font=ctk.CTkFont(size=16, weight="bold"), text_color="#4CAF50").pack(pady=(10, 5))
    sentence_box = ctk.CTkTextbox(right_panel, height=120, font=ctk.CTkFont(size=20), wrap="word", fg_color="#1E1E1E")
    sentence_box.pack(fill="x", padx=20, pady=5)
    sentence_box.insert("0.0", "")
    sentence_box.configure(state="disabled")

    def clear_text():
        nonlocal current_sentence
        current_sentence = ""
        sentence_box.configure(state="normal")
        sentence_box.delete("0.0", "end")
        sentence_box.configure(state="disabled")

    ctk.CTkButton(right_panel, text="Xóa văn bản", command=clear_text, font=ctk.CTkFont(weight="bold"), fg_color="#F44336", hover_color="#D32F2F").pack(pady=10)

    # ==========================================
    # CỘT 2: CAMERA Ở GIỮA 
    # ==========================================
    middle_panel = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    middle_panel.pack(side="left", fill="both", expand=True)
    
    camera_border = ctk.CTkFrame(middle_panel, fg_color="black", border_color="#2196F3", border_width=2, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=8, pady=8) 

    history_frame = ctk.CTkFrame(middle_panel, fg_color="#1E1E1E", corner_radius=10)
    history_label = ctk.CTkLabel(history_frame, text="Lịch sử: ", font=ctk.CTkFont(size=16, weight="bold"), text_color="#4CAF50")

    # ==========================================
    # LOGIC NGƯỜI GÁC CỔNG AI
    # ==========================================
    def toggle_camera():
        nonlocal cap, is_camera_on, last_detected, history_list, current_sentence
        nonlocal test_sequence_1, test_sequence_2, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
        
        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
            is_camera_on = True
            cam_btn.configure(text="Tắt Camera", fg_color="#F44336", hover_color="#D32F2F")
            camera_border.pack(expand=True, padx=20, pady=20) 
            history_frame.pack(fill="x", padx=20, pady=(0, 20), side="bottom") 
            history_label.pack(padx=20, pady=10, anchor="w")
            update_frame()
        else:
            is_camera_on = False
            if cap: cap.release()
            video_label.configure(image="")
            camera_border.pack_forget() 
            history_frame.pack_forget()
            cam_btn.configure(text="Bật Camera", fg_color="#4CAF50", hover_color="#388E3C")
            
            result_label.configure(text="...")
            accuracy_label.configure(text="Sẵn sàng quét...")
            history_list.clear()
            last_detected = ""
            test_sequence_1.clear()
            test_sequence_2.clear()
            prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = None, None, None, None

    cam_btn.configure(command=toggle_camera)

    def update_frame():
        nonlocal last_detected, history_list, current_sentence, frame_counter
        nonlocal test_sequence_1, test_sequence_2, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
        
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame_counter += 1
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                hands_detected = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
                
                raw_text, prob = "", 0
                is_ready = False

                if hands_detected > 0:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # --- NGÃ BA ĐƯỜNG: ĐỊNH TUYẾN DỮ LIỆU ---
                    if hands_detected == 1:
                        test_sequence_2.clear() # Đốt sổ 2 tay
                        
                        handedness = results.multi_handedness[0]
                        hand_landmarks = results.multi_hand_landmarks[0]
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        
                        current_vector, prev_wx_l, prev_wy_l = hand_vectorlize(hand_landmarks.landmark, hand_type, prev_wx_l, prev_wy_l)
                        
                        if lstm_model_1 is not None:
                            test_sequence_1.append(current_vector)
                            test_sequence_1 = test_sequence_1[-30:]
                            if len(test_sequence_1) == 30:
                                raw_text, prob = predict_sign(lstm_model_1, action_labels_1, test_sequence_1)
                                is_ready = True
                                
                    elif hands_detected == 2:
                        test_sequence_1.clear() # Đốt sổ 1 tay
                        
                        current_vector, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = extract_86_features(
                            results, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
                        )
                        
                        if current_vector is not None and lstm_model_2 is not None:
                            test_sequence_2.append(current_vector)
                            test_sequence_2 = test_sequence_2[-30:]
                            if len(test_sequence_2) == 30:
                                raw_text, prob = predict_sign(lstm_model_2, action_labels_2, test_sequence_2)
                                is_ready = True

                else:
                    # KHÔNG THẤY TAY -> RESET MỌI THỨ
                    prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = None, None, None, None
                    test_sequence_1.clear()
                    test_sequence_2.clear()
                    last_detected = ""

                # --- BỘ LỌC 80% CHUNG CHO CẢ 2 NGĂN ---
                # --- BỘ LỌC 80% CHUNG CHO CẢ 2 NGĂN ---
                if is_ready:
                    accuracy_pct = int(prob * 100)
                    
                    # 1. BỘ TỪ ĐIỂN CHUYỂN ĐỔI GIAO DIỆN (VISUAL MAP)
                    SIGN_DISPLAY_MAP = {
                        "DAU_MU": "^",
                        "DAU_MOC": "˘",
                        "DAU_SAC": "´",
                        "DAU_HUYEN": "`",
                        "DAU_HOI": "?",
                        "DAU_NGA": "~",
                        "DAU_NANG": "."
                    }
                    
                    # 2. Bẻ lái hiển thị: Nếu là dấu thì đổi thành ký hiệu, không thì giữ nguyên gốc
                    visual_text = SIGN_DISPLAY_MAP.get(raw_text, raw_text)
                    hover_text = visual_text if raw_text != "KHONG_XAC_DINH" else "Chưa rõ"
                    
                    if accuracy_pct >= 80 and raw_text != "KHONG_XAC_DINH":
                        color_code = "#4CAF50" # Xanh lá
                        # display_text vẫn giữ tên gốc (VD: DAU_NGA) để code logic hiểu
                        display_text = raw_text  
                        status_text = f"Đã xác nhận: {hover_text} ({accuracy_pct}%)"
                    else:
                        display_text = "..." 
                        if accuracy_pct >= 50:
                            color_code = "#FF9800" # Vàng cam
                            status_text = f"Đang phân tích: {hover_text} ({accuracy_pct}%)"
                        else:
                            color_code = "#F44336" # Đỏ
                            status_text = f"Không hợp lệ: {hover_text} ({accuracy_pct}%)"
                            
                    # 3. CẬP NHẬT GIAO DIỆN BẰNG KÝ HIỆU (VISUAL TEXT)
                    result_label.configure(text=visual_text if display_text != "..." else "...")
                    accuracy_label.configure(text=status_text, text_color=color_code)
                    
                    # LOGIC GÕ VĂN BẢN
                    if frame_counter % 10 == 0:
                        if display_text != last_detected:
                            if display_text != "...":
                                # 4. Nhét ký hiệu (visual_text) vào thanh lịch sử cho đẹp
                                history_list.append(visual_text) 
                                if len(history_list) > 6:
                                    history_list.pop(0)
                                history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                
                                # 5. Ở ĐÂY VẪN DÙNG display_text ĐỂ XỬ LÝ GHÉP CHỮ
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

                                sentence_box.configure(state="normal")
                                sentence_box.delete("0.0", "end")
                                sentence_box.insert("0.0", current_sentence)
                                sentence_box.configure(state="disabled")

                            last_detected = display_text

                # Xử lý hình ảnh xuất ra
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                target_w, target_h = middle_panel.winfo_width() - 40, middle_panel.winfo_height() - 120 
                if target_w > 10 and target_h > 10:
                    scale = min(target_w / w, target_h / h)
                    frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.configure(image=imgtk)
                video_label.image = imgtk

            root.after(1, update_frame)

    def on_close():
        if cap: cap.release()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)