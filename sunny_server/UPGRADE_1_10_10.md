# 1.10.10 — Thu tiền khách hàng hàng loạt

## Cách sử dụng

1. Mở Bán vé / Booking → **Thu tiền hàng loạt**.
2. Chọn đúng Đối tác / Khách hàng (có tìm nhanh tên/mã). Danh sách này lấy trực tiếp các booking còn nợ trên server, độc lập với ô tìm kiếm và tháng đang lọc ở bảng phía sau.
3. Nếu cần, chọn khoảng ngày booking. Đổi đối tác/khoảng ngày sẽ bỏ các tick trước đó để tránh thu nhầm dòng đang ẩn.
4. Tick các booking hoặc chọn tất cả đang hiển thị. Kiểm tra tổng thu, ngày thu và ghi chú.
5. Bấm **Xem trước khoản thu**, đối chiếu mã booking và số tiền từng dòng. Sau đó bấm **Xác nhận thu đủ các booking đã chọn**.

Mỗi booking được thu đúng phần còn nợ, giữ lịch sử đã thu trước đó. Một mã đợt liên kết các khoản thu, hiển thị trong lịch sử thanh toán từng booking. Không tạo thêm một dòng thu tổng vào sổ quỹ, vì sổ quỹ đã tổng hợp các khoản theo booking.

Màn hình này chưa hỗ trợ khách trả một phần của tổng các booking. Trường hợp đó tiếp tục ghi nhận theo từng booking; không tự chia tiền theo thứ tự ngày.

## Định danh và quyền

Đối tác được đối chiếu theo ID hoặc tên duy nhất của hồ sơ cũ. Nếu tên trùng/không tìm thấy hồ sơ thì booking không được gom và màn hình báo số dòng cần đối soát. Khách lẻ chưa có định danh được tách riêng từng booking, không gom theo tên để tránh thu nhầm người trùng tên. Đối tác đã ngừng hoạt động nhưng còn nợ vẫn xuất hiện để thu nợ lịch sử.

Tài khoản hạn chế cần quyền xem booking, xem khoản thu và tạo khoản thu. Dùng các quyền hiện có, không thêm migration. Màn hình phân quyền cũng có nút trong danh sách Booking khi đủ quyền.

Server kiểm tra số dư, cùng khách và revision, ghi toàn bộ đợt trong một transaction. Nếu dữ liệu đã đổi thì đóng và mở lại để xem trước số dư mới. Mã đợt chống thu trùng khi gửi lại yêu cầu bị mất phản hồi; không đổi nội dung rồi dùng lại mã đợt cũ. Sửa/xóa khoản thu vẫn theo từng booking và quyền hiện có, không sửa/xóa cả đợt; bản ghi đợt lưu thông tin lúc tạo để đối soát.

## Cập nhật Ubuntu

Ctrl+C tại terminal chạy server rồi thực hiện:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Giữ terminal chạy server, không đóng cửa sổ. Mở web và Ctrl+F5. Không reset dữ liệu. Nếu dùng dịch vụ riêng, collectstatic/restart theo cấu hình thực tế.

## Kiểm tra sau cập nhật

Thử hai booking của một đối tác, trong đó một booking đã thu một phần. Xem trước phải bằng tổng số dư còn lại, không gồm khách khác. Sau xác nhận và tải lại, cả hai tất toán; sổ quỹ chỉ tăng đúng tổng đã xác nhận. Thử sửa dữ liệu từ tab khác giữa preview và xác nhận để kiểm tra thông báo xung đột. Đã có 73 test backend và kiểm thử trình duyệt cục bộ; vẫn cần nghiệm thu trên máy online.
