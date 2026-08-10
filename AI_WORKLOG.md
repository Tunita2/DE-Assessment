# AI Work Log — Data Engineer Assessment (Xbrain / TechX)

Nhật ký sử dụng AI có kiểm chứng trong quá trình thực hiện POC Data Engineer & Mini Knowledge Base.

> **Nguyên tắc**: 
> - Chọn lọc 8–15 entry có ý nghĩa nhất về mặt kỹ thuật và ra quyết định.
> - Trung thực ghi lại các trường hợp AI đề xuất sai/chưa tối ưu và quá trình kiểm chứng, sửa đổi.
> - Tất cả code/tài liệu đưa vào bài nộp đều được hiểu rõ và kiểm chứng thực tế.

---

## 📋 Bảng Nhật ký AI (AI Work Log)

| STT | Việc (Task) | Prompt | Output & đánh giá | Verify & sửa |
| :---: | :--- | :--- | :--- | :--- |
| **01** | Khởi tạo cấu trúc repository & tài liệu dự án | *"Tạo cấu trúc thư mục repo cho bài POC DE theo đúng tài liệu mô tả Xbrain_Assessment_DE_01_Domain_POC và Bài 2 AI Proficiency"* | **AI trả về:** Đầy đủ các thư mục `pipeline/`, `kb/`, `design/`, `sop/`, `ai_proficiency/`, `README.md`, `AI_WORKLOG.md`.<br>**Đánh giá:** Đúng cấu trúc yêu cầu của đề bài, phân tách rõ ràng giữa code pipeline, KB và báo cáo. | **Cách kiểm chứng:** Đối chiếu với bảng thư mục mục *Nộp bài* trong file đề bài Bài 1 và yêu cầu nộp chung Bài 2.<br>**Đã sửa:** Bổ sung thêm `.gitignore` chuẩn Python và `requirements.txt`. |
| **02** | Khảo sát dữ liệu log & phát hiện bất thường dữ liệu (Data Profiling) | *"Viết script phân tích cấu trúc và kiểm tra các dị thường dữ liệu trong file app_logs_7days.jsonl"* | **AI trả về:** Script đọc toàn bộ file bằng `json.loads` nhưng ban đầu giả định mọi dòng đều parse được JSON.<br>**Đánh giá:** Chưa tính đến việc có dòng JSON bị cắt cụt (unterminated strings) khiến script bị crash giữa chừng. | **Cách kiểm chứng:** Chạy thử và gặp `JSONDecodeError` ở dòng 39.<br>**Đã sửa:** Bọc khối `try...except json.JSONDecodeError` theo từng dòng, ghi nhận chính xác 18 dòng malformed JSON và 20 dòng timestamp `not-a-date`. |
| **03** | Xử lý múi giờ và chuẩn hóa Timestamp về UTC | *"Thiết kế logic chuẩn hóa trường timestamp trong log về chuẩn ISO 8601 UTC"* | **AI trả về:** Dùng `datetime.fromisoformat()`.<br>**Đánh giá:** Chưa tối ưu khi gặp các định dạng có offset `+07:00` từ các hệ thống cũ (như ghi nhận trong `GUIDE-01`). | **Cách kiểm chứng:** Đối chiếu với tài liệu `GUIDE-01` và chạy thử test case có `+07:00`.<br>**Đã sửa:** Sử dụng `dateutil.parser.isoparse()` và `.astimezone(timezone.utc)` để chuẩn hóa 596 dòng log có offset về chuẩn `YYYY-MM-DDTHH:MM:SSZ`. |
| **04** | Xây dựng Pipeline End-to-End & Động cơ phân tích 4 câu hỏi | *"Tổ chức code pipeline thành các module models, ingest, validator, storage, analytics và tính toán 4 câu hỏi nghiệp vụ"* | **AI trả về:** Code xử lý và query DuckDB/Pandas, bảng biểu Markdown.<br>**Đánh giá:** Kết quả tính toán chính xác, chỉ ra rõ sự cố spike ngày 30/07 tại `payment-api` và liên hệ trực tiếp với `FAQ-01`/`RUN-01`. | **Cách kiểm chứng:** Viết bộ Unit test (7 test cases trong `test_pipeline.py`) chạy qua `pytest` (100% pass) và đối chiếu thủ công số liệu. |


---

## 🔍 Ghi chú & Đúc kết kinh nghiệm sử dụng AI
- **Verification First**: Luôn đối chiếu code được sinh với dữ liệu thực tế (`data/app_logs_7days.jsonl` và `data/docs/`) trước khi chấp nhận.
- **Edge cases**: AI thường giả định dữ liệu sạch hoàn hảo; cần chủ động yêu cầu xử lý malformed JSON, missing fields, timestamp parsing errors.
