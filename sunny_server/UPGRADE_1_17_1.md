# 1.17.1 — Lọc nhiều phương thức thanh toán

- Bán vé → Báo cáo → Thu theo phương thức; Souvenirs → báo cáo thu tiền: mở Phương thức và tick một hoặc nhiều lựa chọn. Không tick mục nào nghĩa là tất cả. Click bên ngoài hoặc Escape để đóng danh sách.
- Tổng tiền và CSV dùng hợp của các phương thức đã chọn; không nhân đôi khoản thu hay booking dùng nhiều phương thức.
- Khoản thu mới tạo thủ công ở quản trị (thu riêng hoặc hàng loạt) ghi rõ Chưa xác định. Ghi chú không được dùng để đoán phương thức. Booking chưa thu tiền chưa tạo khoản thu trong báo cáo.
- Khoản thu cũ thiếu phương thức tiếp tục thuộc Chưa xác định. Không ghi đè phương thức đã xác nhận ở quầy, thẻ hoặc SePay.

## Cập nhật Ubuntu

Dừng tiến trình đang chạy bằng Ctrl+C tại đúng cửa sổ máy chủ, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py check
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Không có migration mới. Giữ cửa sổ máy chủ mở; không khởi động thêm tiến trình nếu cổng 8000 đang có máy chủ chạy. Tải lại trình duyệt bằng Ctrl+F5 để nhận bộ lọc mới.
