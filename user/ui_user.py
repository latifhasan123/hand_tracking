import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

from core.train_window import hand_vectorlize, hands, mp_draw, mp_hands
from core.translate_window import load_lstm_model, predict_sign

def create_user_menu(root):
    root.title("Hand Sign Translator - Pro Edition")
    # Tăng chiều rộng lên 1250 để chứa đủ 3 cột cho thoáng
    window_width = 1300
    window_height = 700
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{int((screen_width / 2) - (window_width / 2))}+{int((screen_height / 2) - (window_height / 2))}")

    lstm_model, action_labels = load_lstm_model()

    cap = None
    is_camera_on = False
    history_list = []
    last_detected = ""
    current_sentence = "" 
    test_sequence = []
    prev_wx, prev_wy = None, None
    frame_counter = 0

    # ==========================================
    # CỘT 1: SIDEBAR MENU BÊN TRÁI (Chuẩn Web)
    # ==========================================
    sidebar = ctk.CTkFrame(root, width=300, fg_color="#1E1E1E", corner_radius=0)
    sidebar.pack_propagate(False) 
    sidebar.pack(side="left", fill="y")

    # Logo / Tiêu đề
    ctk.CTkLabel(sidebar, text="🌐 VSL TRANSLATE", font=ctk.CTkFont(size=20, weight="bold"), text_color="#2196F3").pack(pady=(30, 30))

    # Các nút Menu chuyển mode
    def dummy_action(mode_name):
        messagebox.showinfo("Tính năng đang phát triển", f"Tính năng '{mode_name}' sẽ sớm ra mắt!")

    ctk.CTkButton(sidebar, text="🎙️ Dịch tự do", font=ctk.CTkFont(size=15), fg_color="#2B2B2B", hover_color="#383838", anchor="w", height=40).pack(fill="x", padx=15, pady=5)
    ctk.CTkButton(sidebar, text="📚 Góc học tập", font=ctk.CTkFont(size=15), fg_color="transparent", hover_color="#383838", anchor="w", height=40, command=lambda: dummy_action("Góc học tập")).pack(fill="x", padx=15, pady=5)
    ctk.CTkButton(sidebar, text="🎮 Minigame", font=ctk.CTkFont(size=15), fg_color="transparent", hover_color="#383838", anchor="w", height=40, command=lambda: dummy_action("Minigame")).pack(fill="x", padx=15, pady=5)
    
    ctk.CTkFrame(sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=20)
    
    # Nút Từ điển
    ctk.CTkButton(sidebar, text="📖 Từ điển (Cheat Sheet)", font=ctk.CTkFont(size=14, weight="bold"), fg_color="#FF9800", hover_color="#F57C00", height=40, command=lambda: dummy_action("Từ điển")).pack(fill="x", padx=15, pady=5)

    # Nút bật tắt Camera ở dưới cùng Sidebar
    cam_btn = ctk.CTkButton(sidebar, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"), fg_color="#4CAF50", hover_color="#388E3C", height=45)
    cam_btn.pack(side="bottom", fill="x", padx=15, pady=20)

    # ==========================================
    # CỘT 3: BẢNG KẾT QUẢ BÊN PHẢI
    # ==========================================
    right_panel = ctk.CTkFrame(root, width=300, fg_color="#2B2B2B", corner_radius=0)
    right_panel.pack_propagate(False)
    right_panel.pack(side="right", fill="y")

    ctk.CTkLabel(right_panel, text="KẾT QUẢ DỊCH", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 0))
    
    # Hiển thị kết quả to và độ tự tin nhỏ hơn ở dưới
    result_label = ctk.CTkLabel(right_panel, text="...", font=ctk.CTkFont(size=60, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=(10, 0))
    accuracy_label = ctk.CTkLabel(right_panel, text="Độ tự tin: 0%", font=ctk.CTkFont(size=14), text_color="gray70")
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
    # CỘT 2: CAMERA Ở GIỮA (Phần rộng nhất)
    # ==========================================
    middle_panel = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    middle_panel.pack(side="left", fill="both", expand=True)
    
    camera_border = ctk.CTkFrame(middle_panel, fg_color="black", border_color="#2196F3", border_width=2, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=8, pady=8) 

    history_frame = ctk.CTkFrame(middle_panel, fg_color="#1E1E1E", corner_radius=10)
    history_label = ctk.CTkLabel(history_frame, text="Lịch sử: ", font=ctk.CTkFont(size=16, weight="bold"), text_color="#4CAF50")

    # ==========================================
    # LOGIC CAMERA & AI
    # ==========================================
    def toggle_camera():
        nonlocal cap, is_camera_on, last_detected, history_list, current_sentence
        nonlocal test_sequence, prev_wx, prev_wy
        
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
            accuracy_label.configure(text="Độ tự tin: 0%")
            history_list.clear()
            last_detected = ""
            test_sequence.clear()
            prev_wx, prev_wy = None, None

    cam_btn.configure(command=toggle_camera)

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
                accuracy_pct = 0

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        # Vẽ điểm nối trên tay nhưng KHÔNG vẽ khung xanh hình chữ nhật nữa
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        landmarks = hand_landmarks.landmark
                        
                        current_vector, prev_wx, prev_wy = hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy)

                        if lstm_model is not None:
                            test_sequence.append(current_vector)
                            test_sequence = test_sequence[-30:] 
                            
                            if len(test_sequence) == 30 and frame_counter % 10 == 0:
                                # Nhận tuple gồm CHỮ và ĐIỂM
                                raw_text, prob = predict_sign(lstm_model, action_labels, test_sequence)
                                accuracy_pct = int(prob * 100)
                                
                                display_text = "..." if raw_text == "KHONG_XAC_DINH" else raw_text
                                
                                result_label.configure(text=display_text)
                                accuracy_label.configure(text=f"Độ tự tin: {accuracy_pct}%")
                                
                                if display_text != last_detected:
                                    if display_text != "...":
                                        history_list.append(display_text)
                                        if len(history_list) > 6:
                                            history_list.pop(0)
                                        history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                        
                                        if display_text == "SPACE": current_sentence += " "
                                        elif display_text == "DEL": current_sentence = current_sentence[:-1]
                                        elif display_text == "CLEAR": current_sentence = ""
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

                else:
                    prev_wx, prev_wy = None, None
                    test_sequence.clear()
                    last_detected = ""

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