# 1.14.7 — Logo Hoi An Memories Show do người dùng cung cấp

Thay dòng chữ in đậm đầu vé của 1.14.6 bằng logo đen nền trong suốt do người dùng cung cấp. Logo giữ tỷ lệ và căn giữa, phù hợp nền giấy trắng/máy in nhiệt. Không thay hình minh họa, QR, thông tin vé hoặc khổ 80 x 110 mm.

Sao lưu trước theo hướng dẫn 1.14.0 rồi cập nhật:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
```

Không có migration mới hoặc cấu hình mới. Nếu khởi động lại runserver, Ctrl+C tại đúng cửa sổ đang chạy rồi chạy lại và giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Mẫu áp dụng cho PDF xuất mới, in và PDF gửi email mới. PDF đã xuất trước đó giữ nguyên; nếu muốn mẫu mới cần tạo lại vé qua quy trình hiện có, kiểm tra QR trước khi in/gửi. Không tự thay PDF lịch sử hay gửi email khi nâng cấp.

Đã kiểm tra bản render PDF, khổ trang và kiểm thử xuất vé/QR/giữ lịch sử. Chưa in thử trên máy nhiệt thật.
