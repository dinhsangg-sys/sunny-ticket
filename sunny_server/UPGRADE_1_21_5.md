# Cập nhật 1.21.5 — Soạn bài giới thiệu dịch vụ

Trong Quản trị → Dịch vụ online → Thêm / Sửa dịch vụ, hai trường nội dung tiếng Việt và tiếng Anh có thanh công cụ định dạng, tiêu đề, danh sách, liên kết, chèn ảnh và xem trước.

Đặt con trỏ giữa các đoạn rồi bấm **Chèn ảnh**, chọn JPEG/PNG/WebP (tối đa 5 MB), nhập mô tả ảnh. Có thể gõ chú thích dưới ảnh. Soạn và lưu từng ngôn ngữ; không tự dịch nội dung. Xem trước kiểm tra nội dung trong khung soạn, sau khi lưu mở trang dịch vụ để xem bố cục thực tế trên điện thoại/máy tính.

Nội dung văn bản cũ vẫn hiển thị như trước. Ảnh minh họa được lưu trong MEDIA_ROOT/online/inline; cần đưa MEDIA_ROOT vào quy trình sao lưu. Chỉ người có quyền thêm/sửa dịch vụ mới tải ảnh. Ảnh đã tải nhưng chưa dùng không tự xóa để tránh làm hỏng bài viết. Không có thư viện video/upload video trong bản này; có thể chèn liên kết video.

## Cập nhật máy chủ

Sao lưu dữ liệu và thư mục media trước khi cập nhật. Dừng tiến trình ứng dụng đang chạy bằng Ctrl+C trong đúng cửa sổ.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Bản này không thêm migration. Giữ cửa sổ ứng dụng mở và tải lại trang quản trị bằng Ctrl+F5.
