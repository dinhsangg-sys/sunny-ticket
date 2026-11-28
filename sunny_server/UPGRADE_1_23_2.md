# 1.23.2 — Email booking tiếng Anh theo nhận diện Sunny

Thay email văn bản thông báo quản trị bằng mẫu HTML tiếng Anh: logo Sunny, header xanh/vàng, mã booking, ngày giờ tạo (giờ Việt Nam), trạng thái, phương thức thanh toán, thông tin khách, từng dịch vụ/loại vé/ngày sử dụng/số lượng/giá vé/thành tiền, tổng đơn, địa điểm giao vé (nếu có), nút mở booking và thông tin doanh nghiệp.

Có hai nội dung rõ ràng:

- **Ticket delivery request**: yêu cầu giao vé và thu tiền ở Đà Nẵng, ghi rõ **Not paid**, chưa xác nhận lịch giao và chưa thu tiền.
- **Payment received**: đơn đã ghi nhận thanh toán, yêu cầu nhân viên kiểm tra và gửi vé.

Không gọi yêu cầu tiền mặt là đã thanh toán hoặc đã xác nhận giao vé. Tiêu đề mail cũng chuyển sang tiếng Anh. Tên dịch vụ/loại vé dùng bản tiếng Anh đã khai báo trong snapshot; nếu chưa có, giữ tên gốc, không tự dịch hay thay đổi đơn cũ.

Email gồm cả HTML và bản text dự phòng. Dữ liệu khách/nội dung giao vé được escape ở bản HTML. Nơi nhận giữ nguyên ONLINE_ADMIN_EMAIL, hoặc email của ONLINE_PAYMENT_OWNER nếu chưa khai báo. Không tự thêm người nhận hoặc gửi xác nhận mới tới khách trong bản này. Quy trình gửi vé đính kèm cho khách vẫn như trước. Không thay đổi cách thu tiền hoặc báo cáo.

## Cập nhật

Không có migration mới. Dừng ứng dụng trong đúng terminal bằng Ctrl+C; sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Nếu chưa cập nhật 1.23.0 thì cần chạy migrate và collectstatic theo [hướng dẫn 1.23.0](UPGRADE_1_23_0.md). Các thông báo booking mới sau khi khởi động lại sẽ dùng mẫu mới; không tự gửi lại email cũ.
