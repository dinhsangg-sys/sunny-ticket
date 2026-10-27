# Sunny Travel Ticket Management — 1.10.10

**1.10.10:** thu tiền khách hàng hàng loạt theo đúng đối tác, tick booking còn nợ và xem trước trước khi xác nhận. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_10.md). Không reset dữ liệu.

**1.10.9:** mở chức năng trong tab mới, sửa nhập tiếng Việt khi tìm vé, tìm nhanh vé trong giá vốn, kéo popup và đồng bộ phiên bản sau lưu cho các chức năng dùng chung dữ liệu. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_9.md). Không reset dữ liệu.

**1.10.8:** bảng Booking gọn một hàng, cố định Thanh toán/Sửa, lọc theo cột, mở form từ đầu, xóa tìm đối tác khi quay lại và dropdown tích hợp tìm nhanh. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_8.md). Không reset dữ liệu.

**1.10.7:** nguồn giá vốn nhập tay cho booking, tìm nhanh đối tác khi sao chép giá và cố định cột thao tác Booking. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_7.md). Không reset dữ liệu.

**1.10.6:** sao chép giá từ đối tác khác có xem trước/chặn ghi đè, và sửa sidebar bị tràn nền. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_6.md). Không reset dữ liệu.

**1.10.5:** phân loại đối tác, quản lý danh mục loại, lọc danh sách/báo cáo/Zalo và gán bảng giá theo loại. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_5.md). Giữ dữ liệu cũ ở Chưa phân loại, không reset.

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
