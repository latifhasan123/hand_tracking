import tkinter as tk
from tkinter import messagebox

from train_window import train_new_word_window
from train_model import train_model
from translate_window import start_translate


# =========================
# TRAIN DATA WINDOW
# =========================
def open_train_window():

    train_new_word_window(root)


# =========================
# TRAIN MODEL
# =========================
def run_train_model():

    try:

        train_model()

        messagebox.showinfo(
            "Success",
            "Model trained successfully"
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )


# =========================
# TRANSLATE
# =========================
def open_translate():

    start_translate()


# =========================
# MAIN WINDOW
# =========================
root = tk.Tk()

root.title("Hand Sign Translator")

root.geometry("400x450")


title = tk.Label(
    root,
    text="Hand Sign Translator",
    font=("Arial", 22, "bold")
)

title.pack(pady=30)


# =========================
# BUTTON TRAIN DATA
# =========================
train_data_button = tk.Button(

    root,

    text="Train Data",

    font=("Arial", 16),

    width=20,

    height=2,

    command=open_train_window
)

train_data_button.pack(pady=10)


# =========================
# BUTTON TRAIN MODEL
# =========================
train_model_button = tk.Button(

    root,

    text="Train Model",

    font=("Arial", 16),

    width=20,

    height=2,

    command=run_train_model
)

train_model_button.pack(pady=10)


# =========================
# BUTTON TRANSLATE
# =========================
translate_button = tk.Button(

    root,

    text="Translate",

    font=("Arial", 16),

    width=20,

    height=2,

    command=open_translate
)

translate_button.pack(pady=10)


root.mainloop()