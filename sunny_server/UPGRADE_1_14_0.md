# 1.14.0 — Souvenirs, nội dung sản phẩm và bán hàng tại quầy

Trang khách dự kiến **https://souvenirs.hoianmemorieslands.com**. Trang quản lý đang dùng là **https://sn.hoianmemorieslands.com** (có chữ `s` trong `memorieslands`). Hai tên miền dùng chung Django/database để không phải chuyển doanh thu bằng thao tác nhập tay hoặc đồng bộ qua trình duyệt. Module mới tắt mặc định đến khi bật cấu hình trên máy chủ.

## Các chức năng

- Trang khách: bộ sưu tập, tìm tên/nhóm, ảnh sản phẩm, giá bán, câu chuyện, video và bài viết. Không cần đăng nhập, không có giỏ mua hàng/thanh toán online theo lựa chọn đã chốt. Tối ưu bố cục điện thoại khi quét QR.
- Quản lý: thêm/sửa SKU, tên, nhóm, giá bán, giá vốn nội bộ, giới thiệu, câu chuyện, thứ tự, trạng thái hiển thị; upload ảnh JPEG/PNG/WebP (10 MB, 24 megapixel), video MP4/WebM (100 MB); nhiều bài viết bằng văn bản. Lưu rồi mở lại để thêm các dòng nội dung tiếp theo. Trạng thái bản nháp/ngừng bán ẩn khỏi khách và danh mục tạo đơn mới.
- QR: một đường dẫn cố định cho mỗi loại sản phẩm/SKU, không phải QR riêng cho từng chiếc. Có tải PNG và trang in tem mặc định 50 × 65 mm. Đổi ảnh/câu chuyện/tên không đổi QR; sản phẩm ngừng hiển thị thì khách thấy không tìm thấy. Chỉ in hàng loạt sau khi kiểm tra tên miền/SSL và quét bằng điện thoại ngoài mạng nội bộ.
- Nhân viên: mục **Bán hàng lưu niệm** trong menu dọc trang bán vé. Tìm sản phẩm, chọn số lượng, thêm nhiều mặt hàng, xem tổng tiền và lưu đơn chờ thanh toán. Giá do danh mục quyết định, không nhập sửa giá tại quầy. Đơn giữ ảnh chụp dữ liệu tên/SKU/giá bán/giá vốn lúc tạo, không đổi theo chỉnh sửa danh mục sau này.
- Xác nhận thu: Tiền mặt, Chuyển khoản hoặc Thẻ. Chỉ xác nhận sau thực nhận; đơn chờ/hủy chưa thành doanh thu. Thẻ dùng biểu phí 1.13.0 theo loại thẻ/nơi phát hành, có báo phí/thực nhận và lưu snapshot. Đơn mới không tự ghi thu khi lưu. Chuyển khoản trong module này xác nhận thủ công; QR ở sản phẩm là QR thông tin, không phải QR thanh toán. SePay tự động của booking vé vẫn riêng, không tự ghép vào đơn lưu niệm.
- Quản lý doanh thu: **Souvenirs → Doanh thu Souvenirs**, theo ngày thu tiền; tổng đơn/sản phẩm/doanh thu/phí thẻ/thực nhận/lợi nhuận và chi tiết. Có xuất CSV UTF-8 theo bộ lọc. Trang quản lý tự lấy mới báo cáo mỗi 15 giây khi đang hiển thị. Nhân viên thường chỉ xem 100 đơn gần nhất của mình, không thấy giá vốn/lợi nhuận hoặc đơn người khác.

Doanh thu Souvenirs nằm trong module riêng, không chép thành booking vé, không cộng lặp vào báo cáo/cashbook vé hiện tại. Phí thẻ của đơn lưu niệm xem trong Souvenirs, biểu phí quản lý chung. Đơn đã thu không sửa/xóa/hủy qua giao diện này; cần quy trình đối soát riêng nếu phát sinh hoàn hàng. Bản này chưa có tồn kho, giao hàng hoặc mua hàng online. Có nhật ký người thao tác, ngày tạo, người xác nhận thu tiền; không chạy thanh toán POS/ngân hàng tự động trong module mới.

