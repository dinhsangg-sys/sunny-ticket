# 1.11.0 — Đưa module bán vé tại quầy vào bản chính thức

Người dùng đã nghiệm thu nhánh codex/counter-sales. Phát hành trên main, giữ tag stable-1.10.13 và đánh dấu pre-1.11.0 tại mã nguồn main trước nâng cấp. Tag chỉ giữ mã nguồn, không thay thế sao lưu dữ liệu.

## Phạm vi

- Quầy riêng cho nhân viên: ngày và người bán do server xác định, khách lẻ, giá bán linh động, không hiển thị giá vốn, dùng mặc định; ghi thu đủ khi tạo booking mới.
- Nhập PDF/JPEG/PNG, vé dọc/ngang và nhiều vé trên trang có vùng phân cách rõ; OCR hỗ trợ, nhân viên kiểm tra lại trước khi xuất. Mẫu duyệt 80x110 mm, QR giữ nguyên và quét lại đầu ra.
- Chọn đúng số vé booking mới cho xuất; cảnh báo số import/đã chọn. QR không được gắn cho booking khác.
- Sửa booking, xác nhận điều chỉnh thu/hoàn, thay file, tạo phiên bản mới theo quyền; giữ lịch sử và bộ vé cũ. Việc ghi nhận hoàn tiền không gọi ngân hàng; chưa có phiếu hoàn độc lập theo ngày.
- PDF xem/tải/in và email khi cấu hình SMTP; chưa nghiệm thu máy in/SMTP thật. Không tự hủy QR cũ ở nhà cung cấp.
- Ticket Management: Báo cáo → Đối chiếu vé nhập / xuất. Trang nhân viên có menu dọc riêng. Đối chiếu bản gốc, từng phiên bản PDF và QR/thông tin.

## 1. Sao lưu bản chính trước khi cập nhật

Các lệnh dưới đây theo máy Ubuntu đã vận hành ở `/home/sunny-ticket`, SQLite và server cổng 8000. Không chạy trong `/home/sunny-ticket-counter-test`. Không sao chép database, private_counter hoặc tài khoản từ bản test sang bản chính.

Dừng server chính bằng Ctrl+C tại terminal đang chạy cổng 8000; không để tiến trình khác tiếp tục ghi. Tại thư mục gốc bản chính, dùng công cụ sao lưu hiện có **trước git pull**:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chỉ tiếp tục khi có dòng `Đã sao lưu và kiểm tra: ...`. ZIP nằm ngoài app, trong `/home/sunny-ticket-backups/`. Giữ đường dẫn ZIP này. Công cụ sao lưu SQLite, nguồn, cấu hình local và các thư mục bên trong app (gồm private_counter nếu có). Nếu database/media/COUNTER_PRIVATE_ROOT nằm ngoài app hoặc dùng PostgreSQL, cần sao lưu đúng database và storage đó riêng; công cụ SQLite không thay thế pg_dump. Không công khai ZIP có dữ liệu cá nhân.

## 2. Cập nhật main và database

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
sudo apt-get update
sudo apt-get install -y fonts-dejavu-core tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng
cd sunny_server
sudo .venv/bin/pip install -r requirements.txt
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
```

Migrate bổ sung role counter, quyền, bảng quản lý nguồn/PDF/QR và phiên bản (accounts 0002, legacy 0008–0010). Không xóa nghiệp vụ hay tự đánh dấu booking cũ đã thu. Không chạy reset_business_data, flush, xóa database hoặc khôi phục dữ liệu test. Nếu Git báo thay đổi local/xung đột, dừng và đối soát; không bỏ cấu hình local bằng reset/restore.

Nếu đang dùng static được Nginx phục vụ từ STATIC_ROOT, chạy collectstatic với đúng cấu hình triển khai trước khi restart dịch vụ. Các lệnh dưới tiếp tục cách runserver đang dùng tại máy này; bản phát hành không tự đổi proxy/systemd/database/settings đang hoạt động.

## 3. Khởi động và kiểm tra

```bash
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Giữ terminal mở, Ctrl+F5 trên domain chính. Không mở thêm tiến trình 8000 nếu đã có tiến trình đang nghe. Nếu đang dùng dịch vụ riêng, restart đúng tên dịch vụ hiện có thay vì chạy thêm runserver.

- Kiểm tra đăng nhập, booking cũ, doanh thu/công nợ và Báo cáo → Đối chiếu vé nhập / xuất.
- Nhân viên đăng nhập tại `/counter/` trên domain chính, dùng tài khoản role counter đã được quản trị tạo trên database chính.
- Chọn loại vé có giá vốn mặc định hợp lệ. Booking quầy mới ghi thu đủ; không tạo giao dịch giả trên dữ liệu thật chỉ để thử giao diện.
- Kiểm tra xem/tải PDF theo quyền; in đúng 80x110, một trang/mỗi vé. Email mặc định tắt đến khi có cấu hình gửi thực tế.

## Quyền và dữ liệu riêng

Quản trị gán `counter__view`, `counter__create` cho nhân viên quầy. Cấp riêng `counter__change`, `counter__settle_adjustment`, `counter__replace_tickets`, `counter__report` theo trách nhiệm. Quản lý xem toàn bộ cần view + report + `counter__report_all`. Superuser active xem toàn bộ; staff/role admin không tự có các quyền này. Không bật superuser cho nhân viên để thay cho cấp quyền.

Nguồn/PDF/QR nằm ở sunny_server/private_counter hoặc COUNTER_PRIVATE_ROOT; chỉ API có xác thực phục vụ, không public bằng static/media/proxy. Sao lưu cả database và thư mục này. Hướng dẫn nghiệp vụ chi tiết ở COUNTER_UPDATE_TEST.md là lịch sử phát triển đã được nghiệm thu; khi vận hành chính thức dùng main, thư mục/cổng chính theo tài liệu này.

## Quay lui

Giữ tag pre-1.11.0 và ZIP sao lưu trước nâng cấp. Nếu cần quay lui: dừng ghi, sao lưu thêm toàn bộ trạng thái sau nâng cấp, rồi khôi phục nhất quán mã nguồn + database + private files từ bản sao được chọn. Không ghi đè dữ liệu mới chỉ bằng đổi nhánh hoặc migrate ngược. Không tự thực hiện rollback vì có thể mất các giao dịch vừa phát sinh.

## Xác nhận trước phát hành

110 test backend đạt; kiểm tra Edge/Playwright với giao diện thật và API giả lập đạt cho quầy, sửa/thay vé, đếm số lượng, báo cáo, menu dọc và hồi quy báo cáo nhà cung cấp. Người dùng đã xác nhận bản test hoạt động. Chưa xác nhận cập nhật máy Ubuntu chính thức cho đến khi chạy các bước trên; GitHub main không tự triển khai lên máy Ubuntu.
