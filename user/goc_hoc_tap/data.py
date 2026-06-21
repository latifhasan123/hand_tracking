"""Static demo data for the VSL Góc học tập UI."""

TOP_MODULES = [
    {"title": "Bảng chữ cái", "desc": "Học bảng chữ cái\nngôn ngữ ký hiệu", "icon": "A", "color": "blue"},
    {"title": "Từ vựng", "desc": "Học từ mới theo\nchủ đề", "icon": "📖", "color": "green"},
    {"title": "Câu giao tiếp", "desc": "Giao tiếp hằng ngày\nbằng ký hiệu", "icon": "💬", "color": "purple"},
    {"title": "Ôn tập", "desc": "Luyện tập và củng cố\nkiến thức", "icon": "⟳", "color": "orange"},
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
    {"title": "Chào hỏi", "icon": "👋", "desc": "Các câu chào hỏi thông dụng", "done": 8, "total": 12, "color": "green"},
    {"title": "Tự giới thiệu", "icon": "🧑", "desc": "Giới thiệu bản thân, sở thích", "done": 6, "total": 12, "color": "purple"},
    {"title": "Hỏi đường", "icon": "🪧", "desc": "Hỏi đường và chỉ dẫn", "done": 7, "total": 12, "color": "blue"},
    {"title": "Mua sắm", "icon": "🛒", "desc": "Hỏi giá và thanh toán", "done": 5, "total": 12, "color": "orange"},
    {"title": "Trường học", "icon": "🏫", "desc": "Câu dùng trong lớp học", "done": 6, "total": 12, "color": "purple"},
    {"title": "Cảm xúc", "icon": "🙂", "desc": "Diễn tả cảm xúc hằng ngày", "done": 7, "total": 12, "color": "pink"},
]

REVIEW_CARDS = [
    {"title": "Các chữ hay nhầm", "icon": "A↔B", "desc": "Ôn lại các chữ dễ nhầm lẫn", "count": "10 câu", "color": "blue"},
    {"title": "Từ đã học gần đây", "icon": "📖", "desc": "Ôn tập những từ vừa học", "count": "15 từ", "color": "green"},
    {"title": "Bài kiểm tra nhanh", "icon": "✅", "desc": "Kiểm tra kiến thức tổng hợp", "count": "10 câu", "color": "purple"},
    {"title": "Luyện phản xạ", "icon": "⚡", "desc": "Tăng tốc độ nhận biết ký hiệu", "count": "8 ký hiệu", "color": "orange"},
]
