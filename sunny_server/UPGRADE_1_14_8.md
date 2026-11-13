# 1.14.8 — Khoảng trắng tự nhiên giữa logo và hình minh họa

Làm sạch đường nối giữa vùng logo và hình cô gái, để khoảng trắng tự nhiên, không kẻ viền phân cách. Giữ logo người dùng cung cấp, khổ 80 x 110 mm và vị trí QR/thông tin vé. PDF đã tạo giữ nguyên; mẫu này áp dụng cho PDF xuất mới hoặc được tạo lại bằng chức năng hiện có.

Sao lưu trước theo hướng dẫn 1.14.0, sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
```

Không có migration hoặc cấu hình mới. Nếu khởi động lại runserver, Ctrl+C tại đúng cửa sổ đang chạy rồi chạy lại, giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Đã kiểm tra render PDF và kiểm thử xuất vé/QR/khổ trang/giữ lịch sử; chưa in máy nhiệt thật. Kiểm tra một PDF mới trước khi in/gửi khách.
