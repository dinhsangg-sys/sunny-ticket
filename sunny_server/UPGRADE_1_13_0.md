# 1.13.0 — Quản lý phí thanh toán thẻ

Phí do bên bán chịu, tính trên số tiền thu bằng thẻ và đã bao gồm VAT theo biểu phí cung cấp. Không cộng phí vào tiền khách phải trả, không phát sinh công nợ do phí. Mỗi giao dịch giữ thông tin loại thẻ/nơi phát hành, kỳ phí/tỷ lệ, ngày thu, số phí và số thực nhận; thay biểu phí không tính lại lịch sử.

## Cập nhật Ubuntu

Sao lưu database trước vì có thêm bảng cấu hình:

```bash
cd /home/sunny-ticket
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chờ **Đã sao lưu và kiểm tra**. Ctrl+C tại terminal đang chạy bản chính cổng 8000. Chạy từng lệnh:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ terminal mở; nếu có dịch vụ thì khởi động lại đúng dịch vụ, không chạy trùng cổng. Giữ cấu hình SePay hiện có. Trình duyệt Ctrl+F5. Migration **0014** thêm bảng biểu phí và quyền mới, không sửa booking hoặc khoản thu cũ. Dữ liệu biểu phí nằm trong SQLite/database, cần sao lưu database đầy đủ; file JSON dữ liệu nghiệp vụ không thay thế bản sao lưu này.

## 1. Khai báo biểu phí trước khi nhân viên thu thẻ

Quản trị vào **Quản lý phí thẻ** ở menu trái Ticket Management, hoặc `/card-fees/`. Superuser được dùng ngay. Tài khoản vai trò admin/operator cần quyền toàn bộ workspace hoặc quyền riêng **Quản lý khai báo phí thanh toán thẻ và thời gian hiệu lực** (`card_fee__manage`). Cấp ở Quản trị → Người sử dụng/nhóm. Vai trò nhân viên quầy chỉ xem mức phí tương ứng qua màn hình thu tiền, không sửa cấu hình.

Form có Loại thẻ (NAPAS/Visa/Mastercard/JCB/UnionPay), Nơi phát hành (Trong nước/Nước ngoài), Phí %, Từ ngày, Đến ngày, Trạng thái, Ghi chú. Phí cho phép 0–100%, tối đa 3 số thập phân. Không có phí cố định trong bản này vì biểu phí cung cấp chỉ theo phần trăm.

**Lần đầu:** chọn Từ ngày muốn bắt đầu áp dụng, bấm **Nạp 10 mức phí mẫu**, kiểm tra và xác nhận. Chỉ nạp mẫu khi chưa có biểu phí; không tự nạp/kích hoạt trong migration. Các mức mẫu đã bao gồm VAT:

| Nơi phát hành | NAPAS | Visa | Mastercard | JCB | UnionPay |
|---|---:|---:|---:|---:|---:|
| Trong nước | 1,60% | 2,55% | 2,50% | 2,50% | 2,50% |
| Nước ngoài | 1,60% | 3,58% | 3,52% | 3,52% | 3,52% |

Biểu phí được áp dụng theo **ngày xác nhận thu tiền**, không phải ngày booking. Ví dụ booking tháng trước thu hôm nay dùng kỳ phí hôm nay. Mỗi cặp loại thẻ/nơi phát hành chỉ có một kỳ đang áp dụng tại một ngày.

**Đổi phí:** sửa ngày kết thúc kỳ cũ, rồi bấm Khai báo kỳ mới và nhập tỷ lệ mới/ngày bắt đầu kế tiếp. Ngày hiệu lực tính cả hai đầu; kỳ cũ kết thúc 30/11 thì kỳ mới bắt đầu 01/12. Không cho kỳ đang áp dụng chồng nhau. Mức phí đã sử dụng (kể cả đã hủy xác nhận nhầm) không được sửa tỷ lệ/loại thẻ/nơi phát hành/ngày bắt đầu; vẫn có thể sửa ngày kết thúc nhưng không loại giao dịch đã thu, ngừng áp dụng và sửa ghi chú.

## 2. Nhân viên thu tiền

Nhân viên tạo booking như trước, rồi mở Xác nhận thanh toán. Khi chọn **Thẻ thanh toán**, bắt buộc chọn **Loại thẻ** và **Nơi phát hành**; không tự chọn thay nhân viên. Hệ thống hiển thị tỷ lệ, phí và thực nhận. Chưa khai báo phí hợp lệ thì nút xác nhận bị chặn. Tính lại phí nếu quản trị vừa đổi biểu phí hoặc sang ngày mới.

Phí = số tiền thu trong lần xác nhận × tỷ lệ / 100, làm tròn đến đồng bằng quy tắc từ 0,5 làm tròn lên. Ví dụ Visa trong nước, khách trả 1.000.000 đ → phí 25.500 đ, thực nhận 974.500 đ, khách đã trả 1.000.000 đ và nợ 0 đ. Phí không tính thêm VAT lần nữa và không thay công thức VAT booking đang có. Server tự tính và kiểm tra lại trước lưu, không nhận số phí tự nhập.

Phí được trừ vào lợi nhuận booking một lần. Cash/Chuyển khoản/SePay không phát sinh phí thẻ. Đây vẫn là xác nhận thu thủ công sau khi kiểm tra giao dịch POS thành công; không tích hợp trừ tiền thẻ tự động.

## 3. Báo cáo và sổ quỹ

- **Báo cáo → Phí thẻ**: lọc ngày thu, loại thẻ, nơi phát hành; xem tiền khách trả, phí bên bán chịu, thực nhận; có Xuất Excel theo bộ lọc.
- **Doanh thu/Lợi nhuận**: doanh thu và đã thu khách giữ nguyên; lợi nhuận đã giảm phí thẻ được ghi nhận. Chi phí vận hành thủ công vẫn tính riêng như trước.
- **Sổ quỹ**: giữ khoản thu khách đủ và thêm dòng chi tự động Phí thanh toán thẻ từ cùng khoản thu; chênh lệch là thực nhận. Không nhập thêm một khoản chi phí thẻ thủ công tương tự để tránh cộng hai lần. Các dòng chi tự động không được tính thêm lần nữa vào lợi nhuận đã trừ phí.
- **Chi tiết booking quầy**: có tổng phí thẻ/thực nhận và lịch sử điều chỉnh. Báo cáo Phí thẻ dùng ngày thu; báo cáo theo ngày booking có thể có khoảng thời gian khác.

Các giao dịch thẻ cũ chưa lưu thông tin thẻ/phí không được tự suy đoán và tính lại. Báo cáo phí chỉ gồm các khoản thu có phí được ghi nhận theo luồng mới.

## 4. Sửa xác nhận nhầm

Người có `counter__reopen_payment` dùng quy trình hủy xác nhận thủ công nhầm tại Chi tiết booking. Khoản thu/phí đang tính được gỡ, nhưng giữ toàn bộ snapshot trong lịch sử. Xác nhận lại bằng Cash/Chuyển khoản thì không còn phí thẻ, bằng thẻ thì chọn và tính phí mới theo ngày thu lại.

Đây là sửa ghi nhận nhầm, không hoàn phí hoặc hoàn tiền POS/ngân hàng thực tế. Booking có thu thẻ thật và cần đổi tổng tiền phải đối soát riêng; bản này chặn điều chỉnh tổng tiền đã thu có phí để không tự suy đoán hoàn phí. Không cho sửa/xóa khoản thu/phí hoặc lịch sử phí trực tiếp từ trình biên tập khác. Không xóa booking còn dữ liệu lịch sử phí thẻ. Khoản thu SePay vẫn theo quy tắc đối soát riêng.

## Xác minh

146 kiểm tra backend và các kiểm thử trình duyệt liên quan đã đạt; migration khớp model.

Kiểm thử dùng dữ liệu giả: 10 mức phí, hiệu lực/không chồng kỳ, quyền quản lý/nhân viên, kiểm tra lựa chọn, báo phí thay đổi trước xác nhận, làm tròn, giữ snapshot, ghi thu gross/nợ 0, giảm lợi nhuận, sửa xác nhận, bảo vệ lịch sử và báo cáo/sổ quỹ/Excel. Không chuyển tiền, trừ thẻ hoặc gửi email thật. Chưa triển khai trực tiếp Ubuntu.
