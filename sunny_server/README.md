# Sunny Travel — bản chính thức 1.11.0

Bản quầy đã được nghiệm thu và phát hành trên main. Đọc [UPGRADE_1_11_0.md](UPGRADE_1_11_0.md) để sao lưu và nâng cấp bản chính. Không chạy các hướng dẫn reset dữ liệu thuộc lịch sử cũ bên dưới khi nâng cấp 1.11.0.

## Lịch sử các bản chuyển đổi

**Lịch sử 1.10.1:** bỏ module ánh xạ, khởi tạo dữ liệu mới theo yêu cầu. Đọc UPGRADE_1_10_1.md và chạy reset_business_data trên máy Ubuntu để xóa nghiệp vụ cũ nhưng giữ tài khoản/quyền. Các hướng dẫn gộp dữ liệu ở phiên bản trước không còn áp dụng.

Bản test 1.10.0 có thay đổi database permissions và bảo toàn quyền người dùng cũ qua migration. Đọc UPGRADE_1_10_0.md trước nâng cấp; không áp dụng mô tả operator/quyền rộng của bản cũ cho tài khoản mới không có quyền đầy đủ.

Bản cập nhật 1.9.8.1: xem [hướng dẫn nâng cấp và cấu hình domain HTTPS](UPGRADE_1_9_8_1.md). Lịch sử lỗi và trạng thái nghiệm thu trong ISSUES.md.

Giữ giao diện và các hàm nghiệp vụ của HTML v1.9.8, tách CSS/JS, thêm Django authentication, dữ liệu chung trên server, revision chống ghi đè, nhật ký lưu và file chiến dịch trên server. HTML gốc ở thư mục cha không bị sửa.

## Chạy test trên Ubuntu

