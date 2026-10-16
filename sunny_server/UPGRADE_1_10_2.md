# 1.10.2 — Nhiều mức giá vốn cùng thời gian

Sửa cách hiểu nghiệp vụ: cùng nhà cung cấp + loại vé + thời gian được có nhiều mức giá vốn. Bỏ chặn trùng khoảng hiệu lực cho giá vốn, vẫn kiểm tra ngày và số tiền hợp lệ. Giá bán đại lý không thay đổi quy tắc.

- Khi tạo booking, ô Giá vốn / vé liệt kê từng mức của từng nhà cung cấp. Dòng mặc định có dấu sao, được ưu tiên; người dùng có thể chọn dòng khác hoặc điều chỉnh số tiền nếu có quyền.
- Một nhà cung cấp/loại vé có một dòng mặc định được đặt qua form khai báo. Nếu không đánh dấu mặc định đang hiệu lực, ưu tiên dòng có ngày bắt đầu mới nhất; cùng ngày thì giữ thứ tự khai báo.
- Mỗi booking lưu mã dòng giá và số tiền snapshot. Thêm mức giá hoặc đổi mặc định không cập nhật booking đã lưu. Khi sửa booking, nếu số tiền khai báo đã thay đổi, mặc định giữ giá đang lưu cho đến khi người dùng chọn lại.
- API tài khoản hạn chế hỗ trợ chọn costPriceId cụ thể hoặc dùng mặc định; server kiểm tra đúng nhà cung cấp, loại vé và ngày. Không chọn được dòng thuộc nguồn khác hoặc đã hết hiệu lực.

## Cập nhật Ubuntu

Nhấn Ctrl+C ở cửa sổ chạy server, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Không có migration mới. **Không chạy reset_business_data** trong lần cập nhật này; giữ nguyên dữ liệu đang nhập. Dùng Gunicorn/Nginx thì collectstatic và restart dịch vụ đang dùng theo cấu hình thực tế. Ctrl+F5 để lấy JavaScript 1.10.2.

## Test nghiệp vụ

Khai báo Eco / Hải Bình Minh hai mức 400 và 410 cùng từ 01/10 và cùng không giới hạn. Đặt 400 mặc định. Booking A dùng 400; booking B chọn 410. Đổi mặc định thành 410 rồi tạo booking C: C dùng 410, A/B giữ nguyên. Giá bán đại lý không đổi theo mức giá vốn.

Giữ nguyên các giới hạn phân quyền/production đã nêu trong các bản trước; bản này chỉ sửa lựa chọn nhiều mức giá vốn.
