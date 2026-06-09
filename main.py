import tkinter as tk

# Sửa lại dòng này: Gọi hàm từ file 'ui' thay vì 'menu_window'
from ui import create_main_menu

if __name__ == "__main__":
    # 1. Khởi tạo cửa sổ gốc của Tkinter
    root = tk.Tk()
    
    # 2. Gọi thợ vẽ giao diện từ file ui.py để vẽ các nút bấm
    create_main_menu(root)
    
    # 3. Kích hoạt chương trình chạy vòng lặp chính
    root.mainloop()