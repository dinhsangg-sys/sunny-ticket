# Lỗi ghi nhận khi kiểm thử online

## Các yêu cầu cập nhật gần đây

### FEATURE-009 — Lọc sản phẩm khi thanh toán tiền vé hàng loạt

- Cập nhật 1.10.12: đã thêm Sản phẩm kết hợp nhà cung cấp/ngày/loại vé; danh sách vé giới hạn theo sản phẩm và bỏ tick booking cũ khi đổi. Xác nhận ghi rõ sản phẩm; có nhóm Chưa xác định. Các dòng chờ dưới đây lưu lịch sử; chờ nghiệm thu online.

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Bằng chứng: popup Thanh toán tiền vé hàng loạt hiện có Nhà cung cấp/Nguồn, khoảng ngày và Loại vé; người dùng muốn thêm bộ lọc theo từng sản phẩm.
- Yêu cầu: dropdown Sản phẩm, mặc định Tất cả sản phẩm, kết hợp đồng thời với nhà cung cấp, khoảng ngày và các loại vé đã chọn.
- Danh sách chọn Loại vé nên giới hạn theo sản phẩm đang chọn để dễ thao tác. Danh sách booking, số booking đã tick và tổng tiền phải cùng theo tập lọc; Chọn tất cả chỉ áp dụng các dòng đang hiển thị.
- Khi đổi sản phẩm, bỏ các tick booking thanh toán cũ và xử lý lựa chọn loại vé không thuộc sản phẩm mới để tránh giữ dòng ẩn. Giữ bên nhận tiền rõ ràng trong bước xác nhận và kiểm tra supplierId trên server như hiện tại.
- Dùng cùng quy tắc xác định sản phẩm với báo cáo: snapshot nếu có, nếu không theo ticketId hoặc tên loại vé duy nhất; tách Chưa xác định khi không thể đối chiếu chắc chắn, không suy đoán sai sản phẩm.
- Chỉ tổng hợp cho bản tiếp theo theo yêu cầu gom tính năng của người dùng; chưa triển khai hoặc đẩy GitHub.

**Cập nhật 1.10.11:** đã triển khai FEATURE-007, UX-012 và FEATURE-008, kiểm tra backend/frontend cục bộ. Các dòng chờ phía dưới lưu lịch sử ghi nhận; chờ nghiệm thu online theo UPGRADE_1_10_11.md.

### FEATURE-008 — Lọc nhà cung cấp khi thanh toán tiền vé hàng loạt

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Yêu cầu: thêm lựa chọn Nhà cung cấp trong popup Thanh toán tiền vé hàng loạt để tìm đúng các booking/loại vé mua từ nhà cung cấp đó và chi trả đúng bên.
- Lọc theo supplierId/nguồn thực tế đã lưu trên từng booking, không suy từ tên loại vé, giá vốn hiện hành hoặc nhà cung cấp mặc định hiện tại. Cùng loại vé có thể thuộc nhiều nhà cung cấp.
- Kết hợp với khoảng ngày và bộ lọc nhiều loại vé; hiển thị rõ Nhà cung cấp/nguồn trên từng dòng, tổng còn phải trả và số dòng đã chọn theo tập lọc. Xem trước/xác nhận phải nêu rõ bên nhận và số tiền.
- Đổi nhà cung cấp hoặc điều kiện lọc phải bỏ các tick thanh toán trước đó để tránh giữ dòng ẩn. Chỉ thanh toán các booking còn nợ của đúng nhà cung cấp đã chọn; kiểm tra lại trước khi ghi, không chi trùng hoặc vượt dư nợ.
- Không gộp các nguồn nhập tay khác nhau chỉ vì cùng supplierId __manual__; nguồn nhập tay hoặc booking thiếu định danh nhà cung cấp cần được tách/đối soát rõ trước khi thanh toán hàng loạt. Giữ nhà cung cấp đã ngừng hoạt động nhưng còn công nợ trong danh sách để thanh toán lịch sử.
- Rà soát quyền chi nhà cung cấp, revision, lịch sử khoản chi và số liệu sổ quỹ; không thêm một khoản chi tổng gây cộng trùng với các khoản chi theo booking.
- Gom cùng FEATURE-007 và UX-012; chờ lệnh tạo bản cập nhật.

