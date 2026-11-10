# 1.14.2 — QR mở catalog trên tên miền sn

QR tạo mới từ trang in tem sản phẩm mở trực tiếp https://sn.hoianmemorieslands.com/souvenirs/catalog/, không dùng subdomain souvenirs. Tất cả tem mở cùng catalog; khách chọn sản phẩm trong bộ sưu tập để xem chi tiết song ngữ. Catalog và trang sản phẩm không yêu cầu đăng nhập; quản trị và bán hàng vẫn có phân quyền.

Không cần DNS/proxy/SSL riêng cho souvenirs. Bản ghi DNS đã tạo có thể giữ nguyên, ứng dụng không dùng nó cho QR mới. SOUVENIRS_PUBLIC_ORIGIN cũ giữ nguyên để không làm ảnh hưởng định tuyến trang quản lý. Không đổi biến đó thành tên miền sn. SOUVENIRS_ENABLED=1 vẫn cần thiết. Nếu muốn thay URL catalog sau này, dùng SOUVENIRS_CATALOG_URL.

QR đã in là ảnh chứa URL cũ nên không tự thay đổi. Cần tải/in lại QR sau cập nhật. Khi tên miền cũ chưa hoạt động thì QR cũ không thể tự chuyển hướng.

Sao lưu trước theo hướng dẫn 1.14.0, sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Không có migration mới. Dừng đúng runserver hiện tại bằng Ctrl+C tại cửa sổ đang chạy rồi khởi động lại, không mở thêm tiến trình trên cổng 8000:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Trong quản lý Souvenirs mở tem QR và tải/in lại. Quét kiểm tra bằng điện thoại. Sản phẩm cần bật Hiển thị cho khách và cho phép bán để xuất hiện trong catalog. Catalog trống không phải lỗi QR nếu chưa công bố sản phẩm nào.
