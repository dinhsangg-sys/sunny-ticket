# 1.10.6 — Sao chép giá và sửa menu sidebar

## Sao chép giá

Đối tác & bảng giá → Bảng giá của đối tác đích → Sao chép giá từ đối tác khác:

1. Chọn nguồn và đích khác nhau.
2. Chọn Giá riêng hoặc Giá đang áp dụng (giá riêng ưu tiên, sau đó bảng chung).
3. Chọn ngày lấy giá nguồn và thời gian áp dụng tại đích.
4. Bấm Xem trước, chọn dòng Sẽ thêm, xác nhận.

Chỉ lấy các loại vé đang dùng có giá hợp lệ tại ngày lấy giá nguồn. Bản này không sao chép toàn bộ các kỳ lịch sử tự động; để lấy mức giá ở thời điểm khác, đổi ngày lấy giá rồi xem trước.

Giá đích đã bao phủ cả khoảng cần sao chép và bằng số tiền được đánh dấu Đã có. Các dòng chồng kỳ khác được đánh dấu Trùng kỳ và bỏ qua. Không ghi đè, tự đóng kỳ giá hoặc xóa giá đích. Muốn thay giá hiện có cần chỉnh kỳ giá riêng trước.

Bản sao là các dòng giá riêng độc lập. Thay giá nguồn sau đó không tự thay giá đích; không thay booking, công nợ hoặc bảng chung đã gán ở đích.

Nếu nguồn có bảng giá chung và người dùng có quyền xem, có thêm nút Gán cùng bảng giá chung. Nút này có xác nhận riêng, chỉ thay bảng chung đích, không tạo các dòng giá riêng; giá riêng đang có ở đích vẫn được ưu tiên.

Tài khoản hạn chế có nút trong màn hình Giá riêng đại lý. Backend yêu cầu agency.view + agency_price.view để xem nguồn, thêm agency_price.create để sao chép. Chế độ giá đang áp dụng cần price_list.view + price_list_item.view; gán cùng bảng chung cần agency.assign_price_list + price_list.view. Kiểm tra revision chống ghi đè, không sao chép khi tên đối tác bị trùng vì mô hình hiện tại vẫn có liên kết giá theo tên.

## Menu sidebar

Desktop dùng cột menu có vùng cuộn riêng theo chiều cao màn hình. Nhà cung cấp, Bảng giá chung, Loại đối tác nằm trong nền tối và cuộn tới được. Mobile giữ menu ngang có cuộn; không thay đổi quyền hay dữ liệu.

## Cập nhật Ubuntu

Nhấn Ctrl+C tại terminal đang chạy server, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không có migration mới trong bản này; lệnh migrate bảo đảm máy đã nhận đầy đủ các quyền từ bản trước. Không reset dữ liệu. Ctrl+F5 để lấy CSS/JavaScript mới. Nếu chạy Gunicorn/Nginx cần collectstatic với đúng môi trường và restart dịch vụ thực tế.

## Kiểm tra sau cập nhật

- Mở màn hình trên máy thấp hoặc zoom lớn, cuộn sidebar đến Loại đối tác, kiểm tra nền/chữ/click. Kiểm tra cả mobile.
- Chọn một nguồn có giá riêng và một đích chưa có giá: xem trước, chọn vài loại, sao chép, tải lại.
- Thử đích đã có giá trùng kỳ: phải bị bỏ qua, dữ liệu không bị ghi đè.
- Thử nguồn dùng bảng chung và trường hợp gán cùng bảng. Kiểm tra booking cũ và công nợ giữ nguyên.
- Thử tài khoản thiếu quyền và hai phiên cùng thay dữ liệu: server phải từ chối phù hợp.

Các kiểm thử backend về sao chép và hồi quy đã đạt; layout sidebar chưa được nghiệm thu bằng trình duyệt online. Giới hạn các chức năng phân quyền khác giữ nguyên như các bản trước.
