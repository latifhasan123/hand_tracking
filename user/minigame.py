import customtkinter as ctk
import pyodbc

# ==========================================
# 1. HÀM KẾT NỐI DATABASE
# ==========================================
def connect_db():
    try:
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=localhost\SQLEXPRESS; '  # <--- KIỂM TRA TÊN SERVER CỦA BẠN
            r'DATABASE=QuanLyUser;'
            r'Trusted_Connection=yes;'
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print("Lỗi kết nối CSDL:", e)
        return None

# ==========================================
# 2. GIAO DIỆN BẢNG XẾP HẠNG (LEADERBOARD)
# ==========================================
class LeaderboardWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Bảng Xếp Hạng")
        self.geometry("400x450")
        self.attributes("-topmost", True)
        
        ctk.CTkLabel(self, text="🏆 TOP 5 CAO THỦ", font=ctk.CTkFont(size=22, weight="bold"), text_color="#FF9800").pack(pady=(20, 10))
        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.load_leaderboard()

    def load_leaderboard(self):
        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Ưu tiên hiển thị Họ Tên (nếu có), không thì hiện Tên đăng nhập
            cursor.execute("SELECT TenDangNhap, HoTen, DiemSo FROM TaiKhoan ORDER BY DiemSo DESC")
            top_players = cursor.fetchmany(5)
            
            for idx, player in enumerate(top_players):
                huy_hieu = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🎖️"
                
                # Xử lý hiển thị tên cho đẹp
                display_name = player.HoTen if player.HoTen else player.TenDangNhap
                row_text = f"{huy_hieu} TOP {idx+1}: {display_name} - {player.DiemSo} điểm"
                
                color = "#FF9800" if idx == 0 else "white"
                ctk.CTkLabel(self.list_frame, text=row_text, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(pady=8, anchor="w")
        finally:
            conn.close()

# ==========================================
# 3. GIAO DIỆN MINIGAME (DASHBOARD)
# ==========================================
class DashboardWindow(ctk.CTkToplevel):
    def __init__(self, parent, username, hoten, current_score):
        super().__init__(parent)
        self.title("Khu vực Minigame")
        self.geometry("500x400")
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 
        
        self.username = username
        self.score = current_score
        
        # Lời chào siêu xịn: Lấy Họ tên thật ra chào, nếu chưa có thì chào bằng Username
        display_name = hoten if hoten else username
        
        ctk.CTkLabel(self, text=f"Xin chào, {display_name}!", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 5))
        self.score_label = ctk.CTkLabel(self, text=f"Điểm hiện tại: {self.score}", font=ctk.CTkFont(size=18), text_color="#4CAF50")
        self.score_label.pack(pady=5)
        
        ctk.CTkButton(self, text="🎮 Bấm vào đây để cày +10 Điểm", font=ctk.CTkFont(weight="bold"), height=50, command=self.add_score).pack(pady=20)
        ctk.CTkButton(self, text="🏆 Xem Bảng Xếp Hạng", fg_color="#FF9800", hover_color="#F57C00", font=ctk.CTkFont(weight="bold"), height=40, command=self.open_leaderboard).pack(pady=10)

    def add_score(self):
        self.score += 10
        self.score_label.configure(text=f"Điểm hiện tại: {self.score}")
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE TaiKhoan SET DiemSo = ? WHERE TenDangNhap = ?", (self.score, self.username))
            conn.commit()
            conn.close()

    def open_leaderboard(self):
        LeaderboardWindow(self)

    def on_closing(self):
        self.master.destroy()

