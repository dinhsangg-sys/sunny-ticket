# SePay — bản thử riêng, chưa bật ngân hàng thật

Luồng thử đã được người dùng xác nhận hoạt động và đưa vào bản 1.12.1. Tính năng trên bản chính vẫn tắt mặc định, chưa kích hoạt ngân hàng thật. Nhánh `codex/sepay` giữ hướng dẫn mô phỏng dưới đây để tham khảo. Không chép database thử lên bản chính. Cần migration 0012; không cần gói Python mới. Xem UPGRADE_1_12_1.md khi cập nhật bản chính.

## Cài trên môi trường thử Ubuntu

Chỉ thao tác thư mục thử `/home/sunny-ticket-counter-test`. Dừng tiến trình **8001** đang chạy trước khi khởi động lại; giữ nguyên bản chính cổng 8000. Sao lưu dữ liệu thử nếu cần giữ lại. Chạy từng lệnh:

```bash
cd /home/sunny-ticket-counter-test
sudo git pull --ff-only origin codex/sepay
cd /home/sunny-ticket-counter-test/sunny_server
sudo .venv/bin/python manage.py migrate
```

Nếu Git báo có thay đổi cục bộ hoặc không thể fast-forward, dừng tại đó và kiểm tra; không dùng reset để bỏ dữ liệu/cấu hình.

Tạo file cấu hình riêng bằng `sudo nano /etc/sunny-sepay-test.env`, điền:

```bash
SEPAY_ENABLED=1
SEPAY_MODE=test
SEPAY_WEBHOOK_SECRET='THAY_BANG_CHUOI_NGAU_NHIEN_TOI_THIEU_32_KY_TU'
SEPAY_BANK_CODE=TestBank
SEPAY_GATEWAY='Test Bank'
SEPAY_ACCOUNT_NUMBER=0123456789
SEPAY_ACCOUNT_NAME='SUNNY TEST'
SEPAY_TTL_SECONDS=900
```

Tự tạo secret bằng `openssl rand -hex 32` và nhập trực tiếp vào file trên máy chủ. Không gửi secret qua chat, không đưa file này lên GitHub. Các thông tin ngân hàng trên là giả để thử. Đặt quyền:

```bash
sudo chmod 600 /etc/sunny-sepay-test.env
sudo chown root:root /etc/sunny-sepay-test.env
```

Ứng dụng không tự đọc file `.env`. Khởi động với cấu hình đã nạp:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay-test.env; set +a; cd /home/sunny-ticket-counter-test/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8001'
```

Giữ cửa sổ này mở trong lúc thử. Đây là máy chủ thử; không thay cách vận hành bản chính bằng lệnh này.

## Thử hai màn hình khi chưa liên kết ngân hàng

1. Windows: chọn **Win + P → Extend**. Đăng nhập nhân viên tại trang thử cổng 8001.
2. Tạo booking chờ thanh toán, chọn **QR chuyển khoản / Màn hình phụ** trên dòng booking. Cho phép popup nếu trình duyệt chặn.
3. Kéo cửa sổ QR sang màn hình phụ, bấm **Toàn màn hình**. Số tiền do server tính từ booking. Chế độ test dùng QR minh họa, **không thể chuyển tiền ngân hàng**.
4. Mở cửa sổ SSH khác. Thay mã STP trong lệnh dưới bằng nội dung đang hiển thị trên QR:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay-test.env; set +a; cd /home/sunny-ticket-counter-test/sunny_server; exec .venv/bin/python manage.py simulate_sepay_payment STP123456789012345678'
```

Lệnh gọi webhook có chữ ký ngay trong ứng dụng, không gọi ngân hàng. Chỉ cho phép phiên `test` còn hạn; bị chặn khi `live`. Booking thử sẽ ghi thu **SePay (TEST)**. Không chạy trên database kinh doanh thật.

5. Trong khoảng 3 giây, cả hai màn hình hiển thị đã thanh toán; nhân viên có thể tiếp tục tạo PDF/in/gửi vé theo quyền được cấp. Hệ thống không tự gửi email hoặc tự in.
6. Thử hủy phiên QR rồi thu tiền mặt/thẻ. Thử sửa booking: phiên QR cũ bị hủy. Khi mạng lỗi, màn hình phụ ẩn QR và không tự kết luận đã thu tiền.

