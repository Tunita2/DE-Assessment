# Mini Knowledge Base cho Trợ lý AI (Phần B)

Thư mục chứa mã nguồn, tài liệu thiết kế và bộ đánh giá mini Knowledge Base (KB) xây dựng từ 8 tài liệu vận hành của Sao Đỏ (`data/docs/`).

## Cấu trúc thư mục

```
kb/
├── README.md            # Thiết kế KB, chiến lược chunking & cơ chế xử lý mâu thuẫn
├── run_kb.py            # Script demo truy vấn KB và đánh giá
├── eval_results.md      # Kết quả chạy thử nghiệm tối thiểu 3 câu hỏi kiểm chứng
├── src/                 # Source code module hóa
│   ├── __init__.py
│   ├── parser.py        # Đọc và trích xuất nội dung từ data/docs/
│   ├── chunker.py       # Phân đoạn tài liệu (semantic/heading-based chunking)
│   ├── indexer.py       # Tạo chỉ mục và metadata (SQLite FTS / BM25 / Vector)
│   └── retriever.py     # Truy vấn, xếp hạng và áp dụng luật ưu tiên phiên bản
├── index/               # Thư mục chứa index KB đã được xây dựng
└── eval/                # Bộ câu hỏi đánh giá benchmark
    └── eval_questions.json # 10 câu hỏi kiểm chứng + ground truth + tiêu chí chấm
```

## 1. Thiết kế Chunking & Metadata
- **Chiến lược Chunking**: Phân đoạn theo tiêu đề mục (Markdown Headings / Semantic Boundary) kết hợp sliding window overlap để bảo toàn ngữ cảnh quy trình SOP.
- **Metadata**: Mỗi chunk lưu kèm: `doc_id`, `doc_title`, `version`, `effective_date`, `department`, `source_file`, `section_title`.

## 2. Cơ chế Xử lý Mâu thuẫn (Conflict Resolution)
- Nhận diện các tài liệu có quy định xung đột nhau (dựa trên phân tích ngày hiệu lực `effective_date` và số hiệu `version`).
- Áp dụng cơ chế **Deterministic Freshness Priority**: Khi có xung đột giữa hai văn bản cùng chủ đề, tài liệu có phiên bản mới nhất và ngày hiệu lực gần nhất sẽ được ưu tiên, đồng thời thêm cảnh báo phiên bản cũ bị deprecated.
