import os
import numpy as np
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import LSTM, Dense
# Thêm 2 thư viện này để phục vụ ép file
import tensorflow as tf
import tf2onnx

def train_lstm_model():
    DATA_PATH = "dataset"
    
    actions = np.array([name for name in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, name))])
    if len(actions) == 0:
        raise Exception("Không tìm thấy dữ liệu! Hãy thu thập ít nhất 1 từ khóa.")
        
    label_map = {label:num for num, label in enumerate(actions)}
    
    sequences, labels = [], []
    
    for action in actions:
        action_path = os.path.join(DATA_PATH, action)
        for file_name in os.listdir(action_path):
            if file_name.endswith('.npy'):
                res = np.load(os.path.join(action_path, file_name))
                sequences.append(res)
                labels.append(label_map[action])
                
    X = np.array(sequences)
    y = to_categorical(labels).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
    
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 43)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(actions.shape[0], activation='softmax')) 
    
    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    
    model.fit(X_train, y_train, epochs=100, batch_size=16) 
    
    model.save('model.h5')
    np.save('labels.npy', actions) 
    
    # ==========================================
    # ĐOẠN THÊM VÀO: TỰ ĐỘNG ÉP SANG ONNX
    # ==========================================
    print("Đang tự động ép sang định dạng siêu nhẹ ONNX...")
    export_model = tf.keras.models.load_model('model.h5', compile=False)
    spec = (tf.TensorSpec((None, 30, 43), tf.float32, name="input"),)
    tf2onnx.convert.from_keras(export_model, input_signature=spec, output_path="model.onnx")
    print("Hoàn tất! File model.onnx đã sẵn sàng để dịch.")
    
    return True