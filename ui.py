import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import time

from train_window import hand_vectorlize, save_to_csv, hands, mp_draw, mp_hands
from train_model import train_model
from translate_window import load_model, predict_sign

def create_main_menu(root):
    root.title("Hand Sign Translator - Admin Dashboard")
    window_width = 1100
    window_height = 700
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{int((screen_width/2)-(window_width/2))}+{int((screen_height/2)-(window_height/2))}")

    cap = None
    is_camera_on = False
    is_testing = False
    sample_count = 0
    current_vector = None
    model = None
    
    history_list = []
    last_detected = ""
    current_sentence = "" # Biến lưu câu

    left_frame = ctk.CTkFrame(root, width=350, corner_radius=0)
    left_frame.pack_propagate(False)
    left_frame.pack(side="left", fill="y")

    title = ctk.CTkLabel(left_frame, text="BẢNG ĐIỀU KHIỂN", font=ctk.CTkFont(size=24, weight="bold"))
    title.pack(pady=(30, 20))

    def toggle_camera():
        nonlocal cap, is_camera_on
        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            is_camera_on = True
            cam_btn.configure(text="Tắt Camera", fg_color="#F44336", hover_color="#D32F2F")
            camera_border.pack(expand=True, padx=20, pady=20) 
            update_frame()
        else:
            is_camera_on = False
            if cap: cap.release()
            video_label.configure(image="")
            camera_border.pack_forget() 
            cam_btn.configure(text="Bật Camera", fg_color="#4CAF50", hover_color="#388E3C")

    cam_btn = ctk.CTkButton(left_frame, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"),
                            fg_color="#4CAF50", hover_color="#388E3C", height=45, command=toggle_camera)
    cam_btn.pack(fill="x", padx=30, pady=(0, 20))
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)

    # --- 1. THU THẬP ---
    ctk.CTkLabel(left_frame, text="1. Thu thập dữ liệu", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(5, 5))
    word_entry = ctk.CTkEntry(left_frame, font=ctk.CTkFont(size=14), placeholder_text="Nhập từ khóa...", height=35)
    word_entry.pack(fill="x", padx=30, pady=5)
    status_label = ctk.CTkLabel(left_frame, text="Đã lưu: 0 mẫu", text_color="gray60")
    status_label.pack(anchor="w", padx=30)

    def save_sample():
        nonlocal sample_count
        word = word_entry.get().strip()
        if not is_camera_on: return messagebox.showwarning("Lỗi", "Hãy bật camera!")
        if current_vector is not None and word != "":
            save_to_csv(word, current_vector)
            sample_count += 1
            status_label.configure(text=f"Đã lưu: {sample_count} mẫu")
            camera_border.configure(border_color="#4CAF50") 
            root.after(300, lambda: camera_border.configure(border_color="#9C27B0" if is_testing else "#2196F3"))

    ctk.CTkButton(left_frame, text="Lưu mẫu (Save)", fg_color="transparent", border_width=2, 
                  text_color=("gray10", "#DCE4EE"), command=save_sample).pack(fill="x", padx=30, pady=5)
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)

    # --- 2. HUẤN LUYỆN ---
    ctk.CTkLabel(left_frame, text="2. Huấn luyện", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(5, 5))
    train_progress = ctk.CTkProgressBar(left_frame, mode="determinate", progress_color="#2196F3")
    train_progress.set(0)

    def run_train_model():
        train_btn.configure(state="disabled", text="Đang Train...")
        train_progress.pack(fill="x", padx=30, pady=(0, 5))
        train_progress.set(0)
        def train_thread():
            for i in range(1, 101, 10):
                train_progress.set(i / 100)
                time.sleep(0.02)
            try:
                train_model()
            except Exception as e:
                pass
            finally:
                train_btn.configure(state="normal", text="Train Model")
                train_progress.pack_forget() 
        threading.Thread(target=train_thread, daemon=True).start()

    train_btn = ctk.CTkButton(left_frame, text="Train Model", font=ctk.CTkFont(weight="bold"), fg_color="#2196F3", command=run_train_model)
    train_btn.pack(fill="x", padx=30, pady=5)
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)

    # --- 3. KIỂM THỬ ---
    ctk.CTkLabel(left_frame, text="3. Kiểm thử ngay", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(5, 5))
    result_label = ctk.CTkLabel(left_frame, text="Kết quả: ...", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=5)

    def toggle_test_mode():
        nonlocal is_testing, model, history_list, last_detected, current_sentence
        if not is_camera_on: return messagebox.showwarning("Lỗi", "Hãy bật camera!")

        if not is_testing:
            model = load_model()
            if model is not None:
                try: model.kneighbors([np.zeros(24)]) 
                except: pass
                is_testing = True
                test_btn.configure(text="Đang Test... (Tắt)", fg_color="#FF9800")
                camera_border.configure(border_color="#9C27B0") 
                history_frame.pack(fill="x", padx=20, pady=10, side="bottom") 
                
                # Hiện khung văn bản
                sentence_title.pack(anchor="w", padx=30, pady=(10,0))
                sentence_box.pack(fill="x", padx=30, pady=5)
            else:
                messagebox.showerror("Lỗi", "Chưa có model.pkl. Hãy Train trước!")
        else:
            is_testing = False
            model = None
            history_list.clear()
            last_detected = ""
            current_sentence = ""
            history_label.configure(text="Lịch sử: ")
            history_frame.pack_forget() 
            test_btn.configure(text="Bật Test (Translate)", fg_color="#9C27B0")
            camera_border.configure(border_color="#2196F3") 
            result_label.configure(text="Kết quả: ...")
            
            # Ẩn khung văn bản
            sentence_title.pack_forget()
            sentence_box.pack_forget()

    test_btn = ctk.CTkButton(left_frame, text="Bật Test (Translate)", font=ctk.CTkFont(weight="bold"), fg_color="#9C27B0", command=toggle_test_mode)
    test_btn.pack(fill="x", padx=30, pady=5)

    # KHUNG VĂN BẢN (Ẩn mặc định)
    sentence_title = ctk.CTkLabel(left_frame, text="Văn bản:", font=ctk.CTkFont(size=14, weight="bold"))
    sentence_box = ctk.CTkTextbox(left_frame, height=50, font=ctk.CTkFont(size=14), wrap="word")
    sentence_box.insert("0.0", "")
    sentence_box.configure(state="disabled")

    # ==========================================
    # KHU VỰC CAMERA (BÊN PHẢI)
    # ==========================================
    right_frame = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    camera_border = ctk.CTkFrame(right_frame, fg_color="black", border_color="#2196F3", border_width=4, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=12, pady=12) 
    history_frame = ctk.CTkFrame(right_frame, fg_color="#1E1E1E", corner_radius=10)
    history_label = ctk.CTkLabel(history_frame, text="Lịch sử: ", font=ctk.CTkFont(size=18, weight="bold"), text_color="#4CAF50")
    history_label.pack(padx=20, pady=10, anchor="w")

    def update_frame():
        nonlocal current_vector, last_detected, history_list, current_sentence
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        landmarks = hand_landmarks.landmark
                        current_vector = hand_vectorlize(landmarks, hand_type)

                        x_min = min([int(lm.x * w) for lm in landmarks]) - 20
                        y_min = min([int(lm.y * h) for lm in landmarks]) - 20
                        x_max = max([int(lm.x * w) for lm in landmarks]) + 20
                        y_max = max([int(lm.y * h) for lm in landmarks]) + 20
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                        display_text = ""
                        if is_testing and model is not None:
                            raw_text = predict_sign(model, current_vector)
                            display_text = "..." if raw_text == "UNKNOWN" else raw_text
                            result_label.configure(text=f"Dịch: {display_text}")
                            
                            # XỬ LÝ LỊCH SỬ VÀ VĂN BẢN
                            # XỬ LÝ LỊCH SỬ VÀ VĂN BẢN
                            # Nếu kết quả mới khác với kết quả vừa nhận diện được trước đó
                            if display_text != last_detected:
                                
                                # Chỉ thực hiện ghép chữ/lưu lịch sử nếu nó không phải là "..."
                                if display_text != "...":
                                    # 1. Cập nhật lịch sử
                                    history_list.append(display_text)
                                    if len(history_list) > 6: 
                                        history_list.pop(0)
                                    history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                    
                                    # 2. Logic ghép chữ
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

                                    # Hiển thị lên ô văn bản
                                    sentence_box.configure(state="normal")
                                    sentence_box.delete("0.0", "end")
                                    sentence_box.insert("0.0", current_sentence)
                                    sentence_box.configure(state="disabled")

                                # Cực kỳ quan trọng: Luôn cập nhật lại biến last_detected kể cả khi nó là "..."
                                # Để khi tay người dùng nghỉ (ra dấu ...), hệ thống sẽ reset nhịp gõ
                                last_detected = display_text
                        elif not is_testing:
                            display_text = word_entry.get()

                        # VẼ TIẾNG VIỆT LÊN CAMERA
                        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(img_pil)
                        try: font = ImageFont.truetype("arial.ttf", 32)
                        except: font = ImageFont.load_default()
                        draw.text((x_min, y_min - 40), str(display_text), font=font, fill=(0, 255, 0)) 
                        frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                target_w, target_h = right_frame.winfo_width() - 60, right_frame.winfo_height() - 150 
                if target_w > 10 and target_h > 10:
                    scale = min(target_w / w, target_h / h)
                    frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.configure(image=imgtk)
                video_label.image = imgtk

            root.after(10, update_frame)

    def on_close():
        if cap: cap.release()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)