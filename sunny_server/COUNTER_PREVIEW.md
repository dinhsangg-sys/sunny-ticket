# Module quầy — bản thử nghiệm riêng

## Bản bổ sung nhập vé, PDF/in và email

Đọc [COUNTER_TICKETS_TEST.md](COUNTER_TICKETS_TEST.md) để cập nhật bản bổ sung. Có migration mới 0009 và thư viện xử lý PDF/QR; chỉ cập nhật thư mục `/home/sunny-ticket-counter-test`, không đưa vào main hoặc thư mục live. Các mô tả chưa có chức năng ở phần phạm vi cũ dưới đây là lịch sử bản quầy đầu tiên.

## Bản sửa chạy thử HTTP nội bộ

Đã sửa trường hợp truy cập bằng HTTP qua IP/cổng 8001 không lưu được giá vốn hoặc không tạo được booking quầy vì trình duyệt thiếu crypto.randomUUID trong ngữ cảnh không bảo mật. Script UUID tương thích được nạp trước các luồng nghiệp vụ, dùng crypto.getRandomValues để tạo UUID v4; không thay hàm native nếu trình duyệt đã hỗ trợ, không dùng Math.random.

Đã kiểm tra frontend thật trên origin HTTP: lưu giá vốn và tạo booking quầy thành công; các trường hợp lỗi/xung đột trước đó vẫn giữ kiểm tra. Kiểm thử riêng xác nhận định dạng/bit UUID v4, mẫu 1000 mã không trùng và việc nạp lặp không thay hàm đã có.

Lấy bản sửa tại **thư mục thử nghiệm** bằng một phiên SSH khác, không tạo thêm server trên cùng cổng:

```bash
cd /home/sunny-ticket-counter-test
sudo git pull --ff-only origin codex/counter-sales
```

Giữ terminal server 8001 đang chạy, ghi lại nội dung chưa lưu rồi Ctrl+F5 trên trình duyệt, nhập lại form và lưu. Chỉ thay frontend nên không cần migration hoặc reset dữ liệu cho bản sửa này. Nhánh main và tag stable giữ nguyên.

Nhánh: `codex/counter-sales`. Chưa gộp vào main hoặc triển khai Ubuntu. Tag ổn định `stable-1.10.13` giữ nguyên; main vẫn là bản ổn định kèm công cụ sao lưu. Chưa xác nhận đã sao lưu dữ liệu web thật.

## Phạm vi đã làm

- Tài khoản role `counter` đăng nhập qua trang hiện có rồi được chuyển đến `/counter/`.
- Màn hình riêng chỉ tải danh mục vé đang hoạt động và tối đa 100 booking của chính người đó. Không tải workspace hoặc script giao diện nội bộ.
- Chọn loại vé, số lượng, nhập giá bán **mỗi vé** theo đồng (0 hợp lệ), tick VAT và ghi chú. Có tìm nhanh vé và tổng tiền bán.
- Ngày booking lấy từ `timezone.localdate()` phía server, giờ Việt Nam; không có ô chọn ngày. POST cố gửi date bị từ chối.
- `customerType=retail`; trường agent và customerName ghi tên đăng nhập, không tạo hồ sơ đại lý mới. Lưu counterSellerId và thời gian để truy vết, không cho client tự gửi người bán.
- Giá vốn/nguồn do server lấy từ mặc định còn hiệu lực của vé và nhà cung cấp còn hoạt động. Nếu có nhiều dòng mặc định, ưu tiên ngày bắt đầu mới nhất như luồng hiện có; nếu cùng mức ưu tiên thì chặn để quản trị xác định lại. Không tự chọn nguồn khi không có mặc định.
- Không trả giá vốn, mức giá vốn, nguồn, lợi nhuận hoặc vatBase/vatAmount cho màn hình quầy. Đây là kiểm soát API, không chỉ ẩn bằng CSS.
- VAT dùng logic hiện tại của hệ thống: bật checkbox sẽ dùng rate 15 và `calculate_booking` hiện có (tính VAT trên chênh lệch). Chưa thêm cách tính thuế mới hoặc cho nhân viên chỉnh thuế suất.
- Lưu bằng transaction/CAS và mã lần lưu chống tạo trùng. Khi lỗi mạng hoặc xung đột, giữ thông tin và thử lại cùng mã. Không tự tạo mới một booking khác sau lỗi chưa rõ kết quả.
- Chưa tự ghi thu tiền: booking mới không có payments. Chưa thêm sửa/xóa booking hoặc thanh toán cho nhân viên quầy. Nội bộ vẫn thấy booking trong dữ liệu/báo cáo hiện tại, loại khách lẻ và tên đăng nhập ở cột khách hàng/đại lý.

## Tài khoản và quyền

Có migration thêm lựa chọn role `counter` và quyền `counter.view`, `counter.create`. Sau migrate, chạy `python manage.py setup_counter_group` để chuẩn bị nhóm Nhân viên bán vé tại quầy. Lệnh không tạo user hoặc sửa booking.

Quản trị tối cao tạo user trong admin, chọn role Nhân viên bán vé tại quầy, giữ is_staff/is_superuser tắt và gán nhóm trên. Không cấp các quyền nội bộ/workspace cho nhân viên quầy. Role counter bị chặn tại các API state, operations, quote, bulk receipt/supplier hiện có; màn hình quầy chỉ cho xem dữ liệu của bản thân.

## Thử trên môi trường riêng

Chỉ chạy trong thư mục thử nghiệm mới, không dùng `/home/sunny-ticket` đang vận hành. Database SQLite đặt trong thư mục checkout riêng nên không dùng database live nếu không cấu hình trỏ về nó.

```bash
git clone --branch codex/counter-sales https://github.com/dinhsangg-sys/sunny-ticket.git /home/sunny-ticket-counter-test
cd /home/sunny-ticket-counter-test/sunny_server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py setup_counter_group
.venv/bin/python manage.py runserver 0.0.0.0:8001
```

Dùng IP máy Ubuntu trong LAN và cổng 8001 để mở trang thử nghiệm. Môi trường mới có dữ liệu trống: cần khai báo vé, nhà cung cấp và giá vốn mặc định, sau đó tạo user quầy để test. Chưa mở proxy/domain chính vào bản thử nghiệm. Nếu cần thử bằng bản sao dữ liệu thật, trước tiên xác nhận ZIP sao lưu đã hoàn tất, chỉ phục hồi vào thư mục test và giữ riêng tư; không ghi đè database đang chạy.

## Kiểm thử và điểm cần nghiệm thu

84 test Django đầy đủ đạt, gồm 7 ca mới: ngày Việt Nam khi UTC sang ngày khác, đúng người bán/khách lẻ/giá vốn/VAT, không rò giá vốn qua JSON, chặn chèn trường, kiểm tra số lượng/giá, mặc định thiếu/trùng/hết hoạt động, quyền/CSRF, xem đúng bản thân, idempotency và xung đột không ghi đè. Playwright/Edge headless với API giả lập xác nhận form không có ngày chọn, đúng người bán, tìm vé, giá linh động, checkbox VAT, ghi chú, payload chỉ có trường được phép và lịch sử riêng.

Chưa nghiệm thu bộ gõ thực tế/quy trình quầy/dữ liệu Ubuntu. Trước khi đưa vào main: xác nhận cách nhập giá mỗi vé, quy tắc VAT hiện tại, giá vốn mặc định của các vé bán và quy trình thu tiền. Chỉ triển khai sau khi sao lưu dữ liệu thật và chấp nhận bản thử nghiệm. Rollback migration/database không được thực hiện tự động; không xóa booking phát sinh sau triển khai để quay về bản cũ.
