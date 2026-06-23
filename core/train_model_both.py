import os
import numpy as np
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import ModelCheckpoint, EarlyStopping
import tensorflow as tf
from keras.callbacks import Callback
import tf2onnx

def train_lstm_model(ui_callback=None):
    DATA_PATH = "dataset_both"
    
    # 1. ĐỌC DỮ LIỆU
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
    
    # Chia dữ liệu: 90% để học, 10% để làm bài kiểm tra (validation)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
    
    # 2. XÂY DỰNG BỘ NÃO (CÓ TÍCH HỢP CHỐNG HỌC VẸT)
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 86)))
    model.add(Dropout(0.2)) # Vũ khí 1: Tắt ngẫu nhiên 20% nơ-ron
    
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(Dropout(0.2)) # Vũ khí 1
    
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dropout(0.2)) # Vũ khí 1
    
    model.add(Dense(64, activation='relu'))
    # Đổi softmax thành sigmoid
    model.add(Dense(actions.shape[0], activation='sigmoid')) 
    
    # Đổi loss function cho phù hợp với sigmoid
    model.compile(optimizer='Adam', loss='binary_crossentropy', metrics=['categorical_accuracy'])
    
    if not os.path.exists('model'):
        os.makedirs('model')
        
    # 3. KÍCH HOẠT VŨ KHÍ BẢO VỆ (Đã đổi tên file save)
    checkpoint = ModelCheckpoint('model/model_both.h5', monitor='val_categorical_accuracy', save_best_only=True, mode='max', verbose=1)
    
    early_stopping = EarlyStopping(monitor='val_categorical_accuracy', patience=20, restore_best_weights=True, verbose=1)
    class UICallback(Callback):
        def on_epoch_end(self, epoch, logs=None):
            if ui_callback:
                acc = logs.get('categorical_accuracy', 0) * 100
                val_acc = logs.get('val_categorical_accuracy', 0) * 100
                ui_callback(epoch + 1, acc, val_acc)
    # 4. BẮT ĐẦU HUẤN LUYỆN
    print("Bắt đầu huấn luyện với hệ thống chống học vẹt...")
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=150, batch_size=16, callbacks=[checkpoint, early_stopping, UICallback()])
    
    # Đã đổi tên file labels
    np.save('model/labels_both.npy', actions) 
    
    # 5. ÉP ONNX SIÊU TỐC TỪ TRÊN RAM
    print("Đang ép thẳng phiên bản ĐỈNH CAO NHẤT sang ONNX...")
    # SỬA SỐ 43 THÀNH 86 Ở ĐÂY
    spec = (tf.TensorSpec((None, 30, 86), tf.float32, name="input"),)
    
    # Đã đổi tên file onnx xuất ra
    tf2onnx.convert.from_keras(model, input_signature=spec, output_path="model/model_both.onnx")
    
    print("🎉 Hoàn tất! File model_both.onnx đã sẵn sàng để dịch mượt mà.")
    
    return True