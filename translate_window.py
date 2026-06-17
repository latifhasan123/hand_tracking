import onnxruntime as ort
import numpy as np

def load_lstm_model():
    try:
        # Load danh sách từ khóa (Đảm bảo tên file action_labels khớp với code cũ của bạn)
        action_labels = np.load("labels.npy") 
        
        # Gọi động cơ ONNX chạy bằng CPU siêu mượt
        session = ort.InferenceSession("model.onnx", providers=['CPUExecutionProvider'])
        
        return session, action_labels
    except Exception as e:
        print("Lỗi load model:", e)
        return None, None

def predict_sign(session, action_labels, test_sequence):
    # Định dạng lại chuỗi 30 khung hình cho đúng chuẩn đầu vào của ONNX
    input_data = np.expand_dims(test_sequence, axis=0).astype(np.float32)
    
    # Dự đoán thời gian thực
    input_name = session.get_inputs()[0].name
    result = session.run(None, {input_name: input_data})[0]
    
    # Lấy ra từ khóa có tỷ lệ chính xác cao nhất
    predicted_word = action_labels[np.argmax(result)]
    return predicted_word