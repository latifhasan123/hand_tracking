# Hand Sign Translator

Realtime hand sign translator using MediaPipe and Deep Learning. This project uses MediaPipe Hand Tracking to detect 21 hand landmarks from webcam input, extracts feature vectors across a sequence of 30 frames, and uses an LSTM neural network model to recognize and translate dynamic hand signs in realtime. The application includes an Admin Dashboard for collecting custom hand sign video sequences, a model training system using TensorFlow/Keras, and a realtime translation window with virtual keyboard typing features using OpenCV and CustomTkinter GUI integration.

## Installation

Clone repository:

```bash
git clone https://github.com/latifhasan123/hand_tracking.git
```

Open project folder
```bash
cd hand_tracking
```

Create virtual enviroment
```bash
python -m venv venv
venv\Scripts\activate
```
Install dependencies
```bash
pip install -r requirements.txt
```

Run project
```bash
python main.py
```

Workflow
Enter a word label and click "Lưu mẫu" (Save Sample) to collect 30-frame video sequences for each hand sign.
Click "Train Model" to train and generate the deep learning model.
Click "Bật Test (Translate)" to start realtime hand sign translation and typing.

The project automatically creates:

dataset/ directory → stores .npy training sequence vectors
model.h5 → trained LSTM deep learning model

Technologies
Python
OpenCV
MediaPipe
NumPy
TensorFlow / Keras
CustomTkinter
Pillow

Notes
Webcam required
Better lighting improves detection accuracy
More training samples improve prediction quality
Supports custom dynamic hand sign training (including SPACE, DEL, CLEAR commands)
Remember to collect a "KHONG_XAC_DINH" (Idle/Noise) class to prevent false predictions
Webcam required
Better lighting improves detection accuracy
More training samples improve prediction quality
Supports custom hand sign training
