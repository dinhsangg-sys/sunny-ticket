# 1.14.3 — Ưu tiên video giới thiệu sản phẩm

Video đầu tiên theo thứ tự khai báo hiển thị ngay đầu trang chi tiết sản phẩm, trước ảnh/mô tả dài. Các video còn lại ở phần nội dung bên dưới. Trang không có video giữ bố cục ảnh hiện tại. Khung video co theo màn hình, giữ nguyên tỉ lệ nội dung, có nút phát/tạm dừng/âm lượng.

Khi mở trang, thử phát có tiếng. Nếu trình duyệt chặn tự phát âm thanh, thử chạy tắt tiếng và hiển thị nút Nghe giới thiệu / Listen to the introduction. Khách bấm một lần để bật tiếng. Không thể bảo đảm tự phát có âm thanh trên mọi điện thoại/trình duyệt; chính sách trình duyệt quyết định. Nếu tệp lỗi, thông báo thử lại được hiển thị. Chỉ video giới thiệu được tự phát; không phát đồng thời các video còn lại.

Giữ nguyên dữ liệu và QR hiện tại, không có migration mới. Trong Sửa nội dung sản phẩm, upload video MP4/WebM và đặt Thứ tự thấp nhất cho video muốn ưu tiên.

## Cập nhật Ubuntu

Sao lưu trước theo hướng dẫn 1.14.0, sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Dừng đúng runserver hiện tại bằng Ctrl+C tại cửa sổ đang chạy rồi khởi động lại:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ chạy web mở. Mở trang chi tiết sản phẩm trên điện thoại để kiểm tra video và âm thanh thực tế, cả tiếng Việt/English. Bản này không tự tạo bản lồng tiếng Anh; âm thanh là từ tệp video đã tải lên.
