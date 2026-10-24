# Kết quả kiểm thử bản chuyển đổi

## 1.10.7 — Giá vốn nhập tay và giao diện Booking

- Toàn bộ 67 test Django đạt, gồm giá nhập tay không cần danh mục nguồn, giá 0 hợp lệ, từ chối giá trống/âm/sai định dạng, kiểm tra quyền, tính lại tổng tiền và bảo vệ nguồn đã chi tiền.
- Node test_booking_updates.cjs đạt: lưu nguồn nhập tay, giá 0/không hợp lệ, nguồn đã thanh toán và tìm không dấu. Các regression test_partners.cjs, test_pricing.cjs, test_frontend.cjs và kiểm tra cú pháp script mới đều đạt.
- Không có migration mới. Chưa nghiệm thu bố cục bằng trình duyệt online hoặc thử trên Ubuntu; cần kiểm tra sau triển khai theo hướng dẫn.

## 1.10.6 — Sao chép giá và sidebar

- Toàn bộ 61 test backend ban đầu của đợt cập nhật đạt; sau bổ sung kiểm tra tên đối tác trùng, chạy lại 10 test của module sao chép đều đạt (tổng 62 ca riêng biệt được kiểm tra trong đợt).
- Kiểm tra preview không ghi, sao chép độc lập, chỉ vé được chọn, giá riêng/kế thừa, bỏ qua trùng/chồng kỳ, gán bảng chung có chủ đích, quyền nguồn/đích và revision.
- Kiểm tra cú pháp copy_prices.js/restricted.js và các regression JavaScript giá/đối tác đạt. Không có migration mới. Sidebar sửa bằng CSS responsive, chưa nghiệm thu hình ảnh trên trình duyệt online.

## 1.10.5 — Loại đối tác

- 52 test backend đạt. Bổ sung phân loại hồ sơ độc lập giá và lịch sử, nhóm mặc định, loại ngừng/không hợp lệ, bảo vệ nhóm có liên kết, kiểm tra quyền quản lý nhóm và phân loại.
- Node test_partners.cjs đạt: lọc hồ sơ, báo cáo/Excel, người nhận Zalo, bổ sung người nhận đúng nhóm và backup danh mục mới. Các kiểm tra JavaScript cũ cũng đạt.
- Migration bổ sung quyền; không yêu cầu reset. Chưa nghiệm thu giao diện trên trình duyệt online.

## 1.10.4 — Thứ tự giá vốn và nhãn mặc định

- 45 test backend đạt; bổ sung kiểm tra quyền sắp xếp, vị trí đầu/cuối, giữ mức mặc định và giá booking khi đổi thứ tự.
- JavaScript kiểm tra thứ tự hiển thị, nhãn ⭐ Mặc định và danh sách chọn giá không đổi đạt; cú pháp pricing.js/restricted.js hợp lệ.
- Migration bổ sung cost_price.reorder. Chưa nghiệm thu GUI trên trình duyệt online.

## 1.10.3 — Xóa loại vé có điều kiện

- 42 test backend đạt; bổ sung xóa vé chưa dùng, chặn vé có tham chiếu, chặn xóa dây chuyền trong cùng payload, dừng giữ lịch sử, lưu dấu đã phát sinh và kiểm tra API tài khoản phân quyền.
- Kiểm tra JavaScript điều kiện sử dụng, các luồng giá/Zalo/backup và cú pháp đạt. Có migration bổ sung quyền xóa; chưa nghiệm thu GUI online.

## 1.10.2 — Nhiều mức giá vốn

- 36 test Django đạt, gồm nhiều giá cùng nhà cung cấp/loại vé/cùng hiệu lực, lấy mặc định hoặc chọn costPriceId cụ thể, chặn chọn sai nguồn/ngày và giữ giá của booking khác.
- JavaScript pricing và cú pháp pricing.js/restricted.js đạt. Không có migration, không yêu cầu xóa dữ liệu. Chờ người dùng test giao diện online sau cập nhật.

