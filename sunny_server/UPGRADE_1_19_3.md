# 1.19.3 — Cờ ngôn ngữ và Google Maps Sunny

- Trang khách chính và Souvenirs dùng cờ Anh/Việt Nam, mũi tên xổ xuống; không hiện tên ngôn ngữ. Giữ nhãn hỗ trợ truy cập và tooltip.
- Khách chưa chọn ngôn ngữ luôn thấy tiếng Anh, kể cả trình duyệt tiếng Việt. Lựa chọn qua nút cờ và cookie cũ hợp lệ được giữ; không đổi dữ liệu đơn hay giá.
- Google Maps dưới logo trỏ đến https://share.google/8FKS1V2zJ0mxKpJE4 theo xác nhận của chủ website. Migration 0005 chỉ điền khi trường Google Maps trống, không ghi đè địa điểm đã cấu hình riêng. Có thể sửa trong Quản trị → Liên hệ & kênh Sunny.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C rồi chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ máy chủ mở. Ctrl+F5 ở trình duyệt. Muốn kiểm tra mặc định tiếng Anh, dùng cửa sổ ẩn danh chưa có cookie ngôn ngữ; khách đã chọn tiếng Việt vẫn giữ tiếng Việt.
