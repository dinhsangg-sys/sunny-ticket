# Kết quả kiểm thử bản chuyển đổi

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
