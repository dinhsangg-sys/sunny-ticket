# 1.20.3 — Đưa phần dịch vụ lên cao hơn

Bỏ dải ba thông điệp “Đi cùng sự thấu hiểu”, “Đặt vé thuận tiện”, “Nhận vé qua email” giữa phần mở đầu và danh sách dịch vụ ở trang chủ. Các thẻ giới thiệu dịch vụ nằm ngay sau phần mở đầu, không còn dải ngăn cách này. Áp dụng cả Việt/Anh; không đổi nội dung bài, giá hoặc đặt vé. Không có migration mới.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C rồi cập nhật theo lệnh dưới đây. Lệnh migrate chỉ áp dụng migration còn thiếu nếu bạn bỏ qua phiên bản trước.

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
