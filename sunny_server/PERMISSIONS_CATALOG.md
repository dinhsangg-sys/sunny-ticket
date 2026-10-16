# Danh sách quyền thao tác Sunny Travel

**Cập nhật 1.10.0:** một phần quyền danh mục/giá/booking/thanh toán đã được thực thi bằng API và giao diện riêng. Các mục khác trong danh mục này vẫn là thiết kế đích, không phải quyền đã hoạt động. Xem phạm vi chính xác tại UPGRADE_1_10_0.md. Quyền `workspace.full_access` là quyền rộng và không dùng cho tài khoản cần giới hạn. Quyền Django Admin chuẩn quản lý user/nhóm vẫn độc lập với các mã đề xuất bên dưới.

Đối chiếu bản web 1.9.8.1: static/js/legacy.js, apps/accounts/admin.py, apps/agencies/admin.py, apps/audit/admin.py, apps/legacy/views.py và templates/agency.html.

Đây là danh mục thiết kế quyền theo các thao tác hiện có, không phải danh sách quyền nghiệp vụ đã triển khai. Mã quyền dưới đây là tên đề xuất, chưa phải codename Django có thể chọn ngay. Hiện ứng dụng vẫn dùng role admin/operator/agency; nhóm và model permissions chủ yếu phục vụ Django Admin.

Quyền xem bao gồm mở màn hình, tìm kiếm, lọc, sắp xếp hiển thị và xem chi tiết trong phạm vi được cấp; không tách quyền cho từng nút lọc/ngày. Quyền ghi không tự bao gồm quyền xem dữ liệu nhạy cảm. Quyền xuất dữ liệu cần cả quyền xem tương ứng và quyền xuất.

## 1. Dashboard

| Mã đề xuất | Quyền |
|---|---|
| dashboard.view | Mở Dashboard, xem số vé và booking |
| dashboard.view_revenue | Xem doanh thu |
| dashboard.view_booking_profit | Xem lợi nhuận booking |
| dashboard.view_net_profit | Xem lợi nhuận thực tế và chi phí vận hành |
| dashboard.view_receivables | Xem tổng phải thu, đã thu, còn nợ và booking còn nợ |
| dashboard.view_charts | Xem biểu đồ theo ngày/loại vé, trong giới hạn chỉ tiêu được phép |

## 2. Bán vé / Booking

| Mã đề xuất | Quyền |
|---|---|
| booking.view | Xem danh sách/chi tiết và trạng thái thanh toán |
| booking.create | Tạo booking khách lẻ hoặc đại lý |
| booking.change | Sửa ngày, khách hàng/đại lý, loại vé, số lượng và ghi chú |
| booking.delete | Xóa booking theo quy tắc hiện có, kể cả ảnh hưởng lịch sử thanh toán liên quan |
| booking.change_sell_price | Nhập hoặc điều chỉnh giá bán khi tạo/sửa |
| booking.view_buy_price | Xem giá vốn tại booking |
| booking.change_buy_price | Chọn hoặc nhập giá vốn tại booking |
| booking.change_expense | Chọn hoặc nhập chi phí gắn booking |
| booking.change_vat | Bật/tắt VAT, chọn hoặc nhập thuế suất |
| booking.view_profit | Xem lợi nhuận booking ở các màn hình được phép |

Tạo booking cần quyền đọc tối thiểu danh mục loại vé và đối tác được phép; không đồng nghĩa được mở toàn bộ hồ sơ đại lý/bảng giá/giá vốn. Sửa giá vốn/VAT/giá bán phải kết hợp create hoặc change. Khi triển khai phải tính toán ở server để không cần gửi giá vốn về tài khoản bị hạn chế.

## 3. Thu tiền khách / Đại lý

| Mã đề xuất | Quyền |
|---|---|
| receipt.view | Xem tổng phải thu, đã thu, còn nợ và lịch sử thu |
| receipt.create | Ghi nhận thu tiền/đặt cọc, một phần hoặc toàn bộ |
| receipt.change | Sửa ngày, số tiền, ghi chú khoản thu |
| receipt.delete | Xóa khoản thu |

## 4. Chi tiền vé / Nhà cung cấp

| Mã đề xuất | Quyền |
|---|---|
| supplier_payment.view | Xem phải trả, đã trả, còn trả và lịch sử chi |
| supplier_payment.create | Ghi nhận chi tiền vé theo booking |
| supplier_payment.delete | Xóa khoản chi tiền vé |
| supplier_payment.bulk_create | Chọn nhiều booking/loại vé và thanh toán hàng loạt |

Web hiện chưa có nút sửa riêng khoản chi nhà cung cấp; không liệt kê quyền sửa như chức năng đã có. Quyền bulk_create cần cả create và phạm vi đọc các booking được chọn.

## 5. Loại vé / Khai báo sản phẩm

| Mã đề xuất | Quyền |
|---|---|
| ticket_type.view | Xem mã, tên vé, nhãn sản phẩm và trạng thái |
| ticket_type.create | Thêm loại vé |
| ticket_type.change | Sửa tên loại vé và nhãn sản phẩm |
| ticket_type.change_status | Bật/ngừng dùng loại vé |
| ticket_type.reorder | Đổi thứ tự bằng nút lên/xuống |

Không có xóa loại vé, danh mục sản phẩm độc lập hoặc phát hành/kiểm soát vé QR trong web hiện tại. Mã loại vé đã lưu là định danh cố định.

## 6. Đại lý / CTV

| Mã đề xuất | Quyền |
|---|---|
| agency.view | Xem danh sách và hồ sơ đại lý |
| agency.view_contact | Xem thông tin liên hệ, điện thoại/Zalo |
| agency.create | Thêm đại lý |
| agency.change | Sửa hồ sơ, thông tin liên hệ và ghi chú |
| agency.change_zalo_link | Sửa link Zalo cá nhân của đại lý — tính năng đã đồng ý cho bản tiếp theo, hiện chưa có |
| agency.change_status | Tạm ngưng/kích hoạt lại đại lý |
| agency.delete | Xóa đại lý chưa phát sinh giao dịch và bảng giá liên quan theo quy tắc web |
| agency.download_import_template | Tải mẫu nhập đại lý/bảng giá |
| agency.import | Xem trước và xác nhận nhập/cập nhật đại lý từ Excel/CSV |

Nhập file có giá cần thêm quyền nhập bảng giá tương ứng; việc xóa đại lý kéo theo xóa bảng giá cần được kiểm tra cả quyền liên quan. Hồ sơ đại lý có trường đồng ý nhận tin cần được kiểm soát khi sửa, không dùng quyền gửi tin để tự thay đổi sự đồng ý.

## 7. Bảng giá bán đại lý

| Mã đề xuất | Quyền |
|---|---|
| agency_price.view | Xem bảng giá riêng, loại vé còn thiếu giá và ngày hiệu lực |
| agency_price.create | Khai báo mức giá bán riêng |
| agency_price.change | Sửa giá và thời gian hiệu lực |
| agency_price.delete | Xóa dòng giá |
| agency_price.import | Nhập/cập nhật nhiều mức giá theo file, gồm điều chỉnh kỳ hiệu lực |

Nhập file không được vượt quyền create/change/delete hoặc phạm vi đại lý được cấp, kể cả thay đổi kỳ giá cũ tự động.

## 8. Giá vốn

| Mã đề xuất | Quyền |
|---|---|
| cost_price.view | Xem giá vốn và thời gian hiệu lực |
| cost_price.create | Khai báo giá vốn |
| cost_price.change | Sửa mức giá vốn và thời gian hiệu lực |
| cost_price.set_default | Đặt giá vốn mặc định cho loại vé, bỏ mặc định các dòng khác |
| cost_price.delete | Xóa khai báo giá vốn |

Sửa khai báo giá vốn không đồng nghĩa được sửa giá vốn của booking lịch sử.

## 9. Chi phí khác — Mẫu chi phí booking

| Mã đề xuất | Quyền |
|---|---|
| expense_template.view | Xem danh mục mẫu chi phí |
| expense_template.create | Thêm mẫu nội dung/số tiền chi phí |
| expense_template.change | Sửa mẫu chi phí |
| expense_template.delete | Xóa mẫu chi phí |

Theo mã hiện tại, khai báo ở màn hình này chỉ tạo mẫu để chọn khi lập booking, không tự chi tiền. Chi vận hành thực tế được ghi ở Sổ quỹ → Chi khác.

## 10. Sổ quỹ / Thu chi

| Mã đề xuất | Quyền |
|---|---|
| cashbook.view | Xem giao dịch và nguồn tự động/thủ công |
| cashbook.view_balances | Xem số dư đầu kỳ, tổng thu/chi, vốn và số dư cuối kỳ |
| capital.create | Ghi nhận vốn ban đầu/bổ sung vốn |
| capital.change | Sửa giao dịch vốn |
| capital.delete | Xóa giao dịch vốn |
| other_income.create | Thêm thu khác |
| other_income.change | Sửa thu khác |
| other_income.delete | Xóa thu khác |
| other_expense.create | Thêm chi khác/chi vận hành |
| other_expense.change | Sửa chi khác |
| other_expense.delete | Xóa chi khác |

Nút Xem/Sửa nguồn phải kiểm tra quyền receipt hoặc supplier_payment tương ứng; cashbook.view không tự cấp quyền sửa nguồn. Phần công nợ nhà cung cấp trong Sổ quỹ cần supplier_payment.view; thanh toán hàng loạt cần supplier_payment.bulk_create.

## 11. Báo cáo

| Mã đề xuất | Quyền |
|---|---|
| report.view_overview | Xem tab Tổng quan theo ngày |
| report.view_revenue_receivables | Xem tab Doanh thu & Công nợ chi tiết |
| report.view_vat | Xem tab VAT, giá trị tính và tiền thuế |
| report.view_monthly | Xem tab Theo tháng |
| report.view_supplier_debt | Xem tab Công nợ tiền vé |
| report.view_costs | Xem giá vốn/chi phí trong báo cáo |
| report.view_profit | Xem lợi nhuận trong báo cáo |
| report.export_excel | Xuất Excel công nợ chi tiết trong phạm vi được xem |

Một số cột VAT hoặc số liệu tổng hợp có thể suy ra giá vốn/lợi nhuận; khi triển khai phải lọc ở backend, không chỉ ẩn cột. Báo cáo hiện không có xuất PDF hoặc xuất Excel riêng cho mọi tab.

## 12. Dữ liệu / Sao lưu / Khôi phục

| Mã đề xuất | Quyền |
|---|---|
| data.view_tools | Mở màn hình công cụ dữ liệu |
| data.backup_full | Xuất JSON toàn bộ dữ liệu |
| data.export_bookings_csv | Xuất booking CSV |
| data.preview_import | Đọc file, xem trước và kiểm tra dữ liệu nhập |
| data.restore_replace | Xác nhận thay thế toàn bộ dữ liệu |
| data.merge | Xác nhận nhập bổ sung/hợp nhất dữ liệu không xung đột |

backup_full bao gồm dữ liệu tài chính và cấu hình; không cấp cho người chỉ được xem một phần. restore_replace/merge tác động nhiều module nên cần quyền quản trị dữ liệu tổng thể, không thể dùng để vượt quyền nghiệp vụ. Luồng khôi phục/hợp nhất hiện có gọi backup() trước thay đổi, do đó cần backup_full hoặc cơ chế backup nội bộ an toàn thay thế khi triển khai. JSON không tự bao gồm nội dung file media.

## 13. Chăm sóc khách hàng / Zalo

| Mã đề xuất | Quyền |
|---|---|
| crm.view | Xem danh sách và nội dung chiến dịch |
| crm.create_campaign | Tạo chiến dịch |
| crm.change_campaign | Sửa tên/nội dung chiến dịch |
| crm.view_recipients | Xem người nhận, điện thoại và tiến độ |
| crm.add_recipients | Bổ sung đại lý hợp lệ vào chiến dịch |
| crm.change_recipient_status | Đánh dấu Đã gửi/Lỗi/Chưa gửi |
| crm.export_progress_csv | Xuất tiến độ chiến dịch CSV |
| crm.change_reminder_template | Sửa mẫu nhắc công nợ mặc định |
| crm.compose_payment_reminder | Soạn/chỉnh bản nháp nhắc công nợ booking |
| crm.copy_content | Sao chép nội dung chiến dịch hoặc tin nhắc |
| crm.open_zalo | Xem hướng dẫn, sao chép số điện thoại và mở Zalo PC |
| crm.upload_media | Thêm ảnh/video chiến dịch |
| crm.download_media | Xem/tải file đính kèm |
| crm.delete_media | Xóa file đính kèm chiến dịch |

Soạn nhắc nợ cần quyền đọc công nợ booking và liên hệ đại lý. Người đã được phép xem nội dung có thể tự sao chép/chụp màn hình; quyền copy_content chỉ kiểm soát nút hỗ trợ. Mở Zalo là hành động cục bộ, không phải quyền tự động gửi. Web chưa có tự gửi Zalo OA hoặc nút xóa chiến dịch.

Bản tiếp theo đã được đồng ý bổ sung nút mở Zalo người nhận: ưu tiên link cá nhân đã lưu, thử link theo số khi thiếu, giữ sao chép số dự phòng. Hành vi này thuộc crm.open_zalo và quyền đọc liên hệ trong phạm vi được cấp, không có nghĩa bảo đảm mở thẳng cuộc trò chuyện PC hoặc tự gửi tin.

## 14. Cổng đại lý

| Mã đề xuất | Quyền |
|---|---|
| agency_portal.access | Vào cổng đại lý được gán |
| agency_portal.view_bookings | Xem booking thuộc đại lý được gán |
| agency_portal.view_receivables | Xem tổng tiền, đã thu, còn nợ của đại lý được gán |

