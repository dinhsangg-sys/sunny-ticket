# 1.11.1 — Thay ảnh mẫu vé đầu ra

Thay phần hình minh họa trong mẫu 80x110 bằng ảnh người dùng cung cấp ngày 30/10/2026. Giữ logo, nhãn, nền thông tin, kích thước trang và tọa độ QR/các trường. Template không chứa QR thật hay thông tin khách. Không thay quy tắc booking, thanh toán hoặc OCR.

## Cập nhật từ 1.11.0

Dừng tiến trình bản chính cổng 8000 tại terminal đang chạy bằng Ctrl+C. Sao lưu theo UPGRADE_1_11_0.md nếu cần giữ trạng thái vận hành trước cập nhật. Sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Giữ terminal mở, Ctrl+F5. Nếu dùng dịch vụ riêng thì restart đúng dịch vụ, không khởi động thêm tiến trình 8000.

Không cần migrate hoặc cài thư viện mới khi đã ở 1.11.0. Nếu chưa nâng cấp 1.11.0, thực hiện đầy đủ UPGRADE_1_11_0.md trước. Không reset database.

Vé tạo mới sử dụng ảnh mới. PDF đã xuất được giữ nguyên, không ghi đè tự động. Nếu muốn thay ảnh cho booking đã xuất, người có quyền thay vé tạo phiên bản mới từ bộ cũ, kiểm tra và xác nhận tạo lại PDF; QR nguồn được giữ nguyên và bản cũ vẫn lưu để đối soát.

Đã render và kiểm tra trực quan mẫu; xuất PDF thử đúng 80x110 và kiểm tra QR; các kiểm tra nhập/xuất vé, phiên bản và báo cáo liên quan đạt. Chưa in thử trực tiếp trên máy POS-80C.
