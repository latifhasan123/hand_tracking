# Hand Sign Translator

Realtime hand sign translator using MediaPipe and Machine Learning. This project uses MediaPipe Hand Tracking to detect 21 hand landmarks from webcam input, converts the hand pose into a feature vector using finger bend angles, finger spread angles, and palm orientation vectors, then uses a machine learning model to recognize and translate hand signs in realtime. The application includes a training window for collecting custom hand sign datasets, a model training system using Scikit-learn, and a realtime translation window with OpenCV and Tkinter GUI integration.

## Installation

Clone repository:

```bash
git clone https://github.com/VHieu1823/hand_tracking.git
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
Click "Train Data" to collect hand sign samples.
Enter a word label and save multiple samples for each hand sign.
Click "Train Model" to generate the machine learning model.
Click "Translate" to start realtime hand sign translation.

The project automatically creates:

dataset.csv → stores training vectors
model.pkl → trained machine learning model

Technologies
Python
OpenCV
MediaPipe
NumPy
Pandas
Scikit-learn
Tkinter
Pillow
Notes
Webcam required
Better lighting improves detection accuracy
More training samples improve prediction quality
Supports custom hand sign training
