import mediapipe as mp
import numpy as np
import os

mp_hands = mp.solutions.hands
# CHÚ Ý: Màng lọc 1 tay khôi phục lại max_num_hands=1
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Hàm: Xử lý 43 số cho MỘT tay
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

# Hàm: Lưu file (Khôi phục lại thư mục cũ dataset)
def save_sequence_to_npy(word, sequence_data):
    base_path = "dataset" 
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