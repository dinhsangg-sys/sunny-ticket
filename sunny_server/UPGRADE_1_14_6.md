# 1.14.6 — Đổi tiêu đề mẫu vé

Thay logo Hoi An Memories Land ở đầu mẫu vé bằng chữ đen đậm Hoi An Memories Show, căn giữa để in máy nhiệt. Kích thước vẫn 80 x 110 mm; không đổi hình minh họa, QR và vị trí thông tin vé.

Mẫu dùng chung cho PDF xuất mới, bản in và tệp PDF gửi email. PDF đã tạo trước cập nhật không tự thay đổi. Để dùng tiêu đề mới cho booking cũ cần tạo lại vé qua quy trình cập nhật/tạo lại vé hiện có và kiểm tra trước khi in/gửi. Không tự gửi email hoặc sửa PDF lịch sử khi nâng cấp.

Sao lưu trước theo hướng dẫn 1.14.0. Sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
```

Không có migration mới, không thay cấu hình SePay/Souvenirs. Nếu khởi động lại runserver, Ctrl+C tại đúng cửa sổ đang chạy rồi chạy lại:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ web mở. Tạo một PDF mới để kiểm tra tiêu đề trước khi in thực tế. Đã kiểm tra render mẫu, kích thước 80 x 110 mm và kiểm thử xuất vé/QR/giữ lịch sử bằng quy trình xuất thực tế của ứng dụng; chưa in trên máy nhiệt thật.
