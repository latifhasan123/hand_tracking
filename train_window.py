import numpy as np
from utils import calculate_angle, calculate_finger_angle, compute_palm_orientation
import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pandas as pd

def hand_vectorlize(landmarks):

    # ==========================================
    # LANDMARKS -> NUMPY
    # ==========================================
    landmarks_np = np.array([
        [lm.x, lm.y, lm.z]
        for lm in landmarks
    ])

    # ==========================================
    # PALM ORIENTATION
    # ==========================================
    palm = compute_palm_orientation(
        landmarks_np
    )

    direction = palm["direction"]
    spread = palm["spread"]
    normal = palm["normal"]

    # ==========================================
    # FINGER BEND
    # Các hàm đã normalize 0 -> 1
    # ==========================================
    angles = [

        # THUMB
        calculate_angle(
            landmarks[0],
            landmarks[1],
            landmarks[2]
        ),

        calculate_angle(
            landmarks[1],
            landmarks[2],
            landmarks[4]
        ),

        # INDEX
        calculate_angle(
            landmarks[0],
            landmarks[5],
            landmarks[6]
        ),

        calculate_angle(
            landmarks[5],
            landmarks[6],
            landmarks[8]
        ),

        # MIDDLE
        calculate_angle(
            landmarks[0],
            landmarks[9],
            landmarks[10]
        ),

        calculate_angle(
            landmarks[9],
            landmarks[10],
            landmarks[12]
        ),

        # RING
        calculate_angle(
            landmarks[0],
            landmarks[13],
            landmarks[14]
        ),

        calculate_angle(
            landmarks[13],
            landmarks[14],
            landmarks[16]
        ),

        # PINKY
        calculate_angle(
            landmarks[0],
            landmarks[17],
            landmarks[18]
        ),

        calculate_angle(
            landmarks[17],
            landmarks[18],
            landmarks[20]
        ),

        # ==========================================
        # FINGER SPREAD
        # ==========================================
        calculate_finger_angle(
            landmarks[1], landmarks[4],
            landmarks[5], landmarks[8]
        ),

        calculate_finger_angle(
            landmarks[5], landmarks[8],
            landmarks[9], landmarks[12]
        ),

        calculate_finger_angle(
            landmarks[9], landmarks[12],
            landmarks[13], landmarks[16]
        ),

        calculate_finger_angle(
            landmarks[13], landmarks[16],
            landmarks[17], landmarks[20]
        )
    ]

    # ==========================================
    # FULL FEATURE VECTOR
    # 14 + 3 + 3 + 3 = 23D
    # ==========================================
    feature = np.concatenate([

        np.array(angles),

        direction,
        spread,
        normal

    ])

    # ==========================================
    # ROUND
    # ==========================================
    feature = np.round(
        feature,
        4
    )

    return feature

# =========================
# MEDIAPIPE
# =========================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# =========================
# SAVE DATASET
# =========================
def save_to_csv(label, vector):

    row = [label] + vector.tolist()

    df = pd.DataFrame([row])

    df.to_csv(
        "dataset.csv",
        mode="a",
        header=False,
        index=False
    )


# =========================
# TRAIN WINDOW
# =========================
def train_new_word_window(parent):

    root = tk.Toplevel(parent)

    root.title("Train New Word")

    root.geometry("1000x700")

    # =========================
    # LEFT PANEL
    # =========================
    left_frame = tk.Frame(root, width=300)

    left_frame.pack(
        side="left",
        fill="y",
        padx=10,
        pady=10
    )

    title = tk.Label(
        left_frame,
        text="Train New Word",
        font=("Arial", 18, "bold")
    )

    title.pack(pady=10)

    word_entry = tk.Entry(
        left_frame,
        font=("Arial", 16)
    )

    word_entry.pack(pady=10)

    status_label = tk.Label(
        left_frame,
        text="Samples: 0",
        font=("Arial", 14)
    )

    status_label.pack(pady=10)

    # =========================
    # CAMERA PANEL
    # =========================
    right_frame = tk.Frame(root)

    right_frame.pack(
        side="right",
        fill="both",
        expand=True
    )

    video_label = tk.Label(right_frame)

    video_label.pack()

    cap = cv2.VideoCapture(0)

    sample_count = 0

    current_vector = None

    # =========================
    # SAVE SAMPLE
    # =========================
    def save_sample():

        nonlocal sample_count
        nonlocal current_vector

        word = word_entry.get()

        if current_vector is not None and word != "":

            save_to_csv(word, current_vector)

            sample_count += 1

            status_label.config(
                text=f"Samples: {sample_count}"
            )

            print("Saved")

    # =========================
    # SAVE BUTTON
    # =========================
    save_button = tk.Button(
        left_frame,
        text="Save Sample",
        font=("Arial", 16),
        command=save_sample
    )

    save_button.pack(pady=20)

    # =========================
    # UPDATE CAMERA
    # =========================
    def update_frame():

        nonlocal current_vector

        success, frame = cap.read()

        if success:

            frame = cv2.flip(frame, 1)

            h, w, c = frame.shape

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:

                for hand_landmarks in results.multi_hand_landmarks:

                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

                    landmarks = hand_landmarks.landmark

                    current_vector = hand_vectorlize(
                        landmarks
                    )

                    # =========================
                    # BOUNDING BOX
                    # =========================
                    x_list = []
                    y_list = []

                    for lm in landmarks:

                        px = int(lm.x * w)
                        py = int(lm.y * h)

                        x_list.append(px)
                        y_list.append(py)

                    x_min = min(x_list) - 20
                    y_min = min(y_list) - 20

                    x_max = max(x_list) + 20
                    y_max = max(y_list) + 20

                    cv2.rectangle(
                        frame,
                        (x_min, y_min),
                        (x_max, y_max),
                        (0,255,0),
                        2
                    )

                    word = word_entry.get()

                    cv2.putText(
                        frame,
                        word,
                        (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0,255,0),
                        2
                    )

            frame_rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            img = Image.fromarray(frame_rgb)

            imgtk = ImageTk.PhotoImage(image=img)

            video_label.configure(image=imgtk)

            video_label.image = imgtk

        root.after(10, update_frame)

    # =========================
    # CLOSE WINDOW
    # =========================
    def on_close():

        cap.release()

        root.destroy()

    root.protocol(
        "WM_DELETE_WINDOW",
        on_close
    )

    update_frame()