### UX-012 — Đóng bộ lọc loại vé khi bấm ra ngoài

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Bằng chứng: màn hình Thanh toán tiền vé hàng loạt, dropdown Loại vé (chọn nhiều). Hiện muốn đóng phải bấm lại ô mở dropdown.
- Yêu cầu: khi dropdown đang mở, click ra ngoài dropdown và nút mở sẽ tự đóng; click lại nút mở vẫn đóng/mở được.
- Click bên trong ô tìm, danh sách checkbox, Chọn tất cả/Bỏ chọn và thao tác cuộn danh sách không đóng dropdown. Đóng bằng click ngoài chỉ ẩn hộp lọc, giữ nguyên từ khóa và lựa chọn, không tự thanh toán hoặc đóng popup chính.
- Kiểm tra thao tác mở/đóng nhiều lần, tránh nhân đôi listener hoặc click mở bị xử lý thành click ngoài ngay lập tức; có thể hỗ trợ Escape đóng riêng dropdown.
- Gom cùng FEATURE-007 (lọc sản phẩm trong báo cáo Doanh thu & Công nợ); chờ người dùng yêu cầu tạo bản cập nhật.

### FEATURE-007 — Lọc theo sản phẩm trong báo cáo Doanh thu & Công nợ

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Bằng chứng: màn hình Báo cáo doanh thu & công nợ chi tiết; người dùng muốn lọc theo từng sản phẩm.
- Yêu cầu: thêm dropdown Sản phẩm với mặc định Tất cả sản phẩm, lấy danh mục sản phẩm từ loại vé (ví dụ Hội An Memories Show, Bà Nà); lọc theo sản phẩm, không nhầm với Loại vé hoặc Loại đối tác.
- Kết hợp đồng thời với khoảng ngày, đối tượng, từ khóa khách hàng/đại lý, trạng thái thanh toán và loại đối tác đang có.
- Danh sách booking, Tổng phải thu, Đã thanh toán, Công nợ còn lại, Booking còn nợ, số booking và file Excel phải cùng phản ánh tập dữ liệu đã lọc; phần mô tả báo cáo thể hiện sản phẩm đang chọn.
- Kiểm tra liên kết ticketId và dữ liệu cũ chỉ có tên loại vé; không tự gán sai sản phẩm khi tên trùng hoặc không tìm thấy danh mục. Cần xử lý rõ nhóm chưa xác định nếu phát sinh.
- Chỉ tổng hợp cho bản tiếp theo theo yêu cầu gom tính năng trong cuộc trò chuyện; chưa triển khai hoặc đẩy GitHub.

### FEATURE-006 — Thu tiền khách hàng cho nhiều booking cùng lúc

- Cập nhật 1.10.10: đã triển khai thu đủ số dư của các booking được tick, chọn đúng đối tác, lọc khoảng ngày, xem trước và xác nhận một lần. Đã kiểm tra backend và frontend cục bộ; các dòng chờ/đề xuất dưới đây là lịch sử. Chưa có phân bổ thanh toán một phần tổng nợ.

- Trạng thái: ghi nhận cho bản tiếp theo; chưa chỉnh code. Người dùng hỏi tick các booking của khách Nhân và ghi nhận một lần khi khách trả toàn bộ.
- Hiện có thanh toán tiền vé hàng loạt cho phía nhà cung cấp; thu tiền từ khách tại bảng Booking hiện dùng từng booking.
- Đề xuất: chọn đúng một đối tác/khách hàng, hiển thị các booking còn nợ, tick từng booking hoặc chọn tất cả trong phạm vi đang lọc; hiển thị tổng dư nợ của các dòng đã chọn và nhập ngày/ghi chú thu tiền chung, xem trước trước khi xác nhận.
- Khi khách trả đủ: ghi nhận phần còn nợ tương ứng cho từng booking, giữ các khoản đã thu trước đó; liên kết các khoản thu vào cùng một đợt để đối soát và không nhân đôi tổng thu trong sổ quỹ/báo cáo.
- Không dùng kết quả tìm kiếm chữ tự do làm bằng chứng cùng khách: có thể khớp ghi chú hoặc tên khác. Đối tác cần gắn đúng ID; khách lẻ trùng tên hoặc thiếu định danh cần phân biệt trước khi gom.
- Nếu hỗ trợ trả một phần tổng nợ, cần thể hiện rõ cách phân bổ và cho xem trước từng booking; đây là đề xuất cần chốt thêm, không tự phân bổ khi chưa rõ.
- Kiểm tra quyền thu tiền, revision, số dư mới nhất; xác nhận một lần và lưu toàn bộ hoặc không lưu gì, chặn bấm lặp, không thu vượt dư nợ, không thu lại booking đã tất toán. Giữ lịch sử và nguồn liên kết khi sửa/xóa giao dịch theo quyền.

