import customtkinter as ctk
from tkinter import messagebox
import user_db

# KHO LƯU TRỮ TOÀN CỤC
CURRENT_USER = None
LEARNED_LETTERS = []

class AuthFrame(ctk.CTkFrame):
    def __init__(self, parent, on_success=None):
        super().__init__(parent, fg_color="transparent")
        self.on_success = on_success
        self.is_login = True
        self.show_pw = False
        self.build_ui()

    def build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Căn giữa màn hình hoàn hảo
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # FIX LỖI: Bỏ pack_propagate(False) đi để khung tự co giãn chiều cao theo Form!
        # Đổi width thành 600
        # Căn giữa màn hình hoàn hảo
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # TẠO CARD (Không set width ở đây nữa)
        card = ctk.CTkFrame(wrapper, fg_color="#182033", corner_radius=28, border_width=1, border_color="#27324A")
        card.pack(pady=20, padx=20)
        
        # BÍ KÍP Ở ĐÂY: Dùng một khung tàng hình để chống sập chiều rộng (ép cứng 550px)
        ctk.CTkFrame(card, width=550, height=0, fg_color="transparent").pack()
        # TUYỆT ĐỐI XÓA DÒNG: card.pack_propagate(False) để khung tự động giãn chiều cao
        
        title_text = "ĐĂNG NHẬP" if self.is_login else "ĐĂNG KÝ TÀI KHOẢN"
        sub_text = "Chào mừng trở lại! Vui lòng đăng nhập." if self.is_login else "Tạo tài khoản để lưu tiến độ và tham gia Minigame."
        
        # Tiêu đề to và nổi bật
        ctk.CTkLabel(card, text=title_text, font=ctk.CTkFont(size=36, weight="bold"), text_color="#28A8FF").pack(pady=(45, 8))
        ctk.CTkLabel(card, text=sub_text, font=ctk.CTkFont(size=16), text_color="#A0AAB5").pack(pady=(0, 35))
        
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=50) # Tăng lề 2 bên
        
        # --- TÊN ĐĂNG NHẬP ---
        ctk.CTkLabel(form, text="Tên đăng nhập *", font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(anchor="w", pady=(0, 8))
        self.user_entry = ctk.CTkEntry(form, height=55, fg_color="#1A222B", border_color="#3A434D", font=ctk.CTkFont(size=16), placeholder_text="Nhập tên tài khoản...")
        self.user_entry.pack(fill="x", pady=(0, 20))
        
        # --- HỌ TÊN & SĐT (CHỈ HIỆN KHI ĐĂNG KÝ) ---
        if not self.is_login:
            ctk.CTkLabel(form, text="Họ và tên *", font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(anchor="w", pady=(0, 8))
            self.name_entry = ctk.CTkEntry(form, height=55, fg_color="#1A222B", border_color="#3A434D", font=ctk.CTkFont(size=16), placeholder_text="Nhập họ tên thật...")
            self.name_entry.pack(fill="x", pady=(0, 20))

            ctk.CTkLabel(form, text="Số điện thoại (Không bắt buộc)", font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(anchor="w", pady=(0, 8))
            self.phone_entry = ctk.CTkEntry(form, height=55, fg_color="#1A222B", border_color="#3A434D", font=ctk.CTkFont(size=16), placeholder_text="Nhập số điện thoại...")
            self.phone_entry.pack(fill="x", pady=(0, 20))

        # --- MẬT KHẨU KÈM NÚT ẨN/HIỆN CHUYÊN NGHIỆP ---
        # --- MẬT KHẨU KÈM NÚT ẨN/HIỆN ---
        # --- MẬT KHẨU KÈM NÚT ICON ẨN/HIỆN CHUYÊN NGHIỆP ---
        ctk.CTkLabel(form, text="Mật khẩu *", font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(anchor="w", pady=(0, 8))
        pw_frame = ctk.CTkFrame(form, fg_color="transparent")
        pw_frame.pack(fill="x", pady=(0, 35))
        
        self.pass_entry = ctk.CTkEntry(pw_frame, height=55, fg_color="#1A222B", border_color="#3A434D", font=ctk.CTkFont(size=16), show="●", placeholder_text="Nhập mật khẩu...")
        self.pass_entry.pack(side="left", fill="x", expand=True)

        def toggle_pw():
            self.show_pw = not self.show_pw
            self.pass_entry.configure(show="" if self.show_pw else "●")
            # Chuyển đổi giữa Icon Mắt (Mở) và Ổ Khóa (Đóng)
            eye_btn.configure(text="👁" if self.show_pw else "🔒")
            
        eye_btn = ctk.CTkButton(
            pw_frame, 
            text="🔒", 
            width=55, 
            height=55, 
            fg_color="#252D3A", 
            hover_color="#2F3846", 
            text_color="#A0AAB5", 
            font=ctk.CTkFont(size=22), # Chỉnh Font to lên để Icon rõ nét
            corner_radius=10, 
            command=toggle_pw
        )
        eye_btn.pack(side="right", padx=(10, 0))

        # --- NÚT XÁC NHẬN ---
        btn_text = "ĐĂNG NHẬP" if self.is_login else "TẠO TÀI KHOẢN"
        ctk.CTkButton(
            form, 
            text=btn_text, 
            height=60, 
            font=ctk.CTkFont(size=18, weight="bold"), 
            corner_radius=14, 
            fg_color="#28A8FF", 
            hover_color="#1E7BBA", 
            command=self.process_auth
        ).pack(fill="x")
        
        # --- CHUYỂN ĐỔI FORM ---
        switch_frame = ctk.CTkFrame(card, fg_color="transparent")
        switch_frame.pack(pady=(20, 45))
        
        ctk.CTkLabel(switch_frame, text="Chưa có tài khoản?" if self.is_login else "Đã có tài khoản?", text_color="#A0AAB5", font=ctk.CTkFont(size=15)).pack(side="left")
        
        def toggle_mode():
            self.is_login = not self.is_login
            self.show_pw = False
            self.build_ui()
            
        ctk.CTkButton(
            switch_frame, 
            text="Đăng ký ngay" if self.is_login else "Đăng nhập", 
            width=0, 
            height=0, 
            fg_color="transparent", 
            hover_color="#182033", 
            text_color="#28A8FF", 
            font=ctk.CTkFont(size=15, weight="bold", underline=True), 
            command=toggle_mode
        ).pack(side="left", padx=(6, 0))

    def process_auth(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        
        if not u or not p:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!")
            return
            
        if self.is_login:
            success, data = user_db.login_user(u, p)
            if success:
                global CURRENT_USER, LEARNED_LETTERS
                CURRENT_USER = data
                LEARNED_LETTERS = user_db.get_learned_letters(data["id"])
                if self.on_success: 
                    self.on_success()
            else:
                messagebox.showerror("Lỗi", data)
        else:
            name = self.name_entry.get().strip()
            phone = self.phone_entry.get().strip()
            if not name:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập Họ và tên (bắt buộc)!")
                return
            success, msg = user_db.register_user(u, p, name, phone)
            if success:
                messagebox.showinfo("Thành công", msg)
                self.is_login = True
                self.build_ui()
            else:
                messagebox.showerror("Lỗi", msg)

def show_auth_window(parent, on_success=None):
    pass