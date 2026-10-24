# 1.10.8 — Booking gọn, lọc cột và tìm đối tác

- Bảng Booking dùng chữ 11px, mỗi booking một hàng. Tên đối tác/loại vé dài có dấu ba chấm, rê chuột để đọc đầy đủ. Thanh toán và Sửa cố định bên phải; Xóa ở cột riêng trong vùng cuộn ngang.
- Bấm tiêu đề cột để lọc chữ, chọn loại vé/trạng thái hoặc nhập khoảng ngày/số. Các điều kiện kết hợp với tìm kiếm và bộ lọc phía trên. Dấu chấm chỉ cột đang lọc; Bỏ lọc cột xóa riêng, Xóa lọc phía trên xóa toàn bộ, kể cả tháng.
- Quay về Đối tác & bảng giá từ màn hình khác sẽ xóa từ khóa tìm kiếm. Mở/đóng hồ sơ hoặc bảng giá trong cùng màn hình vẫn giữ từ khóa; trạng thái và loại đối tác vẫn giữ.
- Mỗi lần mở Tạo/Sửa booking, form bắt đầu ở trên cùng và focus trường Ngày. Nhãn tên nguồn nhập tay chỉ xuất hiện khi chọn nguồn nhập tay.
- Sao chép giá: mỗi trường nguồn/đích chỉ hiển thị một ô chọn. Bấm mở dropdown để tìm theo tên/mã không dấu ngay bên trong; chọn một kết quả để xác nhận, hỗ trợ phím lên/xuống/Enter/Escape. Đổi lựa chọn sẽ hủy bản xem trước cũ.

## Cập nhật Ubuntu

Ctrl+C tại terminal đang chạy server, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không reset dữ liệu, không có migration mới. Migrate bảo đảm máy đã cập nhật các quyền từ bản cũ. Mở web và Ctrl+F5. Nếu dùng dịch vụ production riêng, collectstatic/restart theo cấu hình thực tế.

## Kiểm tra sau cập nhật

Thử bảng Booking với tên dài và số tiền lớn; cuộn ngang/dọc, kiểm tra Thanh toán/Sửa đúng booking và Xóa vẫn truy cập được. Thử nhiều bộ lọc đồng thời và Xóa lọc. Mở lại form sau khi đã cuộn xuống cuối, chuyển trang rồi quay lại đối tác, thử chọn cả nguồn/đích để sao chép giá.

Đã kiểm tra bằng Edge headless trên fixture cục bộ và các regression JavaScript; vẫn cần nghiệm thu với trang online/dữ liệu thực tế. Các thay đổi bảng Booking áp dụng giao diện nghiệp vụ đầy đủ; giao diện thao tác hạn chế vẫn giữ bố cục riêng. Dropdown sao chép giá áp dụng cả hai giao diện.
