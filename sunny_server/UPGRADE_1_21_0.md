# 1.21.0 — Chat tư vấn dịch vụ không dùng API trả phí

Theo yêu cầu không phát sinh phí AI, phiên bản này dùng **FAQ/từ khóa chạy ngay trong Django**, không tích hợp OpenAI, không cần API key, không gọi mô hình bên ngoài và không có phí AI theo tin nhắn. Vẫn dùng tài nguyên máy chủ website đang vận hành; không hứa miễn phí toàn bộ hosting.

## Khách sử dụng

- Có nút chat nổi cạnh nhóm hotline/về đầu trang trên web khách chính và Souvenirs.
- Mở chat → chọn dịch vụ trong ô xổ xuống → nhập câu hỏi.
- Bot chỉ tìm câu trả lời đã được quản trị bật cho đúng dịch vụ. Nhận biết chữ hoa/thường, tiếng Việt không dấu và một số lỗi gõ nhỏ gần giống câu hỏi đã khai báo.
- Câu hỏi khớp nhiều chủ đề sẽ đưa các câu hỏi gợi ý để khách chọn lại. Thiếu câu trả lời hoặc chưa có bản tiếng Anh thì hướng dẫn nhắn nhân viên.
- Có nút WhatsApp/Zalo sử dụng đúng kênh trong cấu hình Liên hệ & kênh Sunny. Nút mở ứng dụng/trang nhắn tin, khách chủ động gửi tin; không tự gửi nội dung chat, không thông báo giả rằng đã có nhân viên nhận cuộc trò chuyện.
- Câu hỏi về giá hướng đến bộ chọn ngày/loại vé có giá hiện hành. Câu hỏi riêng về giao dịch, chưa nhận vé hoặc hoàn tiền chuyển sang nhân viên; bot không đọc booking, khách hàng, giá vốn hoặc xác nhận thanh toán.
- Đây không phải AI tạo sinh như ChatGPT: không tự suy luận hay trả lời kiến thức ngoài bộ câu trả lời đã duyệt. Chất lượng phụ thuộc nội dung/từ khóa quản trị khai báo.

## Khai báo trong quản trị

Vào `/admin/online/servicefaq/` (**Chat Sunny — Câu hỏi / Từ khóa**) hoặc mở Dịch vụ online và kéo xuống phần câu hỏi:

1. Chọn dịch vụ đã công khai.
2. Nhập câu hỏi và câu trả lời chính thức.
3. Nhập từ khóa/cụm từ phân cách bằng dấu phẩy, ví dụ `giờ mở cửa, opening hours, mở cửa lúc`. Tránh từ quá chung như `vé`, `dịch vụ` vì dễ khớp nhiều câu.
4. Nhập câu hỏi/trả lời tiếng Anh để phục vụ khách English.
5. Kiểm tra thông tin rồi bật **Cho phép bot sử dụng**. Mặc định câu mới chưa được dùng.

Ví dụ chủ đề nên chuẩn bị: vị trí, giờ hoạt động/lịch diễn, cách sử dụng vé, nhóm tuổi/chiều cao, bao gồm/không bao gồm, điều kiện đổi/hủy và cách nhận vé. Dùng thông tin đã xác nhận của từng nhà cung cấp; không sao chép lịch/giá minh họa làm thông tin thật. Chat chưa khai báo FAQ vẫn mở được và hướng khách tới nhân viên khi chưa có đáp án.

Quản trị có quyền mặc định. Nhân viên muốn chỉnh bộ câu trả lời cần tài khoản staff và quyền xem/thêm/sửa `online.ServiceFAQ` tương ứng. Không cần quyền xử lý thanh toán để chỉ biên tập FAQ.

## Vận hành

- Không cần đăng ký OpenAI hoặc thêm khóa API. Bản này không có đường gọi OpenAI, kể cả máy chủ đã có sẵn biến OPENAI_API_KEY từ ứng dụng khác.
- Có thể tắt widget và endpoint bằng `SUNNY_CHAT_ENABLED=0` trong `/etc/sunny-sepay.env`, rồi khởi động lại. Mặc định bật.
- Nội dung chat chỉ hiển thị trong trang đang mở; không lưu lịch sử hỏi/đáp vào database hay gửi sang dịch vụ AI. Đổi dịch vụ sẽ làm sạch cuộc trò chuyện đang hiển thị để tránh lẫn chủ đề.
- POST có CSRF; giới hạn câu hỏi 600 ký tự, 20 yêu cầu/phút theo địa chỉ kết nối trên mỗi cache/worker hiện hành. Khi vượt giới hạn vẫn gợi ý liên hệ nhân viên. Không gửi tệp qua chat.
- Thay đổi FAQ có hiệu lực từ câu hỏi tiếp theo; không ảnh hưởng giá hoặc đơn hàng.

## Cập nhật Ubuntu

Có migration **online.0008_service_faq_chat**. Dừng đúng cửa sổ ứng dụng bằng Ctrl+C, sao lưu dữ liệu theo quy trình hiện tại rồi chạy:

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
