# 1.18.0 — Website Sunny, giá online riêng và đơn SePay chờ gửi vé

## Kết quả

- sunnygovn.com: khách chưa đăng nhập thấy trang giới thiệu, dịch vụ và bài viết. /discover/ luôn mở website khách; /management/ mở Ticket Management theo quyền.
- Đăng nhập: quản trị/vận hành trở về trang quản lý; tài khoản counter trở về bán vé theo luồng hiện tại. Quầy/Souvenirs và tên miền cũ tiếp tục hoạt động.
- /admin/online/: quản lý dịch vụ, liên kết với loại vé hiện có, ảnh, nội dung/điều kiện, bài viết và bảng giá online theo ngày sử dụng. Chỉ mục đã Xuất bản mới hiện cho khách. Nội dung là văn bản, không thực thi HTML/script. Ảnh JPEG/PNG/WebP tối đa 5 MB.
- Giá online là bảng riêng, không lấy hoặc sửa giá đại lý. Chặn kỳ giá trùng; chỉ bán ngày có một giá hợp lệ, loại vé đang dùng và giá vốn mặc định hợp lệ.
- Khách chọn ngày sử dụng/số lượng (1–20), họ tên, email nhận vé, điện thoại; xem lại giá mỗi vé và tổng tiền trước khi tạo QR. Server quyết định số tiền. Giữ giá tối đa 30 phút trước khi tạo QR; sau đó theo thời hạn QR đã tạo.
- SePay xác nhận đúng chữ ký/ngân hàng/tài khoản/số tiền/thời gian thì mới tạo booking, ghi thu chuyển khoản một lần và chuyển đơn sang Đã thanh toán — Chờ gửi vé. Dùng nguyên endpoint /api/sepay/webhook/ và cơ chế SEVQR VietinBank hiện có. Sai/thiếu/thừa tiền, giao dịch trễ, mã không hợp lệ cần đối soát, không tự cấp vé.
- /online/staff/: nhân viên nhận đơn, mở công cụ import/tạo PDF/email đang có. Nhận đơn có khóa chống hai nhân viên cùng nhận. Chỉ người được nhận hoặc superuser có thể truy cập bộ vé theo quyền quầy.
- Trạng thái Đã gửi vé dựa trên batch phiên bản hiện tại, đúng email, đã được máy chủ thư tiếp nhận; không có nghĩa khách đã đọc hoặc chắc chắn nhận trong Inbox. Không gửi thư tự động ngay khi thanh toán.
- Khoản thu online hiện trong báo cáo bán vé, gồm báo cáo phương thức. Ngày booking là ngày sử dụng khách chọn, ngày thu là ngày giao dịch ngân hàng. Doanh thu Souvenirs vẫn riêng.

## 1. Sao lưu và cập nhật Ubuntu

Dừng đúng tiến trình máy chủ bằng Ctrl+C. Không dừng proxy đang phục vụ website. Giữ nguyên tên miền cũ và cấu hình SePay hiện tại.

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Có migration online.0001_initial; thêm bảng mới, không xóa booking/giá đại lý/dữ liệu cũ. Không ghi đè database bằng dữ liệu test. Đã có ảnh và bài mẫu trong kiểm thử là fixture tạm, không được đưa vào dữ liệu thật.

## 2. Cấu hình ứng dụng

Trong môi trường hiện đang nạp cho tiến trình (trước đây /etc/sunny-sepay.env), bổ sung các biến từ deploy/online.env.example. Không thay file bằng file mẫu: phải giữ khóa webhook, SMTP, tài khoản nhận tiền và cấu hình cũ. ONLINE_PAYMENT_OWNER là tên đăng nhập một superuser thật đang hoạt động, không phải mật khẩu.

Giữ ONLINE_CHECKOUT_ENABLED=0 lúc đầu. Không chuyển production sang PostgreSQL hoặc đổi DJANGO_SETTINGS_MODULE trong đợt này; giữ môi trường SQLite/development hiện có nếu đó là cách máy chủ đang chạy.

```bash
sudo nano /etc/sunny-sepay.env
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check_online_setup'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Không start tiến trình thứ hai khi 8000 đang có máy chủ. Giữ cửa sổ máy chủ mở theo cách vận hành hiện tại; lệnh trên không cài dịch vụ tự khởi động.

## 3. DNS P.A Việt Nam

Mở quản trị tên miền sunnygovn.com, phần cấu hình bản ghi DNS. Tại thời điểm kiểm tra 24/11/2026, sn.hoianmemorieslands.com trỏ đến 222.255.130.242; sunnygovn.com chưa phân giải trong resolver đang dùng. Xác nhận IP máy proxy vẫn là IP này trước khi lưu.

| Host | Loại | Giá trị | TTL |
| --- | --- | --- | --- |
| @ | A | 222.255.130.242 (IP proxy hiện tại, cần xác nhận) | 3600 |
| www | CNAME | sunnygovn.com | 3600 |

Không trỏ DNS công khai vào IP LAN 172.16.150.157. Không thay MX/TXT phục vụ email. Nếu tên miền đang dùng nameserver ở nơi khác, bản ghi phải được thêm ở nơi đó.

## 4. Nginx/OpenResty và HTTPS

Thực hiện trên máy Nginx/OpenResty đang nhận IP công khai, có thể khác Ubuntu chạy Django. Thêm vhost mới cho sunnygovn.com và www.sunnygovn.com, dùng đúng upstream/static configuration đang chạy cho sn. Không thay thế vhost sn và không đoán localhost:8000 nếu proxy ở máy khác.

deploy/sunnygovn.nginx.example là cấu hình HTTPS tham khảo, KHÔNG copy nguyên: cần thay upstream và đường dẫn chứng chỉ thực tế. Cấp chứng chỉ cho cả sunnygovn.com/www bằng công cụ chứng chỉ hiện có sau khi DNS trỏ đúng. Không reload cấu hình SSL tham chiếu file chứng chỉ chưa tồn tại. Chạy kiểm tra cấu hình bằng đúng nginx/openresty binary đang vận hành, chỉ reload khi kiểm tra thành công.

Chuyển www về https://sunnygovn.com giữ nguyên path/query. Giữ Host và X-Forwarded-Proto khi proxy. Reuse cách phục vụ /static/ hiện có. Không public-alias MEDIA_ROOT hoặc private_counter vì có vé/ảnh nguồn riêng tư.

## 5. Khai báo nội dung và phân quyền

1. /admin/online/service/: thêm dịch vụ, chọn loại vé hiện có, nội dung và điều kiện sử dụng, Xuất bản.
2. /admin/online/onlineprice/: chọn dịch vụ, giá cuối cùng khách trả / vé, từ/đến ngày sử dụng, bật áp dụng. Kết thúc kỳ giá cũ trước khi thêm kỳ mới.
3. /admin/online/article/: viết và xuất bản bài giới thiệu.
4. Nhân viên xử lý cần online | đơn vé online | Xử lý đơn online và gửi vé cho khách, cùng legacy counter.view và counter.create. Quản trị superuser có sẵn. Quyền thay vé cũ dùng counter.replace_tickets hiện có.
5. Quản trị nội dung qua Django admin cần is_staff và quyền add/change/view các model Service/Article/OnlinePrice. Không cấp sửa/xóa trực tiếp OnlineOrder; hồ sơ mua hàng được giữ để đối chiếu.
6. Nhân viên vào /online/staff/ (có ở menu quầy và Ticket Management), Nhận xử lý đơn, kiểm tra QR/số lượng/ngày sử dụng, tạo PDF và gửi email. Không nhập bừa QR hoặc dùng mã đơn làm QR vào cổng.

## 6. Kiểm thử và mở thanh toán

Test trên bản sao riêng với SePay TEST và email locmem/hộp thư thử. Không đổi cấu hình SePay live của quầy đang hoạt động chỉ để test website. Chỉ bật ONLINE_CHECKOUT_ENABLED=1 sau khi đã khai báo người phụ trách, dịch vụ/giá, xác minh email gửi thực tế và website HTTPS hoạt động.

Dùng check_online_setup để kiểm tra cấu hình mà không in khóa/tài khoản ngân hàng. Lệnh này không chứng minh SMTP thật hoặc ngân hàng thật đã hoạt động. Khi sẵn sàng, thay ONLINE_CHECKOUT_ENABLED=1 trong môi trường live, restart đúng tiến trình. Kiểm tra giao dịch nhỏ có giám sát, webhook chỉ ghi thu một lần và nhân viên gửi được PDF. TEST QR được ghi rõ không dùng chuyển tiền thật. Giới hạn yêu cầu theo session/IP có sẵn nhưng khi mở Internet phải dùng giới hạn ở proxy theo IP tin cậy, vì cache mặc định chỉ trong tiến trình.

## 7. Chuyển QR sản phẩm và webhook

Khi domain mới hoạt động, đặt SOUVENIRS_CATALOG_URL=https://sunnygovn.com/souvenirs/catalog/ để QR in mới mở đúng sản phẩm trên domain mới. Không đặt SOUVENIRS_PUBLIC_ORIGIN thành domain chính với mong muốn mở toàn site thành catalog; router bản này bảo vệ domain chính.

Webhook mới là https://sunnygovn.com/api/sepay/webhook/. Kiểm tra endpoint mới và chữ ký trước khi sửa URL trong SePay. Giữ khóa/tài khoản nhận nguyên vẹn vì đợt này chỉ đổi tên miền, không đổi doanh nghiệp nhận tiền. Chỉ dùng một cấu hình webhook chính sau chuyển đổi để tránh nhiễu, hệ thống vẫn chống trùng transaction ID.

Giữ tên miền sn cũ và chứng chỉ cho QR đã in/liên kết cũ. Giai đoạn đầu cho cả hai domain vào cùng app. Sau khi không còn phiên chờ và webhook đã chuyển ổn định mới cân nhắc redirect GET của site cũ; không redirect mù mọi POST/webhook trong lúc còn vận hành.

## Giới hạn vận hành cần biết

Không tích hợp tồn vé/nhà cung cấp hoặc tự phát QR vé mới. Nhân viên vẫn phải chuẩn bị vé thật và xử lý ngoại lệ. Một đơn chứa một loại vé và một ngày sử dụng; có thể tạo các đơn riêng cho các loại khác nhau. Không thêm phí/VAT ngoài giá đã công bố. Hồ sơ giá online là snapshot lịch sử; không sửa số tiền/ngày/loại vé của booking online đã thu tiền bằng luồng sửa tại quầy, cần quản trị xử lý và đối soát. Không tự hoàn tiền ngân hàng. Khách tra trạng thái trong cùng phiên trình duyệt đã đặt; không có tài khoản khách hoặc email tracking link trong bản này.

## Quay lại bản cũ

Tắt nhận đơn online trước; xử lý/đối soát các giao dịch đang chờ. Giữ phiên bản mới để webhook xử lý các QR còn hiệu lực. Không rollback mù code/webhook khi khách còn có thể chuyển tiền. Có thể quay giao diện tên miền về sn và tắt website public trong proxy mà vẫn giữ dữ liệu mới; khôi phục database từ backup sẽ làm mất giao dịch phát sinh sau backup nên chỉ thực hiện sau đối soát.