# ==========================================
# 4. GIAO DIỆN CHÍNH (ĐĂNG NHẬP & ĐĂNG KÝ)
# ==========================================
class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ thống Đăng nhập")
        self.geometry("400x500")
        self.eval('tk::PlaceWindow . center') 
        
        ctk.CTkLabel(self, text="ĐĂNG NHẬP", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 20))
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Tên đăng nhập", width=250, height=40)
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Mật khẩu", show="*", width=250, height=40)
        self.password_entry.pack(pady=10)

        ctk.CTkButton(self, text="Đăng Nhập", font=ctk.CTkFont(weight="bold"), width=250, height=40, command=self.check_login).pack(pady=(20, 10))
        ctk.CTkButton(self, text="Chưa có tài khoản? Đăng ký ngay", fg_color="transparent", hover_color="#2B2B2B", border_width=1, width=250, height=35, command=self.open_register_window).pack(pady=5)
        
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=10)

    def check_login(self):
        user = self.username_entry.get()
        pwd = self.password_entry.get()

        conn = connect_db()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Kéo cả HoTen ra để lát nữa qua Minigame chào cho thân thiện
            cursor.execute("SELECT TenDangNhap, HoTen, DiemSo FROM TaiKhoan WHERE TenDangNhap = ? AND MatKhau = ?", (user, pwd))
            account = cursor.fetchone()
            
            if account:
                self.withdraw() 
                DashboardWindow(self, account.TenDangNhap, account.HoTen, account.DiemSo)
            else:
                self.status_label.configure(text="🔴 Sai thông tin đăng nhập!", text_color="#F44336")
        finally:
            conn.close()

    # --- CỬA SỔ ĐĂNG KÝ VỚI FULL THÔNG TIN ---
    def open_register_window(self):
        reg_window = ctk.CTkToplevel(self)
        reg_window.title("Đăng ký tài khoản")
        reg_window.geometry("450x650") # Cửa sổ dài hơn để chứa đủ các ô
        reg_window.attributes("-topmost", True)
        reg_window.grab_set() 
        
        ctk.CTkLabel(reg_window, text="TẠO TÀI KHOẢN MỚI", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 20))

        # 2 Ô MỚI: Họ Tên & Số Điện Thoại
        reg_hoten = ctk.CTkEntry(reg_window, placeholder_text="Họ và tên đầy đủ", width=280, height=40)
        reg_hoten.pack(pady=8)
        
        reg_sdt = ctk.CTkEntry(reg_window, placeholder_text="Số điện thoại", width=280, height=40)
        reg_sdt.pack(pady=8)

        # 3 Ô CŨ: Username & Password
        reg_user = ctk.CTkEntry(reg_window, placeholder_text="Tên đăng nhập", width=280, height=40)
        reg_user.pack(pady=8)

        reg_pwd = ctk.CTkEntry(reg_window, placeholder_text="Mật khẩu", show="*", width=280, height=40)
        reg_pwd.pack(pady=8)

        reg_pwd_confirm = ctk.CTkEntry(reg_window, placeholder_text="Xác nhận lại mật khẩu", show="*", width=280, height=40)
        reg_pwd_confirm.pack(pady=8)

        reg_status = ctk.CTkLabel(reg_window, text="", font=ctk.CTkFont(size=14))
        reg_status.pack(pady=10)

        def process_register():
            ht = reg_hoten.get()
            sdt = reg_sdt.get()
            u = reg_user.get()
            p1 = reg_pwd.get()
            p2 = reg_pwd_confirm.get()

            if not ht or not sdt or not u or not p1 or not p2:
                reg_status.configure(text="🔴 Vui lòng điền đủ tất cả các ô!", text_color="#F44336")
                return
            if p1 != p2:
                reg_status.configure(text="🔴 Mật khẩu xác nhận không khớp!", text_color="#F44336")
                return

            conn = connect_db()
            if not conn: return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TaiKhoan WHERE TenDangNhap = ?", (u,))
                if cursor.fetchone():
                    reg_status.configure(text="🔴 Tên đăng nhập này đã có người dùng!", text_color="#FF9800")
                else:
                    # BƠM 4 BIẾN VÀO 4 DẤU CHẤM HỎI
                    cursor.execute("INSERT INTO TaiKhoan (TenDangNhap, MatKhau, HoTen, SoDienThoai) VALUES (?, ?, ?, ?)", (u, p1, ht, sdt))
                    conn.commit() 
                    
                    reg_status.configure(text="🟢 Tạo tài khoản thành công!", text_color="#4CAF50")
                    reg_window.after(1500, reg_window.destroy)
            except Exception as e:
                reg_status.configure(text="🔴 Lỗi hệ thống!", text_color="#F44336")
                print(e)
            finally:
                conn.close()

        ctk.CTkButton(reg_window, text="Đăng Ký", font=ctk.CTkFont(weight="bold"), fg_color="#2196F3", hover_color="#1976D2", width=280, height=40, command=process_register).pack(pady=10)

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()