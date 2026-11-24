# 1.19.8 — Biểu tượng và địa chỉ trong footer

Thêm biểu tượng công ty, vị trí, thư và điện thoại; bỏ nhãn Email/Hotline bên ngoài, giữ tên hỗ trợ truy cập. Nới cột thông tin để địa chỉ một dòng trên màn hình từ 1100px; màn hình nhỏ tự xuống dòng, không tràn ngang. Áp dụng trang chính và Souvenirs. Thêm nút về đầu trang và điện thoại rung nhẹ ở góc dưới bên phải; bấm điện thoại mở cuộc gọi hotline qua tel:+84932548145. Tôn trọng cài đặt giảm chuyển động trên thiết bị. Không có migration mới.

Dừng ứng dụng bằng Ctrl+C ở đúng cửa sổ máy chủ, rồi chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ chạy máy chủ mở và Ctrl+F5 trên website.
