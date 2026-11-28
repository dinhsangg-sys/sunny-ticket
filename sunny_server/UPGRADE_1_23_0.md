# 1.23.0 — Chi tiết đơn, phương thức thanh toán và giao vé thu tiền mặt

## Trang đơn hàng

Thông tin khách có nhãn họ tên, email, điện thoại. Từng dịch vụ có loại vé, ngày sử dụng, số lượng, giá một vé và thành tiền. Tổng đơn rõ ràng, số tiền có dấu phân cách. Nội dung Việt/Anh và bố cục điện thoại được hỗ trợ.

Phương thức thanh toán:

- **QR chuyển khoản:** chọn rồi tạo QR, quy trình SePay hiện có. Sau khi tạo QR, không tự chuyển sang tiền mặt; cần nhân viên kiểm tra để tránh thu trùng nếu khách đã chuyển khoản.
- **Visa / Mastercard:** khách có thể chọn để xem thông báo chưa khả dụng. Không thu thông tin thẻ và không xử lý giao dịch thẻ. Phía máy chủ cũng từ chối các phương thức này.
- **Tiền mặt khi giao vé tại Đà Nẵng:** khách xác nhận nhận vé/thu tiền ở Đà Nẵng, có thể ghi khách sạn hoặc địa điểm, rồi gửi yêu cầu. Khách giữ mã đơn hàng; nhân viên liên hệ số điện thoại đã đăng ký. Lịch và địa điểm phải được nhân viên xác nhận, chưa tự bảo đảm còn vé hoặc đã đặt lịch giao.

Ô đồng ý ở thông tin nhận vé đã chuyển lên trước nội dung, căn cùng hàng đầu trên máy tính và điện thoại.

## Tiền mặt và báo cáo

Yêu cầu tiền mặt xuất hiện trong **Đơn vé online** cùng đơn đã thanh toán chờ gửi vé. Khi mới gửi yêu cầu: trạng thái vẫn chưa thanh toán, không tạo QR, không tạo booking tài chính và không ghi nhận doanh thu.

Nhân viên mở đơn để xem số điện thoại và ghi chú giao vé. Sau khi thực sự giao đúng vé và nhận đủ tiền, người có quyền nhập đúng số tiền thực thu, ghi chú và xác nhận **Đã giao vé & thu đủ tiền**. Hệ thống tạo booking theo từng dịch vụ, đối tượng **Digital**, phương thức **Tiền mặt**, ngày thu thực tế; lưu người xác nhận và nhật ký. Xác nhận lại không tạo thêm khoản thu. Ngày sử dụng đã qua hoặc chi tiết/số tiền không khớp phải đối soát trước, không tự ghi nhận.

Quản trị superuser có quyền mặc định. Nhân viên cần các quyền xử lý đơn online, xem/tạo vé tại quầy như trước, và quyền mới **online | Đơn giỏ hàng online | Xác nhận giao vé và thu tiền mặt đơn online** (`online.collect_cash_orders`). Người chỉ xử lý/gửi email vé không tự có quyền thu tiền mặt.

Không đổi khoản thu, giá hay nội dung của đơn cũ. Migration mới `online.0012_cash_delivery_requests` bổ sung trường phương thức, thời gian yêu cầu và thông tin giao vé, cùng quyền thu tiền mặt.

## Thông báo và cấu hình

Thông báo gửi tới `ONLINE_ADMIN_EMAIL`; nếu chưa khai báo thì dùng email tài khoản `ONLINE_PAYMENT_OWNER`. Có thể đặt trong `/etc/sunny-sepay.env`:

```ini
ONLINE_ADMIN_EMAIL=booking@sunnygovn.com
```

Khởi động lại ứng dụng sau khi đổi cấu hình. Nếu email không gửi được, yêu cầu vẫn nằm trong danh sách quản trị để xử lý; không chuyển thành đã thanh toán.

## Sửa lỗi CSRF khi tạo QR

Trang đơn hàng trước đây gửi header Referrer-Policy: no-referrer, có thể làm thiếu nguồn xác thực trên HTTPS. Bản này đổi trang đơn có biểu mẫu sang **same-origin**, giữ CSRF token và kiểm tra nguồn. Nguồn khác không được phép vẫn bị từ chối. Không tắt CSRF hoặc thêm wildcard.

Tên miền công khai vẫn cần nằm trong `DJANGO_CSRF_TRUSTED_ORIGINS`. Sau cập nhật tải lại trang đơn để lấy token mới. Nếu vẫn lỗi, kiểm tra lý do CSRF trong log và header do proxy trả về; không suy đoán đây là lỗi SePay. Đơn quá 30 phút chưa tạo QR/yêu cầu tiền mặt phải đặt lại để kiểm tra giá mới.

## Cập nhật máy chủ

Sao lưu dữ liệu và media. Trong đúng terminal đang chạy ứng dụng, Ctrl+C để dừng trước khi cập nhật; không mở thêm một tiến trình cổng 8000.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ mở; tải lại trang bằng Ctrl+F5. Kiểm tra chế độ SePay trước giao dịch thật, không dùng QR test để nhận tiền thật. Triển khai thực tế và kiểm tra giao dịch/SMTP do người vận hành thực hiện; các kiểm thử mã dùng dữ liệu tách biệt.
