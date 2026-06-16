import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import threading

from translate_window import load_lstm_model, predict_sign
from train_window import hand_vectorlize, save_sequence_to_npy, hands, mp_draw, mp_hands

def create_main_menu(root):
    root.title("Hand Sign Translator - Admin Dashboard (LSTM Edition)")
    window_width = 1100
    window_height = 700
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{int((screen_width/2)-(window_width/2))}+{int((screen_height/2)-(window_height/2))}")

    # ==========================================
    # BIẾN TOÀN CỤC (DÙNG CHUNG)
    # ==========================================
    cap = None
    is_camera_on = False
    is_recording = False
    sequence_data = []
    SEQUENCE_LENGTH = 30 
    
    is_testing = False
    lstm_model = None
    action_labels = None
    test_sequence = [] 
    frame_counter = 0
    prev_wx = None  
    prev_wy = None  
    prediction_buffer = []
    
    sentence = ""      
    last_sign = None

    # ==========================================
    # KHUNG BÊN TRÁI (ĐIỀU KHIỂN)
    # ==========================================
    left_frame = ctk.CTkFrame(root, width=380, corner_radius=0)
    left_frame.pack_propagate(False)
    left_frame.pack(side="left", fill="y")

    title = ctk.CTkLabel(left_frame, text="BẢNG ĐIỀU KHIỂN", font=ctk.CTkFont(size=24, weight="bold"))
    title.pack(pady=(20, 15))

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
                            fg_color="#4CAF50", hover_color="#388E3C", height=40, command=toggle_camera)
    cam_btn.pack(fill="x", padx=30, pady=(0, 15))
    ctk.CTkFrame(left_frame, height=2, fg_color="gray50").pack(fill="x", padx=20, pady=5)

    # --- 1. THU THẬP ---
    ctk.CTkLabel(left_frame, text="1. Thu thập dữ liệu (Chuỗi Video)", font=ctk.CTkFont(size=15, weight="bold"), text_color="#FF9800").pack(anchor="w", padx=30, pady=(5, 5))
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
    ctk.CTkLabel(left_frame, text="2. Huấn luyện Deep Learning", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=30, pady=(5, 5))
    
    def run_train_model():
        train_btn.configure(state="disabled", text="Đang Train (Xem Terminal)...")
        def train_thread():
            try:
                from train_model import train_lstm_model 
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
    
    # --- 3. KIỂM THỬ VÀ VĂN BẢN ---
    ctk.CTkLabel(left_frame, text="3. Kiểm thử ngay", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=30, pady=(10, 0))
    
    result_label = ctk.CTkLabel(left_frame, text="Dịch: ...", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF9800")
    result_label.pack(pady=5)

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
                textbox_border.pack(fill="x", padx=20, pady=(15, 10))
            else:
                messagebox.showerror("Lỗi", "Chưa có model.h5. Hãy Train trước!")
        else:
            is_testing = False
            lstm_model = None
            action_labels = None
            test_sequence = []
            test_btn.configure(text="Bật Test (Translate)", fg_color="#9C27B0")
            camera_border.configure(border_color="#2196F3") 
            result_label.configure(text="Dịch: ...")
            textbox_border.pack_forget()

    test_btn = ctk.CTkButton(left_frame, text="Bật Test (Translate)", font=ctk.CTkFont(weight="bold"), fg_color="#9C27B0", command=toggle_test_mode)
    test_btn.pack(fill="x", padx=30, pady=5)

    # --- KHUNG TEXTBOX CỐ ĐỊNH (CÓ VIỀN MÀU XANH TÔNG XUYỆT TÔNG) ---
    # 1. Tạo một cái Khung làm viền (border_color là màu xanh, viền dày 3px)
    textbox_border = ctk.CTkFrame(left_frame, border_color="#2196F3", border_width=3, corner_radius=10, fg_color="transparent")
    

    # 2. Nhét cái Textbox vào BÊN TRONG cái Khung viền đó (Lưu ý: master bây giờ là textbox_border)
    textbox_sentence = ctk.CTkTextbox(textbox_border, height=100, font=("Helvetica", 18), fg_color="#2b2b2b", text_color="white", corner_radius=8, wrap="word")
    textbox_sentence.pack(fill="both", expand=True, padx=4, pady=4) # padx, pady = 4 để chừa khoảng trống cho cái viền nó ló ra
    textbox_sentence.configure(state="disabled")
    # ==========================================
    # CÁC HÀM XỬ LÝ CỬ CHỈ ĐẶC BIỆT
    # ==========================================
    def action_space():
        nonlocal sentence, last_sign
        sentence += " "  
        last_sign = "SPACE" 
        textbox_sentence.configure(state="normal")    # MỞ KHÓA
        textbox_sentence.delete("1.0", "end")
        textbox_sentence.insert("1.0", sentence)
        textbox_sentence.configure(state="disabled")  # KHÓA LẠI

    def action_del():
        nonlocal sentence, last_sign
        if len(sentence) > 0:
            sentence = sentence[:-1]
        last_sign = "DEL"
        textbox_sentence.configure(state="normal")    # MỞ KHÓA
        textbox_sentence.delete("1.0", "end")
        textbox_sentence.insert("1.0", sentence)
        textbox_sentence.configure(state="disabled")  # KHÓA LẠI

    def action_clear_all():
        nonlocal sentence, last_sign
        sentence = ""    
        last_sign = "CLEAR"
        textbox_sentence.configure(state="normal")    # MỞ KHÓA
        textbox_sentence.delete("1.0", "end")
        textbox_sentence.configure(state="disabled")  # KHÓA LẠI

    # ==========================================
    # KHU VỰC CAMERA BÊN PHẢI
    # ==========================================
    right_frame = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    camera_border = ctk.CTkFrame(right_frame, fg_color="black", border_color="#2196F3", border_width=4, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=12, pady=12) 

    def update_frame():
        nonlocal is_recording, sequence_data, test_sequence, frame_counter, prev_wx, prev_wy, prediction_buffer, sentence, last_sign
        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame_counter += 1
                
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                rgb_frame.flags.writeable = False 
                results = hands.process(rgb_frame) 
                rgb_frame.flags.writeable = True  

                current_vector = np.zeros(43) 

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        landmarks = hand_landmarks.landmark
                        current_vector, prev_wx, prev_wy = hand_vectorlize(landmarks, hand_type, prev_wx, prev_wy)
                        
                        if is_testing and lstm_model is not None:
                            test_sequence.append(current_vector)
                            test_sequence = test_sequence[-30:]
                            
                            if len(test_sequence) == 30 and frame_counter % 10 == 0:
                                predicted_word = predict_sign(lstm_model, action_labels, test_sequence)
                                
                                prediction_buffer.append(predicted_word)
                                prediction_buffer = prediction_buffer[-3:]
                                
                                # LỌC ĐỒNG THUẬN VÀ SOẠN THẢO VĂN BẢN
                                valid_predictions = [p for p in prediction_buffer if p != "KHONG_XAC_DINH"]
                                
                                if len(valid_predictions) >= 2 and valid_predictions[0] == valid_predictions[-1]:
                                    final_word = valid_predictions[-1]
                                    
                                    # CHỈ XỬ LÝ KHI NHẬN DIỆN LÀ KÝ HIỆU MỚI
                                    if final_word != last_sign:
                                        if final_word == "SPACE":
                                            action_space()
                                        elif final_word == "DEL":
                                            action_del()
                                        elif final_word == "CLEAR":
                                            action_clear_all()
                                        else:
                                            # ĐÃ BỎ TỰ ĐỘNG CÁCH CHỮ (Cộng trực tiếp ký tự mới vào)
                                            sentence += final_word
                                            textbox_sentence.configure(state="normal")    # MỞ KHÓA
                                            textbox_sentence.delete("1.0", "end")
                                            textbox_sentence.insert("1.0", sentence)
                                            textbox_sentence.configure(state="disabled")  # KHÓA LẠI
                                            
                                        last_sign = final_word       
                                        result_label.configure(text=f"Dịch: {final_word}")
                                        
                else:
                    # RÚT TAY LÀ MỞ KHÓA PHÍM NGAY LẬP TỨC
                    prev_wx, prev_wy = None, None
                    prediction_buffer.clear() 
                    test_sequence.clear() 
                    last_sign = None

                if is_recording:
                    sequence_data.append(current_vector)
                    cv2.putText(frame, f"DANG QUAY... {len(sequence_data)}/{SEQUENCE_LENGTH}", 
                                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    
                    if len(sequence_data) == SEQUENCE_LENGTH:
                        word = word_entry.get().strip()
                        count = save_sequence_to_npy(word, sequence_data)
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