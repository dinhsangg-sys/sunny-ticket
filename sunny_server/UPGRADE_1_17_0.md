# 1.17.0 — Thu tiền theo phương thức thanh toán

## Vị trí

- Ticket Management → Báo cáo → Thu theo phương thức.
- Souvenirs / Bán hàng lưu niệm → bên dưới Doanh thu Souvenirs, mục Thu tiền theo phương thức thanh toán.
- Trang nghiệp vụ theo quyền → Báo cáo → Thu tiền theo phương thức (khi đã được cấp quyền).
- Đường dẫn riêng: /reports/payment-methods/?source=tickets hoặc ?source=souvenirs.

## Chỉ tiêu và bộ lọc

Từ ngày / Đến ngày theo ngày thu tiền, Phương thức (tất cả/tiền mặt/chuyển khoản/thẻ/chưa xác định). Mặc định tháng hiện tại đến hôm nay; Xóa lọc xem tất cả thời gian.

Bốn nhóm phương thức có tổng tiền và số khoản thu/booking. Có tổng thu, phí thẻ đã lưu, thực nhận theo phí đã lưu, bảng nhóm và chi tiết ngày thu/mã booking hoặc đơn/khách hàng hoặc người bán/phương thức/số tiền/phí/thực nhận. Một booking thu nhiều lần được tính theo từng khoản thu; số booking tổng được đếm riêng, không cộng số booking của từng nhóm để tránh trùng khi một booking dùng nhiều phương thức.

Có xuất CSV UTF-8 mở bằng Excel theo đúng bộ lọc đang áp dụng, gồm phần tổng hợp và chi tiết. Số tiền là giá trị số; các trường văn bản được bảo vệ để không chạy công thức Excel. Không cần cài thêm thư viện.

## Cách tính

- Bán vé: đọc từng khoản trong payments của booking đang hoạt động. Lọc theo date của khoản thu; nếu thiếu date thì dùng createdAt có múi giờ và quy đổi giờ Việt Nam. Không dùng ngày booking để đoán ngày thu và không cộng doanh thu chưa thu.
- Souvenirs: đơn paid chưa xóa, lọc paid_at theo ngày giờ Việt Nam. Đơn chờ, đơn hủy và đơn đã xóa không tính.
- Phương thức theo dữ liệu của chính khoản thu: cash/bank_transfer/card. Nếu thiếu trường phương thức nhưng có snapshot phí thẻ thì nhận diện là thẻ; nếu có provider SePay thì chuyển khoản. Không đoán từ ghi chú hoặc phương thức hiện tại của booking vì booking có thể thu nhiều lần khác phương thức.
- Dữ liệu cũ chưa lưu phương thức nằm trong Chưa xác định. Không tự quy về tiền mặt, không sửa dữ liệu cũ để tạo số liệu báo cáo.
- Khoản thiếu cả ngày thu lẫn timestamp hợp lệ chỉ hiện khi bỏ bộ lọc ngày. Báo cáo cảnh báo số khoản/số tiền chưa xác định ngày, không âm thầm gán ngày booking.
- Phí chỉ lấy từ snapshot đã lưu. Giao dịch thẻ chưa lưu phí được cảnh báo; số thực nhận lúc này chưa trừ phần phí chưa biết. Không áp biểu phí hôm nay vào giao dịch cũ.
- Đây là báo cáo các khoản thu hợp lệ hiện đang lưu, không phải sao kê ngân hàng hoặc sổ hoàn tiền. Booking hủy/xóa không tính; phí không hoàn khi hủy xem tại Sổ quỹ. Đơn Souvenirs đã thu được sửa tiền sẽ phản ánh số tiền đã điều chỉnh vào kỳ thu gốc theo paid_at, giống báo cáo doanh thu Souvenirs hiện có.
- Bản ghi tiền/phí không hợp lệ bị bỏ qua có cảnh báo; không đổi số liệu gốc.

## Quyền

Bán vé: superuser hoặc nhân sự admin/operator có toàn quyền workspace; nếu không toàn quyền cần cả Xem booking và Xem tổng phải thu, đã thu, còn nợ và lịch sử thu (legacy.booking__view + legacy.receipt__view).

Souvenirs: quyền Xem doanh thu Souvenirs của tất cả nhân viên (souvenirs.view_reports), hoặc quản trị có toàn quyền theo cơ chế hiện tại. Chỉ có quyền bán hàng không tự được xem báo cáo toàn bộ cửa hàng. Hai nguồn có kiểm tra quyền độc lập; không đổi source trong URL để vượt quyền. Không hiển thị giá vốn hoặc lợi nhuận trong báo cáo này.

## Cập nhật Ubuntu

Sao lưu theo quy trình hiện tại. Sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Không có migration mới riêng cho 1.17.0. Nếu chưa nâng 1.15.1, chạy manage.py migrate để nhận các migration đã phát hành trước đó.

Khởi động lại tiến trình web hiện tại để nhận endpoint mới. Với runserver thủ công, Ctrl+C tại đúng cửa sổ đang chạy rồi chạy lại, giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Ctrl+F5 trên trang quản lý. Không thay cấu hình SePay, DNS, tài khoản hoặc phân quyền đã có.

## Kiểm tra

Kiểm thử backend: ngày thu khác ngày tạo booking; nhiều lần thu/một booking/nhiều phương thức; thiếu phương thức, không đoán từ ghi chú; ngày giờ Việt Nam; thiếu ngày và phí; loại đơn chờ/hủy/xóa; phân quyền nguồn độc lập; CSV đúng lọc và chống công thức; dữ liệu sai; không ghi vào database. Browser kiểm tra tab báo cáo bán vé, Souvenirs, tổng tiền/phí/thực nhận, lọc phương thức/ngày, tải CSV, chặn khoảng ngày sai, quay lại báo cáo cũ và giao diện điện thoại.
