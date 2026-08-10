# Data Pipeline (Phần A — Log Processing & Reporting)

Module xử lý và chuẩn hóa dữ liệu log 7 ngày của 5 hệ thống nội bộ thuộc Công ty Tài chính Sao Đỏ (`data/app_logs_7days.jsonl`).

---

## 🏛️ Kiến trúc Module

```
pipeline/
├── README.md               # Tài liệu giải trình kỹ thuật, quyết định Parquet & quy tắc làm sạch
├── run_pipeline.py         # Entrypoint thực thi toàn bộ quy trình pipeline
├── report_answers.md       # Báo cáo chi tiết trả lời 4 câu hỏi nghiệp vụ & đối chiếu docs
├── src/
│   ├── __init__.py         # Package exports
│   ├── models.py           # Pydantic schemas (RawLogRecord, CleanedLogRecord, QuarantineRecord)
│   ├── ingest.py           # Stream reader an toàn, bắt lỗi giải mã & cú pháp
│   ├── validator.py        # Rules engine: chuẩn hóa UTC, validate services/levels, deduplication
│   ├── storage.py          # Storage manager: xuất Apache Parquet, SQLite DB, Quarantine JSONL
│   └── analytics.py        # Động cơ phân tích DuckDB SQL & Pandas giải đáp 4 câu hỏi
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py    # Bộ Unit test kiểm thử pipeline
└── output/
    ├── clean_logs.parquet  # Dữ liệu sạch dạng Apache Parquet (nén Snappy)
    ├── clean_logs.db       # Database SQLite cho ad-hoc SQL queries
    ├── quarantine_logs.jsonl # 84 bản ghi bị loại/cách ly kèm nguyên nhân
    └── pipeline_summary.json # Thống kê metadata tổng hợp
```

---

## 🔄 Các Bước Xử Lý của Pipeline

1. **Ingest (Thu nhận stream)**: Đọc từng dòng từ file JSONL, xử lý lỗi cú pháp JSON mà không gây gián đoạn luồng dữ liệu.
2. **Validate & Clean (Kiểm định & Làm sạch)**:
   - **Timestamp**: Chuẩn hóa các định dạng thời gian có múi giờ địa phương (`+07:00`) và UTC (`Z`) về chuẩn **ISO 8601 UTC** (`YYYY-MM-DDTHH:MM:SSZ`).
   - **Service & Level**: Kiểm tra ràng buộc thuộc 5 dịch vụ (`auth-service`, `payment-api`, `web-portal`, `batch-report`, `notification-worker`) và 4 mức log (`INFO`, `WARN`, `ERROR`, `DEBUG`).
   - **Deduplication**: Nhận diện và loại bỏ các bản ghi trùng lặp 100% dựa trên chữ ký `(timestamp_utc, service, level, message, request_id)`.
   - **Quarantine**: Tách riêng các bản ghi lỗi vào file `quarantine_logs.jsonl` có phân loại lý do chi tiết.
3. **Storage (Lưu trữ)**:
   - Lưu trữ dữ liệu sạch dạng **Apache Parquet** tối ưu hóa cho phân tích OLAP.
   - Lưu trữ dạng **SQLite Database** phục vụ truy vấn SQL ad-hoc.
4. **Analytics & Reporting (Phân tích & Lập báo cáo)**:
   - Sử dụng DuckDB SQL và Pandas để tính toán chính xác 4 câu hỏi nghiệp vụ.
   - Tự động xuất báo cáo hoàn chỉnh tại [report_answers.md](file:///d:/DE-assessment/pipeline/report_answers.md).

---

## 💾 Giải trình Quyết định Định dạng Lưu trữ (Storage Format Rationale)

Tại sao chọn **Apache Parquet** cho dữ liệu sạch?
1. **Columnar Storage**: Log dữ liệu thường có nhiều trường, nhưng các câu truy vấn phân tích chỉ cần đọc 2-3 cột (`timestamp`, `service`, `level`). Parquet chỉ nạp các cột cần thiết, giúp giảm I/O từ 60–80%.
2. **Hiệu năng Nén cao (Snappy Compression)**: Dữ liệu log dạng text lặp lại nhiều giúp Parquet đạt tỷ lệ nén cao, tiết kiệm chi phí lưu trữ trên S3 Data Lake.
3. **Tương thích Cloud Data Lake & Query Engines**: Parquet là định dạng chuẩn công nghiệp được hỗ trợ tối ưu trên Amazon Athena, AWS Glue, Spark, DuckDB và Snowflake.

---

## 🚀 Hướng Dẫn Thực Thi

### 1. Chạy Pipeline
```bash
# Từ thư mục gốc repo:
python pipeline/run_pipeline.py
```

### 2. Chạy Unit Tests
```bash
pytest pipeline/tests/ -v
```
