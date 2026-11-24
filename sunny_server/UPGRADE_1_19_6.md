# 1.19.6 — Thông tin công ty ở footer

Trang chính và Souvenirs hiển thị Công ty TNHH Sunny; địa chỉ 36/147 Lê Quý Đôn, Phường Hội An, Thành phố Đà Nẵng, Việt Nam; email info@sunnygovn.com và hotline +84 932 548 145. Có bản tiếng Anh theo ngôn ngữ khách chọn, email và hotline bấm được để gửi thư/gọi điện. Không có migration mới.

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
