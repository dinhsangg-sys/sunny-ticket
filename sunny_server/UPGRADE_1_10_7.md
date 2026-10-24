# 1.10.7 — Giá vốn nhập tay và thao tác nhanh

## Thay đổi

- Tạo/sửa Booking: chọn **Nguồn nhập tay — tự nhập giá vốn**, nhập giá vốn/vé và tên nguồn tùy chọn. Không cần tạo nhà cung cấp hoặc dòng giá vốn. Giá 0 hợp lệ; giá trống, âm hoặc không phải số bị từ chối. Nguồn và giá được lưu riêng theo booking, không sửa giá danh mục hay booking khác. Không cho đổi nguồn/tên nguồn đã có khoản chi.
- Tài khoản hạn chế cần quyền xem giá vốn và sửa giá vốn để nhập tay; màn hình thao tác hạn chế có lựa chọn supplier/manual. Các giới hạn phân quyền đã ghi ở bản trước giữ nguyên.
- Sao chép giá: ô tìm nhanh ở cả đối tác nguồn và đích, tìm theo tên/mã, hỗ trợ không dấu. Gõ tìm làm mất hiệu lực bản xem trước cũ; chọn đúng đối tác rồi xem trước lại.
- Bảng Booking: thu gọn khoảng đệm, cho tên dài xuống dòng và cố định cột Thanh toán/Sửa bên phải. Trên màn hình hẹp, các cột dữ liệu khác vẫn có thể cuộn ngang; nút thao tác giữ tại cạnh phải.

## Cập nhật Ubuntu

Nhấn Ctrl+C tại terminal đang chạy server, rồi chạy lần lượt:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không có migration mới; migrate bảo đảm các bản trước đã đầy đủ. Không chạy reset dữ liệu. Giữ terminal chạy server, mở web và nhấn Ctrl+F5. Nếu dùng dịch vụ khác, collectstatic và restart đúng dịch vụ thực tế.

## Kiểm tra sau cập nhật

1. Tạo booking nhập tay, nhập giá và tên nguồn, lưu rồi tải lại. Kiểm tra giá vốn, lợi nhuận và booking khác giữ nguyên.
2. Sửa booking nhập tay, đổi ngày/loại vé và kiểm tra lựa chọn nhập tay vẫn giữ. Thử nguồn danh mục và nguồn mặc định như trước.
3. Thử ô tìm đối tác bằng tên không dấu/mã, chọn nguồn/đích rồi xem trước và sao chép.
4. Kiểm tra nút Thanh toán/Sửa ở kích thước màn hình đang dùng, khi cuộn dọc/ngang và với tên dài.

67 test backend cùng các kiểm tra JavaScript đã đạt. Chưa nghiệm thu giao diện online; không coi các yêu cầu phân quyền ngoài phạm vi này đã hoàn tất.
