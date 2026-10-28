# 1.10.13 — Tất cả nhà cung cấp và đóng dropdown

## Thay đổi

- Mở Thanh toán tiền vé hàng loạt sẽ mặc định **Tất cả nhà cung cấp**. Danh sách hiển thị booking còn phải trả thuộc các nguồn xác định được, kết hợp sản phẩm, ngày và loại vé đang lọc. Booking thiếu nguồn vẫn cần đối soát; nguồn nhập tay tiếp tục tách riêng từng booking.
- Có thể chọn nguồn cụ thể hoặc quay về Tất cả nhà cung cấp trong dropdown. Đổi phạm vi nguồn sẽ bỏ các tick booking cũ, giữ các điều kiện sản phẩm/ngày/loại vé.
- Ở chế độ Tất cả, nếu chỉ tick booking của cùng một bên thì có thể thanh toán và xem xác nhận đúng bên đó. Tick nhiều bên nhận sẽ bị chặn trước khi gửi yêu cầu; hãy lọc một nhà cung cấp hoặc tách lựa chọn. Không thay đổi cơ chế kiểm tra nhà cung cấp/revision/chống chi trùng trên server.
- Các dropdown tìm nhanh dùng chung tự đóng khi bấm ngoài, kể cả vùng không nhận focus như tiêu đề hoặc nhãn. Giữ nguyên lựa chọn; click ô tìm, kết quả và cuộn bên trong không đóng sớm. Chọn kết quả, Escape và click lại nút mở vẫn hoạt động.
- Listener đóng dùng chung, chỉ theo dõi dropdown đang mở; đóng danh sách không xóa bộ lọc, tick booking hoặc đóng popup chính. Các màn hình chọn đối tác/loại vé dùng helper cũng nhận bản sửa.

## Cập nhật Ubuntu

Ctrl+C tại terminal chạy server rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không có migration mới, không reset dữ liệu. Giữ terminal mở khi thấy Starting development server và nhấn Ctrl+F5 trên web. Nếu báo cổng đã dùng, kiểm tra tiến trình hiện tại trước khi khởi chạy thêm server. Nếu dùng dịch vụ riêng, collectstatic và restart theo cấu hình thực tế.

## Kiểm tra sau cập nhật

Mở popup, kiểm tra Tất cả nhà cung cấp hiển thị đầy đủ nguồn còn nợ trong phạm vi lọc. Chọn nguồn rồi quay lại Tất cả, kiểm tra bỏ tick cũ. Mở dropdown rồi click tiêu đề/nhãn/vùng ngoài: danh sách phải đóng và giữ lựa chọn. Thử cả tìm nhanh, cuộn và Escape; thử thu khách hàng hàng loạt để kiểm tra helper chung. Tick các booking cùng bên nhận để xem xác nhận; chọn lẫn hai nguồn phải được yêu cầu tách.

Đã kiểm tra trên Edge headless cục bộ với frontend thật và API giả lập; cần nghiệm thu với dữ liệu online. Không thay đổi backend hoặc cấu trúc dữ liệu trong bản này.
