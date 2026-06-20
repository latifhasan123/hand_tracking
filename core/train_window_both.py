import mediapipe as mp
import numpy as np
import os

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Hàm 1: Xử lý 43 số cho MỘT tay
def hand_vectorlize(landmarks, hand_type, prev_wx=None, prev_wy=None):
    wx, wy = landmarks[0].x, landmarks[0].y
    vector = []
    
    for i in range(1, 21):
        x = landmarks[i].x - wx
        y = landmarks[i].y - wy
        vector.extend([x, y])
    
    if prev_wx is None or prev_wy is None:
        delta_x = 0.0
        delta_y = 0.0
    else:
        delta_x = wx - prev_wx
        delta_y = wy - prev_wy
        
    if abs(delta_x) < 0.008: delta_x = 0.0
    if abs(delta_y) < 0.008: delta_y = 0.0
        
    delta_x *= 30
    delta_y *= 30    
        
    vector.extend([hand_type, delta_x, delta_y])
    return np.array(vector), wx, wy


# === HÀM MỚI: GHÉP 2 TAY THÀNH 86 SỐ ===
def extract_86_features(results, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r):
    """
    Hàm này lùng sục camera, lấy 43 số tay trái ghép với 43 số tay phải.
    Nếu bị khuất 1 tay -> Trả về None để hủy ngay khung hình đó!
    """
    left_vector = np.zeros(43)
    right_vector = np.zeros(43)
    
    new_wx_l, new_wy_l = prev_wx_l, prev_wy_l
    new_wx_r, new_wy_r = prev_wx_r, prev_wy_r
    
    hands_detected = 0
    
    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label # Nhận diện "Left" hoặc "Right"
            
            if label == "Left":
                left_vector, new_wx_l, new_wy_l = hand_vectorlize(hand_landmarks.landmark, 0, prev_wx_l, prev_wy_l)
                hands_detected += 1
            elif label == "Right":
                right_vector, new_wx_r, new_wy_r = hand_vectorlize(hand_landmarks.landmark, 1, prev_wx_r, prev_wy_r)
                hands_detected += 1

    # CƠ CHẾ KHÓA MỤC TIÊU: Thiếu 1 tay là đuổi về ngay!
    if hands_detected != 2:
        return None, prev_wx_l, prev_wy_l, prev_wx_r, prev_wy_r
        
    # Nối 43 số trái + 43 số phải = 86 số
    vector_86 = np.concatenate([left_vector, right_vector])
    
    return vector_86, new_wx_l, new_wy_l, new_wx_r, new_wy_r


# Hàm 3: Lưu file (Đã đổi sang thư mục mới dataset_both)
def save_sequence_to_npy(word, sequence_data):
    base_path = "dataset_both" 
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        
    word_path = os.path.join(base_path, word)
    if not os.path.exists(word_path):
        os.makedirs(word_path)
        
    files = os.listdir(word_path)
    sample_idx = len(files)
    
    file_path = os.path.join(word_path, f"{sample_idx}.npy")
    np.save(file_path, np.array(sequence_data))
    
    return sample_idx + 1