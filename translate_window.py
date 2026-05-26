import cv2
import pickle
import mediapipe as mp

from train_window import hand_vectorlize

import pickle
import os

model = None

def load_model():

    global model

    if os.path.exists("model.pkl"):

        with open("model.pkl", "rb") as f:

            model = pickle.load(f)

    else:

        print("No model found")


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
# TRANSLATE
# =========================
def start_translate():
    load_model()

    if model is None:
        print("Please train model first")
        return
    cap = cv2.VideoCapture(0)

    translated_text = "..."

    while True:

        success, frame = cap.read()

        if not success:
            break

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

                vector = hand_vectorlize(
                    landmarks
                )

                # =========================
                # PREDICT
                # =========================
                prediction = model.predict(
                    [vector]
                )

                translated_text = prediction[0]

                # =========================
                # BOX
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

                cv2.putText(
                    frame,
                    translated_text,
                    (x_min, y_min - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2
                )

        cv2.imshow(
            "Translator",
            frame
        )

        # =========================
        # KEY EVENT
        # =========================
        key = cv2.waitKey(1)

        # Q TO EXIT
        if key & 0xFF == ord('q'):
            break

        # =========================
        # WINDOW CLOSED
        # =========================
        try:

            visible = cv2.getWindowProperty(
                "Translator",
                cv2.WND_PROP_VISIBLE
            )

            if visible < 1:
                break

        except:
            break

    cap.release()

    cv2.destroyAllWindows()