# 1.19.4 — Cờ tròn và nhãn ENG / VN

Bộ chọn ngôn ngữ trên trang chính và Souvenirs hiển thị cờ tròn cùng nhãn ENG / VN, giữ mũi tên xổ xuống. Tiếng Anh vẫn là mặc định khi chưa chọn. Bỏ liên kết Staff login / Dành cho nhân viên ở chân trang; giữ đăng nhập trên header. Biểu tượng liên hệ đơn sắc xanh đậm trên nền sáng, không ô màu; giữ nguyên các kênh và liên kết. Không có migration mới so với 1.19.3.

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C rồi chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ ứng dụng mở, Ctrl+F5 trên trình duyệt.
