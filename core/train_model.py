import os
import numpy as np
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.callbacks import Callback
import tensorflow as tf
import tf2onnx

def train_lstm_model(ui_callback=None):
    DATA_PATH = "dataset"
    
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
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 43)))
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
    # 3. KÍCH HOẠT VŨ KHÍ BẢO VỆ
    # Vũ khí 2 (Camera an ninh): Chỉ lưu lại file model.h5 khi điểm kiểm tra (val_categorical_accuracy) phá kỷ lục
    checkpoint = ModelCheckpoint('model/model.h5', monitor='val_categorical_accuracy', save_best_only=True, mode='max', verbose=1)
    
    # Vũ khí 3 (Người canh lò): Nếu sau 20 vòng mà điểm không tăng, tự động ngắt và lấy lại bộ não xịn nhất
    early_stopping = EarlyStopping(monitor='val_categorical_accuracy', patience=20, restore_best_weights=True, verbose=1)
    class UICallback(Callback):
        def on_epoch_end(self, epoch, logs=None):
            if ui_callback:
                acc = logs.get('categorical_accuracy', 0) * 100
                val_acc = logs.get('val_categorical_accuracy', 0) * 100
                ui_callback(epoch + 1, acc, val_acc)
    # 4. BẮT ĐẦU HUẤN LUYỆN
    print("Bắt đầu huấn luyện với hệ thống chống học vẹt...")
    # Lưu ý: Cho AI học 150 vòng, lấy X_test ra làm bài kiểm tra chéo (validation_data)
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=150, batch_size=16, callbacks=[checkpoint, early_stopping, UICallback()])
    
    np.save('model/labels.npy', actions) 
    
    # 5. ÉP ONNX SIÊU TỐC TỪ TRÊN RAM
    print("Đang ép thẳng phiên bản ĐỈNH CAO NHẤT sang ONNX...")
    spec = (tf.TensorSpec((None, 30, 43), tf.float32, name="input"),)
    # Lệnh restore_best_weights ở trên đảm bảo biến 'model' lúc này đang chứa kiến thức xịn nhất, không phải kiến thức của vòng cuối cùng bị khét.
    tf2onnx.convert.from_keras(model, input_signature=spec, output_path="model/model.onnx")
    
    print("🎉 Hoàn tất! File model.onnx đã sẵn sàng để dịch mượt mà.")
    
    return True