# Tài liệu đọc 1 — Chia nhỏ tài liệu (Chunking) cho Knowledge Base

> Đọc trước khi làm Phần B của đề. ~10 phút. Bạn không cần biết gì trước về chủ đề này.

## 1. Vì sao phải chia nhỏ tài liệu

Trợ lý AI kiểu RAG (Retrieval-Augmented Generation) trả lời câu hỏi theo 2 bước: **tìm** các đoạn tài liệu liên quan đến câu hỏi, rồi **sinh** câu trả lời dựa trên các đoạn đó. Muốn "tìm" được, tài liệu phải được cắt thành các đoạn nhỏ gọi là **chunk** và đánh index.

Chunk quá to → tìm ra đoạn chứa nhiều nội dung không liên quan, câu trả lời loãng hoặc lạc đề. Chunk quá nhỏ → mất ngữ cảnh (ví dụ một bước trong quy trình bị tách khỏi các bước còn lại, AI đọc bước 3 mà không biết bước 1–2). Chọn cách chia là một quyết định thiết kế — **không có con số đúng cho mọi trường hợp**.

## 2. Ba chiến lược chia phổ biến

| Chiến lược | Cách làm | Ưu | Nhược |
|---|---|---|---|
| **Cố định (fixed-size)** | Cắt mỗi N ký tự/token, thường chồng lấn (overlap) 10–20% | Đơn giản, đều | Cắt ngang câu, ngang bảng, ngang quy trình |
| **Theo cấu trúc (structure-based)** | Cắt theo heading, mục, bảng của tài liệu | Giữ trọn ngữ nghĩa từng mục — hợp với tài liệu có cấu trúc rõ (SOP, chính sách) | Chunk to nhỏ không đều; phụ thuộc tài liệu được viết có cấu trúc |
| **Theo ngữ nghĩa (semantic)** | Dùng mô hình đo độ liên quan giữa các câu để tìm điểm cắt | Chunk "tự nhiên" nhất | Phức tạp, khó giải thích, tốn công — thường chưa cần cho KB nhỏ |

Với tài liệu vận hành/chính sách (như trong data pack), điểm khởi đầu hợp lý thường là **theo cấu trúc**: mỗi mục/quy trình là một chunk, vì người hỏi thường hỏi đúng một mục ("backup giữ bao lâu?", "lỗi X xử lý thế nào?").

## 3. Metadata — phần quan trọng không kém nội dung

Mỗi chunk nên lưu kèm thông tin về nguồn gốc của nó, tối thiểu:

- **Nguồn:** từ tài liệu nào, mục nào (để câu trả lời trích dẫn được).
- **Phiên bản + ngày ban hành:** tài liệu chính sách có thể có nhiều bản — khi hai bản mâu thuẫn, hệ thống phải biết bản nào hiệu lực.
- **Chủ sở hữu (owner):** ai chịu trách nhiệm cập nhật tài liệu đó.

Một knowledge base tốt không chỉ "tìm được đoạn đúng" mà còn **biết đoạn đó còn hiệu lực không và ai bảo chứng cho nó**. Khi tài liệu nguồn thay đổi mà KB không được cập nhật, AI sẽ trả lời theo thông tin cũ một cách rất tự tin — đây là rủi ro vận hành số một của hệ thống RAG.

## 4. Câu hỏi nên tự trả lời khi thiết kế

1. Người dùng sẽ hỏi kiểu câu hỏi gì? (câu hỏi quyết định cách chia hợp lý)
2. Nếu 2 tài liệu nói khác nhau về cùng một điều, hệ thống chọn bản nào — dựa vào metadata gì?
3. Khi một tài liệu được sửa, quy trình cập nhật index gồm những bước nào, ai làm?
