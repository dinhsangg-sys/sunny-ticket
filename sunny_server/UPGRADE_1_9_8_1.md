# Cập nhật 1.9.8.1 — sửa lưu dữ liệu qua HTTPS

## Thay đổi

- Cấu hình trusted origin dùng chung cho development/production. Mặc định chấp nhận chính xác `https://sn.hoianmemorieslands.com`, không dùng wildcard, không tắt CSRF. Địa chỉ IP test `172.16.150.157` và domain này được bổ sung vào danh sách host mặc định.
- Khắc phục cấu hình gây 403 cho đăng xuất, form tạo user/nhóm quyền, lưu loại vé, đại lý/bảng giá, giá vốn, chi phí, chiến dịch và khôi phục dữ liệu.
- API trả thông báo CSRF dạng JSON; form quản trị có trang lỗi ngắn gọn.
- Khi lưu lỗi, giao diện dừng sửa dữ liệu và cung cấp nút tải lại; không đưa HTML thô vào popup, không xác nhận lưu/khôi phục thành công.
- Bấm toàn bộ ô ngày/tháng mở picker trên trình duyệt hỗ trợ, kể cả các ô được tạo động. Trình duyệt không hỗ trợ vẫn dùng ô nhập gốc.
- Tăng phiên bản URL JavaScript để trình duyệt lấy mã mới.

## Nâng cấp trên Ubuntu

Sao lưu database và media trước khi nâng cấp. Bản này không có migration mới và không yêu cầu xóa database.

```bash
cd /duong-dan/sunny-ticket
git pull --ff-only origin main
cd sunny_server
source .venv/bin/activate
python manage.py check
python manage.py test apps.legacy
```

Thay đường dẫn và venv theo nơi bạn đang cài. Nếu Git báo file cấu hình đã sửa trên Ubuntu, giữ bản sao các thay đổi đó và hợp nhất; không dùng reset để bỏ cấu hình hiện tại.

### Nếu đang chạy runserver (development)

Mặc định bản mới đã có domain của bạn. Nếu bạn đang đặt biến môi trường `DJANGO_CSRF_TRUSTED_ORIGINS`, biến đó sẽ thay thế giá trị mặc định; cần sửa đúng biến trước khi khởi động lại:

```bash
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,172.16.150.157,sn.hoianmemorieslands.com
export DJANGO_CSRF_TRUSTED_ORIGINS=https://sn.hoianmemorieslands.com
python manage.py runserver 0.0.0.0:8000
```

Nếu có dòng CSRF_TRUSTED_ORIGINS hoặc ALLOWED_HOSTS tự thêm trong development.py, kiểm tra vì các dòng đó ghi đè cấu hình chung. Lưu các biến vào cấu hình dịch vụ nếu dùng dịch vụ; export ở terminal chỉ tồn tại trong phiên đó.

### Nếu đang chạy Gunicorn/systemd (production)

Sửa trong `/etc/sunny/sunny.env`:

```text
DJANGO_ALLOWED_HOSTS=sn.hoianmemorieslands.com,172.16.150.157,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://sn.hoianmemorieslands.com
```

Nạp môi trường production theo README rồi chạy `python manage.py collectstatic --noinput` và `python manage.py check --deploy`; sau đó `sudo systemctl restart sunny`. Production giữ DEBUG=False và cần proxy gửi đúng `Host` và `X-Forwarded-Proto` như cấu hình Nginx mẫu. Chỉ tin header forwarded khi backend chỉ nhận kết nối từ proxy đáng tin cậy.

## Test lại online

Tải lại trang bằng Ctrl+F5, đăng nhập lại rồi kiểm tra các thao tác đã báo. Tất cả các bản ghi phải vẫn tồn tại sau tải lại. Kiểm tra riêng khôi phục trên dữ liệu test và đối soát số tiền; không lấy nội dung còn trong bộ nhớ trình duyệt làm bằng chứng lưu thành công.

Trong quản trị, kiểm tra tạo user, tạo nhóm và gán quyền. Bản này sửa lỗi gửi/lưu form quản trị; quyền Django nhóm/model hoạt động cho Django Admin. Phân quyền thao tác nghiệp vụ chi tiết vẫn chưa triển khai: ứng dụng nghiệp vụ tiếp tục dùng role admin/operator/agency như bản trước. Không cấp operator nếu muốn hạn chế từng nghiệp vụ.

Đây vẫn là bản test chuyển đổi dùng snapshot JSON và logic tính tiền gốc. Chưa xác minh trên máy Ubuntu hoặc reverse proxy của người dùng; kết quả online cần được kiểm tra sau nâng cấp.