**Cập nhật 1.10.9:** triển khai UX-009, BUG-011, UX-010, BUG-012 và UX-011. Các dòng ghi nhận/chờ bên dưới là lịch sử yêu cầu. Đã kiểm tra backend và giao diện cục bộ; chưa xác nhận nguyên nhân riêng của xung đột trên máy online, cần nghiệm thu sau triển khai.

### UX-011 — Kéo di chuyển popup để xem thông tin phía sau

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Bằng chứng: popup Loại vé đang che danh sách nền; người dùng muốn dùng chuột trái di chuyển popup để đối chiếu thông tin.
- Yêu cầu: giữ chuột trái và kéo vùng tiêu đề popup để di chuyển, thả chuột để đặt tại vị trí mới. Vùng tiêu đề có dấu hiệu kéo được.
- Không bắt thao tác kéo ở ô nhập, dropdown, nút Lưu/Đóng hoặc vùng cuộn nội dung; giữ nguyên nhập liệu, chọn văn bản và cuộn form.
- Giới hạn vị trí theo màn hình để tiêu đề/nút đóng luôn truy cập được; mở popup mới trở về vị trí mặc định, xử lý thay đổi kích thước cửa sổ và màn hình nhỏ phù hợp.
- Kéo chỉ thay vị trí hiển thị, không tự lưu hoặc thay đổi dữ liệu, không tự cho phép thao tác trên trang nền khi popup đang mở.
- Phạm vi xác nhận từ ảnh là popup Loại vé; xem xét áp dụng nhất quán cho các popup biểu mẫu tương tự khi triển khai.
- Gom cùng UX-009, BUG-011, UX-010 và BUG-012; chờ người dùng yêu cầu tạo bản cập nhật.

### BUG-012 — Thêm đối tác liên tiếp bị xung đột dữ liệu

- Mở rộng phạm vi theo yêu cầu mới: rà soát và sửa luồng thêm/lưu liên tiếp cho các chức năng tương tự trong toàn dự án, không chỉ Đối tác. Người dùng xác nhận Thêm loại vé cũng gặp cùng biểu hiện.
- Rà soát cơ chế lưu chung, revision và các wrapper/callback của từng form; kiểm tra các màn hình thêm danh mục/nghiệp vụ dùng cơ chế này như loại vé, đối tác, nhà cung cấp, giá vốn, bảng giá/giá riêng, chi phí và booking. Đây là phạm vi cần kiểm tra, chưa kết luận mọi màn hình đều có lỗi.
- Nghiệm thu mở rộng: tạo nhiều bản ghi liên tiếp trong từng chức năng liên quan, kiểm tra lưu bền vững sau tải lại, trạng thái form và revision sau mỗi lần server xác nhận; không cần tải lại giữa các lần thêm trong một phiên bình thường. Giữ chặn xung đột thật giữa các tab/người dùng, không tự ghi đè hoặc bỏ kiểm tra revision.

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Người dùng báo: thêm thành công một đối tác, tiếp tục thêm đối tác khác thì bị chặn và phải tải lại trang mới thêm được.
- Bằng chứng: form đối tác A042, thông báo Dữ liệu đã được người khác thay đổi; thay đổi vừa nhập chưa được xác nhận lưu trên server, yêu cầu tải lại dữ liệu.
- Chưa xác nhận có người/phiên khác sửa dữ liệu. Không kết luận từ thông báo rằng thực sự có người khác đang thao tác.
- Hướng điều tra: cập nhật serverRevision sau save thành công, thứ tự và số lần yêu cầu lưu, lưu bất đồng bộ/tác vụ nền, callback đóng form và khởi tạo form tiếp theo; phân biệt revision cũ trong cùng tab với xung đột thật giữa nhiều tab/người dùng.
- Yêu cầu: thêm nhiều đối tác liên tiếp trong cùng tab mà không tải lại sau mỗi lần; chỉ báo thành công sau khi server xác nhận. Nếu lưu thất bại phải giữ thông tin vừa nhập và không tạo dòng trùng hoặc coi là đã lưu.
- Giữ cơ chế chống ghi đè: không bỏ kiểm tra revision, không tự ghi đè thay đổi từ phiên khác. Xung đột thật cần thông báo và cách tải lại/đối soát phù hợp.
- Nghiệm thu: thêm ít nhất ba đối tác liên tiếp, mở lại/tải trang kiểm tra đủ dữ liệu và ID không trùng; thử bấm lưu nhanh, mạng chậm và hai phiên sửa đồng thời. Không mất đối tác trước đó hoặc thay đổi không liên quan.
- Gom cùng UX-009, BUG-011 và UX-010, chờ lệnh tạo bản cập nhật.

