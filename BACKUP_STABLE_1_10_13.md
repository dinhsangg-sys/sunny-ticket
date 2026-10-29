# Mốc ổn định và sao lưu trước module mới

Tag `stable-1.10.13` trỏ đến commit `ce7f4ea24eb9dc7426a91ad8c5c9e3c0894c4733`. Không di chuyển hoặc ghi đè tag này khi phát triển module mới. Tag chỉ giữ mã nguồn, không chứa dữ liệu vận hành.

Database trong workspace Windows hiện rỗng (0 byte); không phải bản sao dữ liệu web. Tệp `stable-1.10.13-source.zip` trên Windows chỉ chứa mã nguồn được Git theo dõi, không chứa database/media/.env.

## Sao lưu dữ liệu thật trên Ubuntu

Dừng ứng dụng bằng Ctrl+C tại terminal chạy server. Đảm bảo các tiến trình ghi dữ liệu khác cũng đã dừng, không chỉnh nguồn/media trong lúc sao lưu. Công cụ dưới đây dành cho cấu hình SQLite tại `/home/sunny-ticket/sunny_server/db.sqlite3` đang dùng; nếu đã đổi database hoặc MEDIA_ROOT sang vị trí khác, cần sao lưu đúng nơi đó riêng trước.

```bash
cd /home/sunny-ticket
sudo git pull --ff-only origin main
sudo sunny_server/.venv/bin/python backup_stable_1_10_13.py /home/sunny-ticket
```

Chỉ khi có dòng `Đã sao lưu và kiểm tra: ...` mới xác nhận thành công. ZIP ở `/home/sunny-ticket-backups/sunny-current-<thời điểm>.zip`, ngoài thư mục app, gồm:

- SQLite snapshot dùng backup API, kiểm tra `quick_check` và bảng workspace;
- mã nguồn hiện có (kể cả thay đổi cục bộ), media và cấu hình/tệp .env trong thư mục app;
- manifest có commit đang dùng, thời gian và SHA-256 từng tệp; kiểm tra CRC của ZIP.

Công cụ không chạy migrate/reset, không sửa database gốc. Không đưa `.git`, virtualenv, node_modules, cache, staticfiles được sinh hoặc các ZIP có sẵn vào bản sao. Liên kết tượng trưng sẽ báo lỗi để tránh bỏ sót dữ liệu ở nơi khác. Đây không phải bản sao toàn máy: cấu hình proxy/systemd bên ngoài `/home/sunny-ticket`, storage ngoài và biến môi trường chỉ tồn tại trong tiến trình cần sao lưu riêng nếu có.

ZIP đặt quyền 600 khi tạo, thư mục mới quyền 700. Có tài khoản/mật khẩu băm và dữ liệu riêng; tải thêm một bản về nơi lưu riêng tư, không đẩy ZIP lên GitHub công khai. Giữ bản sao này bất biến trước khi bắt đầu thử module mới.

Khởi động lại sau khi sao lưu:

```bash
cd /home/sunny-ticket/sunny_server
sudo .venv/bin/python manage.py runserver 0.0.0.0:8000
```

## Khôi phục

Không chỉ quay mã nguồn nếu module mới đã thay cấu trúc dữ liệu. Khi cần khôi phục, dừng ứng dụng, sao lưu riêng trạng thái mới nhất, xác minh ZIP và manifest rồi phục hồi mã nguồn/database/media phù hợp. Không tự khôi phục bản cũ khi đã có giao dịch mới sau thời điểm sao lưu mà chưa đối soát. Chưa thực hiện khôi phục hoặc sao lưu dữ liệu Ubuntu trong cuộc trò chuyện này; cần chạy lệnh trên máy thực tế và xác nhận đầu ra.
