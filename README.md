# Sunny Travel Ticket Management — Python test edition

**Bản cập nhật 1.9.8.1:** sửa cấu hình CSRF cho domain HTTPS, thông báo lỗi lưu và thao tác mở lịch. Xem [hướng dẫn nâng cấp](sunny_server/UPGRADE_1_9_8_1.md) nếu đã cài bản trước.

Bản chuyển đổi từ HTML v1.9.8 sang Django để kiểm thử. Giữ các hàm nghiệp vụ JavaScript gốc, bổ sung đăng nhập, quản trị tài khoản, lưu dữ liệu chung, chống ghi đè và cổng đại lý chỉ đọc.

## Clone và chạy thử trên Ubuntu

```bash
git clone https://github.com/dinhsangg-sys/sunny-ticket.git
cd sunny-ticket/sunny_server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py test apps.legacy
python manage.py runserver 127.0.0.1:8000
```

Yêu cầu Python 3.12 trở lên và gói `python3-venv`. Nếu Ubuntu ở máy khác, dùng SSH tunnel từ máy cá nhân: `ssh -L 8000:127.0.0.1:8000 user@ubuntu-host`, sau đó mở http://127.0.0.1:8000 trên máy cá nhân. Không dùng development server để public Internet.

- [Hướng dẫn đầy đủ và triển khai Ubuntu/PostgreSQL](sunny_server/README.md)
- [Checklist nghiệm thu với HTML gốc](sunny_server/CHECKLIST_TEST.md)
- [Kết quả kiểm tra đã chạy](sunny_server/TEST_RESULT.md)

Đây là bản test tương thích, chưa phải backend nghiệp vụ hoàn chỉnh: server lưu snapshot JSON, tính tiền vẫn ở JavaScript, operator có đầy đủ quyền nội bộ và đại lý chỉ đọc. Xem các giới hạn trong hướng dẫn trước khi sử dụng dữ liệu thực tế. Không có mật khẩu mặc định. Môi trường Python, database, tệp người dùng tải lên và thông tin bí mật không nằm trong repository.
