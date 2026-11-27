# 1.22.0 — Quản lý dịch vụ và giá Digital theo nhóm vé

## Quy trình mới

Vào **Website & vé online → Dịch vụ online**, mở một dịch vụ:

1. **Nội dung giới thiệu**: thông tin dịch vụ, hình đại diện, bài giới thiệu Việt/Anh.
2. **Nhóm vé & giá online**: bấm Thêm nhóm vé, đặt tên ECO/HIGH/VIP và tên tiếng Anh; bấm **Lưu và tiếp tục chỉnh sửa**. Bấm **Vé & giá →** trên dòng nhóm.
3. Trong nhóm, bấm Thêm vé và giá Digital. Chọn vé đã khai báo trong hệ thống, nhóm khách (người lớn/trẻ em/người cao tuổi), nhập giá công bố và **giá online mặc định**. Mỗi nhóm khách có một vé đang bán trong nhóm.
4. Có thể bật **Gạch ngang giá công bố**, chỉ áp dụng khi giá online thấp hơn giá công bố. Giá công bố để trống thì không hiển thị; không tự suy ra giá công bố từ giá vốn. Hệ thống hiện chưa có trường giá công bố riêng trong danh mục vé, nên nhập giá tham chiếu cạnh giá online.
5. Lưu và bấm **Quay lại dịch vụ**. Trong tab **Xuất bản**, chọn hiển thị công khai và vé làm giá giới thiệu trên thẻ dịch vụ, nếu muốn.

Giá online nhập tại vé là **giá bán mặc định của Digital**, không cần khai báo bảng giá ngày riêng. Khách thanh toán theo giá online; giá vốn và mã vé lấy từ vé gốc, đối tượng báo cáo vẫn Digital. Vé chỉ đặt được khi vé gốc đang hoạt động và có giá vốn mặc định hợp lệ tại ngày sử dụng.

## Thu gọn giao diện

- Bỏ trường Loại vé mặc định khỏi màn hình dịch vụ.
- Menu Website chỉ giữ Dịch vụ, Bài viết, Liên hệ và Đơn online/chờ gửi vé. Các màn hình giá kỳ cũ, lựa chọn vé rời và dữ liệu đơn kỹ thuật được ẩn khỏi menu; không xóa lịch sử.
- Câu hỏi bot được mở từ liên kết Câu hỏi tư vấn trên trang dịch vụ.
- Trang nhóm vé có giá công bố và giá Digital cạnh nhau, màu nhẹ, không cần đi qua bảng giá rời.

## Dữ liệu và quyền

Migration **online.0011_service_ticket_management** gom các lựa chọn vé hiện có vào nhóm. Vé mặc định cũ được chuyển thành lựa chọn trong nhóm Vé tiêu chuẩn, sao chép các kỳ giá cũ sang lựa chọn mới. Không đổi đơn đã tạo, khoản thu, giá vốn, snapshot hoặc doanh thu.

Các vé cũ chưa có giá mặc định tiếp tục dùng kỳ giá cũ. Khi nhập giá online mặc định tại nhóm, giá này thay thế kỳ giá cũ cho các lần đặt mới, áp dụng mọi ngày có giá vốn hợp lệ. Không tự chọn một kỳ giá để biến thành giá mặc định. Kiểm tra nhóm khách và giá trước khi lưu vé cũ. Giỏ hàng chưa thanh toán dùng vé mặc định cũ phải chọn lại vé; đơn đã tạo vẫn giữ giá snapshot và quy trình xử lý hiện có.

Quản trị viên có toàn quyền. Người được giao quản lý cần quyền thêm/sửa dịch vụ online; quyền sửa dịch vụ cho phép quản lý nhóm và các vé của dịch vụ. Quyền xử lý đơn và gửi vé vẫn riêng như trước.

## Cập nhật máy chủ

Sao lưu cơ sở dữ liệu và media trước khi cập nhật. Dừng tiến trình ứng dụng bằng Ctrl+C trong đúng cửa sổ đang chạy.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
cd sunny_server
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py migrate'
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; .venv/bin/python manage.py check'
sudo .venv/bin/python manage.py collectstatic --noinput
sudo bash -c 'set -a; . /etc/sunny-sepay.env; set +a; cd /home/sunny-ticket/sunny_server; exec .venv/bin/python manage.py runserver 0.0.0.0:8000'
```

Giữ cửa sổ ứng dụng mở, tải lại trang quản trị bằng Ctrl+F5. Kiểm tra một dịch vụ và các nhóm vé trước khi mở bán.