### UX-010 — Tìm nhanh loại vé khi khai báo giá vốn

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Bằng chứng: dropdown Loại vé được khoanh đỏ trong form Khai báo giá vốn.
- Yêu cầu: khi mở dropdown Loại vé, có ô nhập tìm nhanh bên trong danh sách; không thêm một ô tìm riêng thường trực bên ngoài.
- Tìm theo tên hoặc mã loại vé, hỗ trợ có dấu/không dấu và bộ gõ tiếng Việt bình thường; giữ đúng ID vé khi chọn. Dùng được chuột và bàn phím, có thông báo không có kết quả.
- Mở sửa dòng giá vốn phải hiển thị đúng vé đã lưu; chỉ gõ tìm hoặc đóng dropdown không tự thay đổi vé. Không thay giá vốn, nhà cung cấp, kỳ hiệu lực hoặc trạng thái mặc định khi chưa xác nhận lưu.
- Phạm vi hiện tại là Loại vé trong Khai báo giá vốn, theo vùng khoanh; chưa có yêu cầu thay dropdown Nhà cung cấp.
- Gom cùng UX-009 và BUG-011, chờ người dùng yêu cầu tạo bản cập nhật.

### BUG-011 — Ô tìm loại vé trong Booking không gõ được tiếng Việt

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Bằng chứng: ảnh form Tạo booking, ô tìm nhanh trong dropdown Loại vé được khoanh đỏ; người dùng báo không viết được tiếng Việt để tìm kiếm.
- Yêu cầu: nhập và sửa tiếng Việt có dấu bình thường bằng bộ gõ; tìm được loại vé bằng cả từ khóa có dấu và không dấu, vẫn chọn đúng vé.
- Hướng kiểm tra: các sự kiện input/compositionstart/compositionend và việc dựng lại ô tìm, gán value hoặc tự focus trong khi bộ gõ đang ghép dấu. Chưa xác nhận nguyên nhân từ ảnh; cần tránh thay thế input hoặc xử lý phím chọn kết quả khi đang composition.
- Nghiệm thu: gõ các từ Cáp, trẻ, người lớn với bộ gõ tiếng Việt; thêm/xóa ký tự, tìm không dấu, chọn bằng chuột/bàn phím và mở lại dropdown. Không mất chữ, dấu, con trỏ hoặc tự chọn vé khi đang ghép dấu.
- Gom cùng UX-009; chỉ triển khai khi người dùng yêu cầu tạo bản cập nhật.

