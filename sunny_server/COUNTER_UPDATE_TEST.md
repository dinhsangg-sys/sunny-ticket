# Bản test: thanh toán, sửa booking và đối chiếu vé

Chỉ nhánh `codex/counter-sales`. Không thay main, stable hoặc dữ liệu máy chủ chính.

## Cập nhật

Dừng terminal chạy bản test cổng 8001 bằng Ctrl+C rồi chạy:

```bash
cd /home/sunny-ticket-counter-test
sudo git pull --ff-only origin codex/counter-sales
cd sunny_server
sudo .venv/bin/pip install -r requirements.txt
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8001
```

Giữ terminal mở. Ctrl+F5 tại `/counter/`. Migration 0010 thêm quyền và phiên bản bộ vé, không xóa dữ liệu. Sao lưu database cùng `private_counter` trước khi nâng cấp nơi chứa vé quan trọng.

## Cấp quyền

Trong Quản trị → Người sử dụng hoặc Nhóm → quyền của Legacy/Workspace:

| Quyền | Chức năng |
|---|---|
| `counter__view` | Vào quầy, xem danh sách và chi tiết booking của mình |
| `counter__create` | Tạo booking, nhập/xuất/in/gửi vé theo chức năng hiện có |
| `counter__change` | Sửa loại vé, số lượng, giá bán, VAT, email, ghi chú booking của mình |
| `counter__settle_adjustment` | Xác nhận đã thu thêm/hoàn lại khi sửa tổng tiền |
| `counter__replace_tickets` | Upload bộ vé thay thế hoặc tạo phiên bản mới từ bộ cũ; cần có quyền create |
| `counter__report` | Mở báo cáo đối chiếu vé của mình |
| `counter__report_all` | Khi có report và view, xem báo cáo của tất cả nhân viên; không cấp quyền sửa booking người khác |

Quyền mới không tự cấp cho nhân viên hiện có. Superuser được truy cập. Không cấp staff/superuser chỉ để bán vé.

## Thử nghiệp vụ

1. Tạo booking quầy mới: hệ thống ghi khoản thu bằng toàn bộ doanh thu cùng giao dịch lưu; bấm lại cùng request không nhân đôi booking hoặc khoản thu. Booking cũ không tự đánh dấu đã thu. Booking thông thường không đổi quy tắc.
2. Chọn **Chi tiết / Sửa**: xem tổng tiền, đã thu, còn nợ và lịch sử. Người có quyền sửa đổi các trường cho phép. Ngày/người bán/giá vốn không cho sửa ở quầy. Đổi loại vé lấy giá vốn mặc định theo ngày booking; chỉ sửa ghi chú/giá bán giữ giá vốn đã chốt.
3. Nếu tổng tiền đổi, cần quyền điều chỉnh thanh toán và xác nhận thu thêm/hoàn tiền thực tế. Hệ thống không gọi ngân hàng hay hoàn tiền tự động. Khoản thu thêm được ghi mới; khi hoàn, số thu hiện hành giảm và lịch sử giữ đầy đủ các khoản thu trước/sau cùng số hoàn, ngày/người sửa. Đây là điều chỉnh booking; chưa có phiếu hoàn tiền độc lập hoặc sổ hoàn theo ngày riêng. Không xác nhận nếu chưa thực thu/hoàn. Sửa từ phiên cũ bị chặn.
4. Booking đã sửa làm bộ vé trước đó thành phiên bản lưu trữ, không gửi email bộ cũ. Trong **Nhập / In / Gửi vé**, người có quyền chọn **Tạo phiên bản vé mới** để dùng lại QR và sửa thông tin, hoặc upload file gốc mới. Bộ cũ giữ nguyên. Một QR không được dùng cho booking khác, kể cả QR của phiên bản đã thay. QR cũ không tự vô hiệu tại nhà cung cấp; cần đối soát trước khi giao lại vé.
5. Chọn **Báo cáo đối chiếu vé** hoặc `/counter/report/`. Lọc ngày, mã booking, nhân viên, kết quả. Mỗi bộ import/phiên bản là một dòng; chưa import vẫn có dòng. Mở **Xem / Quét lại PDF** để xem file gốc và file xuất cạnh nhau, chọn từng vé/trang.
6. Danh sách so thông tin đã lưu và hash file. Chi tiết đọc trực tiếp PDF đầu ra và quét QR, đối chiếu với QR và trường thông tin ghi nhận khi import: hạn, gói, PARK/SHOW, mã vé, đại lý. Khớp / khác biệt / thiếu dữ liệu được đánh dấu theo từng trường; thông tin đã chủ động sửa cũng được đánh dấu khác. Số lượng so riêng với booking hiện tại; bản lưu trữ có thể khác số lượng hiện tại.

Báo cáo không xác minh hiệu lực QR tại cổng soát vé. OCR nguồn có thể sai, cần nhìn file gốc. Mỗi trang chỉ một QR. File nhiều nguồn mới có thể xem từng nguồn; bộ nhiều file đã import từ bản trước chỉ có ZIP gốc để tải, vì bản cũ chưa giữ từng nguồn riêng. PDF cũ vẫn có thể tải để đối soát, vì vậy không dùng bản lưu trữ để giao lại khách.

## Kiểm tra

96 test backend đạt, gồm kiểm tra thanh toán/idempotency, quyền sửa/thu hoàn, lịch sử và xung đột phiên bản, QR/PDF thực tế, sửa thông tin được phát hiện, phân quyền báo cáo toàn bộ, quyền thay vé và giữ bản cũ. Playwright/Edge với frontend thật và API giả lập đạt luồng tạo booking, nhập/xuất PDF, xác nhận điều chỉnh và đối chiếu hai khung. Chưa kiểm thử máy in hoặc SMTP thật; cấu hình email vẫn theo COUNTER_TICKETS_TEST.md.
