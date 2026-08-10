# Thiết kế Kiến trúc Pipeline trên AWS (Phần A — Mục 4)

Tài liệu thiết kế kiến trúc triển khai pipeline xử lý log hằng ngày cho Công ty Tài chính Sao Đỏ trên hạ tầng đám mây AWS.

---

## 🏗️ 1. Sơ đồ Kiến trúc Tổng thể (Architecture Diagram)

```
[5 Internal Systems] ──(Kinesis Agent / Log Shipper)──> [Amazon S3 (Raw Zone)]
                                                              │
                                                      (S3 Event / EventBridge)
                                                              │
                                                              ▼
                                                      [AWS Step Functions]
                                                              │
                                           ┌──────────────────┴──────────────────┐
                                           ▼                                     ▼
                                  [AWS Glue ETL Job]                    [Amazon Athena]
                             (Clean, Validate, Parquet)             (Ad-hoc SQL Analytics)
                                           │                                     ▲
                                           ▼                                     │
                                [Amazon S3 (Clean Zone)] ────────────────────────┘
                                           │
                                           ▼
                                [Amazon QuickSight / BI]
```

---

## ⚙️ 2. Thuyết minh Luồng Dữ liệu & Danh sách Dịch vụ AWS

### 2.1. Ingestion (Thu thập log)
- **Log Shipper / Kinesis Firehose / S3**: Hệ thống nội bộ đẩy log nén định kỳ về S3 Raw Zone (`s3://saodo-datalake/raw/year=YYYY/month=MM/day=DD/`).

### 2.2. Processing & Transformation (Xử lý & Làm sạch)
- **AWS Glue (Apache Spark)**: Chạy batch job hằng ngày để validate schema, lọc lỗi, chuẩn hóa timestamp và ghi ra Parquet format (`s3://saodo-datalake/clean/`).
- **AWS Lambda / EventBridge**: Kích hoạt pipeline tự động khi có dữ liệu mới hoặc theo lịch cron hàng ngày (01:00 AM).

### 2.3. Analytics & Serving (Phân tích & Báo cáo)
- **AWS Glue Data Catalog**: Quản lý metadata và schema của các partition.
- **Amazon Athena**: Cung cấp giao diện Serverless SQL để truy vấn trực tiếp trên S3 Parquet, phục vụ tạo báo cáo 4 câu hỏi nghiệp vụ và dashboard vận hành.
- **Amazon CloudWatch & SNS**: Giám sát job failure, cảnh báo số lượng ERROR bất thường.

### 2.4. Security & Governance
- **AWS IAM**: Phân quyền tối thiểu (Least Privilege) cho từng service role.
- **AWS KMS**: Mã hóa dữ liệu at-rest (SSE-KMS) và in-transit (TLS).

---

## ⚠️ 3. Các điểm Cần Lưu ý & Chưa chắc chắn (Honesty & Trade-offs)
- **Độ trễ vs Chi phí**: Lựa chọn Daily Batch Glue Job thay vì Streaming Kinesis/Flink để tối ưu chi phí và độ phức tạp vận hành cho POC ban đầu.
- **Kích thước file**: Cần cơ chế Compact small files trong Glue/Spark để tránh lỗi nhiều file nhỏ trên S3 ảnh hưởng hiệu năng Athena.
