# 1.21.2 — Hai đường cong sát chân ô cửa

Đưa hai đường cong trang chủ lên sát chân ô cửa hơn trên máy tính và điện thoại. Dòng chữ nhỏ bên phải đặt dưới đường cong để không chồng nét. Giữ màu và độ cong hiện có; không có migration mới.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C rồi chạy (migrate chỉ áp dụng các bản còn thiếu):

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ ứng dụng mở; Ctrl+F5 trên website. Kiểm tra bằng SePay test và hộp thư thử trước khi nhận đơn thật. Khi triển khai qua dịch vụ production, dùng lệnh khởi động lại dịch vụ đang vận hành thay vì mở thêm server trên cổng đã chiếm.
