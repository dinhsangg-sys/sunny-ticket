# 1.20.4 — Hai đường cong mềm dưới phần mở đầu

Thêm hai đường cong SVG mảnh màu xanh nhạt chạy ngang dưới phần mở đầu trang chủ, từ bên trái sang chân ô cửa. Bỏ đường cong ngắn riêng dưới ô cửa, giữ nền trong suốt. Đường nét tự co theo màn hình, không tương tác hoặc cản bấm. Không có migration mới.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C rồi chạy:

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
