# 1.10.1 — Khởi tạo mới, bỏ ánh xạ

Theo yêu cầu người dùng, phiên bản này bỏ menu/API và xử lý ánh xạ loại vé cũ. Dùng một danh mục vé chung, nhà cung cấp riêng và bảng giá bán đại lý độc lập với nguồn vé. Mỗi giá vốn phải có nhà cung cấp hợp lệ. Cấu hình lại từ dữ liệu trống, không nhập lại backup cũ.

## Xóa dữ liệu nghiệp vụ trên Ubuntu

Lệnh reset chỉ chạy khi bạn chủ động gọi, không chạy tự động mỗi lần migrate hoặc khởi động. Dữ liệu trên máy Ubuntu chưa bị xóa bởi việc đẩy mã lên GitHub.

1. Nhấn Ctrl+C ở cửa sổ đang chạy runserver. Nếu có tiến trình nền khác ghi database thì dừng tiến trình đó trước.
2. Chạy đúng đường dẫn đã xác nhận trên máy của bạn:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py reset_business_data --execute
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

**reset_business_data --execute xóa vĩnh viễn** toàn bộ workspace nghiệp vụ: vé, đại lý, nhà cung cấp, bảng giá, giá vốn, booking, thu/chi, chiến dịch, cấu hình nghiệp vụ cũ; xóa hồ sơ Agency ánh xạ tài khoản, nhật ký ứng dụng/quản trị, các bản ghi attachment và tệp tương ứng trong kho media. Lệnh không đụng tới file backup riêng bên ngoài ứng dụng. Nếu tệp không xóa được do quyền kho media, lệnh báo rõ database đã xóa và liệt kê tệp cần xử lý.

Giữ user, mật khẩu, nhóm và quyền đăng nhập. Gỡ gán đại lý của user vì đại lý cũ đã xóa; sau khi tạo đại lý mới cần gán lại tài khoản đại lý. Xóa tất cả phiên đăng nhập và tăng revision để tab cũ không ghi dữ liệu cũ trở lại.

Có thể xem database đích và số lượng trước khi xóa bằng lệnh không có --execute:

```bash
sudo .venv/bin/python manage.py reset_business_data
```

Không chạy `flush` hoặc xóa db.sqlite3 vì sẽ mất cả tài khoản quản trị.

## Khai báo mới

Tải lại trang Ctrl+F5, đăng nhập lại. Thực hiện:

1. Nhà cung cấp: An Huy, HBM...
2. Loại vé: Eco, High, VIP... mỗi loại khai báo một lần.
3. Giá vốn: loại vé + nhà cung cấp + giá/ngày hiệu lực.
4. Bảng giá chung: Chuẩn/Cấp 1/CTV, nhập giá vé hàng loạt.
5. Đại lý: tạo mới và gán bảng giá; chỉ thêm giá riêng khi có ngoại lệ.
6. Booking: chọn đại lý, loại vé, nguồn cung. Cùng đại lý và vé thì đổi nguồn chỉ đổi giá vốn.

Không còn bước gộp vé hoặc ánh xạ. Lệnh reset cũng có thể dùng cho SQLite/PostgreSQL theo môi trường đang chạy; kiểm tra database đích được in ra trước khi dùng. Trên máy của bạn đang là settings development và SQLite; không tự chuyển sang production trong đợt này.

## Phạm vi chất lượng

Đã kiểm thử reset trong database tạm: preview không thay đổi dữ liệu; execute giữ user/quyền, xóa nghiệp vụ, xóa file, gỡ liên kết đại lý và phiên đăng nhập. Không kết nối trực tiếp máy Ubuntu để xác nhận dữ liệu online đã xóa.

Đây là bản làm sạch luồng khai báo, không tự đồng nghĩa toàn bộ dự án đã đủ chuẩn production. Phần phân quyền chi tiết cho báo cáo/import/restore/CRM nâng cao còn giới hạn như hướng dẫn 1.10.0; snapshot JSON và development server vẫn chưa được thay bằng mô hình production hoàn chỉnh. Các giới hạn này không được đổi nhãn thành đã hoàn tất chỉ vì bỏ module ánh xạ.
