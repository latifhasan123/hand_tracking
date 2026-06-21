# VSL Translate - Folder con `user/goc_hoc_tap`

Folder này tạo giao diện **Góc học tập** bằng Python + CustomTkinter, thiết kế theo giao diện hiện tại của dự án `hand_tracking`.

## 1. Cách đặt folder vào project

Sau khi clone project:

```powershell
git clone https://github.com/latifhasan123/hand_tracking.git
cd hand_tracking
```

Giải nén file zip này vào **thư mục gốc `hand_tracking`** để có cấu trúc:

```text
hand_tracking/
├── user/
│   ├── main_user.py
│   ├── ui_user.py
│   └── goc_hoc_tap/
│       ├── main_study.py
│       ├── study_ui.py
│       ├── data.py
│       ├── theme.py
│       ├── install_into_ui_user.py
│       └── run_study.bat
```

## 2. Cài thư viện cần thiết

Dự án gốc đã dùng CustomTkinter. Nếu máy chưa có, chạy:

```powershell
pip install customtkinter pillow opencv-python numpy
```

Nếu bạn đã tạo môi trường ảo:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install customtkinter pillow
```

## 3. Chạy riêng giao diện Góc học tập

Từ thư mục gốc `hand_tracking`:

```powershell
python user\goc_hoc_tap\main_study.py
```

Hoặc mở trực tiếp:

```powershell
user\goc_hoc_tap\run_study.bat
```

## 4. Nhúng vào nút "Góc học tập" của `user/ui_user.py`

Chạy lệnh:

```powershell
python user\goc_hoc_tap\install_into_ui_user.py
```

Sau đó chạy app gốc:

```powershell
python user\main_user.py
```

Khi bấm nút **Góc học tập**, app sẽ mở cửa sổ giao diện học tập.

## 5. Ghi chú

- Đây là giao diện học tập tĩnh/giả lập để làm UI.
- Phần camera thật vẫn nằm trong `user/ui_user.py` của project gốc.
- Có thể kết nối màn hình `Luyện bằng camera` với OpenCV/AI sau bằng cách gọi lại logic camera trong `ui_user.py`.
