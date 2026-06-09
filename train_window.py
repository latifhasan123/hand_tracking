import numpy as np
import pandas as pd
import mediapipe as mp
from utils import calculate_angle, calculate_finger_angle, compute_palm_orientation

# --- THUẬT TOÁN KHỞI TẠO MEDIAPIPE ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- THUẬT TOÁN TOÁN HỌC TRÍCH XUẤT ĐẶC TRƯNG ---
def hand_vectorlize(landmarks):
    landmarks_np = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
    palm = compute_palm_orientation(landmarks_np)
    
    direction = palm["direction"]
    spread = palm["spread"]
    normal = palm["normal"]

    angles = [
        calculate_angle(landmarks[0], landmarks[1], landmarks[2]),
        calculate_angle(landmarks[1], landmarks[2], landmarks[4]),
        calculate_angle(landmarks[0], landmarks[5], landmarks[6]),
        calculate_angle(landmarks[5], landmarks[6], landmarks[8]),
        calculate_angle(landmarks[0], landmarks[9], landmarks[10]),
        calculate_angle(landmarks[9], landmarks[10], landmarks[12]),
        calculate_angle(landmarks[0], landmarks[13], landmarks[14]),
        calculate_angle(landmarks[13], landmarks[14], landmarks[16]),
        calculate_angle(landmarks[0], landmarks[17], landmarks[18]),
        calculate_angle(landmarks[17], landmarks[18], landmarks[20]),
        calculate_finger_angle(landmarks[1], landmarks[4], landmarks[5], landmarks[8]),
        calculate_finger_angle(landmarks[5], landmarks[8], landmarks[9], landmarks[12]),
        calculate_finger_angle(landmarks[9], landmarks[12], landmarks[13], landmarks[16]),
        calculate_finger_angle(landmarks[13], landmarks[16], landmarks[17], landmarks[20])
    ]

    feature = np.concatenate([np.array(angles), direction, spread, normal])
    return np.round(feature, 4)

# --- THUẬT TOÁN LƯU DỮ LIỆU ---
def save_to_csv(label, vector):
    row = [label] + vector.tolist()
    df = pd.DataFrame([row])
    df.to_csv("dataset.csv", mode="a", header=False, index=False)