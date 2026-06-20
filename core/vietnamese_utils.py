# ==========================================
# TỪ ĐIỂN QUY ĐỔI DẤU TIẾNG VIỆT (FULL IN HOA)
# ==========================================
VIETNAMESE_MAP = {
    # 1. Các dấu tạo chữ cái mới
    "DAU_MU": { 
        'A': 'Â', 'E': 'Ê', 'O': 'Ô'
    },
    "DAU_MOC": { 
        'A': 'Ă', 'O': 'Ơ', 'U': 'Ư'
    },
    
    # 2. Các dấu thanh điệu (Áp dụng cho mọi nguyên âm)
    "DAU_SAC": {
        'A': 'Á', 'Â': 'Ấ', 'Ă': 'Ắ', 'E': 'É', 'Ê': 'Ế', 'I': 'Í', 'O': 'Ó', 'Ô': 'Ố', 'Ơ': 'Ớ', 'U': 'Ú', 'Ư': 'Ứ', 'Y': 'Ý'
    },
    "DAU_HUYEN": {
        'A': 'À', 'Â': 'Ầ', 'Ă': 'Ằ', 'E': 'È', 'Ê': 'Ề', 'I': 'Ì', 'O': 'Ò', 'Ô': 'Ồ', 'Ơ': 'Ờ', 'U': 'Ù', 'Ư': 'Ừ', 'Y': 'Ỳ'
    },
    "DAU_HOI": {
        'A': 'Ả', 'Â': 'Ẩ', 'Ă': 'Ẳ', 'E': 'Ẻ', 'Ê': 'Ể', 'I': 'Ỉ', 'O': 'Ỏ', 'Ô': 'Ổ', 'Ơ': 'Ở', 'U': 'Ủ', 'Ư': 'Ử', 'Y': 'Ỷ'
    },
    "DAU_NGA": {
        'A': 'Ã', 'Â': 'Ẫ', 'Ă': 'Ẵ', 'E': 'Ẽ', 'Ê': 'Ễ', 'I': 'Ĩ', 'O': 'Õ', 'Ô': 'Ỗ', 'Ơ': 'Ỡ', 'U': 'Ũ', 'Ư': 'Ữ', 'Y': 'Ỹ'
    },
    "DAU_NANG": {
        'A': 'Ạ', 'Â': 'Ậ', 'Ă': 'Ặ', 'E': 'Ẹ', 'Ê': 'Ệ', 'I': 'Ị', 'O': 'Ọ', 'Ô': 'Ộ', 'Ơ': 'Ợ', 'U': 'Ụ', 'Ư': 'Ự', 'Y': 'Ỵ'
    }
}

# Danh sách tên các dấu để nhận diện nhanh
LIST_DAU = list(VIETNAMESE_MAP.keys())

def apply_vietnamese_sign(current_sentence, detected_sign):
    """
    Hàm này nhận vào câu hiện tại và dấu vừa quơ được.
    Nếu gắn dấu thành công, trả về câu mới. Nếu thất bại, giữ nguyên.
    """
    # Nếu câu đang trống trơn thì không có gì để gắn dấu
    if len(current_sentence) == 0:
        return current_sentence
        
    # Lấy ký tự cuối cùng ra xem xét
    last_char = current_sentence[-1]
    
    # Tra cứu xem ký tự đó có nằm trong từ điển của cái dấu này không
    if last_char in VIETNAMESE_MAP[detected_sign]:
        # Cắt bỏ ký tự cũ, gắn ký tự đã có dấu vào
        new_char = VIETNAMESE_MAP[detected_sign][last_char]
        return current_sentence[:-1] + new_char
        
    return current_sentence