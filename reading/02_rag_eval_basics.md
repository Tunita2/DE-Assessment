# Tài liệu đọc 2 — Đánh giá chất lượng Knowledge Base

> Đọc trước khi làm Phần B mục 3 (bộ eval). ~10 phút.

## 1. Vì sao phải có bộ đánh giá (eval)

"Knowledge base dựng xong" chưa có nghĩa gì nếu không đo được nó trả lời **đúng hay sai**. Một hệ thống RAG có thể hỏng ở 2 chỗ khác nhau, và phải đo tách bạch:

1. **Tìm sai (retrieval):** câu hỏi không tìm ra đúng đoạn tài liệu chứa câu trả lời.
2. **Trả lời sai (generation):** tìm đúng đoạn rồi nhưng câu trả lời bịa thêm, bỏ sót, hoặc trích sai.

## 2. Hai phép đo cơ bản

| Phép đo | Câu hỏi nó trả lời | Cách đo thủ công (đủ dùng cho KB nhỏ) |
|---|---|---|
| **Retrieval hit** | Đoạn tài liệu đúng có nằm trong kết quả tìm không? | Với mỗi câu hỏi eval, ghi trước "đáp án nằm ở tài liệu X mục Y" → chạy tìm kiếm → kiểm tra X/Y có trong top kết quả |
| **Groundedness** (độ bám nguồn) | Câu trả lời có dựa ĐÚNG trên tài liệu không, hay bịa? | Đối chiếu từng ý trong câu trả lời với đoạn nguồn: ý nào không có trong nguồn = bịa (hallucination) |

## 3. Cách dựng bộ câu hỏi eval tốt

Bộ eval nên phủ nhiều **kiểu** câu hỏi, không chỉ câu dễ:

1. **Tra cứu trực tiếp:** đáp án nằm gọn trong 1 mục ("backup lưu giữ bao lâu?").
2. **Tổng hợp nhiều nguồn:** đáp án phải ghép từ 2 tài liệu ("lỗi X thì xử lý thế nào và khi nào phải escalate?").
3. **Bẫy phiên bản:** câu hỏi mà 2 tài liệu trả lời khác nhau — hệ thống phải theo bản hiệu lực.
4. **Ngoài phạm vi:** câu hỏi KHÔNG có trong tài liệu ("lương thưởng thế nào?") — câu trả lời đúng là **"không có thông tin"**, trả lời bừa = fail. Kiểu này bắt buộc phải có trong bộ eval.

Với mỗi câu hỏi, ghi trước: đáp án mong đợi + tài liệu/mục chứa đáp án + tiêu chí đạt (ví dụ: "nêu đúng 23:30 và 30 ngày, có dẫn nguồn POL-01 v2").

## 4. Tiêu chí chấm một câu trả lời

Một khung đơn giản, chấm tay được:

- **Đạt:** đúng nội dung + có dẫn nguồn + không thêm thông tin ngoài nguồn.
- **Đạt một phần:** đúng nhưng thiếu ý quan trọng, hoặc không dẫn nguồn.
- **Fail:** sai, theo tài liệu hết hiệu lực, hoặc bịa thông tin không có trong nguồn.

Ghi lại tỉ lệ đạt của cả bộ câu hỏi — đó là "điểm sức khoẻ" của KB, chạy lại mỗi lần tài liệu nguồn thay đổi để phát hiện KB xuống cấp.