### UX-009 — Mở chức năng menu trong tab mới

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo theo yêu cầu tổng hợp, chưa chỉnh code.
- Hiện tại: chuột phải vào mục chức năng bên trái chỉ hiện menu trang, không có Mở liên kết trong tab mới.
- Yêu cầu: menu chức năng có liên kết riêng để chuột phải chọn mở tab mới; tab mới phải vào đúng chức năng vừa chọn, thay vì quay về Dashboard. Áp dụng các mục menu có quyền truy cập, kể cả mục được thêm động.
- Giữ click trái điều hướng như hiện tại; hỗ trợ hành vi liên kết chuẩn của trình duyệt như Ctrl+click và nút chuột giữa. Tải lại hoặc dán URL phải mở đúng chức năng, vẫn kiểm tra quyền.
- Kiểm tra nhiều tab cùng sửa dữ liệu: tiếp tục giữ cơ chế revision/chặn ghi đè hiện có; không coi dữ liệu của tab cũ là mới hoặc tự ghi đè thay đổi từ tab khác.
- Chỉ tổng hợp, chưa triển khai hoặc đẩy GitHub; chờ người dùng yêu cầu tạo bản cập nhật.

**Cập nhật 1.10.8:** đã triển khai UX-004 đến UX-008 và kiểm tra bằng trình duyệt cục bộ. Các trạng thái chờ trong phần mô tả dưới đây lưu lại yêu cầu ban đầu; chờ người dùng nghiệm thu online theo UPGRADE_1_10_8.md.

### UX-008 — Lọc tiếp theo cột trong bảng Booking

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Người dùng khoanh hàng tiêu đề bảng Booking và hỏi khả năng lọc tiếp trên kết quả tìm kiếm hiện tại.
- Đề xuất: mở bộ lọc từ tiêu đề từng cột dữ liệu; mã booking/tên khách hàng hoặc đối tác theo từ khóa, loại vé và thanh toán theo lựa chọn, ngày theo khoảng, số lượng/giá vé/tổng tiền/đã thu/còn nợ theo khoảng số. Cột Thao tác không cần bộ lọc.
- Các bộ lọc kết hợp đồng thời với tìm kiếm và bộ lọc ngày/thanh toán phía trên; lọc thêm phải thu hẹp tập kết quả, không âm thầm bỏ điều kiện trước. Có dấu hiệu cột đang lọc và cách bỏ từng lọc; Xóa lọc phải xóa toàn bộ điều kiện.
- Bố trí popup lọc để giữ mỗi booking một hàng và không làm mất vùng nút Thanh toán/Sửa cố định theo UX-004. Xử lý tập rỗng rõ ràng; lọc số theo giá trị số, không theo chuỗi tiền đã định dạng.
- Gom với các yêu cầu UX-004 đến UX-007; chờ lệnh tạo bản cập nhật. Chi tiết giao diện trên là đề xuất triển khai, chưa phải code đã hoàn tất.

### UX-007 — Gộp chọn và tìm đối tác trong một dropdown

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Phản hồi 1.10.7: ô tìm nhanh và select đối tác hiển thị song song theo chiều dọc gây dư thừa.
- Yêu cầu: mỗi trường chỉ có một ô chọn; bấm mở danh sách sẽ thấy ô nhập tìm nhanh bên trong dropdown. Áp dụng cho cả Đối tác nguồn và Đối tác đích trong Sao chép giá.
- Giữ tìm theo tên/mã không dấu, hiển thị tên và mã, chọn đúng ID, báo không có kết quả và hỗ trợ bàn phím. Lựa chọn hiển thị trong ô khi đóng dropdown; không có ô tìm riêng nằm ngoài.
- Khi thay đối tác phải vô hiệu hóa bản xem trước cũ như hiện tại; đóng dropdown không tự đổi lựa chọn hoặc xóa đối tác đích.
- Gom cùng UX-004/005/006; triển khai khi người dùng yêu cầu tạo bản cập nhật.