Muốn đổi sang thu thủ công khi QR còn hạn, vào **Xác nhận đã thanh toán → Hủy phiên QR để đổi cách thu**. Hủy/hết hạn trên phần mềm **không thu hồi QR đã chụp trong ứng dụng ngân hàng**; giao dịch đến sau cần đối soát.

## Bật thanh toán thật sau khi đã liên kết ngân hàng

Với VietinBank, từ 1.12.2 QR và màn hình phụ tự dùng nội dung `SEVQR STP<mã phiên>`. Không bỏ `SEVQR`. Xem UPGRADE_1_12_2.md để lưu cấu hình riêng trên Ubuntu; không nạp cấu hình thử vào bản chính.

Chưa được kiểm chứng với giao dịch ngân hàng thật. Chỉ bật sau khi thử trên dữ liệu riêng và kiểm tra cấu hình:

- Liên kết tài khoản ngân hàng trong SePay; khai báo đúng mã ngân hàng, `gateway`, số tài khoản và tên nhận. Đổi `SEPAY_MODE=live` mới tạo QR chuyển khoản thật qua `vietqr.app`.
- Cấu hình webhook **HMAC-SHA256**, cùng secret riêng đã lưu trên máy chủ. Endpoint `https://TEN-MIEN-THU/api/sepay/webhook/` phải truy cập được từ SePay. Địa chỉ LAN `172.16.150.157:8001` không phải callback công khai; cần cấu hình HTTPS/proxy đúng môi trường thử trước. Không đổi proxy bản chính khi chưa xác định cấu hình đang chạy.
- Chỉ nhận giao dịch tiền vào. Nội dung QR là `STP` + 18 chữ số. Nếu bật lọc mã phía SePay, phải cho phép đúng định dạng này; nếu chưa cấu hình định dạng, không loại bỏ giao dịch thiếu trường `code` vì phần mềm có đọc mã từ `content`.
- Header bắt buộc `X-SePay-Signature` và `X-SePay-Timestamp`; bản này không nhận xác thực kiểu API Key. Đồng hồ máy chủ cần đúng giờ.
- Nút gửi thử của nhà cung cấp có thể dùng `id=0`: chỉ kiểm tra kết nối, không ghi thu. Cần một giao dịch thật được chủ tài khoản cho phép để nghiệm thu trước khi dùng kinh doanh.

Hệ thống kiểm tra chữ ký, thời gian yêu cầu, mã phiên, ngân hàng, tài khoản, đúng số tiền còn nợ và nội dung booking. Trùng ID giao dịch không ghi thu lần hai. Sai/thừa/thiếu tiền, phiên đã hủy, booking đã sửa hoặc không xác định được mã sẽ lưu để đối soát, không tự hoàn thành booking. Chỉ hỗ trợ thanh toán đủ trong một lần chuyển cho mỗi phiên. Webhook đến chậm vẫn có thể được ghi nhận nếu thời điểm ngân hàng nằm trong hạn và booking/phiên chưa đổi.

Quản trị xem giao dịch cần kiểm tra tại **Quản trị → Legacy → Se pay transactions**, hoặc `/admin/legacy/sepaytransaction/?state=review`. Danh sách chỉ đọc; không có nút tự duyệt thu tiền. Dữ liệu thử không bị di chuyển tự động vào bản chính.

## Tài liệu nhà cung cấp

- [Chữ ký HMAC](https://developer.sepay.vn/vi/sepay-webhooks/xac-thuc)
- [Tạo QR và form thanh toán](https://developer.sepay.vn/vi/sepay-webhooks/tao-qr-va-form-thanh-toan)
- [Payload, phản hồi và gửi lại webhook](https://docs.sepay.vn/tich-hop-webhooks.html)

Kiểm thử trong dự án dùng dữ liệu giả, không chuyển tiền và không gửi email thật. Khóa tích hợp và tài khoản nhận tiền được cấu hình trên máy chủ, không nhập qua màn hình nhân viên.

Kết quả kiểm tra: 130 bài kiểm tra backend đạt; migration khớp model. Kiểm thử trình duyệt kiểm tra popup/màn hình phụ, token, lỗi mạng/phục hồi, trạng thái thanh toán tự cập nhật, cùng các luồng xác nhận thủ công, tạo vé, chỉnh booking và điều hướng báo cáo. Chưa xác nhận kết nối SePay thật, máy in thật hoặc cấu hình proxy Ubuntu thực tế.
