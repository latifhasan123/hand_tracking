import customtkinter as ctk
from ui import create_main_menu

if __name__ == "__main__":
    # Kích hoạt giao diện Dark Mode (Tối) thời thượng
    ctk.set_appearance_mode("Dark")
    # Đặt tông màu chủ đạo cho các hiệu ứng là màu xanh lam
    ctk.set_default_color_theme("blue") 

    # Khởi tạo cửa sổ gốc bằng CustomTkinter thay vì tk.Tk()
    root = ctk.CTk()
    
    create_main_menu(root)
    
    root.mainloop()