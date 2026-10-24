# Sunny Travel Ticket Management — 1.10.4

**1.10.4:** nút ↑/↓ sắp xếp danh sách giá vốn và nhãn ⭐ Mặc định cạnh số tiền. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_4.md). Migrate để thêm quyền sắp xếp, không reset dữ liệu.

**1.10.3:** xóa loại vé chưa phát sinh dữ liệu; loại vé đã dùng chỉ dừng sử dụng, giữ lịch sử. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_3.md). Cần migrate để bổ sung quyền, không reset dữ liệu.

**1.10.2:** cho phép cùng nhà cung cấp/loại vé có nhiều giá vốn cùng thời gian, chọn theo từng booking hoặc mặc định. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_2.md). Không chạy reset khi cập nhật bản sửa này.

Bản khai báo mới: một loại vé, nhiều nhà cung cấp, giá vốn theo nguồn và bảng giá bán chung gán cho nhiều đại lý. Đã bỏ module ánh xạ loại vé cũ.

## Máy đã cài trước đó

Xem [hướng dẫn cập nhật và xóa dữ liệu nghiệp vụ](sunny_server/UPGRADE_1_10_1.md). Lệnh reset xóa nghiệp vụ/tệp cũ nhưng giữ tài khoản và phân quyền. Không tự xóa dữ liệu chỉ bằng git pull hoặc migrate.

## Cài mới

```bash
git clone https://github.com/dinhsangg-sys/sunny-ticket.git
cd sunny-ticket/sunny_server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py test apps.legacy
python manage.py runserver 127.0.0.1:8000
```

Python 3.12 trở lên. Không có mật khẩu mặc định; không đưa database, media hoặc secret lên Git.

Xem [phạm vi phân quyền đang hỗ trợ](sunny_server/UPGRADE_1_10_0.md#phạm-vi-phân-quyền-thực-tế-trong-bản-này) và [kết quả kiểm thử](sunny_server/TEST_RESULT.md). Các phần ánh xạ trong tài liệu 1.10.0 chỉ là lịch sử và không còn áp dụng. Chưa hoàn tất toàn bộ danh mục phân quyền hoặc mô hình production; không dùng development server như dịch vụ production.
