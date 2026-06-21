"""Demo data for VSL Translate Minigame UI."""

GAME_MODES = [
    {"key": "guess", "title": "Đoán chữ cái", "icon": "A?", "color": "blue", "desc": "Nhận diện ký hiệu\nchữ cái"},
    {"key": "word", "title": "Ghép từ", "icon": "✚", "color": "green", "desc": "Ghép các ký hiệu\nthành từ"},
    {"key": "react", "title": "Phản xạ nhanh", "icon": "⚡", "color": "yellow", "desc": "Trả lời nhanh,\nghi điểm cao"},
    {"key": "quiz", "title": "Quiz", "icon": "?", "color": "purple", "desc": "Kiểm tra kiến thức\nký hiệu"},
    {"key": "flashcard", "title": "Flashcard", "icon": "▣", "color": "pink", "desc": "Ôn tập bằng\nthẻ ký hiệu"},
    {"key": "wheel", "title": "Vòng quay\nthử thách", "icon": "◉", "color": "teal", "desc": "Quay là chơi,\ntrúng thử thách"},
]

FEATURED_GAMES = [
    {"key": "guess", "title": "Đoán chữ", "desc": "Nhận diện ký hiệu và chọn\nchữ cái đúng.", "icon": "☝", "accent": "blue"},
    {"key": "react", "title": "Phản xạ nhanh", "desc": "Trả lời nhanh nhất có thể\nđể ghi điểm cao.", "icon": "⏱", "accent": "purple"},
    {"key": "quiz", "title": "Quiz kiến thức", "desc": "Trả lời câu hỏi về ngôn ngữ\nký hiệu.", "icon": "✓", "accent": "green"},
]

ANSWER_HISTORY = [
    ("1", "A", True), ("2", "C", True), ("3", "B", True),
    ("4", "A", None), ("5", "D", None), ("6", "B", None),
    ("7", "C", None), ("8", "A", None), ("9", "D", None), ("10", "?", None),
]

REACTION_HISTORY = [
    ("1", "A", "92%", True), ("2", "B", "96%", True), ("3", "C", "88%", True),
    ("4", "X", "91%", True), ("5", "V", "79%", False), ("6", "I", "95%", True),
]

WORD_BANK = ["A", "Ă", "Â", "B", "C", "D", "Đ", "E", "Ê", "G", "H", "I", "K", "L", "M", "N"]

SPIN_SEGMENTS = [
    ("Chữ cái", "A", "#7C3AED"),
    ("Từ vựng", "▰", "#F59E0B"),
    ("Câu giao tiếp", "💬", "#22C55E"),
    ("Thực hành\ncamera", "▣", "#EC4899"),
    ("Quiz nhanh", "⚡", "#0EA5E9"),
    ("Điểm thưởng", "★", "#EAB308"),
]
