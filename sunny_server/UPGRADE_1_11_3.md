# 1.11.3 — QR lớn hơn 30%

Tăng khung ảnh QR từ 18x18 mm lên 23.4x23.4 mm, tức tăng mỗi chiều 30%. Giữ khổ vé 80x110 mm, căn giữa theo chiều ngang và giữ mép dưới; mở rộng lên trên, không đổi vị trí các trường thông tin. Nới nền trắng quanh QR thêm lề 2 mm để hình nền không lẫn vào mã. Không thay nội dung QR.

Dừng server chính cổng 8000 bằng Ctrl+C tại terminal đang chạy, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Nếu dùng dịch vụ riêng thì restart dịch vụ hiện có. Không cần migration hoặc thư viện mới khi đã ở 1.11.0 trở lên. Ctrl+F5 trên trình duyệt. Không reset dữ liệu.

PDF tạo mới dùng QR lớn. PDF đã xuất được giữ nguyên; để áp dụng cho booking cũ, người có quyền thay vé tạo phiên bản mới từ bộ cũ, kiểm tra và xác nhận tạo lại PDF. Không tạo booking/khoản thu mới chỉ để đổi kích thước QR.

Đã kiểm tra trực quan PDF mẫu, kích thước trang/khung QR, nội dung các trường và giải mã QR đầu ra khớp nguồn. Chưa thử in trên máy POS-80C thực tế.