Hiện cổng đại lý chỉ đọc, chưa có tạo booking, xem bảng giá riêng hay tự quản lý thành viên. Không liệt kê các mục này là chức năng hiện hữu.

## 15. Quản trị người dùng / Nhóm / Đại lý / Nhật ký

Các thao tác dưới đây đã có qua Django Admin, tùy quyền staff/superuser và model permissions. Việc tách quyền nhạy cảm bên trong form User là thiết kế cần bổ sung, vì hiện một quyền change_user không phân biệt tất cả trường.

| Mã đề xuất | Quyền |
|---|---|
| admin.access | Truy cập khu vực quản trị (is_staff và quyền phù hợp) |
| user.view | Xem danh sách/chi tiết tài khoản |
| user.create | Tạo tài khoản |
| user.change | Sửa thông tin tài khoản |
| user.delete | Xóa tài khoản theo ràng buộc dữ liệu |
| user.change_status | Khóa/mở tài khoản bằng trạng thái active |
| user.set_password | Đặt lại mật khẩu cho tài khoản |
| user.assign_role | Gán role Sunny |
| user.assign_agency | Gán đại lý cho tài khoản |
| user.assign_groups | Thêm/bỏ nhóm của tài khoản |
| user.assign_permissions | Cấp/thu hồi quyền trực tiếp |
| user.change_staff | Cấp/bỏ quyền vào admin |
| user.change_superuser | Cấp/bỏ superuser — chỉ quản trị tối cao |
| group.view | Xem nhóm và quyền của nhóm |
| group.create | Tạo nhóm |
| group.change | Sửa nhóm |
| group.delete | Xóa nhóm |
| group.assign_permissions | Cấp/thu hồi quyền của nhóm |
| admin_agency.view | Xem bảng Agency ánh xạ tài khoản trong admin |
| admin_agency.create | Tạo Agency ánh xạ trong admin |
| admin_agency.change | Sửa Agency ánh xạ trong admin |
| admin_agency.delete | Xóa Agency ánh xạ nếu không bị ràng buộc |
| audit.view | Xem nhật ký lưu của ứng dụng |

Agency trong admin là bảng ánh xạ tài khoản với legacy_id/name, không thay thế đầy đủ hồ sơ đại lý trong dữ liệu nghiệp vụ. Không nên cho người vận hành sửa hai nơi độc lập. Nhật ký ứng dụng hiện chỉ đọc; không thiết kế quyền thêm/sửa/xóa nhật ký cho người dùng. Django Admin tự ghi lịch sử thao tác quản trị; không có màn hình quản lý Permission riêng được đăng ký trong bản hiện tại, quyền có sẵn được chọn qua user/group.

## 16. Phạm vi dữ liệu đi kèm mọi quyền

- Toàn hệ thống: chỉ người có phạm vi toàn hệ thống được truy cập dữ liệu các đại lý/khách lẻ.
- Một đại lý được gán: chỉ dữ liệu thuộc đại lý của tài khoản; bản hiện tại có gán một Agency cho một user.
- Chỉ bản ghi do mình tạo hoặc danh sách đại lý được phân công: là mở rộng tương lai, chưa có trường ownership/phân công đầy đủ nên chưa thể áp dụng đúng trong bản hiện tại.
- Trường nhạy cảm: giá vốn, lợi nhuận, liên hệ khách hàng/đại lý, chi nhà cung cấp và backup cần kiểm soát riêng; xuất file và báo cáo tổng hợp cũng phải tuân thủ cùng giới hạn.

## Nguyên tắc áp dụng

1. Quyền được cấp trực tiếp hoặc qua nhóm; không có quyền thì mặc định từ chối. Không tự cấp mọi quyền nghiệp vụ chỉ vì user là staff.
2. Backend phải kiểm tra quyền đọc, ghi, bản ghi và trường dữ liệu. Ẩn menu/nút là hỗ trợ giao diện, không thay kiểm tra server.
3. Import, restore, thao tác hàng loạt và xóa dây chuyền phải kiểm tra toàn bộ phạm vi bị tác động.
4. Thu hồi quyền phải có hiệu lực với yêu cầu server tiếp theo, không phụ thuộc việc người dùng còn mở tab cũ.
5. Cần lộ trình chuyển đổi role hiện có, không âm thầm mở rộng quyền của tài khoản đang dùng. Superuser giữ vai trò quản trị tối cao.
6. Không tạo quyền cho đăng nhập/đăng xuất, mở/đóng form, chọn ngày hoặc tìm kiếm riêng; các thao tác này đi theo quyền truy cập/xem thích hợp.
7. Danh mục này chưa thay đổi quyền thực tế và chưa tạo migration. API snapshot hiện tại cần được thay đổi trước khi thực thi an toàn quyền nghiệp vụ chi tiết.
