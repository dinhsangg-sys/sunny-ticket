# 1.16.0 — Giao diện đăng nhập Sunny vàng/trắng

Thiết kế lại /login/ theo màu vàng ấm và trắng, chữ Sunny, biểu tượng mặt trời và ảnh Hội An do người dùng đã cung cấp. Slogan chính thức theo lựa chọn của người dùng: Sunny — Từ lòng người địa phương, đến những hành trình đáng nhớ.

Máy tính: phần thương hiệu/câu chuyện bản địa bên trái, form đăng nhập gọn bên phải. Điện thoại: slogan phía trên, form phía dưới; giảm hình ảnh để ưu tiên thao tác và tránh kéo ngang. Có nút hiện/ẩn mật khẩu, cảnh báo Caps Lock, trạng thái lỗi dễ đọc, điều hướng bàn phím và giảm chuyển động khi trình duyệt yêu cầu.

Giữ nguyên Django LoginView, tên trường username/password, CSRF và đích next. Không thay cơ chế tài khoản, mật khẩu, phân quyền, thanh toán hoặc dữ liệu nghiệp vụ. Không thêm tài khoản mẫu, không gửi thông tin đăng nhập sang dịch vụ bên ngoài. CSS/JS/ảnh phục vụ từ máy chủ của ứng dụng, không phụ thuộc font/CDN bên ngoài. Không có JavaScript vẫn đăng nhập được. Trang quản trị Django /admin/login/ không đổi; thiết kế này áp dụng trang đăng nhập chính /login/.

## Cập nhật Ubuntu

Sao lưu trước theo quy trình hiện có. Sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Không có migration riêng cho 1.16.0. Nếu đang nâng từ trước 1.15.1, chạy thêm manage.py migrate theo hướng dẫn phiên bản đó trước khi khởi động lại.

Nếu cần khởi động lại runserver, Ctrl+C tại đúng cửa sổ đang chạy rồi chạy lại và giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Mở /login/ bằng cửa sổ riêng tư hoặc đăng xuất, Ctrl+F5. Không cần sửa SePay, DNS hoặc quyền người dùng. Nếu giao diện cũ/thiếu ảnh, kiểm tra collectstatic và cấu hình phục vụ /static/ hiện có.

## Kiểm tra

4 kiểm tra backend: trường biểu mẫu/CSRF/tài nguyên static, đăng nhập đúng và giữ next hợp lệ, chặn next sang domain khác, hiển thị lỗi/escape tên đăng nhập và không phản hồi mật khẩu. Browser kiểm tra desktop 1366px, điện thoại 390px và màn hình 320px, không tràn ngang; hiện/ẩn mật khẩu, trạng thái lỗi, focus và fallback không có JS. Không đăng nhập vào tài khoản thật trong quá trình kiểm thử.
