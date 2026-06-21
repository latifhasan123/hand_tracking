"""
Tự động nhúng nút "Góc học tập" vào file user/ui_user.py.

Cách chạy từ thư mục gốc hand_tracking:
    python user\\goc_hoc_tap\\install_into_ui_user.py

Script sẽ tạo bản sao lưu: user/ui_user.py.bak_before_goc_hoc_tap
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_USER = ROOT / "user" / "ui_user.py"
BACKUP = ROOT / "user" / "ui_user.py.bak_before_goc_hoc_tap"

IMPORT_LINE = "from goc_hoc_tap.study_ui import open_study_window"
OLD_CMD = 'command=lambda: dummy_action("Góc học tập")'
NEW_CMD = 'command=lambda: open_study_window(root)'


def main():
    if not UI_USER.exists():
        raise FileNotFoundError(f"Không tìm thấy {UI_USER}")

    text = UI_USER.read_text(encoding="utf-8")
    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")

    changed = False
    if IMPORT_LINE not in text:
        # Ưu tiên chèn sau dòng import customtkinter as ctk.
        if "import customtkinter as ctk" in text:
            text = text.replace("import customtkinter as ctk", f"import customtkinter as ctk\n{IMPORT_LINE}", 1)
        else:
            text = IMPORT_LINE + "\n" + text
        changed = True

    if OLD_CMD in text:
        text = text.replace(OLD_CMD, NEW_CMD, 1)
        changed = True

    if not changed:
        print("Không có gì cần sửa. Có thể file ui_user.py đã được nhúng rồi.")
        return

    UI_USER.write_text(text, encoding="utf-8")
    print("Đã nhúng Góc học tập vào user/ui_user.py")
    print(f"File sao lưu: {BACKUP}")


if __name__ == "__main__":
    main()
