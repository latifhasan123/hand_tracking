import customtkinter as ctk
from ui_user import create_user_menu

if __name__ == "__main__":
    root = ctk.CTk()
    create_user_menu(root)
    root.mainloop()