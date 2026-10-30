# Bản test: thanh toán, sửa booking và đối chiếu vé

Lưu ý 1.12.0: quy tắc tự thu khi tạo của lịch sử bên dưới đã được thay bằng xác nhận thanh toán thủ công cho booking mới. Xem UPGRADE_1_12_0.md để vận hành bản hiện tại.

Chỉ nhánh `codex/counter-sales`. Không thay main, stable hoặc dữ liệu máy chủ chính.

## Cập nhật

Dừng terminal chạy bản test cổng 8001 bằng Ctrl+C rồi chạy:

```bash
cd /home/sunny-ticket-counter-test
sudo git pull --ff-only origin codex/counter-sales
cd sunny_server
sudo .venv/bin/pip install -r requirements.txt
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8001
```

Giữ terminal mở. Ctrl+F5 tại `/counter/`. Migration 0010 thêm quyền và phiên bản bộ vé, không xóa dữ liệu. Sao lưu database cùng `private_counter` trước khi nâng cấp nơi chứa vé quan trọng.

## Cấp quyền

Trong Quản trị → Người sử dụng hoặc Nhóm → quyền của Legacy/Workspace:

| Quyền | Chức năng |
|---|---|
| `counter__view` | Vào quầy, xem danh sách và chi tiết booking của mình |
| `counter__create` | Tạo booking, nhập/xuất/in/gửi vé theo chức năng hiện có |
| `counter__change` | Sửa loại vé, số lượng, giá bán, VAT, email, ghi chú booking của mình |
| `counter__settle_adjustment` | Xác nhận đã thu thêm/hoàn lại khi sửa tổng tiền |
| `counter__replace_tickets` | Upload bộ vé thay thế hoặc tạo phiên bản mới từ bộ cũ; cần có quyền create |
| `counter__report` | Mở báo cáo đối chiếu vé của mình |
| `counter__report_all` | Khi có report và view, xem báo cáo của tất cả nhân viên; không cấp quyền sửa booking người khác |

Quyền mới không tự cấp cho nhân viên hiện có. Superuser được truy cập. Không cấp staff/superuser chỉ để bán vé.

## Thử nghiệp vụ

1. Tạo booking quầy mới: hệ thống ghi khoản thu bằng toàn bộ doanh thu cùng giao dịch lưu; bấm lại cùng request không nhân đôi booking hoặc khoản thu. Booking cũ không tự đánh dấu đã thu. Booking thông thường không đổi quy tắc.
2. Chọn **Chi tiết / Sửa**: xem tổng tiền, đã thu, còn nợ và lịch sử. Người có quyền sửa đổi các trường cho phép. Ngày/người bán/giá vốn không cho sửa ở quầy. Đổi loại vé lấy giá vốn mặc định theo ngày booking; chỉ sửa ghi chú/giá bán giữ giá vốn đã chốt.
3. Nếu tổng tiền đổi, cần quyền điều chỉnh thanh toán và xác nhận thu thêm/hoàn tiền thực tế. Hệ thống không gọi ngân hàng hay hoàn tiền tự động. Khoản thu thêm được ghi mới; khi hoàn, số thu hiện hành giảm và lịch sử giữ đầy đủ các khoản thu trước/sau cùng số hoàn, ngày/người sửa. Đây là điều chỉnh booking; chưa có phiếu hoàn tiền độc lập hoặc sổ hoàn theo ngày riêng. Không xác nhận nếu chưa thực thu/hoàn. Sửa từ phiên cũ bị chặn.
4. Booking đã sửa làm bộ vé trước đó thành phiên bản lưu trữ, không gửi email bộ cũ. Trong **Nhập / In / Gửi vé**, người có quyền chọn **Tạo phiên bản vé mới** để dùng lại QR và sửa thông tin, hoặc upload file gốc mới. Bộ cũ giữ nguyên. Một QR không được dùng cho booking khác, kể cả QR của phiên bản đã thay. QR cũ không tự vô hiệu tại nhà cung cấp; cần đối soát trước khi giao lại vé.
5. Chọn **Báo cáo đối chiếu vé** hoặc `/counter/report/`. Lọc ngày, mã booking, nhân viên, kết quả. Mỗi bộ import/phiên bản là một dòng; chưa import vẫn có dòng. Mở **Xem / Quét lại PDF** để xem file gốc và file xuất cạnh nhau, chọn từng vé/trang.
6. Danh sách so thông tin đã lưu và hash file. Chi tiết đọc trực tiếp PDF đầu ra và quét QR, đối chiếu với QR và trường thông tin ghi nhận khi import: hạn, gói, PARK/SHOW, mã vé, đại lý. Khớp / khác biệt / thiếu dữ liệu được đánh dấu theo từng trường; thông tin đã chủ động sửa cũng được đánh dấu khác. Số lượng so riêng với booking hiện tại; bản lưu trữ có thể khác số lượng hiện tại.

