# 1.23.3 — Quản trị hủy đơn chưa thu tiền và bắt buộc thông tin đặt vé

## Hủy yêu cầu khi tư vấn không thành công / khách muốn hủy

Trong **Đơn vé online**, quản trị superuser thấy nút **Hủy đơn** cạnh đơn chưa thu tiền và chưa tạo QR. Bấm nút để mở mục hủy trong chi tiết, nhập lý do (5–1000 ký tự), tick xác nhận khách muốn hủy/đơn chưa thu tiền rồi bấm **Xác nhận hủy đơn**.

Đơn chuyển sang cancelled, các dòng vé chuyển sang cancelled, biến mất khỏi danh sách chờ và có thể tra cứu qua **Đơn đã hủy**. Lưu người hủy, thời gian và lý do; không xóa cứng lịch sử, không tạo doanh thu hay thay đổi sổ thu. Khách xem lại mã đơn sẽ thấy Booking cancelled, không còn tạo QR/yêu cầu thu tiền.

Chỉ superuser được hủy; nhân viên xử lý vé/thu tiền không tự có quyền này. Đơn có QR, đã thu tiền, đã giao/gửi vé hoặc đã có booking tài chính bị chặn; phải xử lý đối soát theo quy trình có thanh toán, không dùng nút hủy yêu cầu này. Lý do nội bộ hiển thị cho nhân viên xử lý, không hiển thị nguyên văn trên trang khách. Không tự gửi thêm email hủy trong bản này.

## Thông tin nhận vé bắt buộc

Họ tên, email hợp lệ, mã quốc gia, số điện thoại hợp lệ và checkbox đồng ý đều bắt buộc. Dấu * ở nhãn ô nhập; kiểm tra required trong trình duyệt và validate phía máy chủ. Mã quốc gia vẫn mặc định +1, nhưng không được xóa trống rồi tiếp tục. Không tự đoán mã quốc gia từ số điện thoại khi trường mã quốc gia bị thiếu.

## Cập nhật

Sao lưu dữ liệu và media. Dừng ứng dụng bằng Ctrl+C trong đúng cửa sổ đang chạy rồi cập nhật:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Migration **online.0013_unpaid_order_cancellation** thêm trường hủy, không tự hủy hoặc xóa đơn đang có. Tải lại trang bằng Ctrl+F5 sau khi khởi động lại; giữ cửa sổ ứng dụng mở.
