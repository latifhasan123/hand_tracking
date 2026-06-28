import tensorflow as tf
import tf2onnx
import onnx

def convert_model(h5_path, onnx_path, features):
    print(f"Đang ép kiểu {h5_path} sang {onnx_path} (Khuôn: {features} điểm)...")
    try:
        model = tf.keras.models.load_model(h5_path)
        # BÍ KÍP Ở ĐÂY: Nhận đúng số features (43 hoặc 86)
        spec = (tf.TensorSpec((None, 30, features), tf.float32, name="input_layer"),)
        tf2onnx.convert.from_keras(model, input_signature=spec, opset=13, output_path=onnx_path)
        print("✅ Thành công!\n")
    except Exception as e:
        print(f"❌ Lỗi: {e}\n")

# Chạy lệnh ép kiểu cho CẢ 2 BỘ NÃO
# 1. Não 1 tay (43 features)
convert_model("model/model.h5", "model/model.onnx", 43)

# 2. Não 2 tay (86 features)
convert_model("model/model_both.h5", "model/model_both.onnx", 86)