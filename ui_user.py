import customtkinter as ctk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np

# Gọi các thuật toán xử lý hình ảnh và nhận diện
from train_window import hand_vectorlize, hands, mp_draw, mp_hands
from translate_window import load_model, predict_sign

def create_user_menu(root):
    # ==========================================
    # THIẾT LẬP CỬA SỔ TRUNG TÂM
    # ==========================================
    root.title("Hand Sign Translator - Ứng dụng phiên dịch")
    window_width = 1100
    window_height = 700
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    # ==========================================
    # LOAD AI NGAY KHI MỞ APP (Làm nóng trước)
    # ==========================================
    model = load_model()
    if model is not None:
        try:
            dummy_vector = np.zeros(24)
            model.kneighbors([dummy_vector]) 
        except:
            pass

    # ==========================================
    # BIẾN QUẢN LÝ
    # ==========================================
    cap = None
    is_camera_on = False
    
    history_list = []
    last_detected = ""

    # ==========================================
    # KHU VỰC ĐIỀU KHIỂN (BÊN TRÁI)
    # ==========================================
    left_frame = ctk.CTkFrame(root, width=350, corner_radius=0)
    left_frame.pack_propagate(False) 
    left_frame.pack(side="left", fill="y")

    title = ctk.CTkLabel(left_frame, text="PHIÊN DỊCH KÝ HIỆU", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2196F3")
    title.pack(pady=(30, 10))
    
    desc = ctk.CTkLabel(left_frame, text="Hãy giơ tay lên trước camera\nđể ứng dụng tự động nhận diện.", font=ctk.CTkFont(size=14), text_color="gray60")
    desc.pack(pady=(0, 20))

    # --- ĐIỀU KHIỂN CAMERA (Tự động dịch) ---
    def toggle_camera():
        nonlocal cap, is_camera_on, last_detected, history_list
        
        if model is None:
            messagebox.showerror("Lỗi hệ thống", "Không tìm thấy bộ não AI (model.pkl). Vui lòng liên hệ Quản trị viên!")
            return

        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            is_camera_on = True
            cam_btn.configure(text="Tắt Camera", fg_color="#F44336", hover_color="#D32F2F")
            camera_border.pack(expand=True, padx=20, pady=20) 
            history_frame.pack(fill="x", padx=20, pady=10, side="bottom") 
            update_frame()
        else:
            is_camera_on = False
            if cap:
                cap.release()
            video_label.configure(image="")
            camera_border.pack_forget() 
            history_frame.pack_forget()
            cam_btn.configure(text="Bật Camera", fg_color="#4CAF50", hover_color="#388E3C")
            
            # Reset lại kết quả khi tắt cam
            result_label.configure(text="...")
            history_list.clear()
            last_detected = ""
            history_label.configure(text="Lịch sử: ")

    cam_btn = ctk.CTkButton(left_frame, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"),
                            fg_color="#4CAF50", hover_color="#388E3C", height=50, command=toggle_camera)
    cam_btn.pack(fill="x", padx=30, pady=10)

    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=20)

    # --- HIỂN THỊ KẾT QUẢ TẬP TRUNG ---
    result_container = ctk.CTkFrame(left_frame, fg_color="transparent")
    result_container.pack(fill="both", expand=True, pady=20)
    
    ctk.CTkLabel(result_container, text="KẾT QUẢ DỊCH", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(30, 10))
    result_label = ctk.CTkLabel(result_container, text="...", font=ctk.CTkFont(size=80, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=10)

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

    def update_frame():
        nonlocal last_detected, history_list
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                display_text = ""

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                        hand_label = handedness.classification[0].label
                        hand_type = 0 if hand_label == "Left" else 1

                        landmarks = hand_landmarks.landmark
                        current_vector = hand_vectorlize(landmarks, hand_type)

                        x_list = [int(lm.x * w) for lm in landmarks]
                        y_list = [int(lm.y * h) for lm in landmarks]
                        x_min, y_min = min(x_list) - 20, min(y_list) - 20
                        x_max, y_max = max(x_list) + 20, max(y_list) + 20
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                        if model is not None:
                            # Lấy kết quả gốc từ AI
                            raw_text = predict_sign(model, current_vector)
                            
                            # CHUYỂN ĐỔI: Nếu là UNKNOWN thì hiển thị "..."
                            display_text = "..." if raw_text == "UNKNOWN" else raw_text
                            
                            result_label.configure(text=display_text)
                            
                            # THUẬT TOÁN LỊCH SỬ (Chống nhiễu dấu ...)
                            if display_text != "..." and display_text != last_detected:
                                history_list.append(display_text)
                                if len(history_list) > 6:
                                    history_list.pop(0)
                                history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                last_detected = display_text

                        cv2.putText(frame, str(display_text), (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                target_w = right_frame.winfo_width() - 60
                target_h = right_frame.winfo_height() - 150 
                
                if target_w > 10 and target_h > 10:
                    scale = min(target_w / w, target_h / h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    frame_rgb = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.configure(image=imgtk)
                video_label.image = imgtk

            root.after(10, update_frame)

    def on_close():
        if cap:
            cap.release()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)