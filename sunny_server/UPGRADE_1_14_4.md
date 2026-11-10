# 1.14.4 — Sửa QR mở đúng sản phẩm

Sửa hành vi 1.14.2: mỗi tem QR mở đúng trang chi tiết sản phẩm, không mở catalog chung. Ví dụ https://sn.hoianmemorieslands.com/souvenirs/p/<slug>/. Video giới thiệu ưu tiên và nút đổi Việt/Anh giữ nguyên. Khách không cần đăng nhập. Không dùng subdomain souvenirs.

SOUVENIRS_CATALOG_URL hiện có vẫn giữ nguyên URL catalog; ứng dụng suy ra URL sản phẩm từ đường dẫn này. Không cần sửa cấu hình Ubuntu/DNS. Không có migration mới. Sản phẩm phải được công khai để khách xem được.

## Cập nhật Ubuntu

Sao lưu theo hướng dẫn 1.14.0 trước khi cập nhật, sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Dừng đúng runserver hiện tại bằng Ctrl+C ở cửa sổ đang chạy, khởi động lại (không mở thêm tiến trình khi cổng 8000 đang bị chiếm):

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ web mở. Vào Souvenirs → Tem QR / In của từng sản phẩm, tải/in lại. Dòng QR mở phải kết thúc bằng /souvenirs/p/<slug>/, không phải /souvenirs/catalog/. QR cũ đã in/tải không tự đổi URL, cần thay tem. Không thể chuyển QR catalog cũ sang từng sản phẩm vì tất cả QR đó chứa cùng một địa chỉ và không có mã sản phẩm.

## Kiểm tra

Kiểm thử giải mã QR PNG của hai sản phẩm khác nhau, URL khác nhau và đúng slug; truy cập công khai không cần đăng nhập. Kiểm tra hồi quy Souvenirs bao gồm quyền, nội dung, song ngữ, video và thanh toán.
