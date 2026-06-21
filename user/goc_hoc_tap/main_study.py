"""Chạy độc lập giao diện Góc học tập."""

try:
    from .study_ui import run_app
except ImportError:
    from study_ui import run_app


if __name__ == "__main__":
    run_app()
