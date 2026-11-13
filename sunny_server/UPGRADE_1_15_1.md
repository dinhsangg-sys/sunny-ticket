# 1.15.1 — Hủy booking có thanh toán sau đối soát

## Hành vi

Thêm Hủy booking, có quyền riêng và lý do bắt buộc. Áp dụng booking đã ghi nhận thu tiền mặt/thẻ/chuyển khoản/SePay, kể cả booking đã hủy xác nhận thu nhầm nhưng lịch sử từng có phí thẻ. Có thể dùng cho booking chờ nhập nhầm.

Booking được chuyển khỏi danh sách hoạt động sang hồ sơ Booking đã hủy, giữ nguyên snapshot đầy đủ, khoản thu, phí, ghi chú, người hủy, thời điểm, lý do và tham chiếu đối soát. Các báo cáo/doanh thu/VAT/công nợ/số vé hoạt động không còn tính booking này. Không xóa vật lý hồ sơ, file vé hoặc lịch sử QR. Không đổi số liệu của booking khác. Không tái dùng mã booking/lần tạo đã hủy.

- Không thực hiện hoàn tiền ngân hàng, POS hoặc nhà cung cấp. Nhân sự phải đối chiếu và xử lý thực tế trước khi xác nhận. Không tự hủy hóa đơn VAT đã phát hành bên ngoài.
- Không thu hồi vé/PDF đã tải hoặc QR gốc nhà cung cấp; cần liên hệ nhà cung cấp nếu vé đã giao. Ứng dụng chặn xuất/in/gửi tiếp booking đã hủy, giữ các file cũ làm bằng chứng và không tự giải phóng QR đã gắn.
- QR SePay pending/expired của booking bị hủy được vô hiệu hóa. Tiền đến QR cũ giữ trạng thái cần đối soát, không tự ghi vào booking khác. Khoản thu SePay live không được chọn Ghi nhận nhầm, chưa thu thật: phải chọn đã hoàn/hủy thực tế và nhập tham chiếu.
- Báo cáo/sổ quỹ hoạt động được tính lại khi loại booking khỏi hoạt động, không giữ các dòng thu/chi tự sinh của booking trong bảng hiện hành. Hồ sơ gốc nằm trong Booking đã hủy. Đây là sửa dữ liệu nghiệp vụ/booking nhầm, không phải sổ nhật ký kế toán đầy đủ theo ngày thu và hoàn.
- Nếu thực tế ngân hàng/POS không hoàn một phần phí thẻ, nhập đúng Phí thẻ thực tế không được hoàn. Số tiền phải nguyên đồng, không vượt mức phí đã ghi nhận. Hệ thống tạo một khoản Chi trong Sổ quỹ ngày hủy để giữ chi phí này; không làm mất phí khỏi lợi nhuận thực tế. Phần phí giữ lại xem ở Sổ quỹ/chi phí, không nằm trong bảng giao dịch thẻ booking còn hoạt động. Nếu chỉ ghi nhầm, không chịu phí thực tế, để 0.
- Với booking đã chi tiền nhà cung cấp, nhân viên quầy không thể tự hủy; cần quản trị hoặc vận hành có cả quyền hủy và quyền xem chi nhà cung cấp (supplier_payment.view hoặc toàn quyền workspace) đối soát cả khoản chi đó. Không tiết lộ giá vốn/số tiền nhà cung cấp cho nhân viên quầy.

## Phân quyền

Quyền: legacy.booking__cancel_paid — Hủy booking có thanh toán sau đối soát, có lý do và lưu lịch sử.

Superuser và vai trò Quản trị (admin) mặc định có quyền. Những vai trò khác cần được cấp riêng. Quản trị → Người sử dụng/nhóm → Quyền → tìm Hủy booking có thanh toán → chuyển sang quyền đã chọn → Lưu. Nhân viên quầy cần quyền truy cập quầy để mở danh sách; chỉ hủy booking của mình. Nhân sự vai trò vận hành được cấp quyền có thể đối soát booking toàn hệ thống.

## Sử dụng

1. Tại Bán vé tại quầy → Booking của tôi, chọn Hủy booking. Hoặc ở Bán vé / Booking của Ticket Management chọn Hủy booking. Với booking có phí thẻ, bấm Xóa cũng mở quy trình hủy thay vì thông báo chặn không có hướng xử lý.
2. Kiểm tra số tiền đã thu, phí thẻ từng ghi nhận và khoản chi nhà cung cấp (chỉ nhân sự nội bộ được xem).
3. Chọn tình trạng tiền: Ghi nhận nhầm, không thu tiền thật; hoặc Đã hoàn/hủy khoản thu thực tế. Nếu đã hoàn/hủy, nhập mã giao dịch/phiếu hoàn tiền hoặc biên bản từ 5 ký tự.
4. Nhập lý do hủy 5–500 ký tự; phí thẻ thực tế không được hoàn, nếu có.
5. Tick xác nhận đã đối soát tiền khách, phí, nhà cung cấp và tình trạng vé; bấm Xác nhận hủy booking rồi kiểm tra lại báo cáo.
6. Bấm Booking đã hủy để xem hồ sơ. Không có chức năng khôi phục trực tiếp, nếu cần bán lại tạo booking mới và kiểm tra QR phù hợp; không tái gán vé cũ tự động.

Tài khoản không có quyền không thấy nút Hủy booking ở quầy và không gọi được API hủy. Booking từng có khoản thu không xóa trực tiếp qua API dữ liệu đầy đủ; phải đi qua quy trình hủy. Nhập lại JSON cũ chứa booking đã hủy hoặc xóa danh sách mã giữ chỗ bị chặn để không làm sống lại booking đã đối soát.

## Cập nhật Ubuntu

Sao lưu database/media theo quy trình hiện tại trước nâng cấp. Chọn thời điểm bảo trì, dừng đúng tiến trình web ở cửa sổ đang chạy bằng Ctrl+C rồi cập nhật:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Migration legacy.0015 thêm bảng hồ sơ hủy và quyền mới, không xóa dữ liệu hiện có. Hồ sơ hủy lưu trong database, không nằm trong file xuất JSON workspace; cần bản sao lưu SQLite/database đầy đủ để bảo toàn hồ sơ khi khôi phục. Không đổi cấu hình SePay hoặc Souvenirs.

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ web mở, Ctrl+F5 trên trang quản lý/quầy; cấp quyền trước khi nhân viên sử dụng. Không mở thêm server khi cổng 8000 đang có tiến trình.

## Kiểm tra

Kiểm thử quyền/đơn người khác/quản trị mặc định, giữ snapshot/file/lịch sử phí, không tái dùng mã/lần tạo, chặn dữ liệu khôi phục trái quy trình, phí giữ lại chỉ ghi chi một lần, lỗi đầu vào và phiên bản cũ, SePay live cần tham chiếu hoàn tiền, QR chờ bị hủy, chặn truy cập tiếp booking hủy và ẩn tiền nhà cung cấp khỏi quầy. Kiểm tra browser quy trình xác nhận/hồ sơ hủy/làm mới danh sách và hồi quy tạo booking. Chưa thực hiện hoàn tiền thật hoặc thay đổi trực tiếp máy chủ Ubuntu.
