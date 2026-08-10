# Task A — Review Câu trả lời AI (Bài 2 — AI Proficiency)

Bản đánh giá và phản biện kỹ thuật đối với câu trả lời tư vấn kiến trúc của một trợ lý AI (đóng vai trò Senior Data Engineer review cho Junior).

---

## 📜 Đoạn văn bản AI cần Review
> *"Bạn nên lưu toàn bộ log vào S3 Standard-IA vì đây là lựa chọn mặc định rẻ nhất cho data lake. Để thu dữ liệu, cấu hình một Glue job đọc trực tiếp từ database RDS production của khách mỗi 5 phút — đây là pattern chuẩn cho near-real-time. Dữ liệu nên chuyển sang Parquet, một format lưu theo hàng (row-based) nên ghi rất nhanh, phù hợp cho analytics. Với các bước transform nặng chạy khoảng 30–45 phút, dùng AWS Lambda là phù hợp nhất vì không phải quản lý server. Về knowledge base cho RAG, hãy chia tài liệu thành các chunk cố định 4.000 token — kích thước này luôn tốt nhất cho mọi loại tài liệu. Cuối cùng, không cần đánh version cho knowledge base, vì bản mới nhất luôn là bản đúng — cứ ghi đè là được."*

---

## 🔍 Phân tích Chi tiết Các Điểm Sai & Sửa Lại

### 1. Sai lầm về Storage Class S3 (`S3 Standard-IA là mặc định rẻ nhất cho data lake`)
- **Điểm sai**: Khuyên lưu toàn bộ log mới thu thập vào `S3 Standard-IA`.
- **Vì sao sai**: S3 Standard-IA có phí truy xuất dữ liệu (*retrieval fee*) và yêu cầu thời gian lưu trữ tối thiểu 30 ngày. Dữ liệu log mới ingest liên tục được đọc nhiều lần trong quá trình pipeline ETL sẽ làm tăng chi phí đột biến thay vì tiết kiệm.
- **Sửa lại đúng**: Dùng **S3 Standard** cho dữ liệu mới thu thập (hot data), sau 30–90 ngày áp dụng S3 Lifecycle Transition chuyển sang **S3 Infrequent Access (IA)** hoặc **Glacier**.
- **Nguồn kiểm chứng**: *AWS S3 Storage Classes Documentation & Pricing Guide*.

### 2. Sai lầm về Ingestion Pattern (`Glue job đọc trực tiếp RDS Production mỗi 5 phút`)
- **Điểm sai**: Chạy Glue job mỗi 5 phút quét trực tiếp vào database production.
- **Vì sao sai**: AWS Glue ETL job có thời gian khởi động (startup/warmup time 1-2 phút) và tính phí tối thiểu 1 phút DPU. Quét mỗi 5 phút sẽ gây tải nghiêm trọng lên DB Production và chi phí Glue cực kỳ tốn kém, không phải pattern chuẩn cho near-real-time.
- **Sửa lại đúng**: Với CDC/near-real-time, sử dụng **AWS DMS (Database Migration Service)** hoặc **Debezium/Kinesis** đẩy vào S3, hoặc đọc từ **Read Replica**.
- **Nguồn kiểm chứng**: *AWS Well-Architected Framework (Data Analytics Lens)*.

### 3. Sai lầm về định dạng Parquet (`Parquet là format lưu theo hàng (row-based) nên ghi rất nhanh`)
- **Điểm sai**: Nhận định Parquet là "lưu theo hàng" (*row-based*) và ghi nhanh.
- **Vì sao sai**: Parquet là định dạng **lưu trữ theo cột (columnar storage format)**, tối ưu cho việc đọc phân tích (column projection & predicate pushdown), tốc độ ghi thường chậm hơn do nén và mã hóa cột.
- **Sửa lại đúng**: Khẳng định Parquet là columnar format tối ưu cho query analytics (OLAP), còn format row-based là CSV/JSON/Avro.
- **Nguồn kiểm chứng**: *Apache Parquet Documentation & reading/ materials*.

### 4. Sai lầm về thời gian chạy của AWS Lambda (`Transform 30-45 phút dùng AWS Lambda`)
- **Điểm sai**: Dùng AWS Lambda cho job chạy kéo dài 30–45 phút.
- **Vì sao sai**: AWS Lambda có giới hạn thời gian thực thi cứng (*hard execution timeout*) tối đa là **15 phút (900 giây)**. Job 30–45 phút chắc chắn sẽ bị timeout và thất bại.
- **Sửa lại đúng**: Sử dụng **AWS Glue ETL Job**, **AWS EMR (Spark)**, hoặc **AWS ECS/Fargate (Batch Task)** cho các tác vụ transform nặng kéo dài trên 15 phút.
- **Nguồn kiểm chứng**: *AWS Lambda Service Quotas Documentation*.

### 5. Sai lầm về Chunking trong RAG (`Cố định 4.000 token luôn tốt nhất cho mọi tài liệu`)
- **Điểm sai**: Khẳng định chunk size 4.000 token luôn tốt nhất.
- **Vì sao sai**: 4.000 token là kích thước quá lớn cho retrieval chính xác (gây loãng thông tin, mất tín hiệu ngữ nghĩa cục bộ), và vượt quá embedding window tối ưu của nhiều model. Không có một kích thước cố định nào "luôn tốt nhất".
- **Sửa lại đúng**: Chọn chunk size dựa trên cấu trúc tài liệu (thường 256–1.000 token) kèm overlap và phân đoạn theo tiêu đề mục (semantic/section boundaries).
- **Nguồn kiểm chứng**: *Tài liệu reading/01_chunking_basics.md*.

### 6. Sai lầm về Quản trị Phiên bản KB (`Không cần đánh version, cứ ghi đè`)
- **Điểm sai**: Bỏ qua versioning vì cho rằng bản mới nhất luôn đúng.
- **Vì sao sai**: Ghi đè mà không quản lý version sẽ làm mất lịch sử, không thể rollback khi tài liệu mới có sai sót, và không thể giải thích nguồn gốc câu trả lời khi audit.
- **Sửa lại đúng**: Bắt buộc lưu metadata `version`, `effective_date`, `status` để thực hiện version priority và lưu vết audit trail.
- **Nguồn kiểm chứng**: *Tài liệu reading/02_rag_eval_basics.md*.
