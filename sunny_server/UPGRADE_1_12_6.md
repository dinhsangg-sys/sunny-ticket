# 1.12.6 — Xuất Excel báo cáo VAT theo bộ lọc

Vào **Báo cáo → VAT**, chọn Từ ngày/Đến ngày/Thuế suất, bấm **Xuất Excel** bên cạnh Xem VAT. File .xlsx dùng chung hàm lọc và tính tổng với báo cáo hiển thị; áp dụng cả dữ liệu lịch sử. Để trống ngày hoặc chọn Tất cả thuế suất để bỏ điều kiện đó.

File có thông tin khoảng thời gian/thuế suất, số booking và số vé xuất VAT, giá trị tính VAT, tổng tiền VAT; chi tiết gồm mã booking, ngày, khách hàng/đại lý, loại vé, số lượng, tổng giá bán, tổng giá vốn, giá trị tính VAT, VAT %, tiền VAT, kèm Tổng cộng. Số lượng, số tiền và tỷ lệ được lưu dạng số, giữ tiếng Việt; hàng tiêu đề có bộ lọc Excel. Giữ nguyên công thức VAT hiện có, không thay quy tắc thuế.

Không có booking phù hợp, khoảng ngày đảo ngược hoặc thư viện Excel chưa tải được thì hiển thị thông báo và không tạo file. Tính năng dùng thư viện Excel sẵn có trên web; nếu bị chặn CDN, kiểm tra kết nối hoặc chính sách trình duyệt.

## Cập nhật Ubuntu

Sao lưu trước:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chờ **Đã sao lưu và kiểm tra**. Dừng tiến trình bản chính cổng 8000 bằng Ctrl+C tại cửa sổ đang chạy, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở. Nếu có dịch vụ riêng, khởi động lại đúng dịch vụ hiện có thay vì chạy trùng cổng. Không thay cấu hình SePay, không cần migration mới. Trình duyệt nhấn Ctrl+F5 rồi mở Báo cáo → VAT.

Kiểm tra tự động qua trình duyệt: lọc ngày kể cả hai đầu mốc, lọc thuế suất, loại booking không có VAT, so khớp chỉ tiêu trên màn hình với dữ liệu đưa vào thư viện Excel, định dạng số/tiền/tỷ lệ và tiếng Việt, không xuất khi rỗng/ngày sai/thiếu thư viện. Chưa triển khai Ubuntu trực tiếp hoặc mở file bằng Excel trên máy người dùng.
