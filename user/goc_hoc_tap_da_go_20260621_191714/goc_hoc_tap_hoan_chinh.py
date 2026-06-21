from __future__ import annotations

import datetime as dt
import os
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import messagebox, ttk

try:
    import cv2
except Exception:
    cv2 = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


APP_TITLE = "Góc học tập"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "goc_hoc_tap.sqlite3"
SNAPSHOT_DIR = BASE_DIR / "anh_camera"


COLORS = {
    "bg": "#f5f7fb",
    "surface": "#ffffff",
    "surface_2": "#eef3f8",
    "text": "#1f2937",
    "muted": "#64748b",
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "line": "#dbe3ee",
    "sidebar": "#111827",
    "sidebar_hover": "#1f2937",
    "sidebar_active": "#2563eb",
}


FLASHCARDS = [
    ("Toán", "Công thức diện tích hình tròn?", "S = πr²"),
    ("Toán", "Đạo hàm của x² là gì?", "2x"),
    ("Anh văn", "Study nghĩa là gì?", "Học tập"),
    ("Anh văn", "Practice nghĩa là gì?", "Luyện tập"),
    ("Khoa học", "Nước sôi ở bao nhiêu độ C?", "100°C ở áp suất tiêu chuẩn"),
]

QUIZZES = [
    {
        "subject": "Toán",
        "question": "12 x 8 = ?",
        "answer": "96",
        "hint": "Tách thành 12 x (10 - 2).",
    },
    {
        "subject": "Anh văn",
        "question": "Từ trái nghĩa của 'hard' là gì?",
        "answer": "easy",
        "hint": "Nghĩa là dễ.",
    },
    {
        "subject": "Khoa học",
        "question": "Hành tinh gần Mặt Trời nhất là gì?",
        "answer": "sao thủy",
        "hint": "Mercury.",
    },
]


def today_text() -> str:
    return dt.datetime.now().strftime("%d/%m/%Y")


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def normalize_answer(value: str) -> str:
    return " ".join(value.strip().lower().split())


class StudyDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    due_date TEXT NOT NULL DEFAULT '',
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    minutes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def add_task(self, title: str, subject: str, due_date: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO tasks(title, subject, due_date, done, created_at) VALUES (?, ?, ?, 0, ?)",
                (title, subject, due_date, now_iso()),
            )

    def list_tasks(self, include_done: bool = True) -> list[sqlite3.Row]:
        where = "" if include_done else "WHERE done = 0"
        return list(
            self.conn.execute(
                f"SELECT * FROM tasks {where} ORDER BY done ASC, due_date ASC, id DESC"
            )
        )

    def set_task_done(self, task_id: int, done: bool) -> None:
        with self.conn:
            self.conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (1 if done else 0, task_id))

    def delete_task(self, task_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def save_note(self, title: str, body: str, note_id: int | None = None) -> int:
        with self.conn:
            if note_id is None:
                cur = self.conn.execute(
                    "INSERT INTO notes(title, body, updated_at) VALUES (?, ?, ?)",
                    (title, body, now_iso()),
                )
                return int(cur.lastrowid)
            self.conn.execute(
                "UPDATE notes SET title = ?, body = ?, updated_at = ? WHERE id = ?",
                (title, body, now_iso(), note_id),
            )
            return note_id

    def list_notes(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM notes ORDER BY updated_at DESC, id DESC"))

    def delete_note(self, note_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    def add_session(self, subject: str, minutes: int) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO sessions(subject, minutes, created_at) VALUES (?, ?, ?)",
                (subject, minutes, now_iso()),
            )

    def list_sessions(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM sessions ORDER BY created_at DESC, id DESC"))

    def stats(self) -> dict[str, int]:
        tasks_total = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        tasks_done = self.conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
        notes_total = self.conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        minutes_total = self.conn.execute("SELECT COALESCE(SUM(minutes), 0) FROM sessions").fetchone()[0]
        return {
            "tasks_total": int(tasks_total),
            "tasks_done": int(tasks_done),
            "notes_total": int(notes_total),
            "minutes_total": int(minutes_total),
        }

    def close(self) -> None:
        self.conn.close()


class StudyApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=COLORS["bg"])

        self.db = StudyDB(DB_PATH)
        self.current_page = ""
        self.sidebar_buttons: dict[str, tk.Button] = {}

        self.timer_job: str | None = None
        self.timer_seconds_left = 25 * 60
        self.timer_total_seconds = 25 * 60
        self.timer_running = False

        self.card_index = 0
        self.card_showing_answer = False
        self.quiz_index = 0

        self.camera = None
        self.camera_running = False
        self.camera_index = 0
        self.camera_job: str | None = None
        self.camera_photo = None
        self.current_frame = None

        self.selected_note_id: int | None = None
        self.note_rows: list[sqlite3.Row] = []

        self.setup_styles()
        self.build_shell()
        self.show_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        default_font = ("Segoe UI", 10)
        self.option_add("*Font", default_font)
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["surface"], relief="flat")
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Card.TLabel", background=COLORS["surface"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"])
        style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 20, "bold"))
        style.configure("Header.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Segoe UI", 13, "bold"))
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", background=COLORS["primary"], foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", COLORS["primary_dark"])])
        style.configure("Danger.TButton", background=COLORS["danger"], foreground="#ffffff")
        style.configure("Success.TButton", background=COLORS["success"], foreground="#ffffff")
        style.configure("TEntry", padding=8)
        style.configure("TCombobox", padding=8)

    def build_shell(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=230)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        brand = tk.Label(
            self.sidebar,
            text="Góc học tập",
            bg=COLORS["sidebar"],
            fg="#ffffff",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
            padx=22,
            pady=22,
        )
        brand.pack(fill="x")

        nav_items = [
            ("Tổng quan", self.show_dashboard),
            ("Việc cần làm", self.show_tasks),
            ("Luyện tập", self.show_practice),
            ("Camera", self.show_camera),
            ("Pomodoro", self.show_timer),
            ("Ghi chú", self.show_notes),
            ("Thống kê", self.show_stats),
            ("Cài đặt", self.show_settings),
        ]
        for label, command in nav_items:
            self.add_nav_button(label, command)

        self.status_var = tk.StringVar(value="Sẵn sàng.")
        status = tk.Label(
            self.sidebar,
            textvariable=self.status_var,
            bg=COLORS["sidebar"],
            fg="#d1d5db",
            wraplength=185,
            justify="left",
            anchor="sw",
            padx=18,
            pady=18,
        )
        status.pack(side="bottom", fill="x")

        self.main = tk.Frame(self, bg=COLORS["bg"])
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.header = tk.Frame(self.main, bg=COLORS["bg"], padx=24, pady=18)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(value=APP_TITLE)
        ttk.Label(self.header, textvariable=self.title_var, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        self.date_var = tk.StringVar(value=today_text())
        ttk.Label(self.header, textvariable=self.date_var).grid(row=0, column=1, sticky="e")

        self.content = tk.Frame(self.main, bg=COLORS["bg"], padx=24, pady=6)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def add_nav_button(self, label: str, command: Callable[[], None]) -> None:
        button = tk.Button(
            self.sidebar,
            text=label,
            command=lambda: self.safe(command),
            bg=COLORS["sidebar"],
            fg="#e5e7eb",
            activebackground=COLORS["sidebar_hover"],
            activeforeground="#ffffff",
            bd=0,
            relief="flat",
            anchor="w",
            padx=22,
            pady=13,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )
        button.pack(fill="x", padx=10, pady=2)
        self.sidebar_buttons[label] = button

    def set_active_nav(self, label: str) -> None:
        self.current_page = label
        for name, button in self.sidebar_buttons.items():
            if name == label:
                button.configure(bg=COLORS["sidebar_active"], fg="#ffffff")
            else:
                button.configure(bg=COLORS["sidebar"], fg="#e5e7eb")

    def safe(self, action: Callable[[], Any]) -> None:
        try:
            action()
        except Exception as exc:
            self.notify(f"Lỗi: {exc}")
            messagebox.showerror(APP_TITLE, f"Đã có lỗi xảy ra:\n{exc}")

    def notify(self, text: str) -> None:
        self.status_var.set(text)

    def clear_content(self) -> None:
        if self.camera_running:
            self.stop_camera(show_message=False)
        for child in self.content.winfo_children():
            child.destroy()

    def set_title(self, nav: str, title: str) -> None:
        self.set_active_nav(nav)
        self.title_var.set(title)
        self.date_var.set(today_text())

    def card(self, parent: tk.Misc, row: int, column: int, **grid: Any) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Card.TFrame", padding=18)
        frame.grid(row=row, column=column, sticky=grid.pop("sticky", "nsew"), padx=grid.pop("padx", 8), pady=grid.pop("pady", 8), **grid)
        return frame

    def button_row(self, parent: tk.Misc, buttons: list[tuple[str, Callable[[], None], str]]) -> tk.Frame:
        row = tk.Frame(parent, bg=COLORS["surface"])
        row.pack(fill="x", pady=(12, 0))
        for label, command, style in buttons:
            ttk.Button(row, text=label, command=lambda c=command: self.safe(c), style=style).pack(side="left", padx=(0, 8))
        return row

    def show_dashboard(self) -> None:
        self.clear_content()
        self.set_title("Tổng quan", "Tổng quan học tập")
        stats = self.db.stats()

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure((0, 1, 2), weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        summary = [
            ("Việc đã xong", f"{stats['tasks_done']}/{stats['tasks_total']}", COLORS["success"]),
            ("Thời gian học", f"{stats['minutes_total']} phút", COLORS["primary"]),
            ("Ghi chú", str(stats["notes_total"]), COLORS["warning"]),
        ]
        for index, (label, value, color) in enumerate(summary):
            frame = self.card(wrapper, 0, index)
            ttk.Label(frame, text=label, style="Muted.TLabel").pack(anchor="w")
            tk.Label(frame, text=value, bg=COLORS["surface"], fg=color, font=("Segoe UI", 28, "bold")).pack(anchor="w", pady=(8, 0))

        quick = self.card(wrapper, 1, 0, columnspan=2, sticky="nsew")
        ttk.Label(quick, text="Lối tắt", style="Header.TLabel").pack(anchor="w")
        quick_buttons = [
            ("Bắt đầu Pomodoro", self.show_timer, "Primary.TButton"),
            ("Thêm việc", self.show_tasks, "TButton"),
            ("Mở camera", self.show_camera, "TButton"),
            ("Ghi chú mới", self.show_notes, "TButton"),
        ]
        self.button_row(quick, quick_buttons)

        tasks = self.card(wrapper, 1, 2, sticky="nsew")
        ttk.Label(tasks, text="Việc chưa xong", style="Header.TLabel").pack(anchor="w")
        pending = [row for row in self.db.list_tasks(include_done=False)][:6]
        if not pending:
            ttk.Label(tasks, text="Chưa có việc nào. Bạn có thể thêm ở mục Việc cần làm.", style="Muted.TLabel", wraplength=260).pack(anchor="w", pady=12)
        else:
            for row in pending:
                text = f"• {row['title']}"
                if row["due_date"]:
                    text += f"  ({row['due_date']})"
                ttk.Label(tasks, text=text, style="Card.TLabel", wraplength=280).pack(anchor="w", pady=4)
        self.notify("Tổng quan đã được cập nhật.")

    def show_tasks(self) -> None:
        self.clear_content()
        self.set_title("Việc cần làm", "Việc cần làm")

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, minsize=340)
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        form = self.card(wrapper, 0, 0, sticky="ns")
        ttk.Label(form, text="Thêm việc mới", style="Header.TLabel").pack(anchor="w")
        ttk.Label(form, text="Tên việc", style="Card.TLabel").pack(anchor="w", pady=(14, 4))
        self.task_title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.task_title_var, width=34).pack(fill="x")
        ttk.Label(form, text="Môn học", style="Card.TLabel").pack(anchor="w", pady=(12, 4))
        self.task_subject_var = tk.StringVar(value="Tự học")
        ttk.Combobox(form, textvariable=self.task_subject_var, values=["Tự học", "Toán", "Anh văn", "Khoa học", "Văn", "Lịch sử"], state="normal").pack(fill="x")
        ttk.Label(form, text="Hạn hoàn thành", style="Card.TLabel").pack(anchor="w", pady=(12, 4))
        self.task_due_var = tk.StringVar(value=dt.date.today().isoformat())
        ttk.Entry(form, textvariable=self.task_due_var).pack(fill="x")
        self.button_row(form, [("Thêm việc", self.add_task, "Primary.TButton"), ("Làm mới", self.refresh_tasks, "TButton")])

        list_card = self.card(wrapper, 0, 1, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)
        ttk.Label(list_card, text="Danh sách", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        self.tasks_canvas = tk.Canvas(list_card, bg=COLORS["surface"], highlightthickness=0)
        self.tasks_scroll = ttk.Scrollbar(list_card, orient="vertical", command=self.tasks_canvas.yview)
        self.tasks_inner = tk.Frame(self.tasks_canvas, bg=COLORS["surface"])
        self.tasks_window = self.tasks_canvas.create_window((0, 0), window=self.tasks_inner, anchor="nw")
        self.tasks_canvas.configure(yscrollcommand=self.tasks_scroll.set)
        self.tasks_canvas.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self.tasks_scroll.grid(row=1, column=1, sticky="ns", pady=(12, 0))
        self.tasks_inner.bind("<Configure>", lambda event: self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all")))
        self.tasks_canvas.bind("<Configure>", lambda event: self.tasks_canvas.itemconfigure(self.tasks_window, width=event.width))
        self.refresh_tasks()

    def add_task(self) -> None:
        title = self.task_title_var.get().strip()
        subject = self.task_subject_var.get().strip() or "Tự học"
        due_date = self.task_due_var.get().strip()
        if not title:
            messagebox.showwarning(APP_TITLE, "Bạn hãy nhập tên việc cần làm.")
            return
        if due_date:
            try:
                dt.date.fromisoformat(due_date)
            except ValueError:
                messagebox.showwarning(APP_TITLE, "Hạn hoàn thành nên có dạng YYYY-MM-DD, ví dụ 2026-06-21.")
                return
        self.db.add_task(title, subject, due_date)
        self.task_title_var.set("")
        self.refresh_tasks()
        self.notify("Đã thêm việc mới.")

    def refresh_tasks(self) -> None:
        for child in self.tasks_inner.winfo_children():
            child.destroy()
        rows = self.db.list_tasks(include_done=True)
        if not rows:
            ttk.Label(self.tasks_inner, text="Chưa có việc nào. Hãy thêm việc đầu tiên.", style="Muted.TLabel").pack(anchor="w", pady=12)
            return
        for row in rows:
            item = tk.Frame(self.tasks_inner, bg=COLORS["surface"], highlightbackground=COLORS["line"], highlightthickness=1)
            item.pack(fill="x", pady=6)
            item.grid_columnconfigure(0, weight=1)
            done = bool(row["done"])
            title = row["title"]
            if done:
                title = f"✓ {title}"
            label = tk.Label(
                item,
                text=title,
                bg=COLORS["surface"],
                fg=COLORS["muted"] if done else COLORS["text"],
                font=("Segoe UI", 11, "overstrike" if done else "normal"),
                anchor="w",
                padx=12,
                pady=8,
            )
            label.grid(row=0, column=0, sticky="ew")
            meta = f"{row['subject']}"
            if row["due_date"]:
                meta += f" • hạn {row['due_date']}"
            tk.Label(item, text=meta, bg=COLORS["surface"], fg=COLORS["muted"], anchor="w", padx=12).grid(row=1, column=0, sticky="ew")
            ttk.Button(item, text="Bỏ xong" if done else "Hoàn thành", command=lambda task_id=row["id"], state=done: self.safe(lambda: self.toggle_task(task_id, not state))).grid(row=0, column=1, rowspan=2, padx=6, pady=8)
            ttk.Button(item, text="Xóa", command=lambda task_id=row["id"]: self.safe(lambda: self.delete_task(task_id)), style="Danger.TButton").grid(row=0, column=2, rowspan=2, padx=(0, 10), pady=8)

    def toggle_task(self, task_id: int, done: bool) -> None:
        self.db.set_task_done(task_id, done)
        self.refresh_tasks()
        self.notify("Đã cập nhật trạng thái việc cần làm.")

    def delete_task(self, task_id: int) -> None:
        if messagebox.askyesno(APP_TITLE, "Bạn chắc chắn muốn xóa việc này?"):
            self.db.delete_task(task_id)
            self.refresh_tasks()
            self.notify("Đã xóa việc.")

    def show_practice(self) -> None:
        self.clear_content()
        self.set_title("Luyện tập", "Luyện tập")

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure((0, 1), weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        flash = self.card(wrapper, 0, 0, sticky="nsew")
        ttk.Label(flash, text="Thẻ ghi nhớ", style="Header.TLabel").pack(anchor="w")
        self.flash_subject_var = tk.StringVar()
        self.flash_text_var = tk.StringVar()
        tk.Label(
            flash,
            textvariable=self.flash_subject_var,
            bg=COLORS["surface"],
            fg=COLORS["primary"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(18, 4))
        tk.Label(
            flash,
            textvariable=self.flash_text_var,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            wraplength=430,
            justify="center",
            font=("Segoe UI", 18, "bold"),
            padx=20,
            pady=34,
        ).pack(fill="x", pady=8)
        self.button_row(
            flash,
            [
                ("Lật thẻ", self.flip_card, "Primary.TButton"),
                ("Thẻ trước", self.prev_card, "TButton"),
                ("Thẻ sau", self.next_card, "TButton"),
                ("Ngẫu nhiên", self.random_card, "TButton"),
            ],
        )

        quiz = self.card(wrapper, 0, 1, sticky="nsew")
        ttk.Label(quiz, text="Câu hỏi nhanh", style="Header.TLabel").pack(anchor="w")
        self.quiz_subject_var = tk.StringVar()
        self.quiz_question_var = tk.StringVar()
        self.quiz_feedback_var = tk.StringVar(value="")
        tk.Label(quiz, textvariable=self.quiz_subject_var, bg=COLORS["surface"], fg=COLORS["primary"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(18, 4))
        tk.Label(quiz, textvariable=self.quiz_question_var, bg=COLORS["surface"], fg=COLORS["text"], wraplength=430, justify="left", font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 12))
        self.quiz_answer_var = tk.StringVar()
        ttk.Entry(quiz, textvariable=self.quiz_answer_var).pack(fill="x")
        tk.Label(quiz, textvariable=self.quiz_feedback_var, bg=COLORS["surface"], fg=COLORS["muted"], wraplength=430, justify="left").pack(anchor="w", pady=(12, 0))
        self.button_row(
            quiz,
            [
                ("Kiểm tra", self.check_quiz, "Primary.TButton"),
                ("Gợi ý", self.show_quiz_hint, "TButton"),
                ("Câu khác", self.next_quiz, "TButton"),
            ],
        )
        self.update_flashcard()
        self.update_quiz()
        self.notify("Khu luyện tập đã sẵn sàng.")

    def update_flashcard(self) -> None:
        subject, question, answer = FLASHCARDS[self.card_index]
        self.flash_subject_var.set(subject)
        self.flash_text_var.set(answer if self.card_showing_answer else question)

    def flip_card(self) -> None:
        self.card_showing_answer = not self.card_showing_answer
        self.update_flashcard()
        self.notify("Đã lật thẻ.")

    def prev_card(self) -> None:
        self.card_index = (self.card_index - 1) % len(FLASHCARDS)
        self.card_showing_answer = False
        self.update_flashcard()
        self.notify("Đã chuyển sang thẻ trước.")

    def next_card(self) -> None:
        self.card_index = (self.card_index + 1) % len(FLASHCARDS)
        self.card_showing_answer = False
        self.update_flashcard()
        self.notify("Đã chuyển sang thẻ sau.")

    def random_card(self) -> None:
        self.card_index = random.randrange(len(FLASHCARDS))
        self.card_showing_answer = False
        self.update_flashcard()
        self.notify("Đã chọn thẻ ngẫu nhiên.")

    def update_quiz(self) -> None:
        quiz = QUIZZES[self.quiz_index]
        self.quiz_subject_var.set(quiz["subject"])
        self.quiz_question_var.set(quiz["question"])
        self.quiz_answer_var.set("")
        self.quiz_feedback_var.set("Nhập câu trả lời rồi bấm Kiểm tra.")

    def check_quiz(self) -> None:
        quiz = QUIZZES[self.quiz_index]
        answer = normalize_answer(self.quiz_answer_var.get())
        correct = normalize_answer(quiz["answer"])
        if not answer:
            self.quiz_feedback_var.set("Bạn hãy nhập câu trả lời trước.")
            self.notify("Chưa có câu trả lời.")
            return
        if answer == correct:
            self.quiz_feedback_var.set("Đúng rồi. Làm tốt lắm!")
            self.notify("Câu trả lời chính xác.")
        else:
            self.quiz_feedback_var.set(f"Chưa đúng. Đáp án đúng là: {quiz['answer']}")
            self.notify("Đã hiển thị đáp án đúng.")

    def show_quiz_hint(self) -> None:
        self.quiz_feedback_var.set(f"Gợi ý: {QUIZZES[self.quiz_index]['hint']}")
        self.notify("Đã hiển thị gợi ý.")

    def next_quiz(self) -> None:
        self.quiz_index = (self.quiz_index + 1) % len(QUIZZES)
        self.update_quiz()
        self.notify("Đã chuyển câu hỏi.")

    def show_camera(self) -> None:
        self.clear_content()
        self.set_title("Camera", "Luyện tập bằng camera")

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        camera_card = self.card(wrapper, 0, 0, sticky="nsew")
        camera_card.grid_columnconfigure(0, weight=1)
        camera_card.grid_rowconfigure(1, weight=1)
        ttk.Label(camera_card, text="Khung camera", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        self.camera_status_var = tk.StringVar(value="Bấm Bật camera để bắt đầu.")
        ttk.Label(camera_card, textvariable=self.camera_status_var, style="Muted.TLabel").grid(row=0, column=1, sticky="e")

        self.camera_label = tk.Label(
            camera_card,
            text="Camera chưa bật",
            bg="#0f172a",
            fg="#e5e7eb",
            font=("Segoe UI", 18, "bold"),
            anchor="center",
            width=20,
            height=12,
        )
        self.camera_label.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(14, 12))

        controls = tk.Frame(camera_card, bg=COLORS["surface"])
        controls.grid(row=2, column=0, columnspan=2, sticky="ew")
        for label, command, style in [
            ("Bật camera", self.start_camera, "Primary.TButton"),
            ("Tắt camera", self.stop_camera, "TButton"),
            ("Chụp ảnh", self.take_snapshot, "Success.TButton"),
            ("Đổi camera", self.switch_camera, "TButton"),
        ]:
            ttk.Button(controls, text=label, command=lambda c=command: self.safe(c), style=style).pack(side="left", padx=(0, 8))

        note = (
            "Nếu Windows hỏi quyền truy cập camera, hãy cho phép ứng dụng Python. "
            "Camera cần chạy bằng file .py trên máy thật, không phải trong trình xem mã."
        )
        ttk.Label(camera_card, text=note, style="Muted.TLabel", wraplength=780).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.notify("Màn hình camera đã mở.")

    def start_camera(self) -> None:
        if self.camera_running:
            self.camera_status_var.set("Camera đang bật.")
            self.notify("Camera đang chạy.")
            return
        if cv2 is None or Image is None or ImageTk is None:
            missing = []
            if cv2 is None:
                missing.append("opencv-python")
            if Image is None or ImageTk is None:
                missing.append("Pillow")
            messagebox.showerror(APP_TITLE, "Thiếu thư viện camera: " + ", ".join(missing) + "\nHãy cài bằng: pip install opencv-python pillow")
            self.camera_status_var.set("Thiếu thư viện camera.")
            self.notify("Không thể bật camera vì thiếu thư viện.")
            return

        self.release_camera()
        capture = self.open_camera(self.camera_index)
        if capture is None:
            for index in range(3):
                if index == self.camera_index:
                    continue
                capture = self.open_camera(index)
                if capture is not None:
                    self.camera_index = index
                    break
        if capture is None:
            self.camera_label.configure(text="Không tìm thấy camera", image="")
            self.camera_status_var.set("Không mở được camera.")
            messagebox.showwarning(APP_TITLE, "Không mở được camera. Hãy kiểm tra thiết bị, quyền camera của Windows, hoặc thử cắm lại webcam.")
            self.notify("Không mở được camera.")
            return

        self.camera = capture
        self.camera_running = True
        self.camera_status_var.set(f"Đang dùng camera {self.camera_index}.")
        self.notify("Camera đã bật.")
        self.update_camera_frame()

    def open_camera(self, index: int):
        if cv2 is None:
            return None
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, 0] if sys.platform.startswith("win") else [0]
        for backend in backends:
            try:
                capture = cv2.VideoCapture(index, backend) if backend else cv2.VideoCapture(index)
                if capture is not None and capture.isOpened():
                    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
                    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
                    return capture
                if capture is not None:
                    capture.release()
            except Exception:
                continue
        return None

    def update_camera_frame(self) -> None:
        if not self.camera_running or self.camera is None:
            return
        ok, frame = self.camera.read()
        if not ok or frame is None:
            self.camera_status_var.set("Không lấy được khung hình.")
            self.camera_job = self.after(250, self.update_camera_frame)
            return

        self.current_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        label_width = max(self.camera_label.winfo_width(), 640)
        label_height = max(self.camera_label.winfo_height(), 360)
        image.thumbnail((label_width, label_height))
        self.camera_photo = ImageTk.PhotoImage(image=image)
        self.camera_label.configure(image=self.camera_photo, text="")
        self.camera_status_var.set(f"Camera {self.camera_index} đang hiển thị.")
        self.camera_job = self.after(30, self.update_camera_frame)

    def stop_camera(self, show_message: bool = True) -> None:
        self.camera_running = False
        if self.camera_job is not None:
            try:
                self.after_cancel(self.camera_job)
            except tk.TclError:
                pass
            self.camera_job = None
        self.release_camera()
        self.current_frame = None
        if hasattr(self, "camera_label") and self.camera_label.winfo_exists():
            self.camera_label.configure(image="", text="Camera đã tắt")
        if hasattr(self, "camera_status_var"):
            self.camera_status_var.set("Camera đã tắt.")
        if show_message:
            self.notify("Camera đã tắt.")

    def release_camera(self) -> None:
        if self.camera is not None:
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None

    def take_snapshot(self) -> None:
        if self.current_frame is None or cv2 is None:
            messagebox.showinfo(APP_TITLE, "Chưa có hình ảnh để chụp. Hãy bật camera trước.")
            self.notify("Chưa chụp được vì camera chưa có khung hình.")
            return
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        filename = SNAPSHOT_DIR / f"camera_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(str(filename), self.current_frame)
        messagebox.showinfo(APP_TITLE, f"Đã lưu ảnh:\n{filename}")
        self.notify("Đã chụp và lưu ảnh camera.")

    def switch_camera(self) -> None:
        self.camera_index = (self.camera_index + 1) % 3
        was_running = self.camera_running
        self.stop_camera(show_message=False)
        if was_running:
            self.start_camera()
        else:
            if hasattr(self, "camera_status_var"):
                self.camera_status_var.set(f"Đã chọn camera {self.camera_index}. Bấm Bật camera để dùng.")
            self.notify(f"Đã chọn camera {self.camera_index}.")

    def show_timer(self) -> None:
        self.clear_content()
        self.set_title("Pomodoro", "Pomodoro")

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)

        timer = self.card(wrapper, 0, 0, sticky="nsew")
        ttk.Label(timer, text="Bộ đếm học tập", style="Header.TLabel").pack(anchor="w")
        self.timer_display_var = tk.StringVar()
        self.timer_subject_var = tk.StringVar(value="Tự học")
        self.timer_minutes_var = tk.StringVar(value=str(max(1, self.timer_total_seconds // 60)))

        tk.Label(timer, textvariable=self.timer_display_var, bg=COLORS["surface"], fg=COLORS["primary"], font=("Segoe UI", 54, "bold")).pack(pady=(28, 8))
        self.update_timer_display()

        form = tk.Frame(timer, bg=COLORS["surface"])
        form.pack(fill="x", pady=(8, 0))
        ttk.Label(form, text="Môn học", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Combobox(form, textvariable=self.timer_subject_var, values=["Tự học", "Toán", "Anh văn", "Khoa học", "Văn", "Lịch sử"], state="normal", width=24).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(4, 0))
        ttk.Label(form, text="Số phút", style="Card.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Spinbox(form, from_=1, to=180, textvariable=self.timer_minutes_var, width=10).grid(row=1, column=1, sticky="w", pady=(4, 0))

        self.button_row(
            timer,
            [
                ("Bắt đầu", self.start_timer, "Primary.TButton"),
                ("Tạm dừng", self.pause_timer, "TButton"),
                ("Đặt lại", self.reset_timer, "TButton"),
                ("Lưu phiên học", self.save_timer_session, "Success.TButton"),
            ],
        )
        self.notify("Pomodoro đã sẵn sàng.")

    def set_timer_from_inputs(self) -> bool:
        try:
            minutes = int(self.timer_minutes_var.get())
        except ValueError:
            messagebox.showwarning(APP_TITLE, "Số phút phải là số nguyên.")
            return False
        if minutes <= 0:
            messagebox.showwarning(APP_TITLE, "Số phút phải lớn hơn 0.")
            return False
        if not self.timer_running:
            self.timer_total_seconds = minutes * 60
            self.timer_seconds_left = min(self.timer_seconds_left, self.timer_total_seconds)
            if self.timer_seconds_left <= 0:
                self.timer_seconds_left = self.timer_total_seconds
            self.update_timer_display()
        return True

    def update_timer_display(self) -> None:
        minutes, seconds = divmod(max(0, self.timer_seconds_left), 60)
        if hasattr(self, "timer_display_var"):
            self.timer_display_var.set(f"{minutes:02d}:{seconds:02d}")

    def start_timer(self) -> None:
        if not self.set_timer_from_inputs():
            return
        if self.timer_running:
            self.notify("Bộ đếm đang chạy.")
            return
        if self.timer_seconds_left <= 0:
            self.timer_seconds_left = self.timer_total_seconds
        self.timer_running = True
        self.tick_timer()
        self.notify("Đã bắt đầu Pomodoro.")

    def tick_timer(self) -> None:
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.timer_seconds_left <= 0:
            self.timer_running = False
            self.timer_job = None
            messagebox.showinfo(APP_TITLE, "Hết giờ học. Bạn nên nghỉ một chút.")
            self.save_timer_session(silent=True)
            self.notify("Pomodoro đã hoàn thành.")
            return
        self.timer_seconds_left -= 1
        self.timer_job = self.after(1000, self.tick_timer)

    def pause_timer(self) -> None:
        if not self.timer_running:
            self.notify("Bộ đếm đang tạm dừng.")
            return
        self.timer_running = False
        if self.timer_job is not None:
            try:
                self.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None
        self.update_timer_display()
        self.notify("Đã tạm dừng Pomodoro.")

    def reset_timer(self) -> None:
        self.pause_timer()
        try:
            minutes = int(self.timer_minutes_var.get())
        except Exception:
            minutes = 25
            self.timer_minutes_var.set("25")
        self.timer_total_seconds = max(1, minutes) * 60
        self.timer_seconds_left = self.timer_total_seconds
        self.update_timer_display()
        self.notify("Đã đặt lại bộ đếm.")

    def save_timer_session(self, silent: bool = False) -> None:
        subject = self.timer_subject_var.get().strip() or "Tự học"
        elapsed = max(0, self.timer_total_seconds - self.timer_seconds_left)
        minutes = max(1, round(elapsed / 60)) if elapsed else max(1, self.timer_total_seconds // 60)
        self.db.add_session(subject, minutes)
        if not silent:
            messagebox.showinfo(APP_TITLE, f"Đã lưu phiên học {minutes} phút cho môn {subject}.")
        self.notify("Đã lưu phiên học.")

    def show_notes(self) -> None:
        self.clear_content()
        self.set_title("Ghi chú", "Ghi chú")

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, minsize=290)
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        left = self.card(wrapper, 0, 0, sticky="ns")
        ttk.Label(left, text="Danh sách ghi chú", style="Header.TLabel").pack(anchor="w")
        self.notes_listbox = tk.Listbox(left, height=20, activestyle="none", borderwidth=0, highlightthickness=1, highlightbackground=COLORS["line"])
        self.notes_listbox.pack(fill="both", expand=True, pady=(12, 0))
        self.notes_listbox.bind("<<ListboxSelect>>", lambda event: self.safe(self.load_selected_note))
        self.button_row(left, [("Tạo mới", self.clear_note_editor, "TButton"), ("Xóa", self.delete_selected_note, "Danger.TButton")])

        editor = self.card(wrapper, 0, 1, sticky="nsew")
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_rowconfigure(2, weight=1)
        ttk.Label(editor, text="Nội dung", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        self.note_title_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self.note_title_var).grid(row=1, column=0, sticky="ew", pady=(12, 8))
        self.note_body = tk.Text(editor, wrap="word", height=18, bg="#ffffff", fg=COLORS["text"], relief="solid", bd=1, padx=12, pady=10)
        self.note_body.grid(row=2, column=0, sticky="nsew")
        controls = tk.Frame(editor, bg=COLORS["surface"])
        controls.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(controls, text="Lưu ghi chú", command=lambda: self.safe(self.save_note), style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Làm trống", command=lambda: self.safe(self.clear_note_editor)).pack(side="left")
        self.refresh_notes()
        self.notify("Ghi chú đã sẵn sàng.")

    def refresh_notes(self) -> None:
        self.note_rows = self.db.list_notes()
        self.notes_listbox.delete(0, tk.END)
        for row in self.note_rows:
            self.notes_listbox.insert(tk.END, row["title"])

    def load_selected_note(self) -> None:
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        row = self.note_rows[selection[0]]
        self.selected_note_id = int(row["id"])
        self.note_title_var.set(row["title"])
        self.note_body.delete("1.0", tk.END)
        self.note_body.insert("1.0", row["body"])
        self.notify("Đã mở ghi chú.")

    def save_note(self) -> None:
        title = self.note_title_var.get().strip()
        body = self.note_body.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning(APP_TITLE, "Bạn hãy nhập tiêu đề ghi chú.")
            return
        self.selected_note_id = self.db.save_note(title, body, self.selected_note_id)
        self.refresh_notes()
        self.notify("Đã lưu ghi chú.")

    def clear_note_editor(self) -> None:
        self.selected_note_id = None
        self.note_title_var.set("")
        self.note_body.delete("1.0", tk.END)
        self.notes_listbox.selection_clear(0, tk.END)
        self.notify("Đã mở ghi chú mới.")

    def delete_selected_note(self) -> None:
        if self.selected_note_id is None:
            messagebox.showinfo(APP_TITLE, "Hãy chọn ghi chú cần xóa.")
            return
        if messagebox.askyesno(APP_TITLE, "Bạn chắc chắn muốn xóa ghi chú này?"):
            self.db.delete_note(self.selected_note_id)
            self.clear_note_editor()
            self.refresh_notes()
            self.notify("Đã xóa ghi chú.")

    def show_stats(self) -> None:
        self.clear_content()
        self.set_title("Thống kê", "Thống kê")
        stats = self.db.stats()
        sessions = self.db.list_sessions()

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure((0, 1), weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        done_percent = 0
        if stats["tasks_total"]:
            done_percent = round(stats["tasks_done"] / stats["tasks_total"] * 100)

        cards = [
            ("Hoàn thành việc", f"{done_percent}%", COLORS["success"]),
            ("Tổng phút học", f"{stats['minutes_total']}", COLORS["primary"]),
        ]
        for index, (label, value, color) in enumerate(cards):
            frame = self.card(wrapper, 0, index)
            ttk.Label(frame, text=label, style="Muted.TLabel").pack(anchor="w")
            tk.Label(frame, text=value, bg=COLORS["surface"], fg=color, font=("Segoe UI", 34, "bold")).pack(anchor="w", pady=(8, 0))

        history = self.card(wrapper, 1, 0, columnspan=2, sticky="nsew")
        history.grid_columnconfigure(0, weight=1)
        history.grid_rowconfigure(1, weight=1)
        ttk.Label(history, text="Lịch sử phiên học", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(history, text="Làm mới", command=lambda: self.safe(self.show_stats)).grid(row=0, column=1, sticky="e")
        tree = ttk.Treeview(history, columns=("subject", "minutes", "created"), show="headings", height=12)
        tree.heading("subject", text="Môn học")
        tree.heading("minutes", text="Phút")
        tree.heading("created", text="Thời gian")
        tree.column("subject", width=220)
        tree.column("minutes", width=90, anchor="center")
        tree.column("created", width=260)
        tree.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        for row in sessions:
            tree.insert("", tk.END, values=(row["subject"], row["minutes"], row["created_at"]))
        self.notify("Thống kê đã được cập nhật.")

    def show_settings(self) -> None:
        self.clear_content()
        self.set_title("Cài đặt", "Cài đặt")

        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        settings = self.card(wrapper, 0, 0, sticky="nsew")
        ttk.Label(settings, text="Kiểm tra hệ thống", style="Header.TLabel").pack(anchor="w")
        details = [
            f"File dữ liệu: {DB_PATH}",
            f"Thư mục ảnh camera: {SNAPSHOT_DIR}",
            "Camera: " + ("sẵn sàng dùng thư viện" if cv2 is not None and Image is not None and ImageTk is not None else "thiếu opencv-python hoặc Pillow"),
        ]
        for detail in details:
            ttk.Label(settings, text=detail, style="Card.TLabel", wraplength=820).pack(anchor="w", pady=6)
        self.button_row(
            settings,
            [
                ("Mở camera", self.show_camera, "Primary.TButton"),
                ("Làm mới thống kê", self.show_stats, "TButton"),
                ("Lưu phiên mẫu", self.save_sample_session, "Success.TButton"),
            ],
        )
        self.notify("Cài đặt đã mở.")

    def save_sample_session(self) -> None:
        self.db.add_session("Tự học", 5)
        messagebox.showinfo(APP_TITLE, "Đã thêm một phiên học mẫu 5 phút để kiểm tra thống kê.")
        self.notify("Đã lưu phiên học mẫu.")

    def on_close(self) -> None:
        self.stop_camera(show_message=False)
        if self.timer_job is not None:
            try:
                self.after_cancel(self.timer_job)
            except tk.TclError:
                pass
        self.db.close()
        self.destroy()


def main() -> None:
    app = StudyApp()
    app.mainloop()


if __name__ == "__main__":
    main()
