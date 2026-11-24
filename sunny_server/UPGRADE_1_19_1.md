# 1.19.1 — Biểu tượng các kênh, thời tiết gọn trong header, ẩn LINE

## Thay đổi

- Facebook, TikTok, Google Maps, WhatsApp, Zalo và LINE có biểu tượng màu bên cạnh tên khi kênh tương ứng được khai báo. SVG được đóng gói trong template, không cần CDN/font icon; tên kênh vẫn đọc được và liên kết vẫn có nhãn chữ. Áp dụng cho website chính và trang khách Souvenirs. Google Maps vẫn chỉ hiện khi đã có link thật.
- Gỡ LINE theo yêu cầu hiện tại: không hiển thị số LINE hoặc nút LINE. Migration 0004 xóa riêng hai trường line_phone/line_url trong cấu hình hiện tại, giữ Facebook/TikTok/WhatsApp/Zalo. Không tự khôi phục số cũ. Khi đã tạo LINE, quản trị có thể nhập link LINE chính thức để hiển thị sau.
- Thời tiết Hội An thu nhỏ vào header, dưới/cạnh logo Sunny ở trang Trải nghiệm & vé và chi tiết dịch vụ. Chỉ hiện tên địa điểm, nhiệt độ và trạng thái mưa/nắng. Không còn bảng thời tiết lớn chiếm nội dung phía dưới.
- Biểu tượng ⓘ mở dự báo vài ngày và nguồn dữ liệu; click ngoài hoặc Escape đóng lại. Có Việt/Anh, phù hợp điện thoại.
- Không thêm xác suất mưa (%), không cần đăng ký WeatherAPI. Vẫn dùng MET Norway, giữ ghi nguồn và giấy phép trong phần thông tin. Cache tối thiểu 3 giờ cho dự báo toàn cầu theo hướng dẫn nhà cung cấp, hoặc lâu hơn nếu Expires yêu cầu. Không đổi giao dịch, giá hoặc cấu hình SePay.

## Cập nhật Ubuntu

Dừng đúng cửa sổ chạy ứng dụng bằng Ctrl+C. Không dừng Nginx/OpenResty.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ máy chủ mở, không start thêm tiến trình trên cổng 8000. Ctrl+F5 sau cập nhật. Nếu bỏ qua 1.19.0, migrate cũng chạy các bước bổ sung song ngữ và thông tin liên hệ của bản đó.

Kiểm tra: biểu tượng Facebook/TikTok/WhatsApp/Zalo trong footer, không còn LINE; vào /services/ xem thời tiết trong header và thử mở/đóng ⓘ. Nếu nguồn thời tiết không truy cập được, chỉ hiện chưa có dữ liệu; vẫn sử dụng đặt vé bình thường. Việc cấu hình DNS/SSL và kiểm tra nguồn sống trên Ubuntu không nằm trong thay đổi này.