### UX-006 — Mở Tạo booking tại đầu biểu mẫu

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Hiện tại: hộp thoại Tạo booking mở với thanh cuộn dọc ở cuối, các trường đầu biểu mẫu bị khuất.
- Yêu cầu: mỗi lần mở Tạo booking, đặt vị trí cuộn của hộp thoại về đầu để thấy tiêu đề và ô đầu tiên; không giữ vị trí cuộn của lần mở trước.
- Kiểm tra thứ tự focus và các hàm khởi tạo sau khi mở, tránh tự focus trường phía dưới khiến trình duyệt kéo xuống lại. Nếu tự focus thì dùng trường đầu và không làm lệch vị trí cuộn.
- Nghiệm thu: mở mới lần đầu, đóng sau khi cuộn xuống rồi mở lại, mở sau khi lưu booking và ở màn hình thấp/zoom lớn đều bắt đầu trên cùng.
- Gom cùng UX-004 và UX-005; triển khai khi người dùng yêu cầu tạo bản cập nhật.

### UX-005 — Xóa tìm kiếm đối tác khi quay lại màn hình

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh code.
- Hiện tại: tìm đại lý/đối tác, chuyển sang chức năng khác rồi quay lại Đối tác & bảng giá vẫn giữ từ khóa cũ, khiến danh sách tiếp tục bị lọc.
- Yêu cầu: khi điều hướng từ chức năng khác về Đối tác & bảng giá, xóa từ khóa tìm kiếm và hiển thị lại danh sách theo các bộ lọc còn lại. Chưa có yêu cầu reset bộ lọc trạng thái hoặc loại đối tác.
- Không xóa từ khóa trong lúc đang gõ hoặc khi mở/đóng Hồ sơ/Bảng giá tại cùng màn hình. Kiểm tra cả thao tác lưu hồ sơ không làm mất tìm kiếm giữa chừng.
- Gom cùng UX-004; triển khai khi người dùng yêu cầu tạo bản cập nhật.

### UX-004 — Booking gọn một hàng, cố định thao tác chính

- Trạng thái: ghi nhận cho bản cập nhật tiếp theo, chưa chỉnh giao diện.
- Phản hồi sau 1.10.7: nút Xóa xuống dòng làm mỗi booking quá cao.
- Yêu cầu: giảm cỡ chữ bảng vừa đủ đọc; giữ nội dung và các nút của mỗi booking trên một hàng, không xuống dòng.
- Thanh toán và Sửa phải luôn nhìn thấy mà không cần cuộn ngang. Tách Xóa khỏi vùng thao tác cố định; nút Xóa được phép nằm ở vùng phải cuộn ngang mới thấy.
- Kiểm tra với tên đối tác dài, số tiền lớn, zoom và độ rộng màn hình trong ảnh; cột cố định không che sai nội dung, thao tác đúng booking khi cuộn dọc/ngang. Tên quá dài có thể rút gọn bằng dấu ba chấm kèm cách xem đầy đủ.
- Gom yêu cầu, chỉ triển khai khi người dùng yêu cầu tạo bản cập nhật.

### FEATURE-005 — Nguồn giá vốn nhập tay

- Đã triển khai trong 1.10.7: giá và tên nguồn riêng từng booking, không cần danh mục nhà cung cấp. Kiểm tra quyền sửa giá vốn và khóa đổi nguồn đã có chi tiền. Không reset dữ liệu.

### UX-003 — Bảng Booking phải luôn thấy nút Thanh toán và Sửa

- Cập nhật 1.10.7: đã cố định cột thao tác, thu gọn bảng và cho tên dài xuống dòng; chờ nghiệm thu trình duyệt online. Các dòng chờ xử lý dưới đây là ghi nhận ban đầu.

- Trạng thái: đã ghi nhận, chờ gom chỉnh trong bản cập nhật tiếp theo.
- Bằng chứng: ảnh màn hình Bán vé / Booking; bảng vượt chiều rộng vùng nội dung, các nút thao tác bên phải bị khuất và phải kéo thanh cuộn ngang mới thấy.
- Yêu cầu: điều chỉnh kích thước/bố cục để thấy Thanh toán và Sửa mà không cần kéo ngang.
- Hướng xử lý dự kiến: cố định cột thao tác bên phải, thu gọn khoảng đệm/độ rộng cột, cho tên đối tác dài xuống dòng, tối ưu nút và trạng thái thanh toán. Không thu nhỏ toàn trang đến mức khó đọc, không bỏ dữ liệu cần thiết chỉ để ép vừa bảng.
- Nghiệm thu: Thanh toán và Sửa luôn hiển thị, bấm đúng booking ở độ rộng màn hình trong ảnh, khi zoom và khi cuộn dọc; header/cột cố định không chồng sai dữ liệu; kiểm tra tên đối tác dài và số tiền lớn. Trên màn hình nhỏ cần bố cục phù hợp, giữ thao tác chính dễ truy cập.
- Chưa sửa code hoặc đẩy GitHub; gom cùng UX-002 khi người dùng yêu cầu tạo bản cập nhật.

