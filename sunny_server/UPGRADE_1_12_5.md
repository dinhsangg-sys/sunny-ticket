# 1.12.5 — Lọc và tổng hợp booking các tháng trước

Lỗi trong ảnh: tháng 11/2026 kết hợp ngày 22/10/2026 khiến danh sách rỗng, không phải tổng hợp chỉ nhận booking mới. Bản sửa chọn khoảng Từ ngày/Đến ngày sẽ tự bỏ bộ lọc tháng. Chọn tháng mới sẽ bỏ khoảng ngày trước đó. Khi mở lại danh sách với điều kiện cũ bị chồng nhau, khoảng ngày được ưu tiên.

Tổng hợp lấy toàn bộ booking phù hợp trong dữ liệu hiện có, kể cả booking tạo trước ngày cập nhật. Không sửa dữ liệu lịch sử, không phải nhập lại booking. Bộ lọc tìm kiếm/trạng thái/cột khác vẫn kết hợp như trước. Bấm Xóa lọc để xem và tổng hợp toàn bộ thời gian; nếu đã xóa lọc vẫn thiếu dữ liệu, kiểm tra booking có nằm trong dữ liệu đang dùng hay không.

Sao lưu trước:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chờ Đã sao lưu và kiểm tra, Ctrl+C tại terminal đang chạy cổng 8000. Sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở. Với dịch vụ riêng, khởi động lại đúng dịch vụ thay vì tạo tiến trình trùng cổng. Không thay cấu hình SePay. Không migration mới. Sau cập nhật nhấn Ctrl+F5.

Đã kiểm tra trình duyệt với booking lịch sử tháng 10 khi tháng đang chọn là tháng 11, khôi phục điều kiện lọc cũ, chuyển qua lại tháng/khoảng ngày, tổng tiền/đã thu/nợ, kết hợp bộ lọc cột và xóa lọc. Chưa cập nhật trực tiếp Ubuntu.
