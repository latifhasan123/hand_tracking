import sys
import os
# Cho phép Python nhìn ngược ra ngoài thư mục gốc để tìm các file dùng chung
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Gọi các thuật toán xử lý hình ảnh và nhận diện (BẢN MỚI NHẤT)
from core.train_window import hand_vectorlize, hands, mp_draw, mp_hands
from core.translate_window import load_lstm_model, predict_sign

def create_user_menu(root):
    root.title("Hand Sign Translator - Ứng dụng phiên dịch")
    window_width = 1100
    window_height = 700
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    # LOAD BỘ NÃO ONNX MỚI NHẤT
    lstm_model, action_labels = load_lstm_model()

    # CÁC BIẾN QUẢN LÝ CAMERA & CHUỖI KHUNG HÌNH (Đã nâng cấp)
    cap = None
    is_camera_on = False
    history_list = []
    last_detected = ""
    current_sentence = "" 
    
    # Biến phục vụ AI phiên bản chuỗi thời gian
    test_sequence = []
    prev_wx = None
    prev_wy = None
    frame_counter = 0

    # ==========================================
    # KHU VỰC ĐIỀU KHIỂN (BÊN TRÁI)
    # ==========================================
    left_frame = ctk.CTkFrame(root, width=350, corner_radius=0)
    left_frame.pack_propagate(False) 
    left_frame.pack(side="left", fill="y")

    title = ctk.CTkLabel(left_frame, text="PHIÊN DỊCH KÝ HIỆU", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2196F3")
    title.pack(pady=(30, 10))

    def toggle_camera():
        nonlocal cap, is_camera_on, last_detected, history_list, current_sentence
        nonlocal test_sequence, prev_wx, prev_wy
        
        if lstm_model is None:
            messagebox.showerror("Lỗi", "Không tìm thấy bộ não AI (model.onnx). Vui lòng liên hệ Quản trị viên!")
            return

        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            # FIX LAG 1: Ép OpenCV chỉ giữ 1 khung hình mới nhất, không lưu nháp
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
            
            is_camera_on = True
            cam_btn.configure(text="Tắt Camera", fg_color="#F44336", hover_color="#D32F2F")
            camera_border.pack(expand=True, padx=20, pady=20) 
            history_frame.pack(fill="x", padx=20, pady=10, side="bottom") 
            update_frame()
        else:
            is_camera_on = False
            if cap: cap.release()
            video_label.configure(image="")
            camera_border.pack_forget() 
            history_frame.pack_forget()
            cam_btn.configure(text="Bật Camera", fg_color="#4CAF50", hover_color="#388E3C")
            
            result_label.configure(text="...")
            history_list.clear()
            last_detected = ""
            history_label.configure(text="Lịch sử: ")
            
            test_sequence.clear()
            prev_wx, prev_wy = None, None

    cam_btn = ctk.CTkButton(left_frame, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"),
                            fg_color="#4CAF50", hover_color="#388E3C", height=45, command=toggle_camera)
    cam_btn.pack(fill="x", padx=30, pady=10)

    # ==========================================
    # TẠO KHUNG TỪ ĐIỂN NỔI (IN-APP MODAL)
    # ==========================================
    dict_frame = ctk.CTkFrame(root, fg_color="#2B2B2B", border_width=2, border_color="#FF9800", corner_radius=15)
    
    try:
        img = Image.open("vsl_dict.gif") 
        img = img.resize((600, 450), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        lbl = ctk.CTkLabel(dict_frame, text="", image=photo)
        lbl.image = photo 
        lbl.pack(padx=20, pady=(20, 10))
    except Exception:
        err_text = "⚠️ Không tìm thấy ảnh từ điển!\nBạn hãy đảm bảo file 'vsl_dict.gif' nằm cùng thư mục gốc."
        ctk.CTkLabel(dict_frame, text=err_text, font=ctk.CTkFont(size=16), text_color="#FF9800").pack(padx=40, pady=40)

    def close_dictionary():
        dict_frame.place_forget() 

    close_btn = ctk.CTkButton(dict_frame, text="Đóng Từ Điển", font=ctk.CTkFont(weight="bold"),
                              fg_color="#F44336", hover_color="#D32F2F", command=close_dictionary)
    close_btn.pack(pady=(0, 20))

    def show_dictionary():
        dict_frame.place(relx=0.5, rely=0.5, anchor="center")
        dict_frame.lift() 

    dict_btn = ctk.CTkButton(left_frame, text="📖 Từ điển (Cheat Sheet)", font=ctk.CTkFont(size=14, weight="bold"),
                             fg_color="#FF9800", hover_color="#F57C00", height=40, command=show_dictionary)
    dict_btn.pack(fill="x", padx=30, pady=(0, 10))

    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)

    # --- KHU VỰC HIỂN THỊ KẾT QUẢ VÀ VĂN BẢN ---
    result_container = ctk.CTkFrame(left_frame, fg_color="transparent")
    result_container.pack(fill="both", expand=True, pady=5)
    
    ctk.CTkLabel(result_container, text="KẾT QUẢ DỊCH", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5, 0))
    result_label = ctk.CTkLabel(result_container, text="...", font=ctk.CTkFont(size=60, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=5)

    ctk.CTkLabel(result_container, text="VĂN BẢN ĐÃ GHÉP", font=ctk.CTkFont(size=16, weight="bold"), text_color="#4CAF50").pack(pady=(10, 5))
    sentence_box = ctk.CTkTextbox(result_container, height=100, font=ctk.CTkFont(size=20), wrap="word")
    sentence_box.pack(fill="x", padx=20, pady=5)
    sentence_box.insert("0.0", "")
    sentence_box.configure(state="disabled")

    def clear_text():
        nonlocal current_sentence
        current_sentence = ""
        sentence_box.configure(state="normal")
        sentence_box.delete("0.0", "end")
        sentence_box.configure(state="disabled")

    ctk.CTkButton(result_container, text="Xóa văn bản", command=clear_text, font=ctk.CTkFont(weight="bold"), 
                  fg_color="#F44336", hover_color="#D32F2F").pack(pady=10)

    # ==========================================
    # KHU VỰC CAMERA (BÊN PHẢI)
    # ==========================================
    right_frame = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    
    camera_border = ctk.CTkFrame(right_frame, fg_color="black", border_color="#9C27B0", border_width=4, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=12, pady=12) 

    history_frame = ctk.CTkFrame(right_frame, fg_color="#1E1E1E", corner_radius=10)
    history_label = ctk.CTkLabel(history_frame, text="Lịch sử: ", font=ctk.CTkFont(size=18, weight="bold"), text_color="#4CAF50")
    history_label.pack(padx=20, pady=10, anchor="w")

    # FIX LAG 2: Đọc font 1 lần duy nhất ở ngoài vòng lặp
    try:
        vietnamese_font = ImageFont.truetype("arial.ttf", 32)
    except IOError:
        vietnamese_font = ImageFont.load_default()

    def update_frame():
        nonlocal last_detected, history_list, current_sentence
        nonlocal test_sequence, prev_wx, prev_wy, frame_counter
        
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame_counter += 1
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                display_text = ""

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        landmarks = hand_landmarks.landmark
                        
                        # Sử dụng logic mới: Lấy thêm prev_wx, prev_wy
                        current_vector, prev_wx, prev_wy = hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy)

                        x_list = [int(lm.x * w) for lm in landmarks]
                        y_list = [int(lm.y * h) for lm in landmarks]
                        x_min, y_min = min(x_list) - 20, min(y_list) - 20
                        x_max, y_max = max(x_list) + 20, max(y_list) + 20
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                        if lstm_model is not None:
                            test_sequence.append(current_vector)
                            test_sequence = test_sequence[-30:] # Giữ đúng 30 khung hình
                            
                            # Nhận diện khi đủ 30 khung hình
                            if len(test_sequence) == 30 and frame_counter % 10 == 0:
                                raw_text = predict_sign(lstm_model, action_labels, test_sequence)
                                display_text = "..." if raw_text == "KHONG_XAC_DINH" else raw_text
                                result_label.configure(text=display_text)
                                
                                if display_text != last_detected:
                                    if display_text != "...":
                                        history_list.append(display_text)
                                        if len(history_list) > 6:
                                            history_list.pop(0)
                                        history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                        
                                        if display_text == "SPACE":
                                            current_sentence += " "
                                        elif display_text == "DEL":
                                            current_sentence = current_sentence[:-1]
                                        elif display_text == "CLEAR":
                                            current_sentence = ""
                                        
                                        elif len(display_text) == 1:
                                            current_sentence += display_text 
                                        else:
                                            if len(current_sentence) > 0 and current_sentence[-1] != " ":
                                                current_sentence += " "
                                            current_sentence += display_text + " "

                                        sentence_box.configure(state="normal")
                                        sentence_box.delete("0.0", "end")
                                        sentence_box.insert("0.0", current_sentence)
                                        sentence_box.configure(state="disabled")

                                    last_detected = display_text

                        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(img_pil)
                        # Dùng font đã tải ở ngoài
                        draw.text((x_min, y_min - 40), str(display_text), font=vietnamese_font, fill=(0, 255, 0)) 
                        frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
                else:
                    # Nếu rút tay ra, reset lại chuỗi
                    prev_wx, prev_wy = None, None
                    test_sequence.clear()
                    last_detected = ""

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                target_w, target_h = right_frame.winfo_width() - 60, right_frame.winfo_height() - 150 
                if target_w > 10 and target_h > 10:
                    scale = min(target_w / w, target_h / h)
                    frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.configure(image=imgtk)
                video_label.image = imgtk

            # FIX LAG 3: Ép giao diện vẽ nhanh hơn (1 mili-giây thay vì 10)
            root.after(1, update_frame)

    def on_close():
        if cap: cap.release()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)