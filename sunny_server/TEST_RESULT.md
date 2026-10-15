# Kết quả kiểm thử bản chuyển đổi

Môi trường kiểm tra: Windows, Python 3.14, Django 5.2.18, SQLite.

- Django system check: không có lỗi.
- 8 kiểm thử backend thành công: yêu cầu đăng nhập, lưu/đọc dữ liệu, chặn revision cũ, giới hạn dữ liệu đại lý, chặn đại lý ghi, chặn trường hợp trùng tên đại lý, kiểm tra CSRF, từ chối cấu trúc nhập sai, tải/xóa file và render trang nội bộ.
- Node `--check`: JavaScript hợp lệ về cú pháp.
- Có `verify_legacy.py` để đối chiếu tất cả khai báo hàm JavaScript gốc vẫn còn trong bản tách.

Chưa kiểm thử trên Ubuntu/PostgreSQL/Nginx, chưa kiểm thử giao diện bằng trình duyệt và chưa nghiệm thu toàn bộ nghiệp vụ bằng dữ liệu thực tế. Xem CHECKLIST_TEST.md và các giới hạn trong README.md.
