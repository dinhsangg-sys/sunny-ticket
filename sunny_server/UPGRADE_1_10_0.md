# Bản test 1.10.0 — nhiều nguồn vé và bảng giá chung

## Nội dung đã làm

- Một loại vé có nhiều giá vốn theo nhà cung cấp và thời gian hiệu lực. Không gộp mất hai nguồn khi giá vốn bằng nhau.
- Bảng giá bán dùng chung cho nhiều đại lý; khai báo nhiều loại vé cùng lúc, gán bảng cho nhiều đại lý trong một lần.
- Giá bán ưu tiên giá riêng có hiệu lực của đại lý, sau đó bảng chung được gán. Không phụ thuộc nguồn vé. Chưa có giá thì báo thiếu giá; không tự lấy 0.
- Booking mới lưu supplierId/supplierName/costPriceId và giữ snapshot giá. Báo cáo công nợ có tổng hợp theo nguồn đã lưu; lịch sử chưa có nguồn hiển thị riêng "Nguồn cũ chưa gán". Không suy đoán nguồn thanh toán cũ.
- Màn hình ánh xạ loại vé cũ → loại vé chung + nhà cung cấp. Có kiểm tra trên server, xem trước, xác nhận và tải backup trước áp dụng. Không tự sửa/xóa booking hoặc thanh toán cũ. Giá bán khác nhau trùng hiệu lực sau ánh xạ sẽ bị chặn để đối soát.
- Hồ sơ đại lý thêm bảng giá chung và link Zalo. Nút mở người nhận ưu tiên link https://zalo.me/... hợp lệ, fallback theo số, giữ sao chép số dự phòng. Không bảo đảm luôn mở thẳng cuộc trò chuyện PC; không tự gửi/đánh dấu đã gửi.
- Thêm quyền nghiệp vụ thực thi qua API riêng cho tài khoản hạn chế: danh mục, nhà cung cấp, bảng giá, booking, trường giá vốn/lợi nhuận, thu/chi và giao dịch thủ công. Quyền trực tiếp và qua nhóm đều được kiểm tra ở backend.

## Phạm vi phân quyền thực tế trong bản này

1. **Superuser hoặc quyền "Toàn bộ dữ liệu/nghiệp vụ"** dùng giao diện gốc và API snapshot đầy đủ. Đây là quyền rộng, KHÔNG cấp cho người cần hạn chế dữ liệu.
2. **Operator/admin không có quyền đầy đủ** dùng màn hình Nghiệp vụ theo quyền, với form và API riêng. Role không tự mở toàn bộ dữ liệu. Cần cấp quyền xem cùng quyền thêm/sửa/xóa và các quyền trường nhạy cảm thích hợp.
3. Cổng đại lý vẫn chỉ đọc dữ liệu của một đại lý được gán. Không cấp role operator cho đại lý.
4. Khi migrate, nhóm **Sunny - Quyền đầy đủ từ bản cũ** được gán cho tài khoản admin/operator đang có để không làm mất quyền đang dùng. Muốn giới hạn tài khoản cũ: bỏ nhóm này, kiểm tra cả quyền trực tiếp/nhóm khác rồi cấp quyền cần thiết.
5. Trong Django Admin, quyền nằm dưới `Legacy | workspace`, tên tiếng Việt. Mã kỹ thuật dùng dấu `__`, ví dụ booking__create. Quản trị user/nhóm vẫn dùng quyền Django chuẩn; nhóm quản trị được ủy quyền chỉ cấp được permission họ đang có, không tự nâng thành superuser.
6. Chỉ đăng ký các quyền đang có kiểm tra backend. PERMISSIONS_CATALOG.md là danh mục đích, không phải toàn bộ đã triển khai.

**Chưa hoàn tất toàn bộ danh mục phân quyền đã thống nhất:** Dashboard/báo cáo theo từng chỉ tiêu, export/import/restore theo quyền riêng, CRM nâng cao/đính kèm theo quyền riêng và thanh toán hàng loạt theo quyền riêng hiện vẫn dành cho người có quyền đầy đủ. Màn hình hạn chế chưa có bộ lọc/báo cáo giống giao diện gốc, chưa hỗ trợ sửa khoản thu qua nút UI (API đã kiểm tra quyền), xóa các danh mục có liên kết hoặc phạm vi chỉ booking tự tạo/đại lý được phân công. Không có quyền giả để mở những chức năng chưa được kiểm tra an toàn. Đây là bản test theo giai đoạn, chưa phải bản hoàn thành toàn bộ yêu cầu phân quyền.

## Cập nhật trên máy Ubuntu của bạn

Trước tiên sao lưu database (SQLite thường nằm ở `/home/sunny-ticket/sunny_server/db.sqlite3`), thư mục media và file cấu hình khi ứng dụng đã ngừng ghi. Không copy database đang ghi như một bản backup nhất quán. Không xóa database hoặc venv.

