# 1.21.1 — Đối tượng Digital cho booking online

- Booking được khách mua qua web Sunny (giỏ hàng hoặc Thanh toán ngay, cả luồng đặt trực tiếp cũ) có đối tượng báo cáo **Digital**.
- Tên khách, email và điện thoại vẫn được giữ trong đơn để xử lý/gửi vé. Không thay tên khách thật thành Digital.
- Danh sách booking, báo cáo sử dụng nhãn Khách hàng/Đại lý và báo cáo thu tiền theo phương thức hiển thị Digital cho kênh online. Khoản online vẫn thuộc module Bán vé/Booking, không phải Souvenirs.
- Migration `online.0009_online_digital_party` cập nhật nhãn đối tượng cho các booking có `salesChannel=online` đã có. Giữ nguyên doanh thu, tiền đã thu, ngày, giá vốn, phiên bản vé và khách hàng; booking thủ công/đại lý khác không đổi. Revision workspace tăng khi có cập nhật để tránh màn hình cũ lưu đè.
- Không tạo một đại lý có bảng giá riêng hay thay cách tính doanh thu. Booking online không được sửa trực tiếp nhãn đối tượng qua công cụ chỉnh dữ liệu thông thường.

## Cập nhật Ubuntu

Dừng ứng dụng bằng Ctrl+C ở đúng cửa sổ máy chủ, sao lưu dữ liệu theo quy trình hiện tại rồi chạy:

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
