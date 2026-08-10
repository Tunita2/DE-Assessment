# Quy trình Chuẩn (SOP) Cập nhật & Quản trị Knowledge Base (Phần B — Mục 4)

**Mã tài liệu**: SOP-KB-001  
**Phiên bản**: v1.0  
**Áp dụng cho**: Đội ngũ Quản trị Tri thức (Knowledge Engineering) & Vận hành Hệ thống (Ops Team) — Sao Đỏ / Xbrain  

---

## 🎯 1. Mục đích & Phạm vi
Quy trình này quy định các bước tiếp nhận, rà soát, đánh chỉ mục và phát hành cập nhật tài liệu vận hành (SOP, chính sách, hướng dẫn kỹ thuật) vào hệ thống Knowledge Base của Trợ lý AI, đảm bảo trợ lý luôn trả lời theo thông tin chính xác và mới nhất.

---

## 👥 2. Phân công Trách nhiệm (RACI Matrix)
- **Tác giả tài liệu / Khách hàng (Author)**: Soạn thảo, sửa đổi tài liệu nghiệp vụ/kỹ thuật và gửi yêu cầu cập nhật.
- **Knowledge Engineer (DE / KE)**: Thực hiện parse, chunking, re-index, kiểm tra xung đột phiên bản và chạy regression test.
- **Ops Lead / Chuyên viên Vận hành**: Duyệt kết quả chạy thử nghiệm trước khi phát hành lên môi trường chính thức (Production).

---

## 🔄 3. Tần suất Cập nhật
- **Định kỳ**: Hằng tuần vào thứ Sáu (đối với các tài liệu cập nhật thông thường).
- **Khẩn cấp (Hotfix)**: Trong vòng 2 giờ kể từ khi nhận được tài liệu hướng dẫn xử lý sự cố mới hoặc cảnh báo bảo mật khẩn.

---

## 🛠️ 4. Quy trình Thực hiện (5 Bước)

### Bước 1: Tiếp nhận & Kiểm tra Tính hợp lệ
- Kiểm tra số hiệu phiên bản (`version`), ngày ban hành (`effective_date`) và phạm vi thay thế (tài liệu này thay thế tài liệu nào cũ).
- Đảm bảo định dạng đúng chuẩn Markdown / Text có tiêu đề phân cấp rõ ràng.

### Bước 2: Phân tích Xung đột & Đánh dấu Deprecation
- Quét đối chiếu với các tài liệu hiện có trong KB để phát hiện các quy định trái ngược.
- Đánh dấu trạng thái `status: deprecated` cho các chunk thuộc phiên bản cũ đã bị bãi bỏ.

### Bước 3: Chunking & Đánh chỉ mục mới (Re-indexing)
- Thực hiện parse và chunking theo chuẩn quy định tại `kb/README.md`.
- Ghi đè chỉ mục hoặc cập nhật metadata tương ứng trong KB Store.

### Bước 4: Chạy Bộ kiểm thử Hồi quy (Regression Eval)
- Chạy tự động bộ 10 câu hỏi kiểm chứng chuẩn (`kb/eval/eval_questions.json`) kèm tối thiểu 2 câu hỏi mới liên quan đến nội dung tài liệu vừa cập nhật.
- Tỷ lệ đạt tối thiểu: **100%** đối với câu hỏi về chính sách mới và **≥ 90%** đối với toàn bộ benchmark.

### Bước 5: Phê duyệt & Phát hành
- Ops Lead ký duyệt biên bản kiểm thử.
- Triển khai index mới lên môi trường phục vụ Trợ lý AI.
