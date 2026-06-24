import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import customtkinter as ctk
from ui_user import create_user_menu

if __name__ == "__main__":
    root = ctk.CTk()
    create_user_menu(root)
    root.mainloop() 