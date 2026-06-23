"""Static demo data for the VSL Góc học tập UI."""

TOP_MODULES = [
    {
        "title": "Bảng chữ cái",
        "icon": "A",
        "desc": "Học bảng chữ cái\nngôn ngữ ký hiệu",
        "color": "blue"
    },
    # XÓA CỤC TỪ VỰNG ĐI, CHỈ GIỮ LẠI CỤC NÀY VÀ ĐỔI TÊN
    {
        "title": "Từ vựng & Giao tiếp",
        "icon": "💬",
        "desc": "Từ vựng và các câu\ngiao tiếp hằng ngày",
        "color": "purple"
    },
    {
        "title": "Ôn tập",
        "icon": "⟳",
        "desc": "Luyện tập và củng cố\nkiến thức",
        "color": "orange"
    }
]

TODAY_LESSONS = [
    {
        "no": "1",
        "letter": "Chữ A",
        "hand": "✊",
        "desc": "Bàn tay nắm lại,\nngón cái đặt bên cạnh\nngón trỏ.",
        "progress": 0.7,
    },
    {
        "no": "2",
        "letter": "Chữ B",
        "hand": "🖐",
        "desc": "Bàn tay duỗi thẳng,\ncác ngón khép lại,\nlòng bàn tay hướng ra.",
        "progress": 0.55,
    },
    {
        "no": "3",
        "letter": "Chữ C",
        "hand": "🤏",
        "desc": "Bàn tay cong lại tạo\nthành hình chữ C.",
        "progress": 0.3,
    },
]

POPULAR_TOPICS = [
    {"title": "Chào hỏi", "desc": "Các ký hiệu chào hỏi\nthông dụng trong giao tiếp\nhàng ngày.", "icon": "👥", "count": "12 bài học", "color": "green", "progress": 0.55},
    {"title": "Gia đình", "desc": "Học các từ vựng về\nthành viên trong gia đình\nvà người thân.", "icon": "👨‍👩‍👧", "count": "15 bài học", "color": "orange", "progress": 0.45},
    {"title": "Trường học", "desc": "Từ vựng và câu giao tiếp\nthường dùng trong môi\ntrường học đường.", "icon": "🏫", "count": "18 bài học", "color": "purple", "progress": 0.65},
]

ALPHABET = ["A", "Ă", "Â", "B", "C", "D", "Đ", "E", "Ê", "G", "H", "I", "K", "L", "M", "N", "O", "Ô", "Ơ", "P", "Q", "R", "S", "T", "U", "Ư", "V", "X", "Y"]

LETTER_HINTS = {
    "A": ("✊", "Bàn tay nắm lại, ngón cái đặt bên cạnh ngón trỏ."),
    "B": ("🖐", "Duỗi thẳng bàn tay, các ngón khép lại."),
    "C": ("🤏", "Cong bàn tay tạo thành hình chữ C."),
    "D": ("☝", "Dựng ngón trỏ thẳng đứng, các ngón còn lại khép lại."),
    "Đ": ("☝", "Dựng ngón trỏ, giữ tay ổn định trước camera."),
}

VOCAB_TOPICS = [
    {"title": "Chào hỏi", "icon": "👥", "desc": "Xin chào, tạm biệt, cảm ơn", "done": 12, "total": 18, "color": "green"},
    {"title": "Gia đình", "icon": "👨‍👩‍👧", "desc": "Bố, mẹ, anh, chị, em", "done": 15, "total": 22, "color": "orange"},
    {"title": "Trường học", "icon": "🏫", "desc": "Lớp học, giáo viên, bài tập", "done": 18, "total": 28, "color": "purple"},
    {"title": "Cảm xúc", "icon": "😊", "desc": "Vui, buồn, mệt, lo lắng", "done": 10, "total": 16, "color": "blue"},
    {"title": "Số đếm", "icon": "123", "desc": "Số cơ bản trong giao tiếp", "done": 14, "total": 20, "color": "cyan"},
    {"title": "Màu sắc", "icon": "🎨", "desc": "Đỏ, xanh, vàng, tím", "done": 9, "total": 14, "color": "pink"},
]

CONVERSATION_TOPICS = [
    {
        "title": "Chào hỏi",
        "icon": "🤝",
        "desc": "Xin chào, cảm ơn, tôi, tên...",
        "color": "green",
        "done": 0,
        "total": 6,
        "first_label": "XIN CHÀO"
    },
    {
        "title": "Gia đình",
        "icon": "👨‍👩‍👧",
        "desc": "Bố, mẹ",
        "color": "orange",
        "done": 0,
        "total": 2,
        "first_label": "BỐ"
    },
    {
        "title": "Trường học",
        "icon": "🏫",
        "desc": "Giáo viên, học sinh",
        "color": "purple",
        "done": 0,
        "total": 2,
        "first_label": "GIÁO VIÊN"
    },
    {
        "title": "Hỏi đường",
        "icon": "🪧",
        "desc": "Ở đâu, đi thẳng",
        "color": "blue",
        "done": 0,
        "total": 2,
        "first_label": "Ở ĐÂU"
    },
    {
        "title": "Cảm xúc",
        "icon": "🙂",
        "desc": "Vui, buồn",
        "color": "pink",
        "done": 0,
        "total": 2,
        "first_label": "VUI"
    },
    {
        "title": "Mua sắm",
        "icon": "🛒",
        "desc": "Tiền, bao nhiêu",
        "color": "yellow",
        "done": 0,
        "total": 2,
        "first_label": "TIỀN"
    }
]

