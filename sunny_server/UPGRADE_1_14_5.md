# 1.14.5 — Tự chọn ngôn ngữ khi quét QR

Trang khách Souvenirs chọn ngôn ngữ theo thứ tự:

1. Lựa chọn Tiếng Việt / English trong URL (lang=vi hoặc lang=en).
2. Lựa chọn khách đã bấm trước đó, lưu bằng cookie souvenirs_lang trên trình duyệt trong 1 năm.
3. Ngôn ngữ ưu tiên cao nhất trong Accept-Language của trình duyệt: vi/vi-VN dùng tiếng Việt; tiếng Anh hoặc ngôn ngữ khác dùng tiếng Anh. Tôn trọng trọng số q và bỏ ngôn ngữ q=0.
4. Không có hoặc không đọc được thông tin: tiếng Anh.

Đây là nhận diện ngôn ngữ trình duyệt, không phải quốc tịch/vị trí/IP. Khách Việt dùng trình duyệt ưu tiên tiếng Anh sẽ thấy tiếng Anh và có thể tự đổi. Quét QR bằng trình duyệt khác có thể không mang theo cookie cũ. Không thu thập vị trí hay gọi dịch vụ định vị IP. Không ảnh hưởng giao diện quản trị.

Bản dịch nhập trong hồ sơ sản phẩm; trường English trống vẫn dùng nội dung Việt như trước. Âm thanh/video vẫn từ tệp đã upload, không tự dịch hay chuyển giọng. QR sản phẩm của bản 1.14.4 không cần in lại vì không cố định tham số ngôn ngữ. QR catalog cũ của 1.14.2 vẫn cần thay theo hướng dẫn 1.14.4.

## Cập nhật Ubuntu

Sao lưu trước theo hướng dẫn 1.14.0. Không có migration mới.

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Dừng đúng runserver đang chạy bằng Ctrl+C ở cửa sổ đó rồi chạy lại, giữ cửa sổ mở:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Kiểm tra bằng cửa sổ riêng tư để không có cookie chọn trước; thử trình duyệt ưu tiên vi-VN và en-US. Bấm đổi ngôn ngữ, sau đó quét lại QR để kiểm tra lựa chọn được nhớ trên cùng trình duyệt. Có thể kiểm tra header Content-Language bằng curl:

```bash
curl -s -D - -o /dev/null -H 'Accept-Language: vi-VN,vi;q=0.9,en;q=0.8' https://sn.hoianmemorieslands.com/souvenirs/catalog/
curl -s -D - -o /dev/null -H 'Accept-Language:' https://sn.hoianmemorieslands.com/souvenirs/catalog/
```

Kết quả tương ứng Content-Language: vi và en. Response phân biệt theo Accept-Language/Cookie và không cache trang khách để tránh trộn ngôn ngữ.
