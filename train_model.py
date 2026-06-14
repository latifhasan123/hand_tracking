import os
import numpy as np
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import LSTM, Dense

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
    # Gọi thẳng to_categorical từ keras
    y = to_categorical(labels).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
    
    # XÂY DỰNG MẠNG NƠ-RON LSTM CỐT LÕI (Gọi thẳng từ keras)
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 42)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(actions.shape[0], activation='softmax')) 
    
    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    
    # Bắt đầu Train (Học 100 vòng)
    model.fit(X_train, y_train, epochs=100, batch_size=16) 
    
    model.save('model.h5')
    np.save('labels.npy', actions) 
    
    return True