import sys
import os
import time # Thêm thư viện đo FPS
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
    right_panel = ctk.CTkFrame(root, width=320, fg_color="#2B2B2B", corner_radius=0)
    right_panel.pack_propagate(False)
    right_panel.pack(side="right", fill="y")

    ctk.CTkLabel(right_panel, text="KẾT QUẢ DỊCH", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 0))
    result_label = ctk.CTkLabel(right_panel, text="...", font=ctk.CTkFont(size=60, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=(10, 0))
    
    accuracy_label = ctk.CTkLabel(right_panel, text="Sẵn sàng quét...", font=ctk.CTkFont(size=14), text_color="gray70")
    accuracy_label.pack(pady=(0, 5))
    
    # 🌟 TÍNH NĂNG MỚI 1: THANH TIẾN ĐỘ ĐỘ TỰ TIN
    progress_bar = ctk.CTkProgressBar(right_panel, width=200, height=12, corner_radius=10)
    progress_bar.set(0)
    progress_bar.pack(pady=(0, 20))

    ctk.CTkLabel(right_panel, text="VĂN BẢN ĐÃ GHÉP", font=ctk.CTkFont(size=16, weight="bold"), text_color="#4CAF50").pack(pady=(10, 5))
    sentence_box = ctk.CTkTextbox(right_panel, height=120, font=ctk.CTkFont(size=20), wrap="word", fg_color="#1E1E1E")
    sentence_box.pack(fill="x", padx=20, pady=5)
    sentence_box.insert("0.0", "")
    sentence_box.configure(state="disabled")

    # 🌟 TÍNH NĂNG MỚI 2: CỤM PHÍM CHỨC NĂNG MỚI
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

    btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
    btn_frame.pack(pady=10, fill="x", padx=20)
    
    ctk.CTkButton(btn_frame, text="⌫ Xóa", width=80, fg_color="#FF9800", hover_color="#F57C00", command=action_backspace).pack(side="left", padx=(0, 5))
    ctk.CTkButton(btn_frame, text="📋 Copy", width=80, fg_color="#2196F3", hover_color="#1976D2", command=action_copy).pack(side="left", padx=5)
    ctk.CTkButton(btn_frame, text="Xóa hết", width=80, fg_color="#F44336", hover_color="#D32F2F", command=action_clear_all).pack(side="right", padx=(5, 0))

    # ==========================================
    # CỘT 2: CAMERA Ở GIỮA 
    # ==========================================
    middle_panel = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    middle_panel.pack(side="left", fill="both", expand=True)
    
    # 🌟 TÍNH NĂNG MỚI 3: RADAR THEO DÕI TAY
    radar_label = ctk.CTkLabel(middle_panel, text="🔴 Đang tắt camera", font=ctk.CTkFont(size=16, weight="bold"), text_color="gray50")
    radar_label.pack(pady=(15, 5))
    
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
        nonlocal cached_raw_text, cached_prob
        
        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            
            # ÉP ĐỘ PHÂN GIẢI CHUẨN ĐỂ CHỐNG LAG
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            is_camera_on = True
            cam_btn.configure(text="Tắt Camera", fg_color="#F44336", hover_color="#D32F2F")
            camera_border.pack(expand=True, padx=20, pady=5) 
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
            radar_label.configure(text="🔴 Đang tắt camera", text_color="gray50")
            
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
                    radar_label.configure(text="🟢 Đang nhận diện: 1 Tay (Chế độ Phím/Dấu)", text_color="#4CAF50")
                elif hands_detected == 2:
                    radar_label.configure(text="🔵 Đang nhận diện: 2 Tay (Chế độ Từ vựng)", text_color="#2196F3")
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
                                # Tối ưu: Chỉ gọi model mỗi 5 frame (giảm tải 80%)
                                if frame_counter % 5 == 0:
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
                                if frame_counter % 5 == 0:
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
                    if frame_counter % 10 == 0:
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
                target_w, target_h = middle_panel.winfo_width() - 40, middle_panel.winfo_height() - 100 
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