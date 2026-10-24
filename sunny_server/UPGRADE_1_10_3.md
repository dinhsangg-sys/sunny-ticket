# 1.10.3 — Xóa hoặc dừng loại vé

- Loại vé chưa có dữ liệu liên quan có nút Xóa và xác nhận trước khi thực hiện.
- Loại vé đã có booking, giá vốn, giá riêng đại lý hoặc dòng trong bảng giá chung không có nút Xóa; có nút Dừng sử dụng. Có thể kích hoạt lại khi cần.
- Dừng giữ mã, lịch sử booking, thanh toán và báo cáo. Vé dừng không được chọn khi tạo booking mới.
- Backend kiểm tra cả API đầy đủ và API phân quyền. Không thể gọi API để bỏ vé đã dùng, kể cả gửi kèm thao tác xóa các liên kết.
- Dấu hasActivity lưu từ lần phát sinh dữ liệu và không bị xóa khi các dòng liên quan bị xóa sau đó. Đối với dữ liệu cũ, xác định dựa trên các tham chiếu hiện còn và dấu đã lưu; không thể suy ra các bản ghi đã bị xóa trước bản cập nhật này.
- Thêm quyền "Xóa loại vé chưa phát sinh dữ liệu"; tài khoản hạn chế cần quyền xem và quyền xóa. Dừng/kích hoạt cần quyền sửa và thay đổi trạng thái.

## Ubuntu

Ctrl+C ở cửa sổ đang chạy server, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Migration chỉ bổ sung quyền. Không xóa database, không chạy reset_business_data. Ctrl+F5 để nạp JavaScript mới. Nếu dùng Gunicorn/Nginx thì collectstatic với cấu hình triển khai hiện có và restart dịch vụ thực tế.

42 kiểm thử backend đạt; JavaScript kiểm tra điều kiện đã dùng/chưa dùng đạt. Cần nghiệm thu trực tiếp trên trình duyệt sau cập nhật. Giới hạn các phần phân quyền khác của phiên bản trước không thay đổi.
