# 1.12.7 — Khoảng ngày trong Báo cáo Tổng quan

Trong **Báo cáo → Tổng quan**, thay ô Ngày bằng **Từ ngày** và **Đến ngày**. Mặc định cả hai là hôm nay, tương đương báo cáo một ngày cũ. Đổi ngày tự cập nhật; nút Xem vẫn sử dụng được. Lựa chọn được giữ khi đổi tab báo cáo trong phiên đang mở.

Doanh thu, Lợi nhuận, Đã thu, Khách còn nợ, VAT và Còn trả tiền vé tính theo các booking có ngày nằm trong khoảng đã chọn, bao gồm ngày đầu/cuối; áp dụng dữ liệu lịch sử. Đã thu và còn nợ là tình trạng hiện tại của các booking đó, không phải báo cáo giao dịch thu/chi phát sinh riêng trong khoảng ngày. Công thức tính các chỉ tiêu giữ nguyên.

Để trống một đầu mốc sẽ không giới hạn đầu đó; trống cả hai tính toàn thời gian. Không có booking thì các chỉ tiêu về 0. Nếu Từ ngày sau Đến ngày, hiển thị lỗi và ẩn số liệu cũ để tránh nhầm.

## Cập nhật Ubuntu

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chờ **Đã sao lưu và kiểm tra**. Dừng tiến trình bản chính cổng 8000 bằng Ctrl+C tại terminal đang chạy, rồi:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở. Nếu dùng dịch vụ, khởi động lại đúng dịch vụ thay vì chạy trùng cổng. Không migration mới, không thay cấu hình SePay. Trình duyệt nhấn Ctrl+F5.

Kiểm tra trình duyệt: một ngày/khoảng nhiều ngày, hai đầu mốc, dữ liệu lịch sử, giữ lựa chọn khi đổi tab, bỏ giới hạn, khoảng rỗng và ngày đảo ngược; đối chiếu đủ 6 chỉ tiêu và hồi quy điều hướng báo cáo. Chưa triển khai Ubuntu trực tiếp.
