import customtkinter as ctk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time

# Gọi Thuật toán từ các file đã tách
from train_window import hand_vectorlize, save_to_csv, hands, mp_draw, mp_hands
from train_model import train_model
from translate_window import load_model, predict_sign

def create_main_menu(root):
    # ==========================================
    # CĂN GIỮA MÀN HÌNH ỨNG DỤNG
    # ==========================================
    root.title("Hand Sign Translator - Admin Dashboard")
    window_width = 1100
    window_height = 700
    
    # Lấy kích thước màn hình máy tính của bạn
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Tính toán tọa độ X và Y để căn giữa
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    
    # Áp dụng tọa độ vào ứng dụng
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    # ==========================================
    # BIẾN QUẢN LÝ
    # ==========================================
    cap = None
    is_camera_on = False
    is_testing = False
    sample_count = 0
    current_vector = None
    model = None
    
    # Biến cho Lịch sử nhận diện
    history_list = []
    last_detected = ""
    # KHU VỰC ĐIỀU KHIỂN (BÊN TRÁI)
    left_frame = ctk.CTkFrame(root, width=350, corner_radius=0)
    left_frame.pack_propagate(False) # THÊM DÒNG NÀY: Khóa cứng chiều rộng 350px, cấm tự động co giãn
    left_frame.pack(side="left", fill="y")

    title = ctk.CTkLabel(left_frame, text="BẢNG ĐIỀU KHIỂN", font=ctk.CTkFont(size=24, weight="bold"))
    title.pack(pady=(30, 20))

    # --- ĐIỀU KHIỂN CAMERA ---
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
            if cap:
                cap.release()
            video_label.configure(image="")
            camera_border.pack_forget() 
            cam_btn.configure(text="Bật Camera", fg_color="#4CAF50", hover_color="#388E3C")

    cam_btn = ctk.CTkButton(left_frame, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"),
                            fg_color="#4CAF50", hover_color="#388E3C", height=45, command=toggle_camera)
    cam_btn.pack(fill="x", padx=30, pady=(0, 20))

    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=10)

    # --- CHỨC NĂNG 1: THU THẬP ---
    ctk.CTkLabel(left_frame, text="1. Thu thập dữ liệu", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(10, 5))
    
    word_entry = ctk.CTkEntry(left_frame, font=ctk.CTkFont(size=14), placeholder_text="Nhập từ khóa (vd: A)...", height=40)
    word_entry.pack(fill="x", padx=30, pady=5)
    
    status_label = ctk.CTkLabel(left_frame, text="Đã lưu: 0 mẫu", font=ctk.CTkFont(size=14), text_color="gray60")
    status_label.pack(anchor="w", padx=30)

    def save_sample():
        nonlocal sample_count, current_vector
        word = word_entry.get().strip()
        if not is_camera_on:
            messagebox.showwarning("Lỗi", "Hãy bật camera!")
            return
        if current_vector is not None and word != "":
            save_to_csv(word, current_vector)
            sample_count += 1
            status_label.configure(text=f"Đã lưu: {sample_count} mẫu")
            
            # HIỆU ỨNG 1: Nháy viền LED màu Xanh lá khi lưu thành công
            camera_border.configure(border_color="#4CAF50") 
            root.after(300, lambda: camera_border.configure(border_color="#9C27B0" if is_testing else "#2196F3"))

    ctk.CTkButton(left_frame, text="Lưu mẫu (Save)", font=ctk.CTkFont(size=14), fg_color="transparent", 
                  border_width=2, text_color=("gray10", "#DCE4EE"), hover_color=("gray70", "gray30"), command=save_sample).pack(fill="x", padx=30, pady=10)
    
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=10)

    # --- CHỨC NĂNG 2: HUẤN LUYỆN (CÓ PROGRESS BAR) ---
    ctk.CTkLabel(left_frame, text="2. Huấn luyện hệ thống", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(10, 5))
    
    # Thanh tiến trình ẩn đi mặc định
    train_progress = ctk.CTkProgressBar(left_frame, mode="determinate", progress_color="#2196F3")
    train_progress.set(0)

    def run_train_model():
        train_btn.configure(state="disabled", text="Đang Train...")
        train_progress.pack(fill="x", padx=30, pady=(0, 5)) # Hiện thanh tiến trình
        train_progress.set(0)

        # Chạy ngầm để không đơ giao diện
        def train_thread():
            for i in range(1, 101, 5):
                train_progress.set(i / 100)
                time.sleep(0.02)
                
            try:
                train_model()
                
                # --- TẠO POPUP THÔNG BÁO TỰ TẮT SAU 1.5 GIÂY ---
                popup = ctk.CTkToplevel(root)
                popup.title("Thông báo")
                popup.geometry("300x120")
                popup.attributes("-topmost", True) # Luôn nổi lên trên cùng
                
                # Căn giữa popup so với cửa sổ chính
                x = root.winfo_x() + (root.winfo_width() // 2) - 150
                y = root.winfo_y() + (root.winfo_height() // 2) - 60
                popup.geometry(f"+{x}+{y}")
                
                ctk.CTkLabel(popup, text="✅ AI đã học xong!", font=ctk.CTkFont(size=20, weight="bold"), text_color="#4CAF50").pack(expand=True)
                
                # Ra lệnh tự hủy cửa sổ sau 1500ms
                popup.after(1500, popup.destroy)
                # -----------------------------------------------

            except Exception as e:
                messagebox.showerror("Lỗi", str(e))
            finally:
                train_btn.configure(state="normal", text="Train Model")
                train_progress.pack_forget() 

        threading.Thread(target=train_thread, daemon=True).start()

    train_btn = ctk.CTkButton(left_frame, text="Train Model", font=ctk.CTkFont(size=16, weight="bold"), 
                              fg_color="#2196F3", hover_color="#1976D2", height=45, command=run_train_model)
    train_btn.pack(fill="x", padx=30, pady=10)
    
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=10)

    # --- CHỨC NĂNG 3: KIỂM THỬ ---
    ctk.CTkLabel(left_frame, text="3. Kiểm thử ngay", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=30, pady=(10, 5))
    
    result_label = ctk.CTkLabel(left_frame, text="Kết quả: ...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=5)

    def toggle_test_mode():
        nonlocal is_testing, model, history_list, last_detected
        if not is_camera_on:
            messagebox.showwarning("Lỗi", "Hãy bật camera!")
            return

        if not is_testing:
            model = load_model()
            if model is not None:
                
                # --- WARM UP AI (CHỐNG ĐƠ CAMERA LẦN ĐẦU) ---
                import numpy as np
                try:
                    # Tạo một bàn tay ảo (Mảng chứa 23 số 0 tương ứng với 23 đặc trưng góc ngón tay)
                    dummy_vector = np.zeros(24)
                    # Ép AI chạy dự đoán nháp ngay trong nền để "làm nóng" RAM
                    model.kneighbors([dummy_vector]) 
                except:
                    pass
                # --------------------------------------------

                is_testing = True
                test_btn.configure(text="Đang Test... (Tắt)", fg_color="#FF9800", hover_color="#F57C00")
                camera_border.configure(border_color="#9C27B0") 
                history_frame.pack(fill="x", padx=20, pady=10, side="bottom") 
            else:
                messagebox.showerror("Lỗi", "Chưa có model.pkl. Hãy Train trước!")
        else:
            is_testing = False
            model = None
            history_list.clear()
            last_detected = ""
            history_label.configure(text="Lịch sử: ")
            history_frame.pack_forget() # Giấu lịch sử
            test_btn.configure(text="Bật Test (Translate)", fg_color="#9C27B0", hover_color="#7B1FA2")
            camera_border.configure(border_color="#2196F3") # Viền LED xanh khi về chế độ thường
            result_label.configure(text="Kết quả: ...")

    test_btn = ctk.CTkButton(left_frame, text="Bật Test (Translate)", font=ctk.CTkFont(size=14, weight="bold"), 
                             fg_color="#9C27B0", hover_color="#7B1FA2", height=45, command=toggle_test_mode)
    test_btn.pack(fill="x", padx=30, pady=10)

    # ==========================================
    # KHU VỰC CAMERA (BÊN PHẢI)
    # ==========================================
    right_frame = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    
    camera_border = ctk.CTkFrame(right_frame, fg_color="black", border_color="#2196F3", border_width=4, corner_radius=15)
    
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=12, pady=12) 

    # HIỆU ỨNG 3: Khung Lịch sử dịch (Nằm ở dưới cùng bên phải)
    history_frame = ctk.CTkFrame(right_frame, fg_color="#1E1E1E", corner_radius=10)
    history_label = ctk.CTkLabel(history_frame, text="Lịch sử: ", font=ctk.CTkFont(size=18, weight="bold"), text_color="#4CAF50")
    history_label.pack(padx=20, pady=10, anchor="w")

    def update_frame():
        nonlocal current_vector, last_detected, history_list
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
                        
                        # --- XỬ LÝ NHẬN DIỆN TRÁI/PHẢI ---
                        hand_label = handedness.classification[0].label
                        # Quy ước: Left (Trái) = 0, Right (Phải) = 1
                        hand_type = 0 if hand_label == "Left" else 1

                        landmarks = hand_landmarks.landmark
                        
                        # Truyền thêm hand_type vào hàm vectorlize
                        current_vector = hand_vectorlize(landmarks, hand_type)

                        x_list = [int(lm.x * w) for lm in landmarks]
                        y_list = [int(lm.y * h) for lm in landmarks]
                        x_min, y_min = min(x_list) - 20, min(y_list) - 20
                        x_max, y_max = max(x_list) + 20, max(y_list) + 20
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                        display_text = ""
                        if is_testing and model is not None:
                            # 1. Lấy kết quả thô từ AI
                            raw_text = predict_sign(model, current_vector)
                            
                            # 2. CHUYỂN ĐỔI: Nếu là UNKNOWN thì hô biến thành "..."
                            display_text = "..." if raw_text == "UNKNOWN" else raw_text
                            
                            # Cập nhật kết quả lên màn hình (Giữ nguyên chữ "Dịch: " của Admin)
                            result_label.configure(text=f"Dịch: {display_text}")
                            
                            # 3. Cập nhật lịch sử (Bỏ qua dấu "...")
                            if display_text != "..." and display_text != last_detected:
                                history_list.append(display_text)
                                if len(history_list) > 6: # Chỉ giữ lại 6 chữ gần nhất
                                    history_list.pop(0)
                                history_label.configure(text="Lịch sử: " + " ➔ ".join(history_list))
                                last_detected = display_text

                        elif not is_testing:
                            display_text = word_entry.get()

                        cv2.putText(frame, str(display_text), (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Giữ nguyên thuật toán thu phóng tỷ lệ (Resize Aspect Ratio)
                target_w = right_frame.winfo_width() - 60
                target_h = right_frame.winfo_height() - 150 # Chừa thêm khoảng trống cho khung lịch sử bên dưới
                
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