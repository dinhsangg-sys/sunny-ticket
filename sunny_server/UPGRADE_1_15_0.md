# 1.15.0 — Sửa/xóa đơn Souvenirs, ngày giờ tạo và QR SePay

## Chức năng

- Danh sách đơn hiển thị ngày và giờ tạo theo giờ Việt Nam (Asia/Ho_Chi_Minh), ví dụ 2026-11-13 10:15:30. Giữ nguyên ngày/giờ gốc trên máy chủ.
- Quyền mới: souvenirs.edit_orders — Sửa đơn hàng Souvenirs; souvenirs.delete_orders — Xóa đơn hàng Souvenirs. Superuser và vai trò Quản trị (admin) mặc định có hai quyền. Các vai trò khác, kể cả Vận hành có toàn quyền workspace vé, cần được cấp riêng từng quyền.
- Sửa đơn: thêm/bỏ mặt hàng, đổi số lượng, giá bán và ghi chú; bắt buộc lý do và xác nhận. Giữ giá vốn lịch sử cho dòng đã có; dòng sản phẩm thêm mới lấy giá vốn hiện tại. Không đổi người bán, thời gian tạo, trạng thái hoặc ngày thu gốc.
- Đơn đã thu được sửa lại số liệu doanh thu/công nợ nội bộ của Souvenirs; phí thẻ tính lại theo tỷ lệ đã lưu khi thu, không áp biểu phí thị trường mới vào đơn cũ. Không chuyển/thu thêm/hoàn tiền ngân hàng hoặc POS; người dùng cần đối soát chênh lệch tiền thực tế trước khi xác nhận sửa.
- Xóa đơn là xóa khỏi danh sách hoạt động và báo cáo, giữ hồ sơ/lịch sử trong database để đối chiếu. Bắt buộc lý do và xác nhận, không tự hoàn tiền ngân hàng/POS. Báo cáo và CSV tính lại từ các đơn đã thu chưa xóa.
- Nhân viên có quyền sửa/xóa chỉ thao tác đơn của mình. Có thêm quyền Xem doanh thu Souvenirs của tất cả nhân viên thì được thao tác đơn người khác. Quản trị/superuser thấy toàn bộ đơn (100 gần nhất), có thao tác cả trong chi tiết báo cáo để sửa/xóa đơn cũ hơn.
- Có lịch sử người thao tác/thời điểm/lý do; snapshot trước/sau lưu ở máy chủ. Kiểm tra phiên bản để ngăn ghi đè khi người khác vừa sửa, thanh toán hoặc xóa.

## QR SePay cho Souvenirs

- Trong Xác nhận thu tiền, chọn Chuyển khoản. Nếu SePay đã bật và cấu hình hợp lệ, tự tạo QR đúng tổng tiền và tài khoản nhận do máy chủ xác định. Có nút Mở QR trên màn hình phụ.
- Chờ webhook SePay có chữ ký hợp lệ xác nhận đúng mã/số tiền/ngân hàng/tài khoản/thời gian phiên; màn hình đơn tự lấy trạng thái khoảng mỗi 3 giây và cập nhật đã thanh toán/báo cáo. Không xác nhận chỉ vì khách đã quét QR.
- Dùng cùng /api/sepay/webhook/ và các biến SEPAY_* hiện có; không đổi URL webhook, secret hoặc tài khoản nhận của hệ thống bán vé. Đơn Souvenirs lưu riêng, không tạo booking vé hoặc cộng lặp doanh thu vé.
- Với VietinBank giữ tiền tố SEVQR trong nội dung chuyển khoản như hệ thống bán vé. QR test hiển thị rõ THỬ NGHIỆM và không dùng để chuyển tiền thật; chỉ mode live tạo QR ngân hàng.
- Sửa/xóa/hủy đơn hoặc xác nhận bằng cách khác sẽ vô hiệu hóa QR đang chờ. Giao dịch đến QR cũ, sai tiền hoặc đến ngoài thời gian phiên được giữ lại để đối soát, không tự xác nhận đơn đã thay đổi. Đơn sửa cần mở QR mới.
- Nếu SEPAY_ENABLED tắt hoặc cấu hình thiếu, Souvenirs tiếp tục ghi nhận chuyển khoản thủ công theo hành vi cũ. Nếu đang bật mà tạo QR lỗi thì báo lỗi, không tự nhận là đã thu tiền.

## Cập nhật Ubuntu

Sao lưu database/media theo quy trình 1.14.0 trước khi cập nhật. Chọn thời điểm bảo trì và dừng đúng tiến trình web hiện tại bằng Ctrl+C ở cửa sổ đang chạy trước khi nâng cấp/migration. Sau đó:

```bash
cd /home/sunny-ticket
git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
```

Migration mới: souvenirs.0004, thêm phiên bản đơn, lịch sử, dấu xóa và hai quyền. Không xóa dữ liệu cũ. Không cần sửa /etc/sunny-sepay.env nếu SePay bán vé đang hoạt động. Giữ nguyên secret, mode và tài khoản nhận thực tế.

Khởi động lại bằng cấu hình hiện có:

```bash
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ web mở. Tải lại trang nhân viên bằng Ctrl+F5. Không mở thêm runserver nếu cổng 8000 đã có tiến trình chạy.

## Cấp quyền

Quản trị → Người sử dụng → chọn nhân viên → Quyền của người sử dụng, tìm Souvenirs rồi chọn Sửa đơn hàng Souvenirs và/hoặc Xóa đơn hàng Souvenirs → Lưu. Có thể cấp qua nhóm. Quyền bán hàng lưu niệm vẫn riêng; không tự cấp quyền mới cho tất cả nhân viên.

Nhân viên thường chỉ thấy đơn của mình; quản trị thấy Tất cả đơn. Nếu cần nhân viên sửa đơn người khác thì cấp thêm quyền Xem doanh thu Souvenirs của tất cả nhân viên. Sửa/xóa trên giao diện chỉ xuất hiện khi có quyền, API cũng kiểm tra quyền.

## Kiểm tra sau cập nhật

1. Kiểm tra tài khoản chưa cấp quyền không thấy nút sửa/xóa; quản trị và tài khoản đã cấp quyền thấy nút.
2. Sửa một đơn thử, kiểm tra số lượng/tổng tiền/giờ tạo/lịch sử/báo cáo, thử xóa đơn thử. Không thử xóa đơn thật chưa đối soát.
3. Mở đơn chờ và chọn Chuyển khoản, kiểm tra QR, tổng tiền, nội dung SEVQR nếu VietinBank và màn hình phụ.
4. Test mode có thể mô phỏng webhook theo quy trình SEPAY_TEST.md/command hiện có với mã STP của phiên Souvenirs. Không chạy mô phỏng với dữ liệu/live. Thử thật cần khách chuyển đúng nội dung/số tiền rồi đối chiếu log SePay và trạng thái đơn.
5. Chưa thực hiện giao dịch ngân hàng thật trong quá trình phát triển; cần kiểm tra một giao dịch nhỏ phù hợp trên máy chủ sau triển khai.
