import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk

# Gọi Thuật toán từ các file đã tách
from train_window import hand_vectorlize, save_to_csv, hands, mp_draw, mp_hands
from train_model import train_model
from translate_window import load_model, predict_sign

def create_main_menu(root):
    root.title("Hand Sign Translator - Màn hình Quản trị")
    root.geometry("1100x700")

    # BIẾN QUẢN LÝ
    cap = None
    is_camera_on = False
    is_testing = False
    sample_count = 0
    current_vector = None
    model = None

    # KHU VỰC ĐIỀU KHIỂN (BÊN TRÁI)
    left_frame = tk.Frame(root, width=350, bg="#f0f0f0")
    left_frame.pack(side="left", fill="y", padx=10, pady=10)

    title = tk.Label(left_frame, text="Bảng Điều Khiển", font=("Arial", 20, "bold"), bg="#f0f0f0")
    title.pack(pady=10)

    def toggle_camera():
        nonlocal cap, is_camera_on
        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            is_camera_on = True
            cam_btn.config(text="Tắt Camera", bg="#f44336")
            update_frame()
        else:
            is_camera_on = False
            if cap:
                cap.release()
            video_label.config(image="")
            cam_btn.config(text="Bật Camera", bg="#4CAF50")

    cam_btn = tk.Button(left_frame, text="Bật Camera", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", command=toggle_camera)
    cam_btn.pack(fill="x", pady=5, padx=20)

    tk.Frame(left_frame, height=2, bg="#ccc").pack(fill="x", pady=10)

    # CHỨC NĂNG 1: THU THẬP
    tk.Label(left_frame, text="1. Thu thập dữ liệu", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(anchor="w", padx=20)
    word_entry = tk.Entry(left_frame, font=("Arial", 14))
    word_entry.pack(fill="x", padx=20, pady=5)
    
    status_label = tk.Label(left_frame, text="Đã lưu: 0 mẫu", font=("Arial", 12), bg="#f0f0f0")
    status_label.pack(anchor="w", padx=20)

    def save_sample():
        nonlocal sample_count, current_vector
        word = word_entry.get().strip()
        if not is_camera_on:
            messagebox.showwarning("Lỗi", "Hãy bật camera!")
            return
        if current_vector is not None and word != "":
            save_to_csv(word, current_vector)
            sample_count += 1
            status_label.config(text=f"Đã lưu: {sample_count} mẫu")

    tk.Button(left_frame, text="Lưu mẫu (Save)", font=("Arial", 12), command=save_sample).pack(fill="x", padx=20, pady=5)
    tk.Frame(left_frame, height=2, bg="#ccc").pack(fill="x", pady=10)

    # CHỨC NĂNG 2: HUẤN LUYỆN
    tk.Label(left_frame, text="2. Huấn luyện hệ thống", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(anchor="w", padx=20)
    
    def run_train_model():
        try:
            train_model()
            messagebox.showinfo("Thành công", "AI đã học xong!")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    tk.Button(left_frame, text="Train Model", font=("Arial", 12, "bold"), bg="#2196F3", fg="white", command=run_train_model).pack(fill="x", padx=20, pady=10)
    tk.Frame(left_frame, height=2, bg="#ccc").pack(fill="x", pady=10)

    # CHỨC NĂNG 3: KIỂM THỬ
    tk.Label(left_frame, text="3. Kiểm thử ngay", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(anchor="w", padx=20)
    result_label = tk.Label(left_frame, text="Kết quả: ...", font=("Arial", 16, "bold"), fg="red", bg="#f0f0f0")
    result_label.pack(pady=5)

    def toggle_test_mode():
        nonlocal is_testing, model
        if not is_camera_on:
            messagebox.showwarning("Lỗi", "Hãy bật camera!")
            return

        if not is_testing:
            model = load_model()
            if model is not None:
                is_testing = True
                test_btn.config(text="Đang Test... (Tắt)", bg="#ff9800")
            else:
                messagebox.showerror("Lỗi", "Chưa có model.pkl. Hãy Train trước!")
        else:
            is_testing = False
            model = None
            test_btn.config(text="Bật Test (Translate)", bg="#9c27b0")
            result_label.config(text="Kết quả: ...")

    test_btn = tk.Button(left_frame, text="Bật Test (Translate)", font=("Arial", 12), bg="#9c27b0", fg="white", command=toggle_test_mode)
    test_btn.pack(fill="x", padx=20)

    # KHU VỰC CAMERA (BÊN PHẢI)
    right_frame = tk.Frame(root, bg="black")
    right_frame.pack(side="right", fill="both", expand=True)
    video_label = tk.Label(right_frame, bg="black")
    video_label.pack(expand=True)

    def update_frame():
        nonlocal current_vector
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        landmarks = hand_landmarks.landmark
                        current_vector = hand_vectorlize(landmarks)

                        x_list = [int(lm.x * w) for lm in landmarks]
                        y_list = [int(lm.y * h) for lm in landmarks]
                        x_min, y_min = min(x_list) - 20, min(y_list) - 20
                        x_max, y_max = max(x_list) + 20, max(y_list) + 20
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                        display_text = ""
                        if is_testing and model is not None:
                            display_text = predict_sign(model, current_vector)
                            result_label.config(text=f"Dịch: {display_text}")
                        elif not is_testing:
                            display_text = word_entry.get()

                        cv2.putText(frame, str(display_text), (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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