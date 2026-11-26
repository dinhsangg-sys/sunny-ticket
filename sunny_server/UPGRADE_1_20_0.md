# 1.20.0 — Bài dịch vụ, giỏ hàng, thanh toán ngay và quản trị gửi vé

## Luồng khách

- `/services/` và các thẻ Trải nghiệm cho hành trình dẫn đến bài giới thiệu của từng dịch vụ (Ký Ức, Bà Nà, Vin, Lune, Rừng Dừa… do quản trị khai báo).
- Trang dịch vụ: bài viết/ảnh khoảng 3/4 bên trái, chọn ngày, loại vé và số lượng khoảng 1/4 bên phải trên máy tính. Điện thoại xếp dọc. Bộ chọn nằm bên cạnh bài khi cuộn trên máy tính.
- Có hai lựa chọn: **Thêm vào giỏ hàng**, hoặc **Thanh toán ngay**. Thanh toán ngay không qua trang giỏ, không lấy các dịch vụ khác trong giỏ và không xóa giỏ hiện có.
- Biểu tượng giỏ cạnh ngôn ngữ hiển thị số vé. Trong giỏ, khách chọn các dòng cần trả tiền, đổi số lượng/bỏ mục rồi bấm Cập nhật.
- Khách nhập họ tên, email và số điện thoại, kiểm tra dịch vụ/ngày/tổng tiền rồi tạo QR SePay cho toàn bộ đơn. Giá được tính tại máy chủ; nếu giá đổi trước khi tạo đơn, yêu cầu khách mở lại bước kiểm tra.
- Đơn giữ giá 30 phút trước khi tạo QR; QR theo thời hạn SePay đã cấu hình. Thanh toán chỉ được ghi nhận từ webhook hợp lệ, đúng tiền/tài khoản/thời gian. Không xác nhận từ trình duyệt.
- Mỗi dòng dịch vụ được ghi thành booking riêng trong Ticket Management; tổng khoản thu đúng bằng tổng thanh toán, không ghi thêm một khoản thu ở đơn tổng. Lưu mã đơn tổng để đối soát.

## Khai báo bài và vé trong quản trị

1. Vào `/admin/online/service/` → Dịch vụ online. Viết tên, giới thiệu, bài/điều kiện và tải ảnh; có nội dung Việt/Anh. Bật Hiển thị công khai khi sẵn sàng.
2. Có thể giữ Loại vé mặc định cho dịch vụ chỉ có một loại. Nếu bán nhiều loại, bỏ trống vé mặc định và thêm các dòng **Lựa chọn vé online** trong bài: ví dụ `ECO · Người lớn`, `ECO · Trẻ em`, `HIGH · Người lớn`… Mỗi dòng chọn đúng loại vé đã khai báo trong Ticket Management, có tên tiếng Anh và thứ tự riêng.
3. Vào `/admin/online/onlineprice/`: chọn Dịch vụ + Lựa chọn vé, nhập giá online và thời gian áp dụng. Nếu dùng vé mặc định, để trống Lựa chọn vé. Các kỳ giá của cùng lựa chọn không được trùng; mỗi lựa chọn được đặt giá độc lập.
4. Loại vé phải đang hoạt động và có giá vốn/nhà cung cấp mặc định hợp lệ trong Ticket Management. Nếu thiếu dữ liệu, khách không thể chọn loại đó. Không tự lấy giá đại lý làm giá online.

Không tự thêm giá, hình ảnh hoặc nội dung quảng bá chưa được chủ website kiểm tra vào dữ liệu thật. Các dữ liệu cũ giữ nguyên; các dịch vụ cũ dùng vé mặc định vẫn hoạt động.

## Xử lý và gửi vé

- Menu **Đơn vé online** trong trang quản lý, hoặc `/online/staff/`, có phần **Đơn giỏ hàng / Nhiều dịch vụ**. Mặc định hiện đơn đã thanh toán nhưng chưa ghi nhận gửi vé; có nút xem cả đơn đã gửi.
- Trong Django admin có mục **Đơn giỏ hàng online / Chờ gửi vé**, liên kết thẳng đến màn hình xử lý.
- Quản trị có quyền mặc định. Nhân viên cần `online.process_orders` và quyền `legacy.counter__view`, `legacy.counter__create`. Không cấp các quyền này cho khách.
- Mở đơn → kiểm tra khách/dịch vụ/ngày/số lượng → tải PDF/PNG/JPEG → kiểm tra đủ vé → xác nhận và bấm **Gửi vé cho khách**. Gửi đến đúng email đã đặt, không cho đổi người nhận tại màn hình xử lý.
- Mỗi đơn tối đa 8 tệp, mỗi tệp 10 MB, tổng 20 MB. Có thể bỏ tệp đính nhầm trước khi gửi. Vé được lưu trong `sunny_server/private_online_tickets/`, ngoài media công khai; không cấu hình web server phục vụ trực tiếp thư mục này. Sao lưu kèm database và thư mục vé riêng này.
- Nếu đã gửi bằng hộp thư riêng, mở phần **Đã gửi vé bằng hộp thư bên ngoài** rồi nhập ghi chú/tham chiếu và xác nhận. Thao tác ghi nhận này không tự gửi email.
- Hệ thống lưu người xử lý và thời gian. Trạng thái sent nghĩa là SMTP nhận thư, không bảo đảm thư đã vào inbox hoặc khách đã đọc.
- Nếu SMTP lỗi hoặc kết quả không rõ, không tự gửi lại. Kiểm tra hộp thư gửi, có thể gửi thủ công rồi ghi nhận bên ngoài. Nếu ứng dụng bị ngắt khi đang gửi, chờ ít nhất 5 phút rồi đối soát và ghi nhận kết quả bằng phần bên ngoài; không bấm gửi lặp.
- Các đơn online một loại vé trước đây vẫn dùng công cụ nhận/import/in/gửi vé hiện có.

## Email thông báo quản trị

Trong `/etc/sunny-sepay.env` có thể thêm:

```dotenv
ONLINE_ADMIN_EMAIL=info@sunnygovn.com
```

Dùng địa chỉ thực sự muốn nhận thông báo. Nếu để trống, dùng email tài khoản `ONLINE_PAYMENT_OWNER`. Nếu cả hai trống, đơn vẫn xuất hiện trong danh sách chờ xử lý, trạng thái thông báo cho biết chưa cấu hình.

Giữ nguyên SMTP, `DEFAULT_FROM_EMAIL`, ngân hàng và khóa SePay đang dùng. Thanh toán vẫn theo `ONLINE_CHECKOUT_ENABLED`, `ONLINE_PAYMENT_OWNER` và cấu hình SePay/email sẵn có; bản cập nhật không tự bật nhận tiền thật. Chỉ thông báo quản trị sau khi giao dịch được lưu thành công. Thông báo lỗi không làm mất khoản thanh toán đã ghi nhận.

## Cập nhật Ubuntu

Có migration mới `online.0006_service_options_cart_orders`. Dừng đúng cửa sổ ứng dụng bằng Ctrl+C, sao lưu database/media/cấu hình và vé riêng trước khi cập nhật. Nếu đang dùng SQLite, tiện ích sao lưu hiện có đọc cả thư mục ứng dụng; nếu dùng PostgreSQL, sao lưu bằng quy trình database đang vận hành.

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
