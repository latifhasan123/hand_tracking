import onnxruntime as ort
import numpy as np

def load_lstm_model():
    try:
        # Load danh sách từ khóa (Đảm bảo tên file action_labels khớp với code cũ của bạn)
        action_labels = np.load("model/labels.npy") 
        
        # Gọi động cơ ONNX chạy bằng CPU siêu mượt
        session = ort.InferenceSession("model/model.onnx", providers=['CPUExecutionProvider'])
        
        return session, action_labels
    except Exception as e:
        print("Lỗi load model:", e)
        return None, None
def load_lstm_model_both():
    try:
        import onnxruntime as ort
        import numpy as np
        # Trỏ vào file não 2 tay
        lstm_model = ort.InferenceSession("model/model_both.onnx")
        action_labels = np.load("model/labels_both.npy")
        return lstm_model, action_labels
    except Exception as e:
        print("Chưa tìm thấy model 2 tay:", e)
        return None, None
def predict_sign(session, action_labels, test_sequence):
    input_data = np.expand_dims(test_sequence, axis=0).astype(np.float32)
    
    input_name = session.get_inputs()[0].name
    result = session.run(None, {input_name: input_data})[0][0] # Lấy mảng tỷ lệ %
    
    # Tìm điểm số cao nhất và vị trí của nó
    max_prob = np.max(result)
    max_index = np.argmax(result)
    
    # Ép trả về 2 biến: TÊN CHỮ và ĐIỂM SỐ
    if max_prob < 0.5:
        return "KHONG_XAC_DINH", max_prob
        
    predicted_word = action_labels[max_index]
    return predicted_word, max_prob 