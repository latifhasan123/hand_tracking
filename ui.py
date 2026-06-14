import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os

from translate_window import load_lstm_model, predict_sign
from train_window import hand_vectorlize, save_sequence_to_npy, hands, mp_draw, mp_hands

def create_main_menu(root):
    root.title("Hand Sign Translator - Admin Dashboard (LSTM Edition)")
    window_width = 1100
    window_height = 700
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{int((screen_width/2)-(window_width/2))}+{int((screen_height/2)-(window_height/2))}")

    cap = None
    is_camera_on = False
    
    # --- BIẾN QUẢN LÝ QUAY VIDEO ---
    is_recording = False
    sequence_data = []
    SEQUENCE_LENGTH = 30 # Độ dài 1 video (1 giây)

    left_frame = ctk.CTkFrame(root, width=350, corner_radius=0)
    left_frame.pack_propagate(False)
    left_frame.pack(side="left", fill="y")

    title = ctk.CTkLabel(left_frame, text="BẢNG ĐIỀU KHIỂN", font=ctk.CTkFont(size=24, weight="bold"))
    title.pack(pady=(30, 20))

    def toggle_camera():
        nonlocal cap, is_camera_on
        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
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
    ctk.CTkLabel(left_frame, text="1. Thu thập dữ liệu (Chuỗi Video)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF9800").pack(anchor="w", padx=30, pady=(5, 5))
    word_entry = ctk.CTkEntry(left_frame, font=ctk.CTkFont(size=14), placeholder_text="Nhập từ khóa...", height=35)
    word_entry.pack(fill="x", padx=30, pady=5)
    status_label = ctk.CTkLabel(left_frame, text="Đã lưu: 0 mẫu", text_color="gray60")
    status_label.pack(anchor="w", padx=30)

    def check_word(*args):
        word = word_entry.get().strip()
        path = os.path.join("dataset", word)
        if os.path.exists(path):
            status_label.configure(text=f"Đã lưu: {len(os.listdir(path))} mẫu")
        else:
            status_label.configure(text="Đã lưu: 0 mẫu")
            
    word_entry.bind("<KeyRelease>", check_word)

    def start_recording():
        nonlocal is_recording, sequence_data
        word = word_entry.get().strip()
        if not is_camera_on: return messagebox.showwarning("Lỗi", "Hãy bật camera!")
        if word == "": return messagebox.showwarning("Lỗi", "Hãy nhập từ khóa!")
        
        is_recording = True
        sequence_data = []
        camera_border.configure(border_color="#F44336") 

    ctk.CTkButton(left_frame, text="Lưu mẫu (Bấm để quay)", fg_color="transparent", border_width=2, 
                  text_color=("gray10", "#DCE4EE"), command=start_recording).pack(fill="x", padx=30, pady=5)
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)

    # --- 2. HUẤN LUYỆN ---
    ctk.CTkLabel(left_frame, text="2. Huấn luyện Deep Learning", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(5, 5))
    
    import threading
    from train_model import train_lstm_model 
    
    def run_train_model():
        train_btn.configure(state="disabled", text="Đang Train (Xem Terminal)...")
        
        def train_thread():
            try:
                train_lstm_model()
                messagebox.showinfo("Thành công", "Đã huấn luyện xong mô hình LSTM (model.h5)!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Quá trình Train thất bại: {str(e)}")
            finally:
                train_btn.configure(state="normal", text="Train Model")
                
        threading.Thread(target=train_thread, daemon=True).start()

    train_btn = ctk.CTkButton(left_frame, text="Train Model", font=ctk.CTkFont(weight="bold"), fg_color="#2196F3", command=run_train_model)
    train_btn.pack(fill="x", padx=30, pady=5)
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)
    
    # --- 3. KIỂM THỬ NGAY ---
    ctk.CTkLabel(left_frame, text="3. Kiểm thử ngay", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(15, 5))
    result_label = ctk.CTkLabel(left_frame, text="Kết quả: ...", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=5)

    is_testing = False
    lstm_model = None
    action_labels = None
    test_sequence = [] 
    frame_counter = 0

    def toggle_test_mode():
        nonlocal is_testing, lstm_model, action_labels, test_sequence
        if not is_camera_on: return messagebox.showwarning("Lỗi", "Hãy bật camera!")

        if not is_testing:
            lstm_model, action_labels = load_lstm_model()
            if lstm_model is not None:
                is_testing = True
                test_sequence = [] 
                test_btn.configure(text="Đang Test... (Tắt)", fg_color="#FF9800")
                camera_border.configure(border_color="#9C27B0") 
            else:
                messagebox.showerror("Lỗi", "Chưa có model.h5. Hãy Train trước!")
        else:
            is_testing = False
            lstm_model = None
            action_labels = None
            test_sequence = []
            test_btn.configure(text="Bật Test (Translate)", fg_color="#9C27B0")
            camera_border.configure(border_color="#2196F3") 
            result_label.configure(text="Kết quả: ...")

    test_btn = ctk.CTkButton(left_frame, text="Bật Test (Translate)", font=ctk.CTkFont(weight="bold"), fg_color="#9C27B0", command=toggle_test_mode)
    test_btn.pack(fill="x", padx=30, pady=5)

    # ==========================================
    # KHU VỰC CAMERA
    # ==========================================
    right_frame = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    camera_border = ctk.CTkFrame(right_frame, fg_color="black", border_color="#2196F3", border_width=4, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=12, pady=12) 

    def update_frame():
        nonlocal is_recording, sequence_data, test_sequence, frame_counter
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame_counter += 1
                
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame.flags.writeable = False # Khóa ảnh, cấm copy
                results = hands.process(rgb_frame) # Quét AI
                rgb_frame.flags.writeable = True  # Mở khóa lại

                display_text = word_entry.get().strip()
                current_vector = np.zeros(42) 

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        landmarks = hand_landmarks.landmark
                        current_vector = hand_vectorlize(landmarks, hand_type)
                        
                        # --- THUẬT TOÁN KÍCH HOẠT "CỬA SỔ TRƯỢT" KHI TEST ---
                        if is_testing and lstm_model is not None:
                            test_sequence.append(current_vector)
                            test_sequence = test_sequence[-30:]
                            
                            if len(test_sequence) == 30 and frame_counter % 10 == 0:
                                predicted_word = predict_sign(lstm_model, action_labels, test_sequence)
                                
                                if predicted_word != "...":
                                    display_text = predicted_word
                                    result_label.configure(text=f"Dịch: {display_text}")

                        # (ĐÃ XÓA TOÀN BỘ ĐOẠN CODE VẼ TIẾNG VIỆT PIL Ở ĐÂY)

                # Thu thập dữ liệu quay Video
                if is_recording:
                    sequence_data.append(current_vector)
                    cv2.putText(frame, f"DANG QUAY... {len(sequence_data)}/{SEQUENCE_LENGTH}", 
                                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    
                    if len(sequence_data) == SEQUENCE_LENGTH:
                        count = save_sequence_to_npy(word_entry.get().strip(), sequence_data)
                        status_label.configure(text=f"Đã lưu: {count} mẫu")
                        is_recording = False
                        camera_border.configure(border_color="#2196F3") 
                        cv2.putText(frame, "THANH CONG!", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                target_w, target_h = right_frame.winfo_width() - 60, right_frame.winfo_height() - 60 
                if target_w > 10 and target_h > 10:
                    scale = min(target_w / w, target_h / h)
                    frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.configure(image=imgtk)
                video_label.image = imgtk

            root.after(15, update_frame)

    def on_close():
        if cap: cap.release()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)