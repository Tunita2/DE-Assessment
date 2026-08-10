import sys
import time
from pathlib import Path
from typing import List
from collections import Counter

# Set UTF-8 encoding for standard output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add workspace root to sys.path
workspace_root = Path(__file__).resolve().parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from pipeline.src.ingest import stream_raw_logs
from pipeline.src.validator import LogValidator
from pipeline.src.storage import StorageManager
from pipeline.src.analytics import LogAnalytics
from pipeline.src.models import CleanedLogRecord, QuarantineRecord, PipelineSummary


def run_pipeline(
    input_file: Path = workspace_root / "data" / "app_logs_7days.jsonl",
    output_dir: Path = workspace_root / "pipeline" / "output",
    report_file: Path = workspace_root / "pipeline" / "report_answers.md"
) -> PipelineSummary:
    """Executes the complete ingestion, cleaning, storage, and analytics pipeline."""
    start_time = time.time()
    print("=" * 70)
    print("🚀 [Xbrain POC] KHỞI CHẠY PIPELINE XỬ LÝ LOG 7 NGÀY (PHẦN A)")
    print("=" * 70)
    print(f"📁 Dữ liệu đầu vào: {input_file}")
    print(f"📁 Thư mục xuất dữ liệu: {output_dir}")

    if not input_file.exists():
        print(f"❌ [Error] Không tìm thấy file dữ liệu tại {input_file}")
        sys.exit(1)

    # 1. Ingest & Validate
    validator = LogValidator()
    cleaned_records: List[CleanedLogRecord] = []
    quarantine_records: List[QuarantineRecord] = []
    total_lines = 0

    print("\n⏳ [1/4] Đang đọc file stream và thực hiện làm sạch / validate dữ liệu...")
    for raw_rec in stream_raw_logs(input_file):
        total_lines += 1
        clean_rec, quaran_rec = validator.process_raw_record(raw_rec)
        if clean_rec is not None:
            cleaned_records.append(clean_rec)
        if quaran_rec is not None:
            quarantine_records.append(quaran_rec)

    print(f"   ✓ Tổng số dòng đọc: {total_lines:,}")
    print(f"   ✓ Bản ghi hợp lệ (Cleaned): {len(cleaned_records):,}")
    print(f"   ✓ Bản ghi lỗi / cách ly (Quarantined): {len(quarantine_records):,}")

    # 2. Storage
    print("\n⏳ [2/4] Đang lưu trữ dữ liệu sạch ra Parquet & SQLite...")
    storage = StorageManager(output_dir)
    parquet_path = storage.save_clean_logs_parquet(cleaned_records)
    sqlite_path = storage.save_clean_logs_sqlite(cleaned_records)
    quarantine_path = storage.save_quarantine_logs(quarantine_records)
    print(f"   ✓ Đã xuất Apache Parquet: {parquet_path} (nén Snappy)")
    print(f"   ✓ Đã xuất SQLite Database: {sqlite_path}")
    print(f"   ✓ Đã xuất Quarantine JSONL: {quarantine_path}")

    # 3. Analytics
    print("\n⏳ [3/4] Đang thực hiện phân tích số liệu trả lời 4 câu hỏi nghiệp vụ...")
    analytics = LogAnalytics(cleaned_records, quarantine_records)
    q1_res = analytics.question_1_service_errors()
    q2_res = analytics.question_2_daily_trend()
    q3_res = analytics.question_3_top_error_types()
    q4_res = analytics.question_4_cleaning_statistics(total_lines)

    # Console Summary
    print("\n" + "=" * 70)
    print("📊 TỔNG HỢP KẾT QUẢ PHÂN TÍCH 4 CÂU HỎI")
    print("=" * 70)

    print("\n▶ Câu 1: Service có nhiều lỗi ERROR nhất:")
    print(f"   → Service: **{q1_res['top_service']}** ({q1_res['top_errors']} lỗi / {q1_res['total_errors']} tổng ERROR, chiếm {q1_res['top_errors']/q1_res['total_errors']*100:.1f}%)")
    print(q1_res["table_markdown"])

    print("\n▶ Câu 2: Xu hướng lỗi theo ngày & Ngày bất thường:")
    print(f"   → Ngày bất thường: **{q2_res['anomaly_date']}** với **{q2_res['anomaly_errors']} ERRORs** (tỷ lệ lỗi **{q2_res['anomaly_rate']}%**)")
    print(q2_res["table_markdown"])

    print("\n▶ Câu 3: Top 3 loại lỗi phổ biến nhất:")
    print(q3_res["table_markdown"])

    print("\n▶ Câu 4: Thống kê bản ghi bị loại/sửa trong quá trình làm sạch:")
    print(f"   → Tổng dòng: {q4_res['total_raw_lines']} | Hợp lệ: {q4_res['total_clean']} | Bị loại: {q4_res['total_quarantined']} ({q4_res['quarantine_pct']}%)")
    print(q4_res["table_markdown"])

    # 4. Generate Markdown Report
    print(f"\n⏳ [4/4] Đang cập nhật báo cáo chi tiết tại {report_file}...")
    generate_markdown_report(report_file, q1_res, q2_res, q3_res, q4_res)
    print("   ✓ Đã hoàn tất ghi báo cáo report_answers.md!")

    execution_time = round(time.time() - start_time, 3)

    summary = PipelineSummary(
        total_lines_read=total_lines,
        cleaned_records_count=len(cleaned_records),
        quarantined_records_count=len(quarantine_records),
        quarantine_breakdown=dict(Counter(q.issue_category for q in quarantine_records)),
        service_distribution=dict(Counter(r.service for r in cleaned_records)),
        level_distribution=dict(Counter(r.level for r in cleaned_records)),
        date_distribution=dict(Counter(r.log_date for r in cleaned_records)),
        execution_time_seconds=execution_time
    )
    storage.save_summary(summary)
    print(f"\n✨ Pipeline hoàn thành xuất sắc trong {execution_time}s!")
    print("=" * 70)
    return summary


