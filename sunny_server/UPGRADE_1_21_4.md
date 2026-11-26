# 1.21.4 — Bộ chọn vé gọn và rõ hơn

Tên loại vé bên trái, giá tiền ở trên ô số lượng bên phải. Mỗi lựa chọn có nền xanh nhạt, giá nổi bật; tổng tiền có nền vàng nhẹ. Giảm khoảng cách, cỡ tiêu đề và đệm trong khung để nhiều loại vé hiện gọn hơn. Giữ nút bấm/ô số lượng dễ sử dụng và giữ nguyên tính giá, thêm giỏ, thanh toán ngay. Giá vẫn được tính riêng cho từng lựa chọn theo ngày sử dụng.

## Khai báo nhóm loại vé và nhóm khách

Trong **Quản trị → Dịch vụ online → Lựa chọn vé online**, mỗi dòng khai báo:

- **Nhóm loại vé**: ví dụ ECO, HIGH hoặc VIP. Các dòng có cùng nhóm sẽ nằm chung một mục xổ xuống.
- **Nhóm loại vé tiếng Anh**: tên nhóm tiếng Anh nếu cần; ECO/HIGH/VIP có thể giữ nguyên.
- **Nhóm khách**: Người lớn, Trẻ em hoặc Người cao tuổi.
- **Tên lựa chọn**: tên để quản lý, ví dụ ECO · Người lớn.
- **Loại vé có sẵn**: chọn đúng mã vé trong Ticket Management; khai báo giá bán riêng cho dòng đó trong Bảng giá online.

Ví dụ ECO có ba dòng Người lớn/Trẻ em/Người cao tuổi, HIGH có ba dòng tương tự. Chỉ những dòng đang bán và được khai báo mới hiển thị; hệ thống không tự đặt giá trẻ em/cao tuổi. Không tạo hai lựa chọn đang bán trùng nhóm loại vé + nhóm khách. Nếu dùng đầy đủ lựa chọn theo nhóm, có thể bỏ trống Loại vé mặc định của dịch vụ để không hiện thêm mục Vé mặc định.

Khách mở mũi tên của ECO/HIGH/VIP rồi chọn số lượng theo từng nhóm khách. Khi thu lại vẫn giữ số vé đã chọn và tổng tiền; giỏ hàng/đơn lưu rõ nhóm loại vé và nhóm khách.

Có migration mới **online.0010_ticket_groups_audiences**. Các tên cũ có hậu tố rõ ràng NL/TE/NCT, Người lớn/Trẻ em/Người cao tuổi hoặc Adult/Child/Senior được gom tự động; ví dụ Eco NL và Eco TE cùng nằm trong ECO. Những tên không nhận diện được giữ nguyên, quản trị điền nhóm thủ công. Không đổi mã lựa chọn, giá đã khai báo, booking hoặc đơn cũ.

## Cập nhật Ubuntu

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C rồi chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ ứng dụng mở; Ctrl+F5 trên website. Kiểm tra bằng SePay test và hộp thư thử trước khi nhận đơn thật. Khi triển khai qua dịch vụ production, dùng lệnh khởi động lại dịch vụ đang vận hành thay vì mở thêm server trên cổng đã chiếm.
