# 1.16.1 — Chỉnh slogan, font và nền đăng nhập

Slogan: Sunny — Tấm lòng người địa phương, đến những hành trình đáng nhớ.

Bỏ ảnh Hội An/địa điểm khỏi trang đăng nhập. Chỉ dùng nền vàng/trắng với đường cong trừu tượng bằng CSS. Dùng font sans-serif hỗ trợ tiếng Việt, khoảng cách chữ tự nhiên, không giãn chữ âm; bố cục câu slogan theo cụm để dễ đọc, co theo màn hình điện thoại. Không gọi font/ảnh từ bên ngoài. Giữ nguyên biểu mẫu và cơ chế đăng nhập.

Cập nhật Ubuntu:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Không có migration mới. Nếu cần khởi động lại, Ctrl+C tại đúng cửa sổ runserver đang chạy rồi chạy lại và giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Mở /login/ bằng cửa sổ riêng tư hoặc đăng xuất, Ctrl+F5. Kiểm tra font trên máy tính và điện thoại. Đã kiểm tra backend đăng nhập/CSRF/next và browser desktop/mobile/320px, lỗi biểu mẫu, hiện/ẩn mật khẩu, fallback không JS. Trang đăng nhập không có thẻ ảnh hoặc ảnh địa điểm.
