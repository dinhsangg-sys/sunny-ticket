# 1.10.11 — Lọc sản phẩm và thanh toán đúng nhà cung cấp

## Báo cáo doanh thu & công nợ

Trong tab Doanh thu & Công nợ, chọn dropdown **Sản phẩm**, mặc định Tất cả sản phẩm. Bộ lọc kết hợp với ngày, khách/đại lý, loại đối tác và trạng thái thanh toán. Bảng booking, các chỉ số tổng hợp, số booking và Excel cùng áp dụng sản phẩm đã chọn; mô tả báo cáo và tiêu đề thông tin Excel ghi rõ sản phẩm.

Ưu tiên sản phẩm lưu trực tiếp trên booking nếu có; nếu không thì xác định theo ticketId, hoặc tên loại vé duy nhất đối với dữ liệu cũ chưa có ID. Booking không tìm thấy loại vé hoặc tên trùng được đưa vào Chưa xác định sản phẩm. Với dữ liệu cũ không lưu snapshot sản phẩm, việc xác định dựa trên danh mục loại vé hiện tại.

## Thanh toán tiền vé hàng loạt

1. Mở Sổ quỹ / Thu Chi → Thanh toán tiền vé hàng loạt (hoặc từ phần công nợ tiền vé).
2. Chọn **Nhà cung cấp / Nguồn đã chọn trên booking** trước khi tick. Có tìm nhanh; nguồn ngừng hoạt động nhưng còn nợ vẫn xuất hiện.
3. Kết hợp khoảng ngày và Loại vé (chọn nhiều). Các dòng hiển thị rõ bên nhận; cùng loại vé mua từ nguồn khác không bị gộp.
4. Tick booking cần trả. Đổi nhà cung cấp hoặc bộ lọc sẽ bỏ tick cũ để tránh giữ dòng ẩn.
5. Nhập ngày chi/ghi chú, bấm Thanh toán các booking đã chọn. Đối chiếu hộp xác nhận ghi bên nhận, từng mã booking và số tiền trước khi đồng ý.

Lọc dựa vào supplierId thực tế trên booking, không dùng mặc định hoặc bảng giá hiện tại. Nguồn nhập tay tách riêng từng booking để tránh gộp nhầm nhiều người cùng dùng mã __manual__. Booking thiếu nhà cung cấp xác định không đưa vào nhóm; cần đối soát trước.

API kiểm tra cùng bên nhận, dư nợ và revision; ghi cả đợt trong transaction, dùng mã đợt chống chi trùng khi gửi lại. Không tạo thêm khoản chi tổng trong sổ quỹ. Tiếp tục thanh toán đủ số dư từng booking được chọn, không tự phân bổ một khoản chi nhỏ hơn tổng.

Nếu mất phản hồi sau khi xác nhận, có thể chọn gửi lại cùng mã đợt để kiểm tra; nếu vẫn lỗi thì kiểm tra lịch sử hoặc mở lại danh sách trước khi tạo đợt khác. Dữ liệu đổi từ phiên khác sẽ bị chặn, cần mở lại popup để lấy số dư mới.

## Đóng hộp lọc loại vé

Click ra ngoài hoặc nhấn Escape sẽ đóng riêng dropdown Loại vé, giữ nguyên tìm kiếm và các vé đã chọn. Click bên trong, tick và cuộn danh sách không đóng dropdown. Popup thanh toán vẫn mở.

## Cập nhật Ubuntu

Ctrl+C tại terminal đang chạy server rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không reset dữ liệu, không có migration mới. Giữ terminal mở sau khi thấy Starting development server; trên web nhấn Ctrl+F5. Nếu dùng dịch vụ khác, collectstatic và restart đúng dịch vụ thực tế.

## Kiểm tra sau triển khai

Thử hai sản phẩm và đối chiếu Excel với các số tổng. Thử cùng vé Eco nhưng hai nhà cung cấp, chọn từng bên và kiểm tra khoản đã trả trước đó được trừ đúng. Kiểm tra sổ quỹ, tải lại trang để xác nhận lưu bền vững. Thử đóng hộp lọc bằng click ngoài và Escape. Đã đạt 77 test backend và kiểm thử trình duyệt cục bộ; chưa nghiệm thu online.

Các bộ lọc này áp dụng màn hình nghiệp vụ đầy đủ. API chi hàng loạt yêu cầu quyền xem booking, xem giá vốn và xem/tạo chi nhà cung cấp. Không bổ sung màn hình hàng loạt mới cho editor hạn chế trong bản này.