Yêu cầu Python 3.12 trở lên. Các lệnh dưới đây chạy từ thư mục `sunny_server`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py runserver 127.0.0.1:8000
```

Truy cập http://127.0.0.1:8000 và đăng nhập bằng tài khoản vừa tạo. SQLite được dùng cho test nhanh; production dùng PostgreSQL. Không có mật khẩu mặc định.

## Tài khoản và đại lý

- Superuser: truy cập ứng dụng và `/admin/`, quản lý user.
- `operator`: toàn quyền nghiệp vụ nội bộ như HTML gốc, không có quyền quản lý user mặc định. Chỉ cấp cho nhân sự tin cậy.
- `agency`: chỉ xem booking và công nợ của đại lý được gán; không tải toàn bộ dữ liệu nội bộ, không xem giá vốn/lợi nhuận, không được ghi dữ liệu.
- Tạo/nhập đại lý trong ứng dụng trước, sau đó vào `/admin/` tạo user, chọn role và gán Agency tương ứng. Không bật `is_staff` hoặc `is_superuser` cho user đại lý.
- Đổi tên đại lý cần kiểm tra booking cũ vì mô hình HTML đang liên kết bằng tên. Trùng tên đại lý sẽ bị chặn hiển thị dữ liệu trên cổng đại lý.

## Đưa dữ liệu HTML vào server

1. Mở HTML gốc trong đúng trình duyệt đang chứa dữ liệu.
2. Vào Dữ liệu, xuất bản sao lưu JSON đầy đủ.
3. Đăng nhập bản server bằng superuser, vào Dữ liệu và nhập JSON.
4. Đối chiếu số booking, doanh thu, công nợ phải thu/phải trả, tồn quỹ và lợi nhuận.
5. File ảnh/video IndexedDB không nằm trong JSON: tải từ bản cũ rồi thêm lại vào chiến dịch trên server. Sau khi chuyển, xóa metadata tệp cũ không mở được.

Không tự nhập localStorage để tránh nhập nhầm dữ liệu từ trình duyệt khác. Dữ liệu trên server được tải lúc mở trang. Khi có sửa đổi từ người khác, lần lưu tiếp theo sẽ bị từ chối và khóa thao tác; tải lại trang để lấy bản mới. Không tự hợp nhất giao dịch tài chính.

## Phạm vi và giới hạn của bản test

Đây là cầu nối tương thích để test đầy đủ chức năng HTML, chưa phải bản production đã chuẩn hóa nghiệp vụ:

- Booking, giá, công nợ và báo cáo vẫn dùng logic JavaScript gốc; server lưu snapshot JSON trong transaction với revision. Không được coi số tiền do client gửi là dữ liệu đã được backend xác minh.
- Chưa tách bảng nghiệp vụ thành catalog/pricing/bookings/finance, chưa có API giao dịch riêng, quy trình duyệt hoặc nhật ký chi tiết trước/sau từng trường.
- Chưa có phân quyền quản lý/kế toán theo từng thao tác. Operator có quyền tương đương người dùng HTML cũ, gồm nhập/xóa/sửa dữ liệu tài chính.
- Cổng đại lý mới chỉ đọc; chưa hỗ trợ đại lý đặt booking, quản lý nhân viên hoặc xem bảng giá riêng.
- Đồng bộ snapshot sử dụng XMLHttpRequest đồng bộ để giữ nguyên hợp đồng `save()` của mã gốc; phù hợp kiểm thử chuyển đổi, cần thay bằng API bất đồng bộ khi chuẩn hóa backend.
- Mẫu chữ trong HTML về lưu file trên trình duyệt được giữ nguyên ở một số màn hình; trong bản này file mới được tải lên server.
- Excel vẫn tải thư viện XLSX từ CDN như bản gốc; cần Internet. Zalo vẫn gửi thủ công, không tự động gửi.
- Không tuyên bố đã kiểm thử thủ công mọi thao tác trong trình duyệt. Dùng CHECKLIST_TEST.md để nghiệm thu với dữ liệu của bạn.

## Triển khai Ubuntu với PostgreSQL

1. Cài Python/venv, PostgreSQL, Nginx; tạo database và user riêng cho Sunny.
2. Đặt mã nguồn thư mục này ở `/opt/sunny/app`, venv ở `/opt/sunny/venv`.
3. Tạo user hệ thống `sunny`; cấp quyền đọc mã, ghi `/var/lib/sunny/media`; Nginx có quyền đọc `staticfiles`. Tạo thư mục staticfiles trước `collectstatic` và cấp quyền ghi phù hợp cho user chạy lệnh.
4. Sao chép `deploy/sunny.env.example` thành `/etc/sunny/sunny.env`, thay secret, domain và mật khẩu; quyền file `0600`. Giữ secret ngoài mã nguồn.
5. Nạp môi trường bằng shell quản trị có quyền đọc file:

```bash
set -a
. /etc/sunny/sunny.env
set +a
/opt/sunny/venv/bin/python manage.py migrate
/opt/sunny/venv/bin/python manage.py createsuperuser
/opt/sunny/venv/bin/python manage.py collectstatic --noinput
/opt/sunny/venv/bin/python manage.py check --deploy
```

6. Thay domain và đường dẫn chứng chỉ trong `deploy/nginx.conf`, cấp chứng chỉ HTTPS trước khi bật cấu hình TLS. Sao chép service vào `/etc/systemd/system/sunny.service`, cấu hình Nginx vào site riêng; chạy `nginx -t`, `systemctl daemon-reload`, `systemctl enable --now sunny`, rồi reload Nginx.
7. Gunicorn chỉ nghe 127.0.0.1:8000; chỉ Nginx được truy cập trực tiếp từ Internet. Không expose thư mục media bằng Nginx: tệp được tải qua view có kiểm tra đăng nhập.
8. Sao lưu PostgreSQL và `/var/lib/sunny/media` cùng một thời điểm bằng cách tạm ngừng ghi; mã nguồn/migrations lưu theo release. Thử khôi phục trước khi sử dụng thật.

Không đưa dữ liệu thật lên Internet trước khi hoàn tất kiểm thử phân quyền, đối soát và chuẩn hóa các giới hạn nêu trên.