### UX-002 — Tìm kiếm nhanh đối tác trong màn hình sao chép giá

- Cập nhật 1.10.7: đã thêm tìm theo tên/mã không dấu cho nguồn và đích, giữ lựa chọn theo ID và vô hiệu hóa preview khi gõ lại. Chờ nghiệm thu online. Các dòng dưới là ghi nhận ban đầu.

- Trạng thái: đã ghi nhận, chưa chỉnh code; người dùng yêu cầu lưu cho bản sau.
- Bằng chứng: ảnh hộp thoại Sao chép giá từ đối tác khác, khoanh dropdown Đối tác nguồn.
- Yêu cầu: thêm ô nhập tìm nhanh thay cho việc cuộn danh sách đối tác dài.
- Phạm vi dự kiến: cả Đối tác nguồn và Đối tác đích; gõ tên/mã để lọc, hỗ trợ tìm không dấu, hiển thị rõ tên và mã để phân biệt.
- Nghiệm thu: lọc khi gõ, chọn đúng ID đối tác, xử lý không có kết quả; giữ lựa chọn nguồn/đích và không làm sai bước xem trước/xác nhận; dùng được bàn phím và thiết bị cảm ứng.
- Không sửa code, tạo migration hoặc đẩy GitHub trong lần ghi nhận này; gom khi người dùng yêu cầu tạo bản cập nhật tiếp theo.

### BUG-010 — Menu bên trái tràn khỏi nền tối

- Cập nhật 1.10.6: đã sửa vùng cuộn sidebar và nền; chờ kiểm tra trên trình duyệt online.

- Trạng thái: đã sửa trong 1.10.6; chờ nghiệm thu giao diện.
- Bằng chứng: ảnh màn hình Chi phí khác; các mục Nhà cung cấp, Bảng giá chung và Loại đối tác nằm dưới vùng nền tối của sidebar, chữ sáng trên nền sáng nên khó đọc. Phần đầu menu cũng đang ngoài khung nhìn trong ảnh.
- Biểu hiện: chiều cao menu vượt vùng sidebar nhưng các mục bên dưới không có vùng cuộn/nền phù hợp. Chưa xác minh trên trình duyệt kích thước thực tế hoặc mức zoom của người dùng.
- Hướng kiểm tra/sửa dự kiến: bố cục sidebar và vùng cuộn menu riêng theo chiều cao viewport; giữ nền tối bao phủ tất cả mục; kiểm tra sticky/height/overflow và các mục được thêm động.
- Nghiệm thu: toàn bộ menu đọc và bấm được ở màn hình thấp, khi cuộn trang và khi zoom; không chồng nội dung chính; kiểm tra cả giao diện di động và mục đang chọn. Không coi là lỗi mất quyền hoặc mất dữ liệu khi chưa có bằng chứng.

Theo yêu cầu mới nhất của người dùng: chỉ ghi nhận/tổng hợp yêu cầu, chưa sửa code hoặc đẩy GitHub cho đến khi người dùng yêu cầu tạo bản cập nhật.

### FEATURE-004 — Sao chép giá từ đại lý/CTV đã có

- Cập nhật 1.10.6: đã triển khai xem trước, chọn vé/ngày, giá riêng hoặc giá đang áp dụng, bỏ qua trùng/chồng kỳ, sao chép độc lập và lựa chọn gán cùng bảng chung. Có kiểm tra quyền và revision backend. Xem UPGRADE_1_10_6.md; các ghi nhận bên dưới là lịch sử trước triển khai.