## 1.10.1 — Khởi tạo mới

- 33 test Django thành công, gồm xóa nghiệp vụ/media, giữ user/mật khẩu/nhóm, gỡ liên kết đại lý, tăng revision và vô hiệu hóa phiên; chế độ preview không xóa dữ liệu; API ánh xạ đã trả 404.
- Kiểm tra JavaScript về bảng giá/nguồn vé, Zalo, backup và picker đạt; không còn menu/luồng ánh xạ trong frontend đang chạy.
- Không có migration mới; chưa chạy reset trên máy Ubuntu của người dùng, cần chạy lệnh theo UPGRADE_1_10_1.md. Chưa nghiệm thu GUI hoặc production và không coi các phần phân quyền còn thiếu đã hoàn tất.

## Bản test 1.10.0

- 34 kiểm thử Django thành công trên Windows/Python 3.14/SQLite; giữ các regression 1.9.8.1 và bổ sung giá chung/giá riêng, kỳ hiệu lực, hai nguồn cùng giá, ánh xạ và chặn xung đột, bảo toàn booking, chặn API toàn bộ cho tài khoản hạn chế, quyền nhóm/thu hồi, không rò giá vốn/lợi nhuận, chống chèn trường và tự cấp quyền qua nhóm quản trị, server tính giá booking và kiểm tra revision.
- Node: kiểm tra giá bán độc lập nguồn, nguồn bằng giá không bị gộp, ưu tiên giá riêng, giữ lịch sử, khôi phục danh mục mới, kiểm tra link Zalo và picker đều thành công. Các file legacy.js/pricing.js/restricted.js được kiểm tra cú pháp.
- Django check không có lỗi; makemigrations --check không có thay đổi thiếu migration. Giữ đủ 180 khai báo hàm gốc.
- Chưa chạy nghiệm thu GUI trình duyệt, ứng dụng Zalo, Ubuntu/PostgreSQL hoặc proxy online. Không đánh dấu hoàn thành tất cả yêu cầu phân quyền; xem giới hạn UPGRADE_1_10_0.md.

## Bản cập nhật 1.9.8.1

- 14 kiểm thử Django thành công trên Windows/Python 3.14/SQLite, gồm các ca cũ và regression HTTPS origin, logout, tạo user/nhóm quyền/gán permission, chặn origin lạ và thiếu CSRF token.
- Node kiểm tra cú pháp JavaScript thành công; `node test_frontend.cjs` kiểm tra listener picker, fallback và thông báo lỗi thành công.
- `verify_legacy.py`: giữ đủ 180 khai báo hàm gốc (178 tên).
- Chưa kiểm thử trực tiếp trình duyệt, Ubuntu/PostgreSQL hay máy chủ online. Cần nghiệm thu theo UPGRADE_1_9_8_1.md.

Môi trường kiểm tra: Windows, Python 3.14, Django 5.2.18, SQLite.

- Django system check: không có lỗi.
- 8 kiểm thử backend thành công: yêu cầu đăng nhập, lưu/đọc dữ liệu, chặn revision cũ, giới hạn dữ liệu đại lý, chặn đại lý ghi, chặn trường hợp trùng tên đại lý, kiểm tra CSRF, từ chối cấu trúc nhập sai, tải/xóa file và render trang nội bộ.
- Node `--check`: JavaScript hợp lệ về cú pháp.
- Có `verify_legacy.py` để đối chiếu tất cả khai báo hàm JavaScript gốc vẫn còn trong bản tách.

Chưa kiểm thử trên Ubuntu/PostgreSQL/Nginx, chưa kiểm thử giao diện bằng trình duyệt và chưa nghiệm thu toàn bộ nghiệp vụ bằng dữ liệu thực tế. Xem CHECKLIST_TEST.md và các giới hạn trong README.md.