Báo cáo không xác minh hiệu lực QR tại cổng soát vé. OCR nguồn có thể sai, cần nhìn file gốc. Mỗi trang chỉ một QR. File nhiều nguồn mới có thể xem từng nguồn; bộ nhiều file đã import từ bản trước chỉ có ZIP gốc để tải, vì bản cũ chưa giữ từng nguồn riêng. PDF cũ vẫn có thể tải để đối soát, vì vậy không dùng bản lưu trữ để giao lại khách.

## Kiểm tra

96 test backend đạt, gồm kiểm tra thanh toán/idempotency, quyền sửa/thu hoàn, lịch sử và xung đột phiên bản, QR/PDF thực tế, sửa thông tin được phát hiện, phân quyền báo cáo toàn bộ, quyền thay vé và giữ bản cũ. Playwright/Edge với frontend thật và API giả lập đạt luồng tạo booking, nhập/xuất PDF, xác nhận điều chỉnh và đối chiếu hai khung. Chưa kiểm thử máy in hoặc SMTP thật; cấu hình email vẫn theo COUNTER_TICKETS_TEST.md.

## Bản sửa OCR ảnh và thông báo thiếu trường

Nếu QR đã đọc được nhưng chưa xuất PDF, điền đủ sáu trường ở màn hình kiểm tra. Khi bấm tạo PDF, ô thiếu được viền đỏ và nêu tên cụ thể; không phải import lại. Ảnh import mới thử OCR vùng chữ phóng lớn nếu lượt đầu thiếu, bổ sung nhận nhãn tiếng Việt và P4RK do OCR. Không tự đoán giá trị. Đợt vé đã import vẫn giữ dữ liệu gốc để đối soát; điền bổ sung trong bản xuất. Ảnh thực tế có thể cần sửa tay; chưa kiểm nghiệm Tesseract thật với mọi ảnh.

## Nhiều vé ngang/dọc trên cùng trang

Bản bổ sung tách vùng vé theo vị trí QR và khoảng trắng phân cách, đọc text PDF riêng trong từng vùng; ảnh/scan OCR riêng mỗi vùng. Hỗ trợ các vé xếp trên/dưới hoặc cạnh nhau nếu vùng phân cách rõ. Nếu không tách chắc chắn thì báo lỗi yêu cầu cắt từng vé, không dùng chung thông tin cả trang cho nhiều QR. Mỗi QR tạo một trang đầu ra 80x110; số vé được chọn vẫn phải bằng số lượng booking. Tối đa 50 vé/đợt nhập và không cho QR trùng.

Đã kiểm tra thực tế PDF `3 eco 2510.pdf`: 2 trang tách 3 vé, đúng mã riêng từng vé, hạn 25/10/2026, ECO CL AH, PARK/SHOW và AHBN; xuất được 3 trang 80x110 và kiểm tra QR khớp nguồn. Ảnh `2 eco 2410_001.jpg` tách được 2 QR/vùng riêng. Máy phát triển chưa có Tesseract nên chưa xác nhận OCR chữ thật trên JPEG này; môi trường Ubuntu cần Tesseract vie+eng như hướng dẫn cũ. Các trường thiếu vẫn phải điền và kiểm tra trước khi xuất. Không đưa các file nguồn/QR thật vào GitHub.

Số thứ tự vé có thể khác số trang nguồn: hai vé cùng trang sẽ được đánh số 1, 2 nhưng báo cáo vẫn mở đúng trang nguồn 1. Không cần migration/thư viện mới cho bản sửa này.

## Sửa OCR cột giá trị và đọc lại bộ đã import

Sửa trường hợp ảnh hai vé ngang bị thiếu hạn/gói/mã và ô đại lý chứa nhãn hoặc URL. Với bố cục QR bên phải như mẫu, OCR đọc riêng cột giá trị bên dưới QR, giới hạn đáy theo kích thước QR để loại footer. Chạy chế độ một cột; parser giữ dòng, nhận giá trị trước nhãn tiếng Anh, lọc URL/tham số và chỉ nhận mã đại lý hợp lệ. Không gán AHBN cố định cho mọi file.

Đã chạy Tesseract.js với eng+vie trên hai vùng cắt từ ảnh thật `2 eco 2410_001.jpg`: đọc đủ sáu trường cho hai vé, AHBN/ECO CL AH/ngày 24/10/2026, mã riêng đúng từng vé; đưa kết quả qua parser và renderer, xuất hai trang và kiểm tra QR khớp nguồn. Backend Ubuntu vẫn dùng pytesseract/Tesseract native; cần kiểm tra lại trên máy Ubuntu sau cập nhật vì engine/ngôn ngữ có thể khác phiên bản.

Với bộ đã import nhưng chưa xuất, chọn **Đọc lại thông tin từ file gốc**, xác nhận thay kết quả đang sửa, rồi kiểm tra và xuất. Không tạo booking mới. Bộ đã xuất không được ghi đè: người có quyền cần tạo phiên bản mới trước. QR/thứ tự phải giữ nguyên khi đọc lại, nếu khác sẽ bị chặn. Không có migration hoặc thư viện mới.

## Cảnh báo số lượng vé nguồn và vé xuất

Hiển thị liên tục Booking / Đã import / Đã chọn. Khi số import khác số lượng booking, cảnh báo ngay và không tự tick chọn. Cho phép dùng một file nguồn nhiều vé để chọn đúng số cần xuất; không tăng số lượng booking theo file. Nút tạo PDF bị khóa khi chọn thiếu/thừa. Máy chủ vẫn kiểm tra lại trước và trong giao dịch; renderer kiểm tra số trang PDF bằng số vé chọn.

Đã kiểm tra booking 4 vé/import 5 vé: chọn 3 hoặc 5 bị từ chối; chọn các vé 1,2,4,5 xuất đúng 4 trang, chỉ 4 QR được gắn. Frontend kiểm tra bộ đếm, khóa khi chọn 0/5 và chỉ bật khi chọn 4. Danh sách 5 vé nguồn sau xuất vẫn giữ để đối soát, không có nghĩa PDF chứa 5 vé. Không có migration mới.

## Cập nhật file đúng và tạo lại vé

Trong cửa sổ Vé của booking, chọn PDF/ảnh đúng ở ô file phía trên, bấm **Cập nhật file và tạo lại vé**. Hệ thống nhập một bản nháp mới, chọn đúng bộ vừa nhập và mở các trường để kiểm tra. Chọn đủ số vé, sửa ô thiếu/sai, tick xác nhận, bấm **Xác nhận cập nhật và tạo lại vé 80 × 110 mm** nếu booking từng xuất PDF. Không xuất tự động ngay khi upload, vì OCR có thể cần kiểm tra.

Nếu chỉ import sai và chưa xuất, nhân viên có quyền tạo vẫn được nhập file đúng. Nếu đã xuất bất kỳ bộ vé nào, phải có cả quyền tạo và **counter__replace_tickets — Thay bộ vé và phát hành phiên bản mới của booking quầy**. Nếu thiếu, nút được khóa và có hướng dẫn liên hệ quản trị. Quyền mới không tự cấp. Cũng có thể dùng file cũ nhưng chủ động nhập lại thành phiên bản mới để sửa thông tin.

Bộ cũ vẫn giữ nguyên khi file mới chưa xuất hoặc bị lỗi. Chỉ sau khi PDF mới tạo thành công, bộ cũ mới chuyển lưu trữ và không gửi email được nữa. Lưu lại nguồn/PDF/QR để đối chiếu; QR cũ không tự bị hủy tại nhà cung cấp và không được dùng cho booking khác. Thử lại cùng lần upload không tạo thêm bản nháp trùng. Không đổi số lượng hoặc thanh toán booking trong luồng này. Không có migration mới.

## Lối vào từ tài khoản quản trị

Bổ sung liên kết Đối chiếu vé nhập / xuất ở thanh đầu giao diện chính, giao diện nghiệp vụ theo quyền và header Django admin. Báo cáo nằm tại /counter/report/ của bản test cổng 8001. Trang thiếu quyền hiển thị username và quyền cần cấp, API vẫn trả 403. Staff/role admin không tự có quyền báo cáo; cần counter__view + counter__report, thêm counter__report_all nếu xem toàn bộ. Superuser active được xem toàn bộ. Đã kiểm tra cả superuser và staff thiếu quyền; không thay đổi dữ liệu/tự cấp quyền.

## Bố trí báo cáo và menu nhân viên

Trong Ticket Management đầy đủ: chọn **Báo cáo** ở menu trái → tab **Đối chiếu vé nhập / xuất**. Báo cáo hiển thị ngay trong mục này; gỡ liên kết riêng ở thanh đầu. Đường dẫn thẳng tới tab: `/?view=reports&report=tickets#reports`. Liên kết từ Django admin cũng trỏ vào tab này. Giao diện nghiệp vụ theo quyền có nhóm Báo cáo riêng, vẫn kiểm tra quyền trên server.

Trang bán vé nhân viên và trang đối chiếu độc lập có menu dọc bên trái gồm Bán vé tại quầy và Báo cáo đối chiếu vé, mục đang mở được đánh dấu. Menu báo cáo nhân viên chỉ hiện khi có quyền report. Trên màn hình nhỏ menu xếp gọn phía trên để không che nội dung. Quyền xem dữ liệu không thay đổi; chế độ nhúng chỉ bỏ menu lặp, vẫn kiểm tra quyền và chỉ cho iframe cùng origin. Không có migration mới.
