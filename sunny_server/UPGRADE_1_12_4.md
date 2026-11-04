# 1.12.4 — Tổng tiền dự kiến và tổng hợp booking theo ngày

Thêm dòng **Tổng tiền** dưới VAT, trên Ghi chú trong form tạo/sửa booking của Ticket Management. Hiển thị số lượng nhân giá bán mỗi vé, ví dụ 4 × 420.000 = 1.680.000 đ. Cập nhật khi nhập số lượng/giá và khi bảng giá đại lý tự điền. VAT và chi phí không cộng/trừ vào dòng này theo yêu cầu; cách tính doanh thu và lưu dữ liệu hiện có giữ nguyên. Không migration mới, không đổi cấu hình SePay.

Dưới danh sách Booking có bảng **Tổng hợp booking theo ngày**: mỗi ngày một dòng tổng vé, tổng tiền, tổng đã thu, tổng nợ; cuối bảng có Tổng cộng. Ngày là ngày booking. Tất cả số liệu lấy từ đúng các booking đang hiển thị sau bộ lọc tìm kiếm/tháng/từ-đến ngày/trạng thái/các bộ lọc cột. Không còn booking phù hợp thì tổng về 0. Xóa bộ lọc sẽ tính lại theo toàn bộ danh sách. Tổng tiền ở bảng này cộng cột Tổng tiền hiện có (doanh thu sau chi phí theo quy tắc đang dùng), không lấy tổng tiền xem trước của form thay cho doanh thu.

Sao lưu trước cập nhật:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Sau thông báo Đã sao lưu và kiểm tra, dừng tiến trình bản chính cổng 8000 tại terminal đang chạy bằng Ctrl+C. Chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở. Với dịch vụ riêng, khởi động lại đúng dịch vụ hiện có. Không chạy thêm khi cổng đang được dùng. Nếu có Git conflict, kiểm tra trước khi tiếp tục. Không chỉnh file cấu hình ngân hàng hoặc chép database thử vào bản chính.

Trình duyệt nhấn Ctrl+F5, mở Tạo booking. Kiểm tra 4 vé × 420.000 đ hiển thị 1.680.000 đ đúng vị trí. Bản sửa đã kiểm tra giao diện cho số lượng/giá, giá đại lý tự động, VAT, giá 0 và booking đang sửa; kiểm tra hồi quy pricing/frontend đạt. Chưa triển khai trực tiếp Ubuntu.
