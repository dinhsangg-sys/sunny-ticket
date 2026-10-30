# 1.11.2 — Mẫu vé nét đen trắng đã được duyệt

Áp dụng hình nét người phụ nữ dệt vải do người dùng cung cấp và logo Hội An Memories Land chữ đen trên nền trắng, theo mẫu được duyệt ngày 30/10/2026. Giữ nguyên khổ 80x110 mm, nhãn/thông tin và vị trí QR. QR thật không nằm trong template. Không đổi database hoặc nghiệp vụ.

## Cập nhật bản chính

Dừng server chính cổng 8000 bằng Ctrl+C tại terminal đang chạy, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Giữ terminal mở và Ctrl+F5. Nếu chạy bằng dịch vụ thì restart dịch vụ hiện có thay vì mở thêm tiến trình 8000. Không cần migration/thư viện mới nếu đã cập nhật 1.11.0; nếu chưa, theo UPGRADE_1_11_0.md trước. Không reset hoặc chép database test.

Vé tạo mới dùng mẫu đã duyệt. PDF đã xuất được giữ nguyên để đối soát. Muốn áp dụng cho booking đã xuất: dùng quyền thay vé, chọn Tạo phiên bản vé mới, kiểm tra thông tin và xác nhận tạo lại PDF. Không tạo booking hoặc khoản thu mới chỉ để đổi hình mẫu vé.

Đã render/kiểm tra trực quan mẫu, xác nhận trang 80x110 và QR đầu ra khớp nguồn. Các kiểm tra nhập/xuất, quyền, phiên bản và đối chiếu vé liên quan đạt; chưa in thử máy POS-80C thực tế.