## 1. Sao lưu và nâng cấp mã

Chọn thời điểm bảo trì. Dừng tiến trình web chính cổng 8000 bằng Ctrl+C ở terminal đang chạy để ảnh/video không đổi trong khi sao lưu. Sau đó:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chỉ tiếp tục khi có **Đã sao lưu và kiểm tra**. Database chứa sản phẩm/đơn hàng, thư mục media chứa ảnh/video: phải giữ cả hai. Nếu dùng MEDIA_ROOT ngoài thư mục ứng dụng hoặc PostgreSQL, cần sao lưu kho media/database thực tế bằng quy trình phù hợp; tiện ích trên dành cho SQLite hiện tại.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Cần chạy đầy đủ migration **souvenirs.0001_initial** và **souvenirs.0002_saleorder_paid_by** kể cả khi chưa bật module. Không chép database thử vào bản chính. Không cần gói Python mới. Nếu Git xung đột, dừng để kiểm tra, không reset/xóa dữ liệu.

## 2. Bật module trên máy chủ

Giữ nguyên khóa/cấu hình SePay đang có. Mở:

```bash
sudo nano /etc/sunny-sepay.env
```

Bổ sung hai dòng (mỗi biến chỉ xuất hiện một lần):

```bash
SOUVENIRS_ENABLED=1
SOUVENIRS_PUBLIC_ORIGIN=https://souvenirs.hoianmemorieslands.com
```

Lưu Ctrl+O → Enter → Ctrl+X. Giữ quyền file root/600 như hiện có. Khởi động bằng cách nạp cùng file cấu hình:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở theo cách vận hành hiện tại. Nếu có dịch vụ riêng, nạp các biến này vào dịch vụ và khởi động lại đúng dịch vụ thay vì chạy thêm vào cổng đã chiếm. Không phải mở thêm cổng ứng dụng cho shop.

Nhấn Ctrl+F5, mở `/souvenirs/manage/` trên domain `sn` để kiểm tra. Module chưa có sản phẩm thật sau migration; không có dữ liệu mẫu bán hàng được thêm vào database kinh doanh.

## 3. Phân quyền

Superuser có đủ quyền. Quản trị/vận hành có toàn bộ workspace cũng được dùng module. Với nhân viên, cấp các quyền thuộc **Souvenirs | Product** trong quản trị tài khoản/nhóm:

| Quyền | Mã | Phạm vi |
|---|---|---|
| Tạo đơn và xác nhận thu tiền Souvenirs tại quầy | `souvenirs.sell` | Đơn của chính nhân viên; không thấy giá vốn |
| Quản lý sản phẩm, hình ảnh, video và bài viết Souvenirs | `souvenirs.manage_catalog` | Nội dung, giá bán/giá vốn, xuất/in tem |
| Xem doanh thu Souvenirs của tất cả nhân viên | `souvenirs.view_reports` | Báo cáo tổng hợp, chi tiết và xuất CSV |

Quyền bán vé cũ không tự cấp bán souvenirs. Nhân viên role counter đã có quyền bán vé sẽ thấy thêm **Bán hàng lưu niệm** khi module bật; cấp quyền bán souvenirs để mở được. Nếu tài khoản role counter chỉ có quyền souvenirs.sell, đăng nhập sẽ mở trang lưu niệm. Không cần cấp toàn bộ workspace cho nhân viên.

## 4. Tên miền, DNS và HTTPS

Code không tự tạo bản ghi DNS/chứng chỉ SSL trên tài khoản của bạn. Thêm `souvenirs.hoianmemorieslands.com` về cùng reverse proxy/IP công khai đang phục vụ `sn.hoianmemorieslands.com`. Không dùng IP LAN `172.16.150.157` làm IP công khai trên DNS.

Nếu dùng **Nginx Proxy Manager/OpenResty giao diện quản trị**: thêm Proxy Host cho domain souvenirs, chuyển tới cùng backend Ubuntu/cổng 8000 như domain sn. Giữ header Host đúng domain khách truy cập; xin SSL cho domain mới và bật HTTPS. Không thay cấu hình Proxy Host sn đang chạy. Mục giới hạn upload của host **sn** cũng cần đủ 128 MB cho thao tác quản lý video; dùng `client_max_body_size 128m;` tại cấu hình tương ứng. Mỗi video tối đa 100 MB, nên upload từng video để tổng một request không quá giới hạn proxy.

Nếu dùng **Nginx trực tiếp cùng máy chủ Django**, có file tham khảo `deploy/souvenirs.nginx.example`; thay đường dẫn/chứng chỉ theo máy thực tế, kiểm tra `nginx -t` trước reload. Mẫu proxy 127.0.0.1:8000 chỉ dùng khi proxy cùng máy. Nếu proxy ở máy khác, dùng địa chỉ backend/cổng giống host sn đang có. File mẫu không phải lệnh để ghi đè cấu hình hiện tại. Không công khai toàn bộ MEDIA_ROOT bằng alias, vì ảnh/video bản nháp được kiểm tra quyền qua Django.

Khi module đã bật, kiểm tra backend tại SSH thứ hai:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: souvenirs.hoianmemorieslands.com' http://127.0.0.1:8000/
```

Mong đợi 200 cho trang danh mục. Sau khi DNS/SSL hoạt động:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://souvenirs.hoianmemorieslands.com/
```

Mong đợi 200. Nếu 502 kiểm tra tiến trình backend và cấu hình upstream; nếu 400 kiểm tra biến tên miền/Host. Chỉ cấp SSL khi DNS và reverse proxy do bạn quản lý đã đúng.

## 5. Bắt đầu sử dụng

1. Quản lý mở **Souvenirs → Thêm sản phẩm**, nhập SKU/tên/giá/nội dung, upload ảnh/video/bài viết, chọn Hiển thị và lưu. Giá vốn nhập để báo cáo lợi nhuận; nếu để mặc định 0, báo cáo sẽ tính giá vốn 0.
2. Mở **Xem trang khách**, kiểm tra ảnh, câu chuyện, video và bài viết trên điện thoại.
3. Mở **Tem QR / In**, kiểm tra URL, tải PNG hoặc in tem (khổ 50 × 65 mm, một tem/trang). QR trỏ đúng subdomain công khai. Tắt header/footer và chọn khổ tương ứng trong trình in nếu cần.
4. Nhân viên vào **Bán hàng lưu niệm**, thêm hàng/số lượng, lưu đơn, xác nhận thu tiền đúng phương thức. Với thẻ phải có biểu phí đang hiệu lực từ 1.13.0.
5. Quản lý xem **Doanh thu Souvenirs**. Dữ liệu được đọc trực tiếp từ cùng database: không phải import sang trang quản lý. Không tính đơn chờ/hủy vào doanh thu.

Nếu lần lưu mất kết nối, giữ nguyên đơn, kiểm tra danh sách rồi thử lại cùng yêu cầu để tránh tạo lặp. Nếu giá thay đổi trước khi tạo, hệ thống chặn và tải lại danh mục để nhân viên kiểm tra tổng mới.

## Kiểm tra và giới hạn triển khai

159 kiểm tra backend cùng kiểm tra trình duyệt với template thật đã đạt cho công khai/ẩn sản phẩm, upload ảnh/bài viết, QR giải mã đúng URL, video byte-range, quyền nhân viên/quản lý, ảnh chụp giá, hủy đơn chờ, ghi thu một lần, phí thẻ, doanh thu theo ngày, giao diện điện thoại và menu nhân viên. Không chuyển tiền, gửi email, tạo đơn thật hoặc thay dữ liệu production trong kiểm thử. Chưa thay DNS/SSL hoặc triển khai trực tiếp Ubuntu từ phiên làm việc này.
