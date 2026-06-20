import customtkinter as ctk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import threading

from core.translate_window import load_lstm_model, predict_sign

# ==========================================
# ĐỔI CÁP: IMPORT CẢ 2 BỘ ĐỒ NGHỀ CÙNG LÚC
# ==========================================
# Đồ nghề 1 Tay (Đặt bí danh thêm _1)
from core.train_window import hand_vectorlize as hand_vectorlize_1, save_sequence_to_npy as save_sequence_1, hands as hands_1, mp_draw, mp_hands
# Đồ nghề 2 Tay (Đặt bí danh thêm _2)
from core.train_window_both import extract_86_features, save_sequence_to_npy as save_sequence_2, hands as hands_2

def create_main_menu(root):
    root.title("Hand Sign Translator - Admin Dashboard (Pro Edition)")
    window_width = 1100
    window_height = 750 # Tăng nhẹ chiều cao để chứa công tắc
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{int((screen_width/2)-(window_width/2))}+{int((screen_height/2)-(window_height/2))}")

    # ==========================================
    # BIẾN TOÀN CỤC
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
    
    # 4 BIẾN LƯU TỌA ĐỘ CHO CẢ 2 TAY
    prev_wx_l, prev_wy_l = None, None  
    prev_wx_r, prev_wy_r = None, None  
    
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

    # --- CÔNG TẮC CHUYỂN CHẾ ĐỘ ĐỈNH CAO ---
    mode_var = ctk.StringVar(value="1 Tay (43 số)")
    mode_selector = ctk.CTkSegmentedButton(left_frame, values=["1 Tay (43 số)", "2 Tay (86 số)"], variable=mode_var, font=ctk.CTkFont(weight="bold"))
    mode_selector.pack(fill="x", padx=30, pady=(0, 15))

    def toggle_camera():
        nonlocal cap, is_camera_on
        if not is_camera_on:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
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
    ctk.CTkLabel(left_frame, text="1. Thu thập dữ liệu", font=ctk.CTkFont(size=15, weight="bold"), text_color="#FF9800").pack(anchor="w", padx=30, pady=(5, 5))
    word_entry = ctk.CTkEntry(left_frame, font=ctk.CTkFont(size=14), placeholder_text="Nhập từ khóa...", height=35)
    word_entry.pack(fill="x", padx=30, pady=5)
    status_label = ctk.CTkLabel(left_frame, text="Đã lưu: 0 mẫu", text_color="gray60")
    status_label.pack(anchor="w", padx=30)

    def check_word(*args):
        word = word_entry.get().strip()
        # Thay đổi thư mục hiển thị lượng mẫu dựa trên công tắc
        target_dir = "dataset" if mode_var.get() == "1 Tay (43 số)" else "dataset_both"
        path = os.path.join(target_dir, word)
        
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
        mode = mode_var.get()
        train_btn.configure(state="disabled", text="Đang Train (Xem Terminal)...")
        def train_thread():
            try:
                if mode == "1 Tay (43 số)":
                    from core.train_model import train_lstm_model 
                    train_lstm_model()
                    messagebox.showinfo("Thành công", "Đã huấn luyện xong mô hình 1 tay (model.onnx)!")
                else:
                    from core.train_model_both import train_lstm_model 
                    train_lstm_model()
                    messagebox.showinfo("Thành công", "Đã huấn luyện xong mô hình 2 tay (model_both.onnx)!")
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
        
        # Khóa Test 2 Tay ở Admin để tránh xung đột
        if mode_var.get() == "2 Tay (86 số)":
            messagebox.showwarning("Khóa chức năng", "Chế độ Test ở bảng Admin hiện chỉ chạy cho 1 Tay. Vui lòng chuyển sang giao diện User để test dịch 2 tay chuyên nghiệp!")
            return

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

    textbox_border = ctk.CTkFrame(left_frame, border_color="#2196F3", border_width=3, corner_radius=10, fg_color="transparent")
    textbox_sentence = ctk.CTkTextbox(textbox_border, height=100, font=("Helvetica", 18), fg_color="#2b2b2b", text_color="white", corner_radius=8, wrap="word")
    textbox_sentence.pack(fill="both", expand=True, padx=4, pady=4) 
    textbox_sentence.configure(state="disabled")

    # ==========================================
    # CÁC HÀM XỬ LÝ CỬ CHỈ ĐẶC BIỆT
    # ==========================================
    def action_space():
        nonlocal sentence, last_sign
        sentence += " "  
        last_sign = "SPACE" 
        textbox_sentence.configure(state="normal")
        textbox_sentence.delete("1.0", "end")
        textbox_sentence.insert("1.0", sentence)
        textbox_sentence.configure(state="disabled")

    def action_del():
        nonlocal sentence, last_sign
        if len(sentence) > 0:
            sentence = sentence[:-1]
        last_sign = "DEL"
        textbox_sentence.configure(state="normal")
        textbox_sentence.delete("1.0", "end")
        textbox_sentence.insert("1.0", sentence)
        textbox_sentence.configure(state="disabled")

    def action_clear_all():
        nonlocal sentence, last_sign
        sentence = ""    
        last_sign = "CLEAR"
        textbox_sentence.configure(state="normal")
        textbox_sentence.delete("1.0", "end")
        textbox_sentence.configure(state="disabled")

    # ==========================================
    # KHU VỰC CAMERA BÊN PHẢI (TRÁI TIM CỦA CÔNG TẮC)
    # ==========================================
    right_frame = ctk.CTkFrame(root, fg_color="black", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    camera_border = ctk.CTkFrame(right_frame, fg_color="black", border_color="#2196F3", border_width=4, corner_radius=15)
    video_label = ctk.CTkLabel(camera_border, text="")
    video_label.pack(padx=12, pady=12) 

    def update_frame():
        nonlocal is_recording, sequence_data, test_sequence, frame_counter
        nonlocal prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r, prediction_buffer, sentence, last_sign
        
        mode = mode_var.get()
        # Chuyển đổi bộ não đếm tay dựa theo công tắc
        current_hands = hands_1 if mode == "1 Tay (43 số)" else hands_2

        if is_camera_on and cap is not None:
            success, frame = cap.read()
            if success:
                frame_counter += 1
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame.flags.writeable = False 
                
                results = current_hands.process(rgb_frame) 
                rgb_frame.flags.writeable = True  

                current_vector = None 

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                    # ==========================================
                    # NGÃ BA ĐƯỜNG: XỬ LÝ THEO CHẾ ĐỘ
                    # ==========================================
                    if mode == "1 Tay (43 số)":
                        # Chỉ lấy tay đầu tiên camera thấy
                        handedness = results.multi_handedness[0]
                        hand_landmarks = results.multi_hand_landmarks[0]
                        hand_type = 0 if handedness.classification[0].label == "Left" else 1
                        current_vector, prev_wx_l, prev_wy_l = hand_vectorlize_1(hand_landmarks.landmark, hand_type, prev_wx_l, prev_wy_l)
                        
                        # Chỉ test khi đang ở mode 1 tay
                        if is_testing and lstm_model is not None:
                            test_sequence.append(current_vector)
                            test_sequence = test_sequence[-30:]
                            if len(test_sequence) == 30 and frame_counter % 10 == 0:
                                predicted_word = predict_sign(lstm_model, action_labels, test_sequence)
                                prediction_buffer.append(predicted_word)
                                prediction_buffer = prediction_buffer[-3:]
                                valid_predictions = [p for p in prediction_buffer if p != "KHONG_XAC_DINH"]
                                
                                if len(valid_predictions) >= 2 and valid_predictions[0] == valid_predictions[-1]:
                                    final_word = valid_predictions[-1]
                                    if final_word != last_sign:
                                        if final_word == "SPACE": action_space()
                                        elif final_word == "DEL": action_del()
                                        elif final_word == "CLEAR": action_clear_all()
                                        else:
                                            sentence += final_word
                                            textbox_sentence.configure(state="normal")
                                            textbox_sentence.delete("1.0", "end")
                                            textbox_sentence.insert("1.0", sentence)
                                            textbox_sentence.configure(state="disabled")
                                        last_sign = final_word       
                                        result_label.configure(text=f"Dịch: {final_word}")
                    else:
                        # CHẾ ĐỘ 2 TAY (86 Số)
                        current_vector, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r = extract_86_features(
                            results, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
                        )
                else:
                    prev_wx_l, prev_wy_l = None, None
                    prev_wx_r, prev_wy_r = None, None
                    prediction_buffer.clear() 
                    test_sequence.clear() 
                    last_sign = None

                # ==========================================
                # LƯU FILE THEO CHẾ ĐỘ
                # ==========================================
                if is_recording and current_vector is not None:
                    sequence_data.append(current_vector)
                    cv2.putText(frame, f"DANG QUAY... {len(sequence_data)}/{SEQUENCE_LENGTH}", 
                                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    
                    if len(sequence_data) == SEQUENCE_LENGTH:
                        word = word_entry.get().strip()
                        # Chọn hàm lưu file tương ứng
                        save_fn = save_sequence_1 if mode == "1 Tay (43 số)" else save_sequence_2
                        count = save_fn(word, sequence_data)
                        
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

            root.after(1, update_frame)

    def on_close():
        if cap: cap.release()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)