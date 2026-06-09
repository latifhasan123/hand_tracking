import pickle
import os

def load_model():
    """Thuật toán tải AI từ bộ nhớ"""
    if os.path.exists("model.pkl"):
        with open("model.pkl", "rb") as f:
            return pickle.load(f)
    return None

def predict_sign(model, vector, threshold=0.45):
    """Thuật toán dự đoán chữ cái dựa trên khoảng cách KNN"""
    if model is None:
        return "..."
    
    distances, indices = model.kneighbors([vector])
    min_distance = distances[0][0]
    
    if min_distance < threshold:
        prediction = model.predict([vector])
        return prediction[0]
    else:
        return "UNKNOWN"