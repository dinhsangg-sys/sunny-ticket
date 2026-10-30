# 1.11.4 — Dời QR sang trái

Giữ QR 23.4x23.4 mm, chuyển mép trái ảnh QR về 8 mm để không che tay nhân vật. Giữ lề trắng 2 mm và mép dưới QR, bỏ ô trắng cũ ở giữa hình nền. Không đổi nội dung QR, khổ vé 80x110 hoặc các trường thông tin.

Dừng server chính cổng 8000 bằng Ctrl+C tại terminal đang chạy, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Nếu dùng dịch vụ riêng thì restart đúng dịch vụ. Không cần migration hoặc thư viện mới khi đã ở 1.11.0 trở lên. Ctrl+F5. PDF mới dùng bố cục mới; PDF đã xuất giữ nguyên. Muốn áp dụng cho booking cũ, người có quyền thay vé tạo phiên bản mới, kiểm tra và xác nhận xuất lại. Không tạo booking/khoản thu mới chỉ để đổi vị trí QR.

Đã kiểm tra trực quan vùng tay nhân vật và các trường thông tin; kiểm tra kích thước/vị trí QR, khổ trang và giải mã QR đầu ra khớp nguồn. Chưa in thử máy POS-80C thực tế.
