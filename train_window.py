import mediapipe as mp
import math
import numpy as np
import os

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

def hand_vectorlize(landmarks, hand_type):
    # Lấy tọa độ cổ tay (điểm 0) làm gốc
    wx, wy = landmarks[0].x, landmarks[0].y
    vector = []
    for i in range(1, 21):
        x = landmarks[i].x - wx
        y = landmarks[i].y - wy
        vector.extend([x, y])
    
    # 20 điểm x 2 (tọa độ x,y) = 40 giá trị. 
    # Nếu hệ thống cũ của bạn dùng 24, bạn có thể giữ nguyên thuật toán cũ của bạn ở đây.
    # Dưới đây tôi giả định vector của bạn có chiều dài cố định (ví dụ 42 giá trị gồm cả hand_type)
    vector.extend([hand_type, 0]) # Bổ sung để đủ định dạng
    return np.array(vector)

# --- THUẬT TOÁN LƯU DỮ LIỆU VIDEO (3D) ---
def save_sequence_to_npy(word, sequence_data):
    base_path = "dataset"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        
    word_path = os.path.join(base_path, word)
    if not os.path.exists(word_path):
        os.makedirs(word_path)
        
    # Đếm số lượng file hiện có để đặt tên file mới (0.npy, 1.npy...)
    files = os.listdir(word_path)
    sample_idx = len(files)
    
    file_path = os.path.join(word_path, f"{sample_idx}.npy")
    # sequence_data là mảng 2 chiều: [30 frames x chiều_dài_vector]
    np.save(file_path, np.array(sequence_data))
    
    return sample_idx + 1 # Trả về tổng số lượng mẫu hiện tại