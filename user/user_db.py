import pyodbc

# Nhớ sửa lại SERVER cho đúng với máy của bạn nhé!
DB_CONFIG = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=.\SQLEXPRESS;" 
    r"DATABASE=QuanLyUser;"
    r"Trusted_Connection=yes;"
)

def get_conn():
    return pyodbc.connect(DB_CONFIG)

def login_user(username, password):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, TenDangNhap FROM TaiKhoan WHERE TenDangNhap = ? AND MatKhau = ?", (username, password))
        row = cursor.fetchone()
        if row:
            return True, {"id": row[0], "username": row[1]}
        return False, "Sai tài khoản hoặc mật khẩu!"
    except Exception as e:
        return False, f"Lỗi DB: {e}"

def register_user(username, password, fullname, phone):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM TaiKhoan WHERE TenDangNhap = ?", (username,))
        if cursor.fetchone():
            return False, "Tên đăng nhập đã tồn tại!"
        
        # Thêm HoTen và SoDienThoai vào câu lệnh INSERT (DiemSo mặc định là 0)
        cursor.execute(
            "INSERT INTO TaiKhoan (TenDangNhap, MatKhau, DiemSo, HoTen, SoDienThoai) VALUES (?, ?, 0, ?, ?)", 
            (username, password, fullname if fullname else None, phone if phone else None)
        )
        conn.commit()
        return True, "Đăng ký thành công!"
    except Exception as e:
        return False, f"Lỗi DB: {e}"

def get_learned_letters(user_id):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT BaiHoc FROM TienDoHocTap WHERE ID_TaiKhoan = ?", (user_id,))
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []

def mark_as_learned(user_id, lesson):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM TienDoHocTap WHERE ID_TaiKhoan = ? AND BaiHoc = ?", (user_id, lesson))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO TienDoHocTap (ID_TaiKhoan, BaiHoc) VALUES (?, ?)", (user_id, lesson))
            conn.commit()
        return True
    except Exception as e:
        print("Lỗi lưu tiến độ:", e)
        return False
def update_study_stats(user_id, accuracy, time_minutes=0, session_time_minutes=None, topic_type="alphabet"):
    """
    Hàm Backend nâng cấp: Hỗ trợ rẽ nhánh thời gian thực hành.
    Nếu topic_type == 'conversation' -> Cộng vào ThoiGianGiaoTiep.
    Nếu topic_type == 'alphabet'     -> Cộng vào ThoiGianHoc.
    """
    try:
        # Khớp lệnh linh hoạt cho cả code cũ lẫn code mới
        actual_mins = session_time_minutes if session_time_minutes is not None else time_minutes

        conn = get_conn()
        cursor = conn.cursor()

        # 1. Bốc cả ThoiGianHoc lẫn ThoiGianGiaoTiep lên
        cursor.execute("""
            SELECT ChuoiNgayHoc, ThoiGianHoc, ISNULL(ThoiGianGiaoTiep, 0) as ThoiGianGiaoTiep, 
                   DoChinhXacTB, NgayHocCuoi, TongSoLanTap 
            FROM TaiKhoan WHERE ID = ?
        """, (user_id,))
        row = cursor.fetchone()
        if not row: return None

        chuoi_ngay = row.ChuoiNgayHoc or 0
        thoi_gian_alpha = row.ThoiGianHoc or 0
        thoi_gian_gt = row.ThoiGianGiaoTiep or 0
        do_chinh_xac = row.DoChinhXacTB or 0
        tong_lan = row.TongSoLanTap or 0
        ngay_cuoi = row.NgayHocCuoi

        from datetime import date, timedelta
        today = date.today()

        # 2. Tính chuỗi ngày học Streak
        if ngay_cuoi:
            if type(ngay_cuoi) == str:
                from datetime import datetime
                ngay_cuoi = datetime.strptime(ngay_cuoi, "%Y-%m-%d").date()
            if ngay_cuoi == today - timedelta(days=1): chuoi_ngay += 1
            elif ngay_cuoi < today - timedelta(days=1): chuoi_ngay = 1
        else: chuoi_ngay = 1

        new_tong_lan = tong_lan + 1
        new_do_chinh_xac = int(((do_chinh_xac * tong_lan) + accuracy) / new_tong_lan)

        # 3. BỘ CỔNG RẼ NHÁNH THỜI GIAN
        if topic_type == "conversation":
            new_thoi_gt = thoi_gian_gt + actual_mins
            new_thoi_alpha = thoi_gian_alpha
        else:
            new_thoi_alpha = thoi_gian_alpha + actual_mins
            new_thoi_gt = thoi_gian_gt

        # 4. Cập nhật xuống DB
        cursor.execute("""
            UPDATE TaiKhoan
            SET ChuoiNgayHoc = ?, ThoiGianHoc = ?, ThoiGianGiaoTiep = ?, 
                DoChinhXacTB = ?, NgayHocCuoi = ?, TongSoLanTap = ?
            WHERE ID = ?
        """, (chuoi_ngay, new_thoi_alpha, new_thoi_gt, new_do_chinh_xac, str(today), new_tong_lan, user_id))
        conn.commit()

        return {
            "ChuoiNgayHoc": chuoi_ngay,
            "ThoiGianHoc": new_thoi_alpha,
            "ThoiGianGiaoTiep": new_thoi_gt,
            "DoChinhXacTB": new_do_chinh_xac
        }
    except Exception as e:
        print("Lỗi update_study_stats:", e)
        return None
def get_leaderboard(limit=5):
    """Lấy danh sách Top người chơi có điểm số cao nhất"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        # Lấy HoTen (nếu null thì lấy TenDangNhap) và DiemSo, sắp xếp giảm dần
        cursor.execute(f"""
            SELECT TOP {limit} 
                   ISNULL(HoTen, TenDangNhap) as TenHienThi, 
                   DiemSo 
            FROM TaiKhoan 
            ORDER BY DiemSo DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print("Lỗi get_leaderboard:", e)
        return []

def get_user_minigame_stats(user_id):
    """Lấy thông tin thành tích cá nhân để hiển thị cột bên phải"""
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DiemSo, DoChinhXacTB, ChuoiNgayHoc, TongSoLanTap 
            FROM TaiKhoan 
            WHERE ID = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                "DiemSo": row[0] or 0,
                "DoChinhXacTB": row[1] or 0,
                "ChuoiNgayHoc": row[2] or 0,
                "TongSoLanTap": row[3] or 0
            }
        return None
    except Exception as e:
        print("Lỗi get_user_minigame_stats:", e)
        return None