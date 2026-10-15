# Checklist nghiệm thu so với HTML gốc

Các ô chưa đánh dấu cần người sử dụng test trong trình duyệt. Dùng dữ liệu mẫu, không sửa dữ liệu gốc.

- [ ] Đăng nhập/đăng xuất; user bị khóa không đăng nhập được.
- [ ] Loại vé: tạo, sửa, bật/tắt, tìm kiếm, thứ tự, tham chiếu booking cũ.
- [ ] Đại lý: tạo/sửa, tìm kiếm, nhập Excel và xử lý trùng.
- [ ] Giá đại lý: thêm/sửa, hiệu lực theo ngày, nhập/cập nhật hàng loạt.
- [ ] Giá vốn: thêm/sửa, nhiều mức giá và lựa chọn khi tạo booking.
- [ ] Booking: tạo/sửa/xóa, khách lẻ/đại lý, mã booking, VAT, chi phí, ghi chú.
- [ ] Booking: tìm kiếm, lọc thời gian, trạng thái thanh toán.
- [ ] Thu khách: thu một phần/toàn bộ, sửa/xóa; không vượt công nợ theo UI gốc.
- [ ] Chi nhà cung cấp: trả một phần/toàn bộ, xóa, đối chiếu công nợ.
- [ ] Chi phí khác: thêm/sửa/xóa, đối chiếu lợi nhuận.
- [ ] Sổ quỹ: vốn, thu khác, chi khác, giao dịch booking, số dư và bộ lọc.
- [ ] Dashboard: ngày/tháng, biểu đồ, tổng doanh thu/lợi nhuận/công nợ.
- [ ] Báo cáo: mọi tab/bộ lọc, xuất Excel/CSV, đối chiếu bản gốc.
- [ ] Dữ liệu: backup JSON, khôi phục thay thế, hợp nhất, chặn xung đột.
- [ ] Zalo: mẫu nhắc nợ, chiến dịch, người nhận, trạng thái, CSV, sao chép và mở Zalo PC.
- [ ] Tệp Zalo: thêm ảnh/video, tải từ trình duyệt khác, xóa; đại lý không tải được.
- [ ] Hai trình duyệt: cùng revision, một người lưu trước; người sau bị chặn ghi đè và tải lại thấy dữ liệu mới.
- [ ] Đóng/mở trình duyệt hoặc restart server vẫn giữ dữ liệu.
- [ ] Đại lý A chỉ thấy booking của A; không thấy B, khách lẻ, giá vốn, lợi nhuận.
- [ ] Đại lý không vào API state, API media hoặc admin; user chưa gán đại lý không có dữ liệu.
- [ ] Thử nhập JSON sai định dạng và dữ liệu cũ thiếu trường.
- [ ] Đối chiếu trước/sau chuyển đổi: booking, doanh thu, đã thu, phải thu, đã trả, phải trả, số dư quỹ, lợi nhuận.
