# Sunny Travel Ticket Management — 1.12.2

**1.12.2:** QR VietinBank tự thêm `SEVQR ` trước mã thanh toán; màn hình phụ hiển thị đúng toàn bộ nội dung chuyển khoản. Ngân hàng khác giữ mã hiện có. SePay vẫn tắt mặc định, chưa cấu hình thanh toán thật trên máy chủ. [Hướng dẫn cập nhật và lưu cấu hình](sunny_server/UPGRADE_1_12_2.md). Không migration mới.

**1.12.1:** đưa tích hợp SePay đã nghiệm thu trên bản thử vào mã chính thức. **Giữ tắt mặc định**, chưa bật thanh toán ngân hàng thật; tiếp tục thu tiền thủ công như 1.12.0. Cần migration 0012. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_12_1.md). Khi có tài khoản SePay sẽ tiếp tục cấu hình ngân hàng và webhook.

**1.12.0:** thêm Tiền mặt/Thẻ thanh toán/Chuyển khoản (mặc định Tiền mặt). Booking quầy mới chờ nhân viên xác nhận thực thu rồi mới hoàn thành và xuất vé; không tự ghi thu khi tạo. Thêm khu vực soạn mẫu email, xem/chỉnh nội dung trước gửi kèm PDF. Giữ nguyên dữ liệu cũ. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_12_0.md). Cần migrate 0011 để lưu nội dung email.

**1.11.4:** dịch QR sang trái để không che tay nhân vật, giữ QR 23.4 mm và khổ 80x110; bỏ ô trắng tại vị trí cũ. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_11_4.md). Không migration mới.

**1.11.3:** tăng khung QR thêm 30% (18 lên 23.4 mm), giữ khổ 80x110 và các trường thông tin. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_11_3.md). Không có migration mới.

**1.11.2:** áp dụng mẫu nét đen trắng và logo chữ đen/nền trắng đã được duyệt để in nhiệt. Giữ khổ 80x110 và vị trí QR/thông tin; PDF cũ giữ nguyên. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_11_2.md). Không có migration mới.

**1.11.1:** thay ảnh mẫu vé đầu ra bằng ảnh mới do người dùng cung cấp, giữ khổ 80x110 và QR/thông tin. PDF đã xuất được giữ nguyên. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_11_1.md). Không cần migration mới.

**1.11.0 chính thức:** đưa bản quầy đã nghiệm thu vào main: thanh toán, nhập/xuất/in vé 80x110, sửa và thay vé theo quyền, báo cáo đối chiếu trong mục Báo cáo, menu dọc nhân viên. [Hướng dẫn nâng cấp bản chính](sunny_server/UPGRADE_1_11_0.md). Sao lưu trước khi pull; không reset và không chép dữ liệu test sang bản chính.

**1.10.13:** mặc định Tất cả nhà cung cấp trong thanh toán tiền vé hàng loạt; dropdown tìm nhanh tự đóng khi bấm ngoài, giữ lựa chọn. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_13.md). Không reset dữ liệu.

**1.10.12:** lọc sản phẩm trong Thanh toán tiền vé hàng loạt, giới hạn loại vé tương ứng và bỏ tick cũ khi đổi sản phẩm. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_12.md). Không reset dữ liệu.

**1.10.11:** lọc sản phẩm trong báo cáo doanh thu/công nợ và Excel; lọc đúng nhà cung cấp khi chi tiền vé hàng loạt; bấm ngoài/Escape đóng riêng bộ lọc loại vé. [Hướng dẫn cập nhật](sunny_server/UPGRADE_1_10_11.md). Không reset dữ liệu.

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
