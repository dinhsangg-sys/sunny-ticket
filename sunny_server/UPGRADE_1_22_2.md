# 1.22.2 — Mã quốc gia và số điện thoại

Ở thông tin nhận vé (giỏ hàng, thanh toán ngay và biểu mẫu đặt vé cũ), mã quốc gia và số điện thoại nằm cạnh nhau. Mặc định mã **+1**. Có thể gõ tên quốc gia hoặc mã gọi quốc tế để lọc, hoặc bấm mũi tên rồi cuộn chọn. Danh sách gồm các quốc gia phổ biến; cũng có thể nhập trực tiếp một mã có trong danh sách. Hỗ trợ phím mũi tên, Enter, Escape.

Ví dụ chọn Việt Nam +84 rồi nhập 0932 548 145 sẽ lưu +84932548145; chọn Mỹ +1 rồi nhập 2025550100 sẽ lưu +12025550100. Có thể dán số quốc tế đầy đủ khi mã đã chọn khớp. Kiểm tra cấu trúc số, không xác minh chủ thuê bao hay khả năng nhận cuộc gọi. Không gọi dịch vụ trả phí.

Số được lưu có mã quốc tế vào đơn online và các dòng đơn, hiển thị ở trang xử lý vé; quản trị có thể tìm đơn theo số này. Dữ liệu đơn cũ không bị chuyển đổi. Quốc gia dùng để ghép mã gọi, không dùng suy đoán quốc tịch hoặc ngôn ngữ.

Không có migration mới. Cập nhật theo [1.22.0](UPGRADE_1_22_0.md): git pull, check, collectstatic, khởi động lại ứng dụng và Ctrl+F5. Nếu chưa chạy migration 1.22.0 thì cần thực hiện trước.
