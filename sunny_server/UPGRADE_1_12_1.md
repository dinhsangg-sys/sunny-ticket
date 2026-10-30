# 1.12.1 — Lưu tích hợp SePay, chưa kích hoạt thanh toán thật

Người dùng đã hoàn tất thử nghiệm luồng SePay. Đưa mã vào bản chính để giữ kết quả; mặc định `SEPAY_ENABLED=0`. Chưa có tài khoản/ngân hàng liên kết nên không bật QR chuyển khoản thật, không cấu hình webhook thật và không tự nhận tiền qua SePay.

Khi tắt, màn hình bán vé tiếp tục ba phương thức Tiền mặt / Thẻ thanh toán / Chuyển khoản và xác nhận thực thu thủ công như 1.12.0. Nút QR SePay không hiện; webhook không ghi thu. Không có thay đổi mẫu vé hoặc quy tắc phân quyền quầy.

## Cập nhật Ubuntu bản chính

Không chép database hoặc file cấu hình SePay của bản thử sang bản chính. Không nạp `/etc/sunny-sepay-test.env` khi chạy bản chính. Sao lưu tại thư mục bản chính trước:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chỉ tiếp tục khi có thông báo **Đã sao lưu và kiểm tra**. Giữ đường dẫn ZIP để phục hồi nếu cần.

Dừng tiến trình bản chính cổng 8000 bằng Ctrl+C ở cửa sổ đang chạy. Nếu đang dùng dịch vụ, dùng đúng tên dịch vụ thực tế; không chạy thêm tiến trình vào cổng đang chiếm. Sau đó chạy từng lệnh:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo env SEPAY_ENABLED=0 .venv/bin/python manage.py migrate
sudo env SEPAY_ENABLED=0 .venv/bin/python manage.py check
sudo env SEPAY_ENABLED=0 .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Migration 0012 chỉ thêm bảng phiên QR và nhật ký giao dịch, không xóa/chuyển đổi dữ liệu booking. Nếu có cơ chế khởi động dịch vụ riêng, đặt `SEPAY_ENABLED=0` trong cấu hình của dịch vụ đó và khởi động lại bằng cơ chế hiện có. Lệnh runserver trên phù hợp cách vận hành hiện tại; giữ terminal mở. Không đụng tiến trình thử cổng 8001.

Kiểm tra trang bán vé: không có nút QR SePay; tạo booking vẫn chờ xác nhận thực thu. Kiểm tra báo cáo và in vé như trước. Nếu Git báo xung đột hoặc cổng đang sử dụng, dừng để kiểm tra, không xóa dữ liệu hoặc chạy reset.

## Khi đã có tài khoản SePay

Tiếp tục liên kết ngân hàng, cấu hình secret HMAC mới trên Ubuntu, callback HTTPS và thử đối soát giao dịch thật được chủ tài khoản cho phép trước khi bật `SEPAY_ENABLED=1` / `SEPAY_MODE=live`. Không tái sử dụng khóa thử đã xuất hiện trong ảnh chụp. Hướng dẫn mô phỏng và yêu cầu tích hợp tại SEPAY_TEST.md.

## Xác minh

130 kiểm tra backend và các kiểm thử trình duyệt về QR/màn hình phụ, xác nhận thủ công, tạo vé, mẫu email, chỉnh booking và báo cáo đã đạt trên mã tích hợp. Người dùng xác nhận bản thử hoạt động. Chưa xác nhận với tài khoản SePay/ngân hàng thật; chưa triển khai máy chủ Ubuntu trực tiếp từ phiên làm việc này.
