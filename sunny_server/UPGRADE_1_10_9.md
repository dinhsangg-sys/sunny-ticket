# 1.10.9 — Tab mới, tìm vé và lưu liên tiếp

## Thay đổi

1. Menu chức năng dùng liên kết riêng: chuột phải chọn Mở liên kết trong tab mới, Ctrl+click hoặc chuột giữa. URL dạng /#bookings, /#costs mở đúng chức năng khi tải lại. Các mục Nhà cung cấp, Bảng giá chung, Loại đối tác cũng hỗ trợ. Giao diện hạn chế dùng liên kết cho các mục được cấp quyền.
2. Tìm loại vé trong Booking giữ nguyên ô nhập khi lọc và chờ bộ gõ kết thúc ghép dấu; Enter lúc đang ghép dấu không tự chọn vé. Hỗ trợ tìm có dấu/không dấu.
3. Khai báo giá vốn có tìm nhanh bên trong dropdown Loại vé theo tên/mã, giữ lựa chọn đã lưu khi mở sửa. Nhà cung cấp vẫn dùng dropdown hiện có.
4. Giữ chuột trái ở tiêu đề popup biểu mẫu để kéo di chuyển, không kéo từ ô nhập hoặc nút. Giữ popup trong màn hình; mở form mới về vị trí mặc định. Trang nền vẫn bị khóa thao tác khi form mở.
5. API trạng thái trả cả dữ liệu chuẩn hóa và revision đã xác nhận, không cho cache phản hồi. Luồng lưu chung cập nhật mốc dữ liệu đã xác nhận sau mỗi lần thành công. Nếu gặp 409, đọc lại server: chỉ thử lại một lần khi server vẫn trùng mốc đã xác nhận, hoặc chấp nhận nếu server đã có chính xác bản cần lưu. Nếu dữ liệu khác thì tiếp tục chặn để tránh ghi đè, giữ thông tin đang nhập. Áp dụng chung các chức năng dùng save()/api/state, không chỉ Đối tác và Loại vé.

Không bỏ kiểm tra revision hoặc tự gộp dữ liệu từ nhiều tab. Nếu một tab khác thực sự đã sửa dữ liệu thì vẫn cần tải lại/đối soát. Chưa xác minh cấu hình proxy hoặc nguyên nhân riêng của lỗi online; bản này kiểm tra và gia cố cơ chế chung, cần nghiệm thu trên máy đang sử dụng.

## Cập nhật Ubuntu

Nhấn Ctrl+C ở terminal đang chạy server, sau đó chạy lần lượt:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không có migration mới; migrate bảo đảm đủ các bản trước. Không reset dữ liệu. Mở web và Ctrl+F5. Nếu dùng dịch vụ riêng, collectstatic và restart đúng dịch vụ thực tế.

## Kiểm tra sau cập nhật

- Thêm ít nhất ba đối tác rồi ba loại vé liên tiếp, không tải lại giữa các lần; tải lại một lần cuối để kiểm tra đủ dữ liệu. Thử các form thường dùng như giá vốn, bảng giá và booking.
- Tìm Cáp treo/Người lớn bằng bộ gõ Telex/VNI và bằng từ không dấu trong Booking; thử tìm theo mã khi khai báo giá vốn.
- Chuột phải menu để mở tab mới, kiểm tra đúng chức năng; thử Ctrl+click, Back/Forward và tải lại.
- Kéo popup sang bên, kiểm tra nút đóng còn thấy, các ô nhập vẫn hoạt động; đóng/mở lại về vị trí mặc định.
- Hai tab cùng sửa: tab cũ không được ghi đè thay đổi của tab đã lưu. Khi bị chặn, ghi lại thông tin form trước khi tải lại.

68 test backend và kiểm thử trình duyệt cục bộ đã đạt; chưa nghiệm thu online. Các popup giao diện đầy đủ dùng cơ chế kéo chung; editor của giao diện hạn chế vẫn là biểu mẫu trong trang.
