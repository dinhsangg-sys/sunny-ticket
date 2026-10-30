# 1.12.2 — Nội dung QR VietinBank và cấu hình Ubuntu

VietinBank yêu cầu nội dung chuyển khoản bắt đầu bằng `SEVQR`. Bản này tạo nội dung `SEVQR STP<mã phiên>` trong QR thật và hiển thị giống hệt ở màn hình phụ. Nhận diện VietinBank qua mã `VietinBank`, `ICB`, `970415` hoặc gateway `VietinBank`; ngân hàng khác không thêm tiền tố. Mã STP nội bộ giữ nguyên để đối chiếu webhook, kể cả khi ngân hàng thêm số tham chiếu phía trước hoặc trường `code` của SePay trống. Không thay đổi quy tắc kiểm tra chữ ký, tài khoản, số tiền, trạng thái phiên và chống ghi thu trùng.

Tài liệu: https://docs.sepay.vn/ket-noi-vietinbank.html

SePay vẫn tắt mặc định. QR thử vẫn là QR minh họa, không chuyển tiền thật. Không có migration mới so với 1.12.1. Dữ liệu và mẫu vé giữ nguyên. Các PDF đã xuất không bị tạo lại.

## 1. Sao lưu rồi cập nhật bản chính

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chờ thông báo **Đã sao lưu và kiểm tra**. Sau đó Ctrl+C tại terminal đang chạy bản chính cổng 8000 (nếu dùng dịch vụ, dừng đúng dịch vụ hiện có). Chạy từng lệnh:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo env SEPAY_ENABLED=0 .venv/bin/python manage.py migrate
sudo env SEPAY_ENABLED=0 .venv/bin/python manage.py check
```

Không chép database hoặc cấu hình của bản thử sang bản chính. Nếu cổng đang chiếm/xung đột Git, kiểm tra trước khi tiếp tục; không reset hoặc xóa dữ liệu.

## 2. Lưu cấu hình ngân hàng và khóa trên máy chủ

```bash
sudo nano /etc/sunny-sepay.env
```

Nếu file đã có khóa, giữ nguyên khóa HMAC mới đã tạo trên SePay; bổ sung/cập nhật các dòng còn thiếu. Mỗi biến chỉ một dòng, không để bản trùng ở cuối file:

```bash
SEPAY_ENABLED=0
SEPAY_MODE=live
SEPAY_WEBHOOK_SECRET='KHOA_HMAC_MOI_DUNG_NHU_TREN_SEPAY'
SEPAY_BANK_CODE=VietinBank
SEPAY_GATEWAY=VietinBank
SEPAY_ACCOUNT_NUMBER='SO_TAI_KHOAN_VIETINBANK_DA_LIEN_KET'
SEPAY_ACCOUNT_NAME='TEN_NGUOI_THU_HUONG_DUNG_TREN_NGAN_HANG'
SEPAY_TTL_SECONDS=900
```

Thay các giá trị hướng dẫn bằng thông tin thật trực tiếp trên Ubuntu. Không gửi khóa qua chat/GitHub, không dùng khóa thử đã xuất hiện trong ảnh. `SEPAY_GATEWAY` phải khớp giá trị gateway trong giao dịch SePay; VietinBank dự kiến là `VietinBank`, cần kiểm tra payload khi nghiệm thu.

Ctrl+O → Enter → Ctrl+X, rồi:

```bash
sudo chown root:root /etc/sunny-sepay.env
sudo chmod 600 /etc/sunny-sepay.env
```

Ứng dụng không tự đọc file env. Chạy với file đã nạp và **ép tắt SePay trong bước cập nhật này**:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; export SEPAY_ENABLED=0; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở theo cách vận hành hiện tại. Nếu sử dụng systemd/Gunicorn, nạp file qua cấu hình dịch vụ đang dùng và giữ SEPAY_ENABLED=0; không chạy thêm runserver vào cổng đã chiếm.

## 3. Chưa bật webhook ngay sau nâng cấp

Callback dự kiến `https://sn.hoianmemorieslands.com/api/sepay/webhook/`, xác thực HMAC-SHA256. Khi tính năng còn tắt, endpoint trả 503 là đúng. Cần kiểm tra proxy HTTPS trỏ đúng bản chính, chữ ký/timestamp, gateway/tài khoản thực tế trước khi bật và nghiệm thu giao dịch thật được chủ tài khoản cho phép. Không chuyển tiền bằng QR cũ thiếu SEVQR; mở lại phiên để lấy QR mới sau cập nhật. Không nhập nội dung chuyển khoản bằng tay nếu có thể quét QR mới.

## Kiểm thử

Kiểm tra tự động: nội dung QR khớp màn hình phụ; các bí danh VietinBank; ngân hàng khác không đổi; webhook đọc nội dung có SEVQR và tham chiếu ngân hàng, code trống; thông báo trùng không ghi thu lại. Chưa thực hiện giao dịch ngân hàng thật hoặc triển khai Ubuntu từ phiên làm việc này.
