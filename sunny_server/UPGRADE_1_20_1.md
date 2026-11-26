# 1.20.1 — Giá giới thiệu trên thẻ dịch vụ

Thẻ dịch vụ ở trang chủ và danh sách trải nghiệm có giá **Giá từ … đ / From … đ** ở góc dưới bên phải, kèm loại vé và ghi chú tùy ngày sử dụng.

## Cách chọn giá giới thiệu

Vào **Quản trị → Dịch vụ online → mở dịch vụ**:

- **Giá giới thiệu trên thẻ → Tự chọn giá thấp nhất đang có thể đặt** (mặc định): chọn giá thấp nhất hợp lệ trong bảng online, cho ngày sử dụng từ hôm nay đến 365 ngày tới.
- **Dùng loại vé mặc định**: lấy giá từ loại vé mặc định của dịch vụ.
- **Chọn một lựa chọn vé**: ở trường **Loại vé làm giá giới thiệu**, chọn loại muốn giới thiệu (ví dụ ECO · Trẻ em). Danh sách chỉ có lựa chọn thuộc dịch vụ đang sửa. Lưu dịch vụ, tạo các lựa chọn và giá online trước, rồi quay lại chọn nếu đây là dịch vụ mới.

Không nhập một giá quảng cáo rời với bảng giá online. Giá hết hạn, loại vé ngừng bán, kỳ giá trùng hoặc không có cấu hình giá vốn hợp lệ sẽ không được dùng. Nếu loại được chọn không còn giá hợp lệ thì ẩn giá, không tự chuyển sang một loại khác. Giá khi khách chọn ngày/đặt vé vẫn do máy chủ tính theo ngày và loại thực tế; không thay đổi tổng thanh toán hay đơn cũ.

## Cập nhật Ubuntu

Có migration mới **online.0007_service_card_price**. Dừng đúng cửa sổ ứng dụng bằng Ctrl+C và sao lưu dữ liệu như quy trình hiện tại trước khi cập nhật.

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
