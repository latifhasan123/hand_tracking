import numpy as np
from keras.models import load_model
import os

def load_lstm_model():
    if os.path.exists('model.h5') and os.path.exists('labels.npy'):
        # Gọi thẳng load_model từ keras
        model = load_model('model.h5')
        labels = np.load('labels.npy')
        return model, labels
    return None, None

def predict_sign(model, labels, sequence_data):
    # Định dạng lại ma trận (1 mẫu, 30 khung hình, 42 tọa độ)
    res = model.predict(np.expand_dims(sequence_data, axis=0), verbose=0)[0]
    
    max_idx = np.argmax(res)
    confidence = res[max_idx]
    
    # Nếu độ tự tin trên 80% thì mới xuất kết quả
    if confidence > 0.8:
        return labels[max_idx]
    else:
        return "..."