Nếu cập nhật qua GitHub, tải các file của gói này lên repository rồi trên Ubuntu:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py test apps.legacy
```

Các lệnh dùng đúng đường dẫn venv và chủ sở hữu root đã xác nhận trên máy hiện tại. Máy triển khai khác cần dùng tài khoản sở hữu tương ứng. Nếu Git báo xung đột development.py, giữ bản sao cấu hình và hợp nhất, không reset bỏ cấu hình.

Server hiện chạy bằng runserver trong terminal: nhấn Ctrl+C tại cửa sổ đang chạy, migrate xong thì chạy lại:

```bash
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Giữ terminal mở. Nếu chuyển sang Gunicorn thì chạy collectstatic với môi trường production và restart đúng service thực tế, không mặc định cho rằng đã có service sunny. Sau nâng cấp nhấn Ctrl+F5.

## Thiết lập ví dụ Eco / An Huy / HBM

1. Dùng superuser; xuất backup JSON trước thao tác, giữ bản backup database/media ngoài repository.
2. Nhà cung cấp → tạo An Huy và HBM.
3. Loại vé → thêm vé chung Eco (không xóa Eco An Huy/Eco HBM cũ).
4. Giá vốn → khai báo Eco + An Huy + giá/ngày hiệu lực; thêm Eco + HBM + giá/ngày hiệu lực. Nếu muốn dùng giá vốn cũ qua ánh xạ, không tạo thêm các kỳ giá trùng.
5. Bảng giá chung → tạo Chuẩn/Cấp 1/CTV → Khai báo giá hàng loạt → nhập giá Eco và các vé khác → Gán nhiều đại lý.
6. Hồ sơ đại lý có thể đổi bảng giá được gán. Các dòng Bảng giá trong hồ sơ là giá riêng, luôn ưu tiên hơn bảng chung; muốn đại lý theo bảng chung cần xử lý các kỳ giá riêng đang hiệu lực một cách có chủ đích.
7. Gộp loại vé cũ → chọn Eco An Huy → Eco/An Huy, Eco HBM → Eco/HBM → kiểm tra/xem trước → xác nhận. Gộp nhãn không sửa booking lịch sử.
8. Tạo booking mới, chọn đại lý/vé Eco rồi chọn nguồn trong ô Giá vốn / vé. Giá bán giữ nguyên khi đổi nguồn, giá vốn/lợi nhuận thay đổi. Khi đã có nhà cung cấp được khai báo, booking mới phải chọn dòng có nguồn; các booking cũ vẫn sửa được và giữ snapshot lịch sử.
9. Giá vốn cũ đã có thanh toán không được đổi sang nhà cung cấp khác; cần đối soát thay vì chuyển nợ sang người khác.

### Ví dụ nhóm nhân viên chỉ tạo booking

Tạo nhóm với Xem booking + Tạo booking. Form cung cấp danh mục tối thiểu để chọn đại lý, vé và nguồn. Giá bán/giá vốn được lấy và lợi nhuận được tính ở server; không cấp Xem giá vốn hoặc Xem lợi nhuận nếu không cần. Không gán nhóm Quyền đầy đủ từ bản cũ. Có thể cấp riêng Sửa booking, Thu tiền khách hoặc các quyền khác sau khi kiểm tra tài khoản thực tế.

## Kiểm thử nghiệm thu

- Một đại lý + Eco, chọn hai nguồn: cùng giá bán, đúng hai giá vốn; cùng giá vốn vẫn có hai nguồn.
- Giá riêng, bảng chung, hết hạn, chưa có giá và kỳ giá trùng được xử lý đúng.
- Gán nhiều đại lý, giá mới không làm đổi booking đã lưu.
- Ánh xạ xem trước không ghi dữ liệu; sau áp dụng booking/mã/thu/chi lịch sử giữ nguyên.
- Export/restore JSON mới giữ đủ suppliers/priceLists/priceListItems/ticketMappings. Backup cũ vẫn đọc được; khôi phục thay thế backup cũ sẽ bỏ các danh mục mới không có trong file, đúng ý nghĩa thay thế toàn bộ.
- Tài khoản hạn chế không tải /api/state/, không gửi được trường bị cấm, không vượt quyền khi gọi API trực tiếp, thu hồi nhóm có hiệu lực ở yêu cầu tiếp theo.
- Nút Zalo kiểm tra link ưu tiên, số điện thoại fallback và xác nhận đúng người nhận. Chưa kiểm thử ứng dụng Zalo PC thực tế.

Mô hình lưu chính vẫn là snapshot JSON với revision; API hạn chế chỉnh từng bản ghi và tính booking ở backend nhưng chưa chuyển toàn bộ sang bảng quan hệ riêng. Cần nghiệm thu trình duyệt, Ubuntu/PostgreSQL và dữ liệu thực tế trước vận hành chính thức.
