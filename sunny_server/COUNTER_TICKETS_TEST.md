# Bản bổ sung module quầy: nhập QR, xuất PDF, in và email

Chỉ trên nhánh `codex/counter-sales`. Không đổi main hoặc stable-1.10.13, không tự thay dữ liệu live. Test tại thư mục/cổng riêng.

## Cập nhật Ubuntu thử nghiệm

Ctrl+C tại terminal chạy server **8001**, không dừng server chính 8000. Sau đó:

```bash
cd /home/sunny-ticket-counter-test
sudo git pull --ff-only origin codex/counter-sales
sudo apt-get update
sudo apt-get install -y fonts-dejavu-core tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng
cd sunny_server
sudo .venv/bin/pip install -r requirements.txt
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8001
```

Giữ terminal mở, Ctrl+F5 trên trang thử nghiệm. Không reset database. Migration 0009 thêm bảng quản lý bộ vé và QR đã gắn; không xóa booking cũ. Chưa triển khai rollback tự động; sao lưu database cùng thư mục private_counter trước khi thay đổi môi trường có dữ liệu quan trọng.

## Tạo booking và nhập vé

- Có thêm Email khách hàng (không bắt buộc) và file PDF/JPEG/PNG khi tạo booking. Cho chọn nhiều file ảnh/PDF trong cùng lần, tối đa 20 file, tổng 20 MB và 50 trang/vé.
- Booking được lưu trước; nếu nhập vé lỗi thì booking vẫn tồn tại, không tạo lại. Dùng nút **Nhập / In / Gửi vé** trong Booking của tôi để nhập lại hoặc nhập sau.
- PDF/ảnh có thể có nhiều vé với QR riêng nếu có khoảng trắng phân cách rõ giữa các vùng vé. Nếu không tách rõ, cần cắt từng vé trước; không tự đoán thông tin của nhiều QR. File bị khóa, QR mờ/không đọc được hoặc QR trùng trong lần nhập bị từ chối.
- PDF có text đọc trực tiếp. Ảnh/PDF scan dùng Tesseract vie+eng nếu cài được; nếu OCR thiếu/sai, các trường để trống hoặc cần sửa ở bước kiểm tra. Không có cam kết đọc tự động mọi bố cục. JPEG/PNG chỉ mang QR cũng được nhập, nhưng phải điền đủ trường trước khi xuất.

## Xem trước và xuất/in

1. Chọn bộ file đã nhập, xem từng ảnh QR và các trường: hạn dùng, gói dịch vụ, giờ PARK/SHOW, mã vé, đại lý gốc.
2. Chọn số vé đúng bằng số lượng booking. Nếu file có 12 vé nhưng booking 4 vé, chỉ tick đúng 4 trang cho booking đó. Không tự tăng số lượng hoặc nhân bản QR.
3. Kiểm tra/sửa thông tin theo vé gốc và tick xác nhận. Ngày tạo booking không thay hạn sử dụng trên vé. Phần mềm không tự suy diễn loại vé nguồn có đúng SKU booking hay không; nhân viên phải đối chiếu gói dịch vụ trước khi xác nhận.
4. Bấm **Tạo PDF theo mẫu 80 × 110 mm**. Ảnh QR được lấy từ nguồn, không tạo lại từ mã vé in chữ; hệ thống quét lại PDF đầu ra và so payload với QR nguồn từng vé. Mỗi vé một trang 80x110 mm.
5. Dùng **Tải PDF**, **Mở PDF riêng** hoặc **In vé**. Chọn khổ giấy 80x110 mm và Actual size/100%, kiểm tra lề máy in. Nếu trình duyệt không mở được print từ khung preview, mở PDF riêng và dùng nút In/Ctrl+P. Chưa test máy in vật lý; gọi print không chứng minh đã in thành công.

