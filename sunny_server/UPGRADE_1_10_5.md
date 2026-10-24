# 1.10.5 — Phân loại đối tác

## Chức năng

- Hồ sơ đối tác có trường Loại đối tác. Nhóm ban đầu: Đại lý du lịch, Hướng dẫn viên, Khách sạn/lưu trú, Cộng tác viên cá nhân và Khác.
- Hồ sơ cũ giữ nguyên, hiển thị Chưa phân loại; không tự suy đoán nhóm từ tên đối tác.
- Mục Loại đối tác: thêm, đổi tên, ngừng/kích hoạt. Ngừng không xóa hồ sơ đã gán, không được gán mới vào nhóm ngừng. Không có nút xóa nhóm.
- Đối tác & bảng giá: bộ lọc và cột loại đối tác. Trường loại đối tác độc lập bảng giá, trạng thái hoạt động và vai trò đăng nhập.
- Bảng giá chung → Gán nhiều đại lý: lọc theo loại đối tác và chọn tất cả kết quả. Những đối tác ngoài bộ lọc giữ trạng thái chọn cũ; bảng giá không tự thay đổi khi đổi loại đối tác.
- Báo cáo → Doanh thu & Công nợ: lọc theo loại đối tác, tổng tiền và Excel lấy đúng các dòng đang lọc. Các tab khác chưa có bộ lọc này. Báo cáo phân nhóm theo hồ sơ hiện tại, không viết lại booking lịch sử. Khi chọn một nhóm đối tác, khách lẻ không thuộc kết quả.
- Zalo → Tạo chiến dịch: chọn loại người nhận, vẫn kiểm tra số điện thoại, trạng thái hoạt động và sự đồng ý nhận tin như trước. Bộ lọc được lưu trong chiến dịch; Thêm đại lý mới chỉ thêm người hợp lệ thuộc nhóm đã chọn. Không tự gửi tin.
- Backup JSON giữ danh mục partnerTypes và partnerTypeId trong hồ sơ. Import Excel hiện tại giữ phân loại của hồ sơ đang có, hồ sơ mới để Chưa phân loại; chưa có cột phân loại trong mẫu Excel.

## Quyền

Tài khoản hạn chế cần agency.view + agency.change + agency.classify để phân loại trong hồ sơ. Quản lý nhóm dùng partner_type.view/create/change/change_status tương ứng. Superuser và quyền toàn bộ workspace dùng giao diện đầy đủ như trước.

Mã loại đối tác trong dữ liệu dùng cho liên kết, không tự thay đổi khi sửa tên. Tài khoản đăng nhập vẫn gán Agency riêng như trước. Các hạn chế phân quyền ngoài phạm vi chức năng này không thay đổi.

## Ubuntu

Nhấn Ctrl+C tại terminal đang chạy server rồi chạy:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Ctrl+F5 trên website, mở Đối tác & bảng giá → Hồ sơ → Loại đối tác. Không chạy reset và không xóa database. Migration chỉ bổ sung quyền; các nhóm mặc định dùng fallback cho đến khi danh mục được lưu lần đầu. Nếu dùng Nginx/Gunicorn, collectstatic và restart dịch vụ thực tế với cấu hình hiện tại.

## Kiểm thử

52 test backend đạt, gồm hồ sơ cũ chưa phân loại, không đổi giá/lịch sử khi phân loại, loại không tồn tại/ngừng dùng, không xóa nhóm đã có liên kết và quyền phân loại/quản lý nhóm.

JavaScript kiểm tra bộ lọc, danh sách báo cáo/Excel, người nhận Zalo và backup đạt. Chưa nghiệm thu GUI trên trình duyệt/server online; test lại với một đối tác mỗi nhóm sau cập nhật.
