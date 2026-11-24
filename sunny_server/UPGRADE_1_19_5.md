# 1.19.5 — Logo Sunny chính thức

Thay chữ thương hiệu ở đầu/chân trang khách chính và Souvenirs bằng ảnh PNG do chủ website cung cấp. Giữ nền trong suốt và tỷ lệ ảnh gốc. Bấm logo về trang chủ Sunny /discover/, kể cả từ Souvenirs. Không đổi mẫu vé hoặc quyền đăng nhập. Không có migration mới.

Dừng ứng dụng bằng Ctrl+C ở đúng cửa sổ máy chủ, rồi chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ chạy máy chủ mở và Ctrl+F5 trên website.
