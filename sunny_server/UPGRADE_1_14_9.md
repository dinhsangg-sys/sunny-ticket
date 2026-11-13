# 1.14.9 — Giờ tạo trong danh sách booking nhân viên

Trong Bán vé tại quầy → Booking của tôi, cột Ngày đổi thành Ngày / Giờ tạo, ví dụ 2026-11-13 10:15:30. Giữ ngày booking hiện có và thêm giờ tạo từ createdAt đã lưu trên máy chủ, theo múi giờ Asia/Ho_Chi_Minh (UTC+7), không phụ thuộc múi giờ máy khách. Không dùng giờ thanh toán hoặc giờ sửa booking.

Booking cũ có createdAt hợp lệ sẽ hiện giờ ngay; booking không có timestamp hoặc thiếu thông tin múi giờ chỉ hiện ngày, không gán giờ giả. Không sửa lịch sử, không đổi ngày booking/bộ lọc và không có migration mới.

## Cập nhật Ubuntu

Sao lưu trước theo quy trình hiện tại. Sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Tải lại trang nhân viên bằng Ctrl+F5. Nếu cần khởi động lại runserver, Ctrl+C ở đúng cửa sổ đang chạy rồi chạy lại và giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Kiểm tra danh sách với booking có giờ tạo và booking cũ. Kiểm thử trình duyệt dùng múi giờ America/Los_Angeles vẫn hiển thị đúng UTC+7, trường hợp 00:00:00 và trường hợp thiếu/lỗi timestamp; kiểm tra luồng tạo booking hiện có.