File PDF nguồn không bị sửa. Sau xác nhận, bộ QR/thông tin đầu ra được giữ cố định; in/tải lại không tạo QR mới. QR đã gắn với booking khác bị chặn; một booking không được xuất thêm bộ QR khác. Sai thông tin sau xác nhận cần quản trị đối soát, chưa có luồng hủy/cấp lại tự động trong bản thử nghiệm.

Đã thử file mẫu 12 trang/hai bố cục do người dùng cung cấp: đọc được các trường và xác minh QR đầu ra khớp nguồn cả 12 trang. Đây là kiểm tra nội dung QR, không xác nhận vé còn hạn hoặc được cổng soát vé chấp nhận.

## Email

Mặc định **tắt gửi email thật**. Xuất PDF/in vẫn hoạt động khi chưa có SMTP. Để thử mail, quản trị cấu hình các biến môi trường cho tiến trình server thử nghiệm:

```text
COUNTER_EMAIL_ENABLED=1
DJANGO_DEFAULT_FROM_EMAIL=tickets@example.com
DJANGO_EMAIL_HOST=smtp.example.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_USE_TLS=1
DJANGO_EMAIL_USE_SSL=0
DJANGO_EMAIL_HOST_USER=tickets@example.com
DJANGO_EMAIL_HOST_PASSWORD=<mat-khau-ung-dung-hoac-thong-tin-SMTP>
```

Giá trị trên chỉ là ví dụ, cần dùng nhà cung cấp/hộp thư thực tế. Không đưa mật khẩu lên GitHub hoặc gửi qua chat. Nếu dùng file môi trường, bảo vệ quyền truy cập và bảo đảm tiến trình chạy dưới sudo thực sự nhận các biến; dự án không tự đọc file .env. TLS và SSL không bật cùng lúc. Có thể đặt COUNTER_TICKET_FONT nếu cần đường dẫn font Việt riêng.

Sau khi PDF sẵn sàng, kiểm tra email và bấm **Gửi PDF vé qua email**, rồi xác nhận người nhận. Chỉ gửi PDF đầu ra của booking, không gửi file nguồn hoặc dữ liệu giá vốn. Một bộ vé được gửi một lần; bấm lặp không gửi thêm. Thành công nghĩa máy chủ thư tiếp nhận, không chứng minh khách đã nhận/đọc. Khi lỗi/timeout, trạng thái cần đối soát sẽ chặn gửi lại tự động để tránh gửi trùng; chưa có nút bỏ trạng thái/hủy đợt gửi cho nhân viên. Chưa thử SMTP thật vì chưa có cấu hình gửi.

## Lưu trữ và quyền

File nguồn/QR/PDF ở `sunny_server/private_counter`, hoặc COUNTER_PRIVATE_ROOT nếu cấu hình riêng. Đường dẫn không được public static/media; file chỉ được lấy qua API kiểm tra tài khoản và booking. Không cấu hình Nginx/public file server để lộ thư mục này. Nhân viên không xem/tải/gửi bộ vé của người khác; superuser có thể đối soát. Các thao tác dùng quyền counter.view/counter.create hiện có.

Sao lưu cả database và private_counter, không chỉ database. Không đưa file vé thật/QR thật vào GitHub. Chỉ template nền đã duyệt, không có QR thật, được đưa vào mã nguồn. Cần đối soát bộ vé khi ai đó sửa số lượng/xóa booking từ màn hình nội bộ; không tự tái cấp mã QR.

## Kiểm thử

92 test backend hồi quy đạt; các ca mới kiểm tra PDF/JPEG/PNG, QR trùng, số lượng/xác nhận, khổ trang, trích text, kiểm tra QR đầu ra, quyền chéo nhân viên, PDF same-origin, gắn QR cho booking khác, đóng băng bộ vé, email bị tắt hoặc gửi một lần, timeout không gửi lại. Email dùng backend hộp thư giả lập, không gửi ra bên ngoài. Frontend thật với API giả lập kiểm tra review, xác nhận, preview/link PDF, nút in và trạng thái mail chưa cấu hình. Chưa nghiệm thu OCR với mọi ảnh thực tế, máy in vật lý hoặc SMTP thật.
