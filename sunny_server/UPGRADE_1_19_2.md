# 1.19.2 — Biểu tượng kênh ngay dưới logo Sunny

- Footer website chính: đặt các biểu tượng thành một hàng dưới logo Sunny / Local Heart. Lasting Memories.
- Không hiện tên mạng xã hội, tiêu đề nhóm hoặc mũi tên. Giữ tên trong aria-label và tooltip để người dùng bàn phím/trình đọc màn hình nhận biết đúng kênh.
- Áp dụng kiểu biểu tượng gọn dưới thương hiệu ở footer trang khách Souvenirs. Trên điện thoại có thể tự xuống hàng nếu thêm nhiều kênh.
- Giữ nguyên liên kết, cấu hình liên hệ và việc ẩn LINE. Không có migration mới so với 1.19.1.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ máy chủ mở và Ctrl+F5 ở trình duyệt. Nếu bỏ qua các bản 1.19.0/1.19.1 thì cần chạy manage.py migrate trước khi khởi động để bổ sung trường/bảng và ẩn LINE.
