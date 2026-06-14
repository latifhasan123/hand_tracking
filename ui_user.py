import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Gọi các thuật toán xử lý hình ảnh và nhận diện
from train_window import hand_vectorlize, hands, mp_draw, mp_hands
from translate_window import load_model, predict_sign

def create_user_menu(root):
    root.title("Hand Sign Translator - Ứng dụng phiên dịch")
    window_width = 1100
    window_height = 700
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    model = load_model()
    if model is not None:
        try:
            dummy_vector = np.zeros(24)
            model.kneighbors([dummy_vector]) 
        except:
            pass

    cap = None
    is_camera_on = False
    history_list = []
    last_detected = ""
    current_sentence = "" 

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
        
        if model is None:
            messagebox.showerror("Lỗi", "Không tìm thấy bộ não AI (model.pkl). Vui lòng liên hệ Quản trị viên!")
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
            if cap: cap.release()
            video_label.configure(image="")
            camera_border.pack_forget() 
            history_frame.pack_forget()
            cam_btn.configure(text="Bật Camera", fg_color="#4CAF50", hover_color="#388E3C")
            
            result_label.configure(text="...")
            history_list.clear()
            last_detected = ""
            history_label.configure(text="Lịch sử: ")

    cam_btn = ctk.CTkButton(left_frame, text="Bật Camera", font=ctk.CTkFont(size=16, weight="bold"),
                            fg_color="#4CAF50", hover_color="#388E3C", height=45, command=toggle_camera)
    cam_btn.pack(fill="x", padx=30, pady=10)

    # ==========================================
    # TẠO KHUNG TỪ ĐIỂN NỔI (IN-APP MODAL)
    # ==========================================
    # Khung này tạo sẵn nhưng sẽ bị giấu đi (chưa dùng .place)
    dict_frame = ctk.CTkFrame(root, fg_color="#2B2B2B", border_width=2, border_color="#FF9800", corner_radius=15)
    
    try:
        img = Image.open("vsl_dict.gif") 
        img = img.resize((600, 450), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        lbl = ctk.CTkLabel(dict_frame, text="", image=photo)
        lbl.image = photo 
        lbl.pack(padx=20, pady=(20, 10))
    except Exception:
        err_text = "⚠️ Không tìm thấy ảnh từ điển!\nBạn hãy đảm bảo file ảnh tên là 'vsl_dict.jpg'\nvà nằm cùng thư mục code."
        ctk.CTkLabel(dict_frame, text=err_text, font=ctk.CTkFont(size=16), text_color="#FF9800").pack(padx=40, pady=40)

    def close_dictionary():
        dict_frame.place_forget() # Giấu khung từ điển đi

    close_btn = ctk.CTkButton(dict_frame, text="Đóng Từ Điển", font=ctk.CTkFont(weight="bold"),
                              fg_color="#F44336", hover_color="#D32F2F", command=close_dictionary)
    close_btn.pack(pady=(0, 20))

    # --- NÚT BẬT TỪ ĐIỂN ---
    def show_dictionary():
        # Gọi khung từ điển nổi lên ngay chính giữa ứng dụng
        dict_frame.place(relx=0.5, rely=0.5, anchor="center")
        dict_frame.lift() # Ép nó nổi lên trên cùng, đè lên cả camera

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

    def update_frame():
        nonlocal last_detected, history_list, current_sentence
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
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        landmarks = hand_landmarks.landmark
                        current_vector = hand_vectorlize(landmarks, hand_type)

                        x_list = [int(lm.x * w) for lm in landmarks]
                        y_list = [int(lm.y * h) for lm in landmarks]
                        x_min, y_min = min(x_list) - 20, min(y_list) - 20
                        x_max, y_max = max(x_list) + 20, max(y_list) + 20
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                        if model is not None:
                            raw_text = predict_sign(model, current_vector)
                            display_text = "..." if raw_text == "UNKNOWN" else raw_text
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
                        try:
                            font = ImageFont.truetype("arial.ttf", 32)
                        except IOError:
                            font = ImageFont.load_default()
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