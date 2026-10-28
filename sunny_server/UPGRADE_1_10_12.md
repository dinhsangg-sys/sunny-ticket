# 1.10.12 — Sản phẩm trong thanh toán tiền vé hàng loạt

## Cách dùng

Mở Thanh toán tiền vé hàng loạt, chọn Nhà cung cấp/Nguồn và **Sản phẩm** (mặc định Tất cả sản phẩm). Kết hợp khoảng ngày và Loại vé để tìm các booking cần trả. Danh sách loại vé chỉ hiển thị các vé thuộc sản phẩm đang chọn.

Đổi sản phẩm sẽ bỏ các tick booking cũ, xóa từ khóa tìm loại vé và đặt lại lựa chọn tất cả loại vé thuộc sản phẩm mới. Nhà cung cấp và khoảng ngày vẫn giữ. Chọn tất cả booking chỉ áp dụng các dòng đang hiển thị; số lượng/tổng tiền tính trên các dòng đã tick.

Bước xác nhận ghi rõ nhà cung cấp, sản phẩm, mã booking và số tiền. API vẫn kiểm tra nhà cung cấp thực tế, số dư, revision và chống chi trùng như bản 1.10.11; bộ lọc sản phẩm chỉ thu hẹp tập booking được chọn, không đổi nguồn hoặc dữ liệu booking.

Sản phẩm dùng cùng quy tắc báo cáo: snapshot trên booking nếu có; nếu không theo ticketId hoặc tên loại vé duy nhất. Chưa xác định sản phẩm được tách riêng khi không thể đối chiếu chắc chắn. Với snapshot lịch sử khác danh mục hiện tại, loại vé được phép xuất hiện ở cả các nhóm sản phẩm có dữ liệu tương ứng, nhưng mỗi nhóm chỉ hiện đúng booking của mình.

## Cập nhật Ubuntu

Ctrl+C ở terminal chạy server, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không reset dữ liệu, không có migration mới. Giữ terminal mở sau Starting development server, mở web và Ctrl+F5. Nếu dùng dịch vụ riêng, collectstatic/restart theo cấu hình thực tế.

## Kiểm tra sau cập nhật

Chọn nhà cung cấp có nhiều sản phẩm, lần lượt lọc từng sản phẩm và kiểm tra danh sách loại vé/booking. Tick một số dòng rồi đổi sản phẩm: các tick phải được bỏ và tổng trở về 0. Chọn lại các dòng muốn trả, kiểm tra bên nhận/sản phẩm và tiền trong xác nhận trước khi đồng ý. Nguồn nhập tay và bộ lọc ngoài/Escape giữ cách hoạt động như bản trước.

Đã kiểm tra trình duyệt cục bộ với toàn bộ frontend và API giả lập; cần nghiệm thu với dữ liệu online. Chức năng mới áp dụng giao diện nghiệp vụ đầy đủ.
