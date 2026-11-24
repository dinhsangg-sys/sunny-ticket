# 1.18.1 — Quay về trang chính Sunny từ Souvenirs

Catalog và chi tiết sản phẩm có liên kết Trang chủ Sunny / Sunny home ở đầu trang, cùng liên kết quay về ở chân trang. Header co giãn trên điện thoại. Logo Souvenirs vẫn mở bộ sưu tập như trước.

Trên sunnygovn.com/www, liên kết dùng /discover/ cùng host và giao thức, nên không ép HTTPS khi SSL chưa hoàn tất. /discover/ luôn mở website giới thiệu, kể cả đã đăng nhập quản trị. Trên tên miền Souvenirs cũ hoặc host khác, liên kết dùng PUBLIC_SITE_URL (mặc định https://sunnygovn.com) để không mở nhầm catalog riêng.

## Cập nhật Ubuntu

Dừng đúng cửa sổ máy chủ bằng Ctrl+C, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ máy chủ mở và Ctrl+F5 trên trình duyệt. Không có migration mới so với 1.18.0. Nếu chưa chạy migration của 1.18.0 thì cần chạy manage.py migrate trước. Không đổi dữ liệu, giá, QR hoặc cấu hình ngân hàng. Cấu hình Nginx/DNS/SSL không thay đổi trong bản này.