- Trạng thái: đã triển khai trong 1.10.6; chờ nghiệm thu online.
- Vị trí: màn hình Bảng giá của một đối tác, ví dụ Hoàng Linh trong ảnh, hiện các loại vé chưa khai báo giá.
- Yêu cầu: chọn đại lý/CTV nguồn đã có giá để sao chép sang đối tác đang mở, tránh khai báo từng loại vé.
- Luồng đề xuất để triển khai: nút Sao chép giá → tìm/chọn đối tác nguồn → chọn các loại vé/dòng giá và ngày hiệu lực → xem trước → xác nhận.
- Cần hiển thị rõ giá riêng của nguồn hay giá kế thừa từ bảng chung. Không tự chuyển bảng giá được gán cho đối tác đích; phương án mặc định đề xuất là sao chép các dòng giá riêng. Nếu nguồn chỉ có bảng chung, hiển thị rõ và cho chọn gán cùng bảng thay vì âm thầm tạo giá riêng.
- Bảo vệ dữ liệu: không tự ghi đè giá đích. Mặc định bổ sung dòng còn thiếu; nếu gặp kỳ giá trùng/xung đột, liệt kê và yêu cầu chọn cách xử lý trong bước xem trước. Giữ nguyên giá nguồn, booking, công nợ và lịch sử đã lưu.
- Kiểm tra quyền đọc giá nguồn và thêm/sửa giá đích tại backend; dùng revision chống ghi đè. Bản sao là dữ liệu độc lập, đổi giá nguồn sau đó không tự đổi giá đích.
- Các lựa chọn về nguồn giá kế thừa, sao chép kỳ lịch sử hay giá đang hiệu lực và xử lý trùng là thiết kế đề xuất, chưa được người dùng xác nhận chi tiết.
- Chưa sửa code, chưa tạo migration hoặc đẩy GitHub.

## 1.10.5 — Phân loại đối tác

- Thêm Loại đối tác và danh mục quản lý, bộ lọc danh sách; giữ hồ sơ cũ chưa phân loại và không đổi giá/lịch sử.
- Nối bộ lọc vào báo cáo doanh thu/công nợ, Excel, chọn đối tác gán bảng giá và chiến dịch Zalo. Thêm quyền phân loại/quản lý nhóm, hướng dẫn UPGRADE_1_10_5.md.

## 1.10.4 — Sắp xếp danh sách giá vốn và nhãn mặc định

- Thêm nút lên/xuống từng dòng và lưu sortOrder; không đổi mảng gốc, ID giá, mặc định hay snapshot booking.
- Thêm nhãn xanh ⭐ Mặc định cạnh giá đang được cấu hình mặc định.
- Có quyền backend cost_price.reorder và migration 0006; không yêu cầu reset dữ liệu.

## 1.10.2 — Sửa nhiều mức giá vốn đồng thời

- Người dùng xác nhận cùng nhà cung cấp/loại vé/cùng thời gian có thể có nhiều giá vốn. Booking tự chọn dòng hoặc dùng mặc định. Thay thế giả định cũ rằng mọi kỳ giá vốn phải không trùng.
- Đã bỏ chặn ở frontend/backend; API chọn costPriceId và fallback mặc định, giữ snapshot booking. Hướng dẫn UPGRADE_1_10_2.md, không reset dữ liệu trong bản vá này.

## 1.10.1 — Yêu cầu khởi tạo mới

- Người dùng yêu cầu xóa hết dữ liệu cũ và bỏ module ánh xạ. Đã bỏ menu/API/logic ánh xạ; bổ sung management command reset_business_data để xóa nghiệp vụ, media, nhật ký và phiên, giữ tài khoản/nhóm/quyền.
- Không tự xóa dữ liệu online khi migrate. Cần chạy lệnh --execute trên Ubuntu theo UPGRADE_1_10_1.md; agent không có kết nối máy đó để thực hiện hoặc xác nhận kết quả.
- Các yêu cầu ánh xạ/gộp vé của 1.10.0 bên dưới là lịch sử, đã được yêu cầu mới thay thế. Giới hạn phân quyền còn lại vẫn được theo dõi, không coi là đã hoàn tất.

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
