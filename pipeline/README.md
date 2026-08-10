# Pipeline xử lý Log (Phần A — Data Pipeline)

Thư mục chứa mã nguồn pipeline xử lý dữ liệu log 7 ngày của 5 hệ thống nội bộ thuộc Công ty Tài chính Sao Đỏ (`data/app_logs_7days.jsonl`).

## Cấu trúc thư mục

```
pipeline/
├── README.md            # Tài liệu giải trình pipeline & phương pháp làm sạch
├── run_pipeline.py      # Entrypoint thực thi toàn bộ quy trình pipeline
├── report_answers.md    # Báo cáo trả lời 4 câu hỏi nghiệp vụ của khách hàng
├── src/                 # Source code module hóa
│   ├── __init__.py
│   ├── ingest.py        # Đọc dữ liệu thô & kiểm tra tính hợp lệ
│   ├── validator.py     # Nhận diện lỗi dữ liệu & phân loại bản ghi không hợp lệ
│   ├── transform.py     # Làm sạch, chuẩn hoá và chuyển đổi định dạng
│   └── analytics.py     # Tổng hợp số liệu và tính toán báo cáo 4 câu hỏi
└── output/              # Thư mục chứa dữ liệu sạch (Parquet / SQLite) và bảng biểu
```

## Các bước xử lý của Pipeline
1. **Ingest & Validate**: Đọc từng dòng jsonl, kiểm tra cấu trúc JSON, validate schema và các trường bắt buộc (timestamp, service, level, message, ...).
2. **Transform & Clean**:
   - Chuẩn hóa timestamp về chuẩn ISO 8601 UTC.
   - Chuẩn hóa service name và log level.
   - Tách và lưu trữ riêng các bản ghi lỗi dữ liệu (quarantine/discard log) kèm lý do.
3. **Storage (Lưu trữ)**: Lưu trữ dữ liệu sạch dưới định dạng Apache Parquet phân vùng theo ngày/service.
4. **Analytics & Reporting**: Truy vấn và tổng hợp kết quả trả lời 4 câu hỏi nghiệp vụ.
