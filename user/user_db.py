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
def update_study_stats(user_id, accuracy, time_minutes):
    """
    Hàm chuẩn của Kỹ sư Backend: Tự động tính toán Chuỗi ngày học dựa trên ngày hiện tại,
    cộng dồn thời gian và tính lại Độ chính xác trung bình.
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 1. Lấy dữ liệu cũ của user lên
        cursor.execute("SELECT ChuoiNgayHoc, ThoiGianHoc, DoChinhXacTB, NgayHocCuoi, TongSoLanTap FROM TaiKhoan WHERE ID = ?", (user_id,))
        row = cursor.fetchone()
        if not row: return None

        chuoi_ngay = row.ChuoiNgayHoc or 0
        thoi_gian = row.ThoiGianHoc or 0
        do_chinh_xac = row.DoChinhXacTB or 0
        tong_lan = row.TongSoLanTap or 0
        ngay_cuoi = row.NgayHocCuoi

        from datetime import date, timedelta
        today = date.today()

        # 2. Thuật toán tính Chuỗi ngày học (Streak)
        if ngay_cuoi:
            if type(ngay_cuoi) == str:
                from datetime import datetime
                ngay_cuoi = datetime.strptime(ngay_cuoi, "%Y-%m-%d").date()
                
            if ngay_cuoi == today - timedelta(days=1):
                chuoi_ngay += 1  # Hôm qua có học -> Tăng chuỗi
            elif ngay_cuoi < today - timedelta(days=1):
                chuoi_ngay = 1   # Bỏ lỡ > 1 ngày -> Mất chuỗi, đếm lại từ đầu
            # (Nếu ngay_cuoi == today thì giữ nguyên chuỗi không tăng thêm)
        else:
            chuoi_ngay = 1 # Học lần đầu tiên

        # 3. Tính toán các chỉ số khác
        new_tong_lan = tong_lan + 1
        new_do_chinh_xac = int(((do_chinh_xac * tong_lan) + accuracy) / new_tong_lan)
        new_thoi_gian = thoi_gian + time_minutes

        # 4. Ghi đè vào Database
        cursor.execute("""
            UPDATE TaiKhoan
            SET ChuoiNgayHoc = ?, ThoiGianHoc = ?, DoChinhXacTB = ?, NgayHocCuoi = ?, TongSoLanTap = ?
            WHERE ID = ?
        """, (chuoi_ngay, new_thoi_gian, new_do_chinh_xac, str(today), new_tong_lan, user_id))
        conn.commit()

        # Trả về dữ liệu mới để cập nhật lên UI ngay lập tức
        return {
            "ChuoiNgayHoc": chuoi_ngay,
            "ThoiGianHoc": new_thoi_gian,
            "DoChinhXacTB": new_do_chinh_xac
        }
    except Exception as e:
        print("Lỗi update_study_stats:", e)
        return None