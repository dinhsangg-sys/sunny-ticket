# 1.19.0 — Song ngữ, thời tiết Hội An và kênh liên hệ Sunny

## Những thay đổi

### Việt / English

Website chính có chuyển Tiếng Việt / English trên đầu trang. Giao diện trang chủ, dịch vụ, bài viết, đặt vé, thông tin đơn và trạng thái thanh toán đã có hai ngôn ngữ; màn hình nghiệp vụ nội bộ vẫn giữ tiếng Việt. Thứ tự lựa chọn: query lang=vi/en → cookie khách đã chọn (đồng bộ với Souvenirs trên cùng host) → ngôn ngữ ưu tiên đầu tiên của trình duyệt. Nếu ưu tiên là tiếng Việt thì hiển thị Việt; các trường hợp còn lại/không nhận diện được mặc định English. Đây là lựa chọn ngôn ngữ trình duyệt, không xác định quốc tịch khách.

Quản trị → Website & vé online → Dịch vụ/Bài viết có thêm tiêu đề, tóm tắt và nội dung tiếng Anh. Quản trị nhập bản dịch; nếu trường tiếng Anh chưa có thì dùng nội dung Việt hiện có, không tự bịa bản dịch. Slug, loại vé, số lượng, bảng giá, tiền thanh toán và quyền truy cập không đổi khi đổi ngôn ngữ. Đơn mới lưu thêm tên dịch vụ tiếng Anh trong snapshot; đơn cũ tiếp tục dùng tên gốc. Mẫu email gửi vé vẫn do nhân viên/quản trị soạn theo chức năng đang có.

### Bảng thời tiết

Hiển thị ngay dưới header/logo trong Trải nghiệm & vé (/services/) và trang chi tiết dịch vụ. Có nhiệt độ dự báo hiện tại, khoảng nhiệt độ và tóm tắt mưa/nắng cho hôm nay và hai ngày tiếp theo, theo giờ Việt Nam. Khoảng nhiệt độ được tổng hợp từ các mốc dự báo còn lại, không phải số đo đầy đủ của cả ngày đã qua. Dữ liệu là dự báo mô hình, không phải cảm biến đo tại quầy; không có phần trăm mưa nếu nguồn không cung cấp.

Nguồn: MET Norway Locationforecast, tọa độ trung tâm Hội An 15.8801, 108.3380. Ghi nguồn, link giấy phép CC BY 4.0 và thời điểm cập nhật trên giao diện. Không dùng Open-Meteo free endpoint cho website thương mại. Không cần API key MET Norway. API có điều kiện sử dụng, không có cam kết luôn sẵn sàng:
- https://api.met.no/doc/locationforecast/HowTO
- https://api.met.no/doc/TermsOfService
- https://api.met.no/doc/License

Trình duyệt gọi API cùng website /api/public/weather/. Server gọi nguồn cố định, không nhận tọa độ/URL từ khách. Forecast được lưu cache file và tuân theo Expires, If-Modified-Since; giới hạn thời gian tải, chống gọi trùng và backoff khi lỗi. Khi nguồn lỗi có thể dùng bản đã lưu trong 6 giờ sau hạn cache, có thông báo; nếu không có dữ liệu hợp lệ thì báo tạm thời chưa tải được, không hiển thị số liệu giả/0°C. Không ảnh hưởng đặt vé/thanh toán. Trang tải nội dung trước; thời tiết tải riêng.

Cache mặc định sunny_server/weather_cache/ cần quyền ghi của tiến trình ứng dụng. Không public alias thư mục này. Nếu cần tắt riêng widget data: HOI_AN_WEATHER_ENABLED=0. Có thể đổi HOI_AN_WEATHER_USER_AGENT bằng chuỗi có tên ứng dụng/domain và thông tin liên hệ công khai hợp lệ. Mặc định xác định SunnyGovn và repo công khai của dự án.

### Kênh chính thức và liên hệ

Quản trị → online → Liên hệ & kênh Sunny:
https://sunnygovn.com/admin/online/sitecontact/1/change/

Có Facebook, TikTok, Google Maps, WhatsApp, Zalo, LINE và số điện thoại LINE. Các đường dẫn hợp lệ có nút tại chân trang website chính và Souvenirs, mở tab mới. Kênh để trống được ẩn. Chỉ nhận HTTPS của đúng dịch vụ, không cho URL javascript/giả tên miền hoặc chứa mật khẩu. Chỉnh sửa cần quyền change_sitecontact và quyền vào Django admin; superuser có sẵn.

Khai báo ban đầu theo thông tin chủ website đã gửi:
- Facebook: https://www.facebook.com/sunnytravelleisure
- TikTok: https://www.tiktok.com/@sunny.travel.leis
- WhatsApp: https://wa.me/84932548145 (+84 932 548 145)
- Zalo: https://zalo.me/0932548145 (đã chuẩn hóa bỏ +84 0)
- LINE: hiển thị số +84932548145, chưa tự tạo link từ số điện thoại. Khi có link kết bạn LINE (line.me hoặc lin.ee), nhập vào LINE URL; nút đó sẽ thay cho số hiển thị.
- Google Maps: chờ đường dẫn chính thức, chưa hiển thị.

Migration chỉ điền các trường rỗng, không ghi đè thông tin đã khai báo. Không xác minh quyền sở hữu các tài khoản bằng thao tác website; đường dẫn/số liên hệ được lấy từ chủ website. Không gửi tin nhắn thử hoặc thư thật cho bất cứ tài khoản nào.

## Cập nhật Ubuntu

Có migration online.0002 (trường nội dung tiếng Anh) và online.0003 (liên hệ). Phải migrate trước khi khởi động lại để tránh lỗi thiếu cột/bảng.

Dừng đúng cửa sổ ứng dụng bằng Ctrl+C, giữ Nginx/OpenResty hoạt động. Sao lưu trước:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Không thay file .env hoặc cấu hình ngân hàng. Giữ cửa sổ máy chủ mở theo cách vận hành hiện tại. Không start thêm tiến trình khi 8000 đang có server. Ctrl+F5 trong trình duyệt.

## Kiểm tra sau cập nhật

1. /discover/?lang=vi và ?lang=en: nút ngôn ngữ, menu, slogan; chuyển sang dịch vụ/bài viết vẫn giữ lựa chọn.
2. /services/?lang=en: bảng Hoi An weather nằm phía trên danh sách; nhiệt độ/dự báo nguồn thật hoặc thông báo chưa tải được, không phải dữ liệu mẫu.
3. Kiểm tra API trên Ubuntu ở cửa sổ khác:

```bash
curl -s -H 'Host: sunnygovn.com' http://127.0.0.1:8000/api/public/weather/
```

Nếu available=false: kiểm tra kết nối HTTPS đi ra api.met.no, chứng chỉ CA và quyền ghi cache; không tắt xác thực SSL để lách lỗi. Lần kiểm tra HTTP nguồn thật từ môi trường phát triển Windows bị thiếu chuỗi CA tin cậy; chưa xác minh được dữ liệu sống trực tiếp từ Ubuntu. Các kiểm thử dùng dữ liệu giả lập có đánh dấu, không đưa vào website thật.

4. Quản trị nhập nội dung Anh cho các dịch vụ/bài viết thật. Chân trang phải có Facebook, TikTok, WhatsApp, Zalo và số LINE đã khai báo. Bổ sung Google Maps/link LINE khi có.
5. Đơn thử ở môi trường TEST: đổi ngôn ngữ không đổi giá, trạng thái SePay và cơ chế gửi vé. Không tạo thanh toán thật chỉ để kiểm tra giao diện.

Không đổi DNS/HTTPS/proxy trong bản này. Không thay thông tin merchant hoặc bật thanh toán đang tắt.
