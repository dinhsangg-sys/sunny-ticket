# 1.12.3 — Sửa xác nhận thanh toán thủ công nhầm

Thêm quyền **Hủy xác nhận thu tiền thủ công nhầm, đưa booking quầy về chờ thanh toán** (`counter__reopen_payment`). Không tự cấp cho nhóm nhân viên hiện có. Superuser có quyền; nhân viên phải có quyền vào quầy và quyền mới, chỉ sửa booking của mình. Quyền tạo/xác nhận thu lại (`counter__create`) và sửa nội dung booking (`counter__change`) vẫn riêng biệt.

## Sử dụng

1. Vào **Bán vé tại quầy → Booking của tôi → Chi tiết / Sửa** của booking đã xác nhận nhầm.
2. Trong **Sửa xác nhận thanh toán nhầm**, chọn phương thức sẽ thanh toán (Tiền mặt / Thẻ thanh toán / Chuyển khoản), nhập lý do từ 5–500 ký tự.
3. Bấm **Đưa về chờ thanh toán**, kiểm tra số tiền và xác nhận thao tác.
4. Booking về chờ thanh toán, đã thu về 0; số tiền cần thu bằng tổng booking. Xác nhận thu nhầm được gỡ khỏi tổng thu hiện hành nhưng lưu đầy đủ khoản thu cũ, lý do, người thực hiện, thời điểm trong lịch sử và audit. Không gọi ngân hàng, không hoàn tiền thật.
5. Nếu chuyển khoản qua SePay, bấm **QR chuyển khoản / Màn hình phụ** rồi chờ thông báo tiền vào. Nếu thu thủ công, chỉ xác nhận sau khi kiểm tra đã nhận đủ tiền thực tế. Trường hợp chỉ ghi sai phương thức nhưng đã nhận tiền thật, đối chiếu khoản thực nhận đó khi xác nhận lại; không thu khách thêm lần nữa.

Chặn xuất/tải/in/gửi PDF trong khi chờ thanh toán lại. File vé, QR và phiên bản nội dung vé được giữ để sử dụng sau khi xác nhận đúng; vé khách đã nhận trước đó không bị thu hồi từ xa. Mở lại cửa sổ vé sau khi sửa trạng thái để cập nhật giao diện.

Không áp dụng cho khoản thu có provider SePay hoặc booking lịch sử chưa dùng luồng xác nhận thủ công. Khoản ngân hàng đã vào cần đối soát/hoàn tiền riêng; không đổi thành chưa thanh toán bằng nút này. Phiên QR SePay cũ chưa thanh toán được hủy khi sửa; QR đã lưu/chụp trong ngân hàng không tự mất hiệu lực.

## Cập nhật Ubuntu

Sao lưu trước:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chờ **Đã sao lưu và kiểm tra**. Ctrl+C ở cửa sổ đang chạy bản chính cổng 8000, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
```

Migration 0013 khai báo quyền mới, không xóa/chuyển đổi dữ liệu. Giữ nguyên file cấu hình SePay mới đã điền trên máy chủ. Với cách chạy hiện tại, nạp cấu hình rồi khởi động:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở. Nếu dùng dịch vụ, khởi động lại đúng dịch vụ thay vì tạo tiến trình trùng cổng. Bản này không tự thay giá trị SEPAY_ENABLED hiện tại trên máy chủ.

## Cấp quyền

Đăng nhập quản trị → Người sử dụng → chọn nhân viên → Quyền của người sử dụng. Tìm **Hủy xác nhận thu tiền thủ công nhầm** (hoặc `reopen`), chuyển quyền sang ô đã chọn và lưu. Có thể cấp qua nhóm để áp dụng cho nhiều nhân viên. Không cần cấp toàn quyền dữ liệu. Đăng nhập lại/tải mới trang quầy để thấy chức năng.

Lịch sử xem ở **Chi tiết / Sửa → Lịch sử thay đổi → Hủy xác nhận thu nhầm**. Khoản thu cũ không bị mất dấu dù không còn tính vào số đã thu hiện tại.

## Kiểm tra

138 kiểm tra backend đạt; migration khớp model. Kiểm thử trình duyệt luồng mới và hồi quy xác nhận thủ công/sửa booking đạt.

Kiểm tra quyền/booking riêng/CSRF, lý do, dữ liệu cũ, chặn khoản thu provider, lưu lịch sử, retry không hủy hai lần, rollback xung đột, chặn xác nhận từ cửa sổ cũ, chặn PDF khi chưa thu lại và mở lại PDF sau xác nhận. Thêm kiểm thử trình duyệt cho cấp quyền, lý do, phương thức và trạng thái danh sách. Không chuyển tiền, gửi email hoặc thay dữ liệu Ubuntu trực tiếp trong kiểm thử.
