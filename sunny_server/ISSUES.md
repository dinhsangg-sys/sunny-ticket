# Lỗi ghi nhận khi kiểm thử online

## Tiến độ bản test 1.10.0

- Đã tạo mô hình nhà cung cấp + giá vốn theo nguồn, bảng giá chung gán nhiều đại lý và giá riêng ưu tiên, ánh xạ vé có xem trước giữ lịch sử.
- FEATURE-003: đã thêm link Zalo trong hồ sơ và mở người nhận ưu tiên link hợp lệ, giữ fallback số điện thoại. Chờ nghiệm thu Zalo PC/trình duyệt thực tế.
- FEATURE-002: đã có API/màn hình riêng và quyền backend cho các danh mục, giá, booking, thanh toán và thu/chi. CHƯA hoàn thành mọi mục trong PERMISSIONS_CATALOG.md; các chức năng chưa tách an toàn tiếp tục yêu cầu quyền đầy đủ. Xem UPGRADE_1_10_0.md, không đánh dấu toàn bộ yêu cầu phân quyền đã hoàn thành.

## Phạm vi bản cập nhật tiếp theo — người dùng đã đồng ý

- Triển khai phân quyền chi tiết theo PERMISSIONS_CATALOG.md, không chỉ bổ sung tên quyền. Hỗ trợ cấp trực tiếp/qua nhóm, kiểm tra backend, phạm vi dữ liệu và trường nhạy cảm; menu/nút phản ánh quyền thực tế. Cần sửa cơ chế snapshot trước khi cho phép tài khoản có quyền hạn chế sử dụng.
- Bổ sung mở Zalo người nhận theo FEATURE-003 bên dưới.
- Bảo toàn dữ liệu và các chức năng hiện có; kiểm thử hồi quy và tài khoản quyền hạn chế trước phát hành. Ghi rõ migration/cấu hình và cách chuyển role hiện có khi nâng cấp.
- Đây là phạm vi đã thống nhất để làm trong bản tiếp theo; chưa triển khai hoặc phát hành các tính năng này.

## FEATURE-003 — Mở Zalo người nhận từ ứng dụng

- Trạng thái: người dùng đồng ý đưa vào bản cập nhật tiếp theo cùng phân quyền chi tiết.
- Thêm nút Mở Zalo người nhận tại các điểm liên hệ Zalo hiện có: đại lý, nhắc thanh toán và người nhận chiến dịch.
- Cho phép lưu link Zalo cá nhân do đại lý cung cấp; ưu tiên link hợp lệ đã lưu, nếu không có thì thử liên kết theo số điện thoại đã chuẩn hóa.
- Giữ sao chép số điện thoại làm dự phòng. Không cam kết luôn mở thẳng đúng cuộc trò chuyện Zalo PC; phụ thuộc Zalo/trình duyệt/cài đặt người nhận. Không tự gửi tin hoặc tự đánh dấu Đã gửi khi mở liên kết.
- Kiểm tra URL đầu vào để chỉ chấp nhận HTTPS trên host Zalo được hỗ trợ, không chấp nhận URL javascript/data hoặc host giả mạo. Mở liên kết từ click trực tiếp và không cho trang ngoài truy cập opener.
- Bổ sung quyền sửa link liên hệ vào hồ sơ đại lý; quyền xem/mở liên hệ theo phạm vi đại lý và quyền CRM trong danh mục.
- Nghiệm thu: link lưu sẵn, link theo số, số không hợp lệ, chưa có liên hệ, fallback sao chép, quyền hạn chế, mở trên PC/điện thoại; xác nhận đúng người trước gửi và không thay đổi trạng thái thanh toán/chiến dịch.

## FEATURE-002 — Thiếu quyền nghiệp vụ vé, booking và khai báo

- Trạng thái: đã xác nhận thiếu chức năng, chưa triển khai.
- Bằng chứng: ảnh trang /admin/accounts/user/2/change/; danh sách quyền đang là quyền model Django Admin, không có mục quyền nghiệp vụ tạo vé, đặt vé và khai báo theo yêu cầu người dùng.
- Hiện trạng: backend ứng dụng dùng role admin/operator/agency; operator có quyền nghiệp vụ nội bộ rộng. Chưa thể cấp operator rồi giới hạn riêng tạo/sửa booking hoặc danh mục bằng các quyền trong ảnh.
- Phạm vi đề xuất: quyền xem/thêm/sửa/xóa riêng cho loại vé, booking, đại lý, bảng giá và giá vốn; quyền chi phí, thu/chi, báo cáo, giá vốn/lợi nhuận, nhập/khôi phục dữ liệu và CRM cần được tách tương ứng khi chuẩn hóa phân quyền.
- Yêu cầu thực thi: cấp trực tiếp hoặc qua nhóm trong admin; giới hạn giao diện và bắt buộc kiểm tra ở backend, kể cả gọi API trực tiếp; kiểm soát cả trường dữ liệu nhạy cảm và phạm vi đại lý.
- Ràng buộc kỹ thuật: API hiện ghi toàn bộ snapshot, nên chỉ thêm tên permission hoặc ẩn nút không đủ an toàn. Cần API theo nghiệp vụ hoặc cơ chế kiểm tra thay đổi và dữ liệu đọc trước khi cho phép lưu snapshot; không tuyên bố đã hỗ trợ phân quyền chi tiết khi chưa thực thi ở backend.
- Nghiệm thu: tài khoản chỉ được tạo booking không sửa danh mục/giá vốn; tài khoản chỉ xem không ghi được; kiểm tra cấp qua nhóm, thu hồi quyền, gọi API trực tiếp, dữ liệu nhạy cảm và cách bảo toàn quyền người dùng hiện có khi nâng cấp.
- Không nằm trong bản vá CSRF 1.9.8.1; chưa sửa code, chưa đẩy tính năng lên GitHub.

## Trạng thái phát hành 1.9.8.1

- BUG-001 đến BUG-009: đã sửa cấu hình CSRF dùng chung và bổ sung xử lý lỗi; 14 test backend thành công, gồm lưu snapshot các module, logout HTTPS, tạo user/nhóm và gán permission Django. Chờ người dùng nghiệm thu online từng thao tác; chưa xác nhận nguyên nhân chi tiết của từng ảnh API 403 riêng lẻ.
- BUG-008: lỗi lưu nhóm đã sửa; quyền Django Admin được kiểm thử. Phân quyền chi tiết cho từng nghiệp vụ trong ứng dụng chưa triển khai, tiếp tục dùng role như bản trước.
- UX-001: đã thêm mở picker khi bấm toàn ô date/month, có xử lý trình duyệt không hỗ trợ; kiểm thử JavaScript thành công, chờ kiểm tra trực tiếp trình duyệt.
- Hướng dẫn nâng cấp: UPGRADE_1_9_8_1.md. Không có migration mới.
- Các mục bên dưới giữ nguyên ghi nhận ở thời điểm báo lỗi; trạng thái phát hành ở đây là thông tin mới nhất.

## UX-001 — Bấm toàn bộ ô ngày trong bộ lọc để mở lịch

- Trạng thái: đã ghi nhận, chờ thực hiện trong bản cập nhật tiếp theo.
- Yêu cầu: bấm vào phần chữ ngày hoặc bất kỳ vùng nào trong ô ngày sẽ mở bộ chọn lịch, không cần nhắm vào biểu tượng lịch.
- Bằng chứng: ảnh bộ lọc Khoảng thời gian trên Dashboard, khoanh phần chữ ngày trong ô Từ ngày.
- Phạm vi: ô ngày của các bộ lọc, gồm Từ ngày/Đến ngày ở Dashboard và các màn hình lọc tương ứng; kiểm tra riêng bộ lọc tháng nếu áp dụng cùng hành vi.
- Hướng thực hiện: dùng showPicker() từ thao tác click trực tiếp nếu trình duyệt hỗ trợ; giữ khả năng nhập ngày và sử dụng bàn phím, không làm thay đổi giá trị/bộ lọc chỉ vì mở lịch; xử lý an toàn trường hợp API không hỗ trợ hoặc bị từ chối.
- Nghiệm thu: click phần chữ, khoảng trống và biểu tượng đều mở lịch trên trình duyệt hỗ trợ; chọn ngày cập nhật bộ lọc theo luồng hiện tại; không lỗi trên thiết bị cảm ứng hoặc trình duyệt không hỗ trợ; vẫn dùng được Tab và nhập bằng bàn phím.
- Chưa sửa code, triển khai hoặc đẩy thay đổi GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-009 — Khai báo giá vốn không lưu được

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh form Khai báo giá vốn tại sn.hoianmemorieslands.com; thông báo không lưu được dữ liệu, trang đã khóa; phản hồi HTML có tiêu đề 403 Forbidden.
- Thao tác: Giá vốn → khai báo giá vốn → Lưu.
- Kết quả mong muốn: lưu giá vốn, thời gian hiệu lực và trạng thái mặc định hợp lệ; tải lại vẫn còn và chọn đúng khi tạo booking.
- Kết quả thực tế: bước lưu bị HTTP 403 và khóa giao diện.
- Liên quan nhóm lỗi lưu chung: save() → PUT /api/state/. Cần kiểm tra CSRF/origin, phiên và quyền; ảnh này không hiển thị lý do chi tiết của 403 nên chưa xác nhận nguyên nhân cụ thể.
- Nghiệm thu: thêm/sửa giá vốn, hiệu lực từ/đến ngày, giá vốn mặc định và nhiều mức giá; chọn đúng giá khi tạo booking; giữ nguyên giá vốn của booking lịch sử; tải lại đối chiếu dữ liệu. Kiểm tra cả trường hợp thiếu loại vé hoặc số tiền không hợp lệ.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-008 — Thêm quyền trong quản trị chưa hoạt động

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Người dùng báo các chức năng thêm người dùng và thêm quyền trong quản trị đều chưa hoạt động, bị lỗi.
- Thêm người dùng được theo dõi ở BUG-007, đã có ảnh xác nhận lỗi trusted origin/CSRF.
- Bằng chứng bổ sung: ảnh tại `/admin/auth/group/add/` xác nhận lỗi khi thêm nhóm quyền. Django trả HTTP 403, `CSRF verification failed`, lý do `Origin checking failed - https://sn.hoianmemorieslands.com does not match any trusted origins.`
- Nguyên nhân lỗi lưu nhóm đã xác nhận: domain HTTPS chưa nằm trong trusted origins của cấu hình đang chạy, cùng nguyên nhân BUG-001 và BUG-007. Ảnh chưa xác nhận kết quả các thao tác gán quyền khác.
- Kiểm tra trong bản cập nhật: tạo/sửa nhóm quyền; gán/bỏ quyền cho nhóm và user; gán user vào nhóm; tạo/sửa user và role/agency; kiểm tra lưu qua domain HTTPS và quyền thực tế sau đăng nhập lại.
- Lưu ý thiết kế hiện tại: Django groups/model permissions và trường role của Sunny là hai cơ chế khác nhau; các view nghiệp vụ đang kiểm tra role, chưa thực thi quyền chi tiết theo nhóm. Cần đối chiếu cơ chế hiện tại khi xử lý phản ánh này, không báo gán quyền thành công đồng nghĩa đã áp dụng cho mọi thao tác nghiệp vụ.
- Nghiệm thu: thao tác quản trị lưu được, quyền được áp dụng đúng phạm vi đã hỗ trợ, không cấp nhầm quyền quản trị hoặc dữ liệu đại lý khác; ghi rõ các quyền nghiệp vụ chi tiết chưa triển khai.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-007 — Tạo người dùng trong Django Admin bị 403 CSRF

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh tại /admin/accounts/user/add/ trên sn.hoianmemorieslands.com; Django báo `CSRF verification failed` và `Origin checking failed - https://sn.hoianmemorieslands.com does not match any trusted origins.`
- Thao tác: quản trị → thêm người dùng → gửi form tạo tài khoản.
- Kết quả mong muốn: tạo tài khoản hợp lệ, lưu vai trò/đại lý được gán, có thể đăng nhập theo quyền.
- Kết quả thực tế: HTTP 403 do origin HTTPS chưa nằm trong CSRF_TRUSTED_ORIGINS của cấu hình đang chạy.
- Nguyên nhân đã xác nhận từ ảnh: cùng cấu hình trusted origins với BUG-001. Đây là form Django Admin, không dùng API snapshot /api/state/.
- Phạm vi: lỗi cấu hình CSRF ảnh hưởng cả form quản trị và thao tác ghi dữ liệu nghiệp vụ; cần kiểm thử cả hai luồng sau sửa.
- Nghiệm thu: superuser tạo/sửa user, đổi mật khẩu, gán role/agency; đăng nhập tài khoản mới và kiểm tra phạm vi quyền; origin không được tin cậy vẫn bị chặn. Không bỏ kiểm tra CSRF để khắc phục.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-006 — Khôi phục thay thế toàn bộ dữ liệu bị 403

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh màn hình Dữ liệu tại sn.hoianmemorieslands.com; phần xem trước khôi phục hiển thị 18 loại vé, 22 đại lý, 35 booking, 1 giao dịch sổ quỹ. Hộp thoại báo không lưu được dữ liệu, trang đã khóa, phản hồi HTML có tiêu đề 403 Forbidden.
- Thao tác: chọn file backup → xem trước khôi phục toàn bộ → xác nhận khôi phục thay thế toàn bộ.
- Kết quả mong muốn: lưu dữ liệu khôi phục lên server sau xác nhận; tải lại vẫn còn dữ liệu và các tổng đối soát khớp file backup.
- Kết quả thực tế: file đã được đọc đến bước xem trước nhưng bước lưu server bị từ chối HTTP 403. Chưa xác minh dữ liệu đang lưu trên server; không coi dữ liệu trong bộ nhớ trình duyệt là khôi phục thành công.
- Liên quan BUG-002 đến BUG-005: dùng chung save() → PUT /api/state/. Cần xác minh CSRF/origin, session và quyền; ảnh không cho thấy lý do chi tiết của 403.
- Nghiệm thu: backup trước thay thế, khôi phục file hợp lệ, tải lại đối soát số lượng và số tiền; thử hợp nhất và chặn xung đột; khi lưu thất bại không báo thành công hoặc để người dùng hiểu nhầm dữ liệu đã được khôi phục trên server.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-005 — Tạo chiến dịch chăm sóc khách hàng Zalo không lưu được

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh form Tạo chiến dịch Zalo tại sn.hoianmemorieslands.com; tên chiến dịch "Lịch hoạt động tháng 2026-10", chưa chọn tệp, người nhận mặc định là 0. Hộp thoại báo không lưu được dữ liệu, trang đã khóa; phản hồi HTML có tiêu đề 403 Forbidden.
- Thao tác: Chăm sóc khách hàng / Zalo → Tạo chiến dịch → nhập tên và nội dung → Tạo chiến dịch.
- Kết quả mong muốn: lưu chiến dịch trên server và mở màn hình chiến dịch; dữ liệu tồn tại sau tải lại.
- Kết quả thực tế: lưu bị HTTP 403 và giao diện bị khóa; ảnh chưa thể hiện hoạt động gửi tin hoặc tải tệp.
- Liên quan BUG-002/003/004: tạo chiến dịch dùng chung save() → PUT /api/state/. Cần kiểm tra CSRF/origin, session và quyền; chưa xác nhận nguyên nhân cụ thể từ ảnh vì không thấy lý do chi tiết của 403.
- Nghiệm thu: tạo/sửa chiến dịch không tệp và có tệp; tải lại; danh sách người nhận hợp lệ; cập nhật trạng thái người nhận; tải/xóa tệp; xuất CSV và soạn/sao chép nội dung. Không coi thao tác tạo chiến dịch là tự động gửi tin Zalo.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-004 — Thêm chi phí khác không lưu được

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh form Thêm chi phí tại sn.hoianmemorieslands.com, nội dung nhập là "ship"; thông báo không lưu được dữ liệu, trang đã khóa, phản hồi HTML có tiêu đề 403 Forbidden.
- Thao tác: Chi phí khác → Thêm chi phí → nhập thông tin → Lưu.
- Kết quả mong muốn: ghi nhận chi phí trên server, xuất hiện trong danh sách và được tính đúng trong các báo cáo liên quan sau khi tải lại.
- Kết quả thực tế: lưu bị từ chối HTTP 403 và giao diện bị khóa.
- Liên quan BUG-002/003: dùng chung save() → PUT /api/state/. Cần kiểm tra CSRF/origin, session và quyền; ảnh chưa hiển thị lý do chi tiết của 403 nên chưa xác nhận nguyên nhân cuối cùng.
- Nghiệm thu: thêm/sửa/xóa chi phí, tải lại kiểm tra lưu bền vững, đối chiếu ảnh hưởng đến báo cáo và sổ quỹ theo logic HTML gốc; thông báo lỗi không hiển thị HTML thô.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-003 — Thêm đại lý và bảng giá không lưu được

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Người dùng báo lỗi cả thêm đại lý và bảng giá; ảnh xác nhận lỗi khi lưu form Hồ sơ đại lý, mã A001.
- Kết quả thực tế: hộp thoại không lưu được dữ liệu, trang bị khóa, phản hồi HTML có tiêu đề 403 Forbidden.
- Kết quả mong muốn: lưu đại lý/bảng giá thành công, hiển thị đúng và tồn tại sau tải lại trang.
- Liên quan BUG-002: các thao tác này dùng chung save() → PUT /api/state/. Khả năng lỗi CSRF/origin chung với BUG-001; chưa xác nhận lý do chi tiết của phản hồi 403 trong ảnh này.
- Hướng xử lý bản cập nhật: kiểm tra cấu hình HTTPS public, CSRF, phiên đăng nhập và quyền cho toàn bộ luồng lưu chung; sửa thông báo lỗi HTML thô.
- Nghiệm thu riêng: tạo/sửa đại lý; thêm/sửa bảng giá riêng theo ngày hiệu lực; nhập bảng giá; tải lại và đối chiếu dữ liệu; đảm bảo đại lý chỉ thấy phạm vi được cấp.
- Phạm vi bằng chứng: ảnh là form đại lý, chưa có ảnh lỗi bảng giá riêng; lỗi bảng giá được ghi nhận theo mô tả của người dùng.
- Chưa sửa code, triển khai hoặc đẩy bản vá GitHub; gom cho bản cập nhật tiếp theo theo yêu cầu người dùng.

## BUG-001 — Đăng xuất trả về 403 CSRF

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh người dùng gửi, trang Django báo `Origin checking failed - https://sn.hoianmemorieslands.com does not match any trusted origins.`
- Thao tác: nhấn Đăng xuất trên bản online.
- Kết quả mong muốn: kết thúc phiên đăng nhập và chuyển về trang đăng nhập.
- Kết quả thực tế: HTTP 403, CSRF verification failed.
- Nguyên nhân xác định từ ảnh: origin HTTPS public chưa được tin cậy trong cấu hình Django đang chạy. Ảnh cũng cho thấy DEBUG=True; chưa xác định cấu hình reverse proxy thực tế.
- Kiểm tra mã hiện tại: CSRF_TRUSTED_ORIGINS chỉ đọc biến môi trường trong production.py; development.py không có cấu hình này.
- Hướng sửa: cho phép cấu hình trusted origins qua môi trường trong cấu hình chung; bổ sung hướng dẫn domain HTTPS và reverse proxy, vẫn giữ kiểm tra CSRF. Không dùng wildcard và không tắt CSRF.
- Nghiệm thu: đăng xuất POST hợp lệ qua domain HTTPS thành công, session kết thúc; origin không được phép vẫn bị 403; kiểm tra các POST lưu dữ liệu và tải file qua cùng domain.
- Chưa sửa code, chưa triển khai hoặc đẩy bản vá GitHub; gom theo yêu cầu người dùng cho bản cập nhật tiếp theo.

