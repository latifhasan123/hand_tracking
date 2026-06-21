"""Run this file to preview the VSL Translate Minigame UI."""

try:
    from .minigame_ui import MinigameWindow
except ImportError:
    from minigame_ui import MinigameWindow


if __name__ == "__main__":
    app = MinigameWindow()
    app.mainloop()
