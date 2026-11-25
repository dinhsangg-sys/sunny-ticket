# 1.19.9 — Ô cửa sổ Hội An trên trang chủ

Thay hình vòm đơn giản bằng ô cửa gỗ, tường vàng, đèn lồng và mái phố cổ theo ảnh tham chiếu của chủ website. Phối nền kem ấm, xanh đậm và vàng dịu theo mẫu; nền ngoài ô cửa trong suốt, không có khung vuông. Nền ảnh được xử lý bỏ chữ; chữ thật trên web đổi Việt/Anh và co theo kích thước ô cửa. Ảnh WebP được lưu trong static/img, không gọi dịch vụ ảnh ngoài khi khách truy cập. Không có migration mới.

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
