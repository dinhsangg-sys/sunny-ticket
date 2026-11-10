# 1.14.1 — Souvenirs song ngữ Việt / Anh

- Trang khách có nút Tiếng Việt / English; giữ ngôn ngữ khi xem sản phẩm, quay lại danh mục và tìm kiếm. Bộ lọc và từ khóa giữ nguyên khi đổi ngôn ngữ.
- Quản lý nhập thêm tên, nhóm sản phẩm, giới thiệu, câu chuyện, chú thích ảnh/video và tiêu đề/nội dung bài viết tiếng Anh trong hồ sơ sản phẩm. Các trường English không bắt buộc; thiếu bản dịch dùng nội dung tiếng Việt. Không tự dịch các nội dung có sẵn.
- Tìm kiếm theo tên tiếng Việt/Anh hoặc SKU, có hỗ trợ bỏ dấu. Mã QR cũ giữ nguyên; khi mở QR mặc định tiếng Việt, khách có thể chuyển English.
- Giao diện bán hàng/quản trị nội bộ vẫn tiếng Việt. Giá luôn tính bằng VND; đơn hàng/doanh thu không thay đổi.

## Cập nhật Ubuntu

Sao lưu database và media trước khi cập nhật theo UPGRADE_1_14_0.md. Sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Migration souvenirs.0003 chỉ thêm các cột bản dịch trống, không thay thế dữ liệu cũ. Không cần chỉnh cấu hình tên miền/SOUVENIRS_ENABLED nếu 1.14.0 đã hoạt động.

Khởi động lại tiến trình hiện tại để nạp mã mới. Với runserver thủ công, Ctrl+C tại đúng cửa sổ đang chạy rồi chạy lại (không khởi động bản thứ hai khi cổng 8000 đang bị chiếm):

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ này mở. Vào Souvenirs → sửa sản phẩm → nhập các trường English → lưu. Mở trang khách, chuyển English và kiểm tra cả ảnh/video/bài viết, tìm kiếm và quay lại danh mục.

## Kiểm tra

14 kiểm thử Souvenirs đạt: chuyển ngôn ngữ, tìm tên Anh, giữ bộ lọc, fallback, escape HTML, các trường quản lý, cùng các luồng đơn hàng/phân quyền/thanh toán hiện có. Kiểm tra browser template thật desktop/mobile và migration phải đạt trước khi phát hành.