## BUG-002 — Tạo loại vé không lưu được, trang bị khóa

- Trạng thái: đã ghi nhận, chờ sửa trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh người dùng gửi tại domain sn.hoianmemorieslands.com; hộp thoại báo không lưu được dữ liệu, trang đã khóa, kèm HTML có tiêu đề 403 Forbidden.
- Thao tác: Loại vé → thêm loại vé → nhập thông tin → Lưu.
- Kết quả mong muốn: lưu loại vé lên server và hiển thị trong danh sách, tải lại vẫn còn.
- Kết quả thực tế: yêu cầu lưu bị HTTP 403; giao diện khóa thao tác và hiển thị HTML lỗi thô trong alert.
- Mã liên quan: static/js/legacy.js, serverRequest gửi PUT /api/state/ với X-CSRFToken; mọi phản hồi ngoài 2xx hiện khóa giao diện và đưa responseText vào alert.
- Giả thuyết: cùng cấu hình origin/CSRF với BUG-001. Chưa xác nhận vì ảnh này không hiển thị lý do chi tiết của phản hồi 403; cũng cần kiểm tra phiên đăng nhập và role tài khoản.
- Hướng sửa: kiểm tra trusted origin và token/session khi lưu; thay HTML lỗi thô bằng thông báo dễ hiểu, phân biệt lỗi phân quyền/CSRF/phiên hết hạn/xung đột; không báo lưu thành công khi server từ chối, không tự ghi đè dữ liệu.
- Nghiệm thu: tạo/sửa loại vé qua domain HTTPS thành công và tồn tại sau tải lại; origin sai vẫn bị chặn; lỗi 403 có thông báo phù hợp; xác nhận các chức năng dùng chung API lưu không bị ảnh hưởng.
- Chưa sửa code, chưa triển khai hoặc đẩy bản vá GitHub; gom theo yêu cầu người dùng cho bản cập nhật tiếp theo.
