# 1.12.0 — Xác nhận thanh toán quầy và mẫu email gửi vé

Thay quy tắc tự ghi thu đủ khi tạo booking quầy bằng luồng chờ thanh toán → nhân viên xác nhận đã nhận đủ tiền → hoàn thành. Áp dụng cho booking quầy tạo mới sau cập nhật. Không sửa/xóa khoản thu hay phân loại lại các booking đã có từ bản cũ.

## Vận hành

1. Trong Bán vé tại quầy, chọn **Tiền mặt / Thẻ thanh toán / Chuyển khoản**; mặc định Tiền mặt. Nhập loại vé, số lượng, giá và thông tin khác như trước. Bấm **Lưu booking chờ thanh toán**.
2. Booking được lưu chưa có khoản thu, hiển thị Chờ thanh toán và phương thức dự kiến. Ngày/người bán/giá vốn vẫn do server xác định. Có thể import và kiểm tra vé gốc trước, nhưng chưa xuất/in/gửi PDF.
3. Sau khi thực nhận đủ tiền, bấm **Xác nhận đã thanh toán** trên danh sách, hoặc **Xác nhận thanh toán booking** trong cửa sổ vé. Hộp thoại hiển thị tổng/đã thu/cần thu và cho chọn lại đúng phương thức trước khi ghi nhận.
4. Bấm **Xác nhận đã nhận đủ tiền**. Hệ thống ghi phần còn thiếu theo tổng tiền hiện tại, phương thức, ngày/giờ và người xác nhận; chuyển booking sang hoàn thành. Để sau/đóng cửa sổ không ghi thu.
5. Tiếp tục kiểm tra và xuất/in/gửi vé. Bản nháp import không bị lỗi phiên bản chỉ vì xác nhận thu tiền; các ô OCR đang sửa được giữ khi xác nhận trong cửa sổ vé. Bấm lặp hoặc thử lại sau mất kết nối không nhân đôi khoản thu.

Đây là ghi nhận thu tiền thủ công, không tự trừ thẻ/kiểm tra giao dịch ngân hàng. Không xác nhận nếu chưa nhận tiền. Booking giá 0 vẫn cần xác nhận hoàn thành; không tạo khoản thu 0 giả.

## Quyền và sửa booking

Người có counter__view + counter__create được xác nhận cho booking của mình; không cần quyền thanh toán mới. Superuser có thể đối soát. Người chỉ xem không xác nhận được, không xem/sửa booking nhân viên khác qua API.

Khi booking mới còn chờ thanh toán, người có quyền sửa được đổi thông tin/giá/phương thức theo phạm vi đã cấp mà không tự thu tiền. Thông tin thay đổi làm lần xác nhận dùng phiên bản cũ bị chặn, phải mở lại kiểm tra số tiền. Sau khi hoàn thành không sửa phương thức của khoản thu đã ghi nhận ở form quầy; điều chỉnh tổng tiền vẫn cần quyền thu/hoàn và xác nhận thực tế như trước. Mỗi khoản thu thêm giữ phương thức trong lịch sử.

Các booking cũ giữ nguyên tiền đã thu và trạng thái nghiệp vụ trước đó. Phương thức lịch sử chưa được ghi nhận hiển thị Chưa ghi nhận, không tự gán Tiền mặt cho dữ liệu cũ. Booking thường ngoài quầy giữ quy tắc thanh toán hiện có.

## Cập nhật bản chính

Sao lưu database và private_counter theo UPGRADE_1_11_0.md trước nâng cấp nơi có dữ liệu quan trọng. Dừng tiến trình cổng 8000 bằng Ctrl+C tại terminal đang chạy, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Giữ terminal mở và Ctrl+F5. Nếu đang dùng dịch vụ thì restart đúng dịch vụ, không mở thêm tiến trình 8000. Cần migrate 0011 để thêm nơi lưu tiêu đề/nội dung email thực tế. Không cần thư viện mới khi đã ở 1.11.x. Không reset dữ liệu hoặc sao chép database test.

## Kiểm tra

Backend kiểm tra mặc định/cả ba phương thức, không tự ghi thu khi tạo/sửa chờ thanh toán, xác nhận rõ ràng, số tiền từ server, từ chối phiên cũ/injection, quyền sở hữu/CSRF, chống ghi trùng, ngày/người xác nhận, giá 0, bảo toàn booking cũ và chặn xuất/email trước thanh toán. Giao diện thật/API giả lập kiểm tra chọn phương thức, chờ/hoàn thành, Để sau, bấm hai lần, xác nhận trong cửa sổ vé và giữ dữ liệu đang sửa. Không có giao dịch thẻ/ngân hàng thật trong quá trình thử.

## Mẫu email gửi vé

- Mở **Mẫu email gửi vé** ở menu trái của Ticket Management hoặc trang nhân viên; đường dẫn `/counter/email-template/`. Django admin cũng có lối vào.
- Quản trị superuser hoặc role admin/operator có quyền toàn bộ workspace được lưu mẫu dùng chung. Nhân viên quầy có quyền xem được đọc mẫu; không tự sửa mặc định cho mọi người.
- Soạn tiêu đề (tối đa 200 ký tự, không xuống dòng) và nội dung văn bản thường (tối đa 10000 ký tự), giữ xuống dòng. Chèn ô thay thế bằng các nút: mã booking, loại vé, số lượng, tổng tiền, ngày booking, người bán, email người nhận, phương thức thanh toán. Dạng ví dụ: `{{ma_booking}}`. Có phần xem trước minh họa; lưu mẫu không gửi email.
- Trong **Nhập / In / Gửi vé**, sau thanh toán và xuất PDF, có email khách, tiêu đề/nội dung đã điền theo booking và thông báo PDF tự đính kèm. Nhân viên có thể chỉnh lời nhắn riêng, hoặc bấm **Lấy mẫu email hiện tại** nếu quản trị vừa đổi mẫu. Kiểm tra rồi bấm **Gửi PDF vé qua email**, xác nhận người nhận. Không chọn đường dẫn file tùy ý; server tự gắn đúng PDF của phiên bản vé đang chọn đã xác minh.
- Nếu chưa cấu hình SMTP vẫn có thể soạn/lưu mẫu và xem nội dung, nhưng nút gửi thật bị khóa. Cấu hình gửi theo COUNTER_TICKETS_TEST.md; không lưu mật khẩu SMTP trong mẫu email.
- Mỗi đợt gửi lưu email người nhận, tiêu đề, nội dung và trạng thái để đối soát. Gửi lặp y hệt không nhân đôi email; không dùng thay nội dung đã gửi để gửi lại ngầm. Khi máy chủ thư timeout, cần quản trị đối soát trước khi gửi lại. Không khẳng định khách đã nhận/đọc chỉ dựa vào SMTP tiếp nhận.
- Các email gửi từ bản cũ chưa lưu tiêu đề/nội dung sẽ để trống phần lịch sử nội dung, không điền mẫu mới thay cho nội dung cũ. PDF và các lần gửi đã có được giữ nguyên.

Migration 0011 chỉ thêm hai trường trống cho bảng bộ vé; không xóa booking/PDF/QR hoặc đặt lại trạng thái thanh toán. Đã kiểm tra backend mẫu/ô thay thế/quyền/phiên bản/chống header injection, email giả lập đính kèm PDF thật và lưu nội dung; kiểm tra giao diện khu vực mẫu, xem trước, không tự gửi khi lưu và chỉnh thư trước gửi. Không gửi email thật trong quá trình thử.
