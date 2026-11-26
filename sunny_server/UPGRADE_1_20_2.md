# 1.20.2 — Chỉ hiển thị Giá từ và chọn loại vé giới thiệu

Thẻ dịch vụ chỉ hiển thị **Giá từ … đ / From … đ**, bỏ tên loại vé và dòng Tùy ngày sử dụng.

## Chọn một giá bất kỳ làm giá giới thiệu

Vào **Quản trị → Dịch vụ online → mở dịch vụ**:

1. Ở **Cách chọn giá giới thiệu**, chọn **Chọn một lựa chọn vé**.
2. Ở **Loại vé hiển thị Giá từ**, chọn loại vé muốn giới thiệu, rồi lưu. Không bắt buộc là loại có giá thấp nhất; ví dụ chọn HIGH 700.000 đ vẫn hiển thị 700.000 đ dù ECO có giá 300.000 đ.
3. Giá lấy từ bảng giá online hợp lệ của chính loại được chọn. Nếu loại đó có nhiều kỳ giá, lấy mức thấp nhất còn đặt được của loại đó; không tự đổi sang loại vé khác. Giá khi khách chọn ngày vẫn tính theo ngày/loại thực tế.

Vẫn có hai chế độ tùy chọn khác: tự lấy giá thấp nhất hoặc dùng vé mặc định. Không tự thay lựa chọn quản trị đã lưu.

Không có migration mới so với 1.20.1. Nếu bỏ qua bản cũ, lệnh migrate dưới đây sẽ áp dụng các migration còn thiếu.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C và sao lưu dữ liệu theo quy trình đang dùng trước khi cập nhật.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ ứng dụng mở; Ctrl+F5 trên website. Kiểm tra bằng SePay test và hộp thư thử trước khi nhận đơn thật. Khi triển khai qua dịch vụ production, dùng lệnh khởi động lại dịch vụ đang vận hành thay vì mở thêm server trên cổng đã chiếm.