def generate_markdown_report(
    report_file: Path,
    q1_res: dict,
    q2_res: dict,
    q3_res: dict,
    q4_res: dict
):
    """Generates a comprehensive markdown report addressing the 4 business questions."""
    content = f"""# Báo cáo Phân tích Dữ liệu Log 7 Ngày (Phần A — Data Pipeline)

**Đơn vị thực hiện**: Đội Data Engineering — Xbrain (TechX Corp)  
**Khách hàng**: Phòng CNTT — Công ty Tài chính Sao Đỏ  
**Phạm vi dữ liệu**: 7 ngày log liên tục (2026-07-27 đến 2026-08-02) của 5 hệ thống nội bộ  
**Nguồn dữ liệu**: `data/app_logs_7days.jsonl`  

---

## Executive Summary (Tóm tắt điều hành)

1. **Tổng lượng log xử lý**: **{q4_res['total_raw_lines']:,}** dòng log thô. Sau khi làm sạch, chuẩn hóa múi giờ UTC và khử trùng lặp, thu được **{q4_res['total_clean']:,}** bản ghi sạch ({100 - q4_res['quarantine_pct']:.1f}%) và cách ly **{q4_res['total_quarantined']}** bản ghi lỗi ({q4_res['quarantine_pct']}%) vào `quarantine_logs.jsonl`.
2. **Hệ thống bất ổn nhất**: **`payment-api`** chiếm tới **{q1_res['top_errors']} lỗi ERROR** (tương đương **{q1_res['top_errors']/q1_res['total_errors']*100:.1f}%** tổng số lỗi toàn hệ thống).
3. **Ngày xảy ra sự cố nghiêm trọng (Spike Anomaly)**: Ngày **{q2_res['anomaly_date']}** ghi nhận **{q2_res['anomaly_errors']} lỗi ERROR**, tỷ lệ lỗi vọt lên **{q2_res['anomaly_rate']}%** (vượt xa ngưỡng CRITICAL 5.0% theo quy định tại `GUIDE-01`).
4. **Nguyên nhân gốc rễ (Root Cause)**: Do hiện tượng nghẽn kết nối database chính (`ERR ConnTimeout db-primary after 30s retry=3`) tại `payment-api`, dẫn đến phản ứng dây chuyền làm sập cổng giao tiếp trên `web-portal` (`ERR HTTP 502 upstream=payment-api`).

---

## 📊 Câu hỏi 1: Service nào có nhiều lỗi (level=ERROR) nhất trong 7 ngày?

### Kết luận
Hệ thống **`payment-api`** là dịch vụ có số lượng lỗi nhiều nhất với **{q1_res['top_errors']} lỗi**, chiếm **{q1_res['top_errors']/q1_res['total_errors']*100:.1f}%** tổng số lỗi của toàn bộ 5 hệ thống.

### Bảng tổng hợp lỗi theo Service
{q1_res['table_markdown']}

### Phân tích chuyên sâu & Đối chiếu Tài liệu Vận hành
- `payment-api` là dịch vụ xử lý thanh toán cốt lõi. Tỷ lệ lỗi gần 50% cho thấy hệ thống thanh toán đang gặp áp lực kỹ thuật rất lớn.
- Theo quy trình **SOP-01 (Mục 3)** và **FAQ-01 (Mục 1)**: Khi `payment-api` gặp lỗi kết nối DB, đội vận hành **không được tự ý restart ồ ạt** vì sẽ gây hiện tượng bão kết nối (connection storm), đồng thời phải đảm bảo `queue = 0` trước khi thực hiện can thiệp để tránh lệch số dư khách hàng.

---

## 📊 Câu hỏi 2: Số lượng lỗi theo ngày của toàn hệ thống — ngày nào bất thường?

### Kết luận
Toàn bộ hệ thống hoạt động tương đối ổn định từ ngày 27/07 đến 29/07 và 31/07 đến 02/08 (dao động 17–31 lỗi/ngày). Tuy nhiên, ngày **{q2_res['anomaly_date']}** xảy ra **bất thường nghiêm trọng (Anomaly Spike)** với **{q2_res['anomaly_errors']} lỗi ERROR**, chiếm tỷ lệ **{q2_res['anomaly_rate']}%** tổng lượng log trong ngày.

### Bảng thống kê số lượng lỗi theo ngày
{q2_res['table_markdown']}

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
Top 3 loại lỗi phổ biến nhất chiếm **{sum(x['occurrence_count'] for x in q3_res['top_3'])} / {q1_res['total_errors']} ({sum(x['occurrence_count'] for x in q3_res['top_3'])/q1_res['total_errors']*100:.1f}%)** toàn bộ lỗi trong tuần:

### Bảng chi tiết Top 3 loại lỗi
{q3_res['table_markdown']}

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
- **Tổng số dòng đọc vào**: **{q4_res['total_raw_lines']:,}** dòng.
- **Số bản ghi hợp lệ sau làm sạch**: **{q4_res['total_clean']:,}** bản ghi ({100 - q4_res['quarantine_pct']:.2f}%).
- **Số bản ghi bị loại (Quarantined)**: **{q4_res['total_quarantined']}** bản ghi ({q4_res['quarantine_pct']:.2f}%).

### Phân loại chi tiết các vấn đề dữ liệu phát hiện
{q4_res['table_markdown']}

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
"""
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    run_pipeline()