REVIEW_CARDS = [
    {"title": "Các chữ hay nhầm", "icon": "A↔B", "desc": "Ôn lại các chữ dễ nhầm lẫn", "count": "10 câu", "color": "blue"},
    {"title": "Từ đã học gần đây", "icon": "📖", "desc": "Ôn tập những từ vừa học", "count": "15 từ", "color": "green"},
    {"title": "Bài kiểm tra nhanh", "icon": "✅", "desc": "Kiểm tra kiến thức tổng hợp", "count": "10 câu", "color": "purple"},
    {"title": "Luyện phản xạ", "icon": "⚡", "desc": "Tăng tốc độ nhận biết ký hiệu", "count": "8 ký hiệu", "color": "orange"},
]
# ==========================================
# CHI TIẾT BÀI HỌC (DATA MỒI CHO AI)
# ==========================================
LESSON_DETAILS = {
    # --- 1. NHÓM CHÀO HỎI ---
    "XIN CHÀO": {
        "label": "XIN CHÀO", 
        "title": "Xin chào", 
        "desc": "Vuốt cằm hoặc vẫy tay để chào.", 
        "icon": "👋", 
        "topic_type": "conversation",
        "order": 101
    },
    "CẢM ƠN": {
        "label": "CẢM ƠN", 
        "title": "Cảm ơn", 
        "desc": "Gật đầu nhẹ kết hợp tay chạm cằm đưa ra.", 
        "icon": "🙏", 
        "topic_type": "conversation",
        "order": 102
    },
    "XIN LỖI": {
        "label": "XIN LỖI", 
        "title": "Xin lỗi", 
        "desc": "Bàn tay xoa nhẹ lên ngực trái.", 
        "icon": "🙇", 
        "topic_type": "conversation",
        "order": 103
    },
    "TẠM BIỆT": {
        "label": "TẠM BIỆT", 
        "title": "Tạm biệt", 
        "desc": "Vẫy tay nhẹ nhàng để kết thúc hội thoại.", 
        "icon": "👋", 
        "topic_type": "conversation",
        "order": 104
    },
    "TÔI": {
        "label": "TÔI", 
        "title": "Tôi (Đại từ)", 
        "desc": "Dùng ngón trỏ chỉ thẳng vào ngực mình.", 
        "icon": "🙋", 
        "topic_type": "conversation",
        "order": 105
    },
    "TÊN": {
        "label": "TÊN", 
        "title": "Tên", 
        "desc": "Chạm hai ngón trỏ và giữa của hai tay vào nhau thành hình dấu nhân.", 
        "icon": "🏷️", 
        "topic_type": "conversation",
        "order": 106
    },

    # --- 2. NHÓM GIA ĐÌNH ---
    "BỐ": {
        "label": "BỐ", 
        "title": "Bố / Ba", 
        "desc": "Ký hiệu chỉ người cha trong gia đình.", 
        "icon": "👨", 
        "topic_type": "conversation",
        "order": 201
    },
    "MẸ": {
        "label": "MẸ", 
        "title": "Mẹ", 
        "desc": "Ký hiệu chỉ người mẹ trong gia đình.", 
        "icon": "👩", 
        "topic_type": "conversation",
        "order": 202
    },

    # --- 3. NHÓM TRƯỜNG HỌC ---
    "GIÁO VIÊN": {
        "label": "GIÁO VIÊN", 
        "title": "Giáo viên", 
        "desc": "Ký hiệu chỉ thầy hoặc cô giáo.", 
        "icon": "👨‍🏫", 
        "topic_type": "conversation",
        "order": 301
    },
    "HỌC SINH": {
        "label": "HỌC SINH", 
        "title": "Học sinh", 
        "desc": "Ký hiệu chỉ học sinh đang đi học.", 
        "icon": "🎒", 
        "topic_type": "conversation",
        "order": 302
    },

    # --- 4. NHÓM HỎI ĐƯỜNG ---
    "Ở ĐÂU": {
        "label": "Ở ĐÂU", 
        "title": "Ở đâu?", 
        "desc": "Câu hỏi dùng để tìm vị trí, địa điểm.", 
        "icon": "📍", 
        "topic_type": "conversation",
        "order": 401
    },
    "ĐI THẲNG": {
        "label": "ĐI THẲNG", 
        "title": "Đi thẳng", 
        "desc": "Chỉ hướng đi thẳng về phía trước.", 
        "icon": "⬆️", 
        "topic_type": "conversation",
        "order": 402
    },

    # --- 5. NHÓM CẢM XÚC ---
    "VUI": {
        "label": "VUI", 
        "title": "Vui vẻ", 
        "desc": "Thể hiện trạng thái cảm xúc vui mừng.", 
        "icon": "😄", 
        "topic_type": "conversation",
        "order": 501
    },
    "BUỒN": {
        "label": "BUỒN", 
        "title": "Buồn bã", 
        "desc": "Thể hiện trạng thái cảm xúc buồn chán.", 
        "icon": "😢", 
        "topic_type": "conversation",
        "order": 502
    },

    # --- 6. NHÓM MUA SẮM ---
    "TIỀN": {
        "label": "TIỀN", 
        "title": "Tiền", 
        "desc": "Ký hiệu liên quan đến tiền bạc, thanh toán.", 
        "icon": "💵", 
        "topic_type": "conversation",
        "order": 601
    },
    "BAO NHIÊU": {
        "label": "BAO NHIÊU", 
        "title": "Bao nhiêu?", 
        "desc": "Dùng để hỏi về số lượng hoặc giá cả.", 
        "icon": "⚖️", 
        "topic_type": "conversation",
        "order": 602
    }
}
