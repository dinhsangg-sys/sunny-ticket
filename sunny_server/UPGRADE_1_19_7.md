# 1.19.7 — Bố trí thông tin công ty trong footer

Đưa thông tin công ty lên ngay dưới slogan ở cột giữa, bỏ hàng riêng phía dưới và đường ngăn. Chữ nội dung 16px, tên công ty 19px; email/hotline mỗi dòng để dễ đọc. Áp dụng trang chính và Souvenirs, tự xếp dọc trên điện thoại. Không có migration mới.

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
