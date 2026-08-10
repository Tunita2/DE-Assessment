# Báo cáo Phân tích Dữ liệu Log 7 Ngày (Phần A — Data Pipeline)

**Đơn vị thực hiện**: Đội Data Engineering — Xbrain (TechX Corp)  
**Khách hàng**: Phòng CNTT — Công ty Tài chính Sao Đỏ  
**Phạm vi dữ liệu**: 7 ngày log liên tục (2026-07-27 đến 2026-08-02) của 5 hệ thống nội bộ  
**Nguồn dữ liệu**: `data/app_logs_7days.jsonl`  

---

## Executive Summary (Tóm tắt điều hành)

1. **Tổng lượng log xử lý**: **2,923** dòng log thô. Sau khi làm sạch, chuẩn hóa múi giờ UTC và khử trùng lặp, thu được **2,839** bản ghi sạch (97.1%) và cách ly **84** bản ghi lỗi (2.87%) vào `quarantine_logs.jsonl`.
2. **Hệ thống bất ổn nhất**: **`payment-api`** chiếm tới **139 lỗi ERROR** (tương đương **48.4%** tổng số lỗi toàn hệ thống).
3. **Ngày xảy ra sự cố nghiêm trọng (Spike Anomaly)**: Ngày **2026-07-30** ghi nhận **140 lỗi ERROR**, tỷ lệ lỗi vọt lên **27.4%** (vượt xa ngưỡng CRITICAL 5.0% theo quy định tại `GUIDE-01`).
4. **Nguyên nhân gốc rễ (Root Cause)**: Do hiện tượng nghẽn kết nối database chính (`ERR ConnTimeout db-primary after 30s retry=3`) tại `payment-api`, dẫn đến phản ứng dây chuyền làm sập cổng giao tiếp trên `web-portal` (`ERR HTTP 502 upstream=payment-api`).

---

## 📊 Câu hỏi 1: Service nào có nhiều lỗi (level=ERROR) nhất trong 7 ngày?

### Kết luận
Hệ thống **`payment-api`** là dịch vụ có số lượng lỗi nhiều nhất với **139 lỗi**, chiếm **48.4%** tổng số lỗi của toàn bộ 5 hệ thống.

### Bảng tổng hợp lỗi theo Service
| Service             |   Số lỗi (ERROR) |   Tỷ lệ (%) |
|---------------------|------------------|-------------|
| payment-api         |              139 |       48.43 |
| web-portal          |               41 |       14.29 |
| batch-report        |               37 |       12.89 |
| notification-worker |               35 |       12.2  |
| auth-service        |               35 |       12.2  |

### Phân tích chuyên sâu & Đối chiếu Tài liệu Vận hành
- `payment-api` là dịch vụ xử lý thanh toán cốt lõi. Tỷ lệ lỗi gần 50% cho thấy hệ thống thanh toán đang gặp áp lực kỹ thuật rất lớn.
- Theo quy trình **SOP-01 (Mục 3)** và **FAQ-01 (Mục 1)**: Khi `payment-api` gặp lỗi kết nối DB, đội vận hành **không được tự ý restart ồ ạt** vì sẽ gây hiện tượng bão kết nối (connection storm), đồng thời phải đảm bảo `queue = 0` trước khi thực hiện can thiệp để tránh lệch số dư khách hàng.

---

## 📊 Câu hỏi 2: Số lượng lỗi theo ngày của toàn hệ thống — ngày nào bất thường?

### Kết luận
Toàn bộ hệ thống hoạt động tương đối ổn định từ ngày 27/07 đến 29/07 và 31/07 đến 02/08 (dao động 17–31 lỗi/ngày). Tuy nhiên, ngày **2026-07-30** xảy ra **bất thường nghiêm trọng (Anomaly Spike)** với **140 lỗi ERROR**, chiếm tỷ lệ **27.4%** tổng lượng log trong ngày.

### Bảng thống kê số lượng lỗi theo ngày
| Ngày (UTC)   |   Số ERROR |   Số WARN |   Số INFO |   Tổng Log |   Tỷ lệ Lỗi (%) |
|--------------|------------|-----------|-----------|------------|-----------------|
| 2026-07-27   |         19 |        45 |       335 |        399 |            4.76 |
| 2026-07-28   |         27 |        47 |       305 |        379 |            7.12 |
| 2026-07-29   |         29 |        36 |       320 |        385 |            7.53 |
| 2026-07-30   |        140 |        46 |       325 |        511 |           27.4  |
| 2026-07-31   |         17 |        46 |       320 |        383 |            4.44 |
| 2026-08-01   |         24 |        38 |       328 |        390 |            6.15 |
| 2026-08-02   |         31 |        45 |       316 |        392 |            7.91 |

### Biểu đồ Xu hướng Lỗi (ASCII Error Trend)
```
2026-07-27 [ 19 ERRORs] ██ (4.76%)
2026-07-28 [ 27 ERRORs] ███ (7.12%)
2026-07-29 [ 29 ERRORs] ███ (7.53%)
2026-07-30 [140 ERRORs] ████████████████████████████████ (27.40%)  <-- 🚨 CRITICAL SPIKE
2026-07-31 [ 17 ERRORs] █ (4.44%)
2026-08-01 [ 24 ERRORs] ██ (6.15%)
2026-08-02 [ 31 ERRORs] ███ (7.91%)
```

### Đánh giá mức độ nghiêm trọng (Severity Assessment)
- Căn cứ theo **GUIDE-01 (Ngưỡng cảnh báo hiện hành)**: Ngưỡng cảnh báo CRITICAL được kích hoạt khi tỷ lệ ERROR > 5.0%. Ngày 30/07 tỷ lệ lỗi đạt **27.40%** (gấp hơn 5.4 lần ngưỡng CRITICAL).
- Căn cứ theo **SOP-02 (Quy trình Escalation)**: Đây là sự cố mức độ **P1 (Critical Outage)** vì làm tê liệt cổng thanh toán và giao dịch của khách hàng, đòi hỏi thời hạn phản ứng trong vòng 15 phút và phải lập biên bản Post-mortem trong 3 ngày làm việc.

---

## 📊 Câu hỏi 3: Top 3 loại lỗi phổ biến nhất, thuộc service nào?

### Kết luận
Top 3 loại lỗi phổ biến nhất chiếm **192 / 287 (66.9%)** toàn bộ lỗi trong tuần:

### Bảng chi tiết Top 3 loại lỗi
| Service      | Thông điệp Lỗi (Error Pattern)                   |   Số lần xuất hiện |   Tỷ lệ trong tổng ERROR (%) |
|--------------|--------------------------------------------------|--------------------|------------------------------|
| payment-api  | ERR ConnTimeout db-primary after 30s retry=3     |                114 |                        39.72 |
| web-portal   | ERR HTTP 502 upstream=payment-api path=/checkout |                 41 |                        14.29 |
| batch-report | ERR NullPointer in ReportBuilder step=aggregate  |                 37 |                        12.89 |

### Phân tích cơ chế phát sinh lỗi & Hướng khắc phục:

1. **`ERR ConnTimeout db-primary after 30s retry=3` (`payment-api` — 114 lần)**:
   - *Nguyên nhân*: Database chính (`db-primary`) quá tải kết nối hoặc cạn kiệt connection pool trong giờ cao điểm.
   - *Đối chiếu FAQ-01 / SOP-01*: Cần phối hợp với DBA để tối ưu pool size và tuning query, tránh restart đột ngột làm dồn ứ transaction.

2. **`ERR HTTP 502 upstream=payment-api path=/checkout` (`web-portal` — 41 lần)**:
   - *Nguyên nhân*: Lỗi thứ cấp (cascading failure). Cổng giao diện `web-portal` gọi API thanh toán nhưng `payment-api` bị nghẽn DB và không phản hồi kịp (timeout).
   - *Đối chiếu FAQ-01 (Mục 3)*: Đây hoàn toàn là hệ quả của `payment-api`. Đội vận hành cần tập trung giải quyết triệt để tại `payment-api`, không can thiệp điều chỉnh `web-portal`.

3. **`ERR NullPointer in ReportBuilder step=aggregate` (`batch-report` — 37 lần)**:
   - *Nguyên nhân*: Job báo cáo tổng hợp cuối ngày (chạy lúc 23:00) gặp dữ liệu đầu vào bị khuyết thiếu (do các giao dịch thanh toán ban ngày bị lỗi/không ghi nhận đủ).
   - *Đối chiếu RUN-01 (Mục 2)*: Cần chờ dữ liệu giao dịch được bù đắp/đồng bộ hoàn tất, sau đó thực hiện rerun job bằng lệnh idempotent theo ngày; không rerun ngay khi dữ liệu gốc còn thiếu.

---

## 📊 Câu hỏi 4: Thống kê bản ghi bị loại/sửa trong bước làm sạch dữ liệu

### Thống kê tổng quan
- **Tổng số dòng đọc vào**: **2,923** dòng.
- **Số bản ghi hợp lệ sau làm sạch**: **2,839** bản ghi (97.13%).
- **Số bản ghi bị loại (Quarantined)**: **84** bản ghi (2.87%).

### Phân loại chi tiết các vấn đề dữ liệu phát hiện
| Loại vấn đề dữ liệu     |   Số lượng |   Tỷ lệ trong Quarantine (%) | Hành động xử lý                                       |
|-------------------------|------------|------------------------------|-------------------------------------------------------|
| Duplicate Record        |         28 |                        33.33 | Loại bỏ bản ghi trùng lặp (Deduplication)             |
| Invalid Timestamp       |         20 |                        23.81 | Loại bỏ (giá trị không thể parse thành mốc thời gian) |
| Missing / Invalid Level |         18 |                        21.43 | Loại bỏ (trường level bị null/thiếu)                  |
| Malformed JSON          |         18 |                        21.43 | Loại bỏ (dòng log bị cắt cụt / lỗi cú pháp JSON)      |

### Giải trình Lý do & Quyết định Kỹ thuật (Technical Decisions)

1. **Malformed JSON (18 bản ghi)**:
   - *Mô tả*: Các dòng log bị cắt ngang đột ngột (unterminated strings) do buffer flush bị gián đoạn hoặc lỗi mạng khi ghi log.
   - *Quyết định*: Không thể parse thành đối tượng có cấu trúc đáng tin cậy -> **Loại bỏ vào Quarantine**.

2. **Invalid Timestamp format (20 bản ghi)**:
   - *Mô tả*: Trường timestamp có giá trị rác như `"not-a-date"` (ví dụ dòng log số 34: `timestamp="not-a-date"`).
   - *Quyết định*: Thời gian là trường định danh cốt lõi để phân vùng và phân tích chuỗi thời gian (time-series). Không có timestamp chính xác thì bản ghi mất giá trị phân tích -> **Loại bỏ vào Quarantine**.

3. **Missing / Invalid Log Level (18 bản ghi)**:
   - *Mô tả*: Trường `level` bị null hoặc bị khuyết (ví dụ dòng 11: chỉ có `timestamp`, `service`, `message="Heartbeat ok"`, `request_id`).
   - *Quyết định*: `level` là tiêu chí quan trọng để phân loại sự cố (INFO/WARN/ERROR). Việc tự ý gán nhãn có thể gây sai lệch chỉ số SLA/ngưỡng cảnh báo -> **Loại bỏ vào Quarantine**.

4. **Duplicate Records (28 bản ghi)**:
   - *Mô tả*: Các bản ghi trùng lặp 100% về `(timestamp_utc, service, level, message, request_id)` do cơ chế log shipper gửi lại (at-least-once delivery retry).
   - *Quyết định*: Giữ lại 1 bản ghi duy nhất đầu tiên, đưa các bản ghi trùng thừa vào Quarantine để đảm bảo tính toán thống kê (ERROR count, log volume) chính xác tuyệt đối không bị phóng đại.

5. **Chuẩn hóa Múi giờ (596 bản ghi ghi giờ địa phương +07:00)**:
   - *Mô tả*: Theo lưu ý trong `GUIDE-01`, một số hệ thống cũ ghi giờ địa phương (`+07:00`) thay vì UTC.
   - *Quyết định*: Pipeline tự động phát hiện offset múi giờ và chuẩn hóa toàn bộ về **ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`)**, đồng thời phân vùng `log_date` theo ngày UTC.

---

## 💾 Định dạng Lưu trữ Dữ liệu Sạch (Storage Rationale)

Toàn bộ dữ liệu sạch được lưu dưới định dạng **Apache Parquet** (`pipeline/output/clean_logs.parquet`) và **SQLite Database** (`pipeline/output/clean_logs.db`):

| Tiêu chí | Apache Parquet | JSON/CSV Truyền thống | Lý do Lựa chọn |
| :--- | :--- | :--- | :--- |
| **Kiểu lưu trữ** | Columnar (Theo cột) | Row-based (Theo hàng) | Tối ưu hóa đọc chỉ các cột cần thiết (`service`, `level`, `timestamp`) phục vụ phân tích OLAP |
| **Dung lượng & Nén** | Nén Snappy cao, dung lượng giảm 70–85% | Không nén hoặc nén thô, tốn dung lượng | Tiết kiệm chi phí lưu trữ S3 Data Lake và băng thông truyền tải |
| **Predicate Pushdown** | Hỗ trợ lọc trực tiếp tại mức block (Min/Max statistics) | Phải quét tuần tự toàn bộ file | Tăng tốc độ truy vấn trên Amazon Athena / DuckDB lên gấp 5-10 lần |
| **Schema Enforcement** | Lưu kèm kiểu dữ liệu chặt chẽ (int64, string, category) | Schema không tường minh, dễ lỗi type casting | Đảm bảo tính nhất quán dữ liệu downstream |
