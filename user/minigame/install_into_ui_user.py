r"""
Optional helper: patch user/ui_user.py to open the Minigame UI.

Run from the project root:
    python user\minigame\install_into_ui_user.py

This script makes a backup before editing. Because every source code version can be
slightly different, please review the result if it cannot find the Minigame button.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_FILE = ROOT / "user" / "ui_user.py"
BACKUP = ROOT / "user" / "ui_user.py.bak_minigame"

IMPORT_LINE = "from user.minigame.minigame_ui import open_minigame_window\n"


def main():
    if not UI_FILE.exists():
        print(f"Không tìm thấy file: {UI_FILE}")
        return

    text = UI_FILE.read_text(encoding="utf-8", errors="ignore")
    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print(f"Đã tạo backup: {BACKUP}")

    if IMPORT_LINE.strip() not in text:
        lines = text.splitlines(True)
        insert_at = 0
        while insert_at < len(lines) and (lines[insert_at].startswith("import ") or lines[insert_at].startswith("from ")):
            insert_at += 1
        lines.insert(insert_at, IMPORT_LINE)
        text = "".join(lines)

    # Try common button text patterns.
    replacements = [
        ('text="Minigame"', 'text="Minigame", command=lambda: open_minigame_window(self)'),
        ("text='Minigame'", "text='Minigame', command=lambda: open_minigame_window(self)"),
        ('text="🎮 Minigame"', 'text="🎮 Minigame", command=lambda: open_minigame_window(self)'),
        ("text='🎮 Minigame'", "text='🎮 Minigame', command=lambda: open_minigame_window(self)"),
    ]

    changed = False
    for old, new in replacements:
        if old in text and new not in text:
            text = text.replace(old, new, 1)
            changed = True
            break

    UI_FILE.write_text(text, encoding="utf-8")
    print("Đã thêm import cho Minigame UI.")
    if changed:
        print("Đã thử gắn command cho nút Minigame trong ui_user.py.")
    else:
        print("Chưa tự gắn được command cho nút Minigame.")
        print("Bạn thêm thủ công vào nút Minigame:")
        print("    command=lambda: open_minigame_window(self)")
        print("và thêm dòng import ở đầu file:")
        print("    from user.minigame.minigame_ui import open_minigame_window")


if __name__ == "__main__":
    main()
