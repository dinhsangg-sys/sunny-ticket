# 1.10.4 — Sắp xếp giá vốn và nhãn mặc định

- Màn hình Giá vốn có cột Thứ tự, nút ↑/↓ trên mỗi dòng. Dòng đầu/cuối tự khóa nút tương ứng. Thứ tự được lưu trên server, giữ khi tải lại và khi sửa dòng giá.
- Dòng được cài mặc định hiển thị badge xanh **⭐ Mặc định** cạnh số tiền. Nhãn này thể hiện cấu hình mặc định; khi lập booking giá vẫn cần đang trong thời gian hiệu lực.
- Sắp xếp chỉ thay đổi danh sách quản lý giá vốn; không đổi thứ tự lưu trong mảng dữ liệu, mã dòng, mức mặc định hoặc cách tự chọn giá của booking. Giá và nguồn của booking đã lưu không thay đổi.
- Tài khoản hạn chế có quyền Xem giá vốn + Sắp xếp thứ tự các dòng giá vốn mới được dùng nút. Việc sắp xếp được kiểm tra trên server và dùng revision chống ghi đè.

## Ubuntu

Nhấn Ctrl+C tại terminal đang chạy server, sau đó:

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo .venv/bin/python manage.py migrate
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

Ctrl+F5 trên website. Có migration bổ sung quyền sắp xếp, không reset dữ liệu. Nếu dùng staticfiles qua Nginx/Gunicorn thì collectstatic bằng môi trường production và restart đúng dịch vụ đang dùng.

Nghiệm thu: đưa dòng cuối lên, đưa dòng đầu xuống, tải lại; sửa giá rồi kiểm tra vị trí không đổi; mặc định vẫn đúng và booking cũ không đổi. Giới hạn các tính năng khác không thay đổi trong bản cập nhật này.
