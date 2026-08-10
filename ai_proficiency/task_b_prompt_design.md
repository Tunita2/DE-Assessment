# Task B — Thiết kế Prompt Trích xuất Dữ liệu có Kiểm chứng (Bài 2 — AI Proficiency)

Thiết kế prompt trích xuất thông tin có cấu trúc (Structured JSON) từ trường `message` tự do trong log hệ thống, kèm bộ test case và phương pháp đánh giá định lượng.

---

## 🎯 1. Prompt Hoàn chỉnh (System & User Prompt Template)

### System Prompt
```markdown
Bạn là một chuyên gia trích xuất dữ liệu log kỹ thuật cho hệ thống phân tích sự cố.
Nhiệm vụ của bạn là đọc một chuỗi log message tự do và trích xuất thành đối tượng JSON có cấu trúc chính xác theo schema quy định.

QUY TẮC BẮT BUỘC:
1. Chỉ trích xuất thông tin xuất hiện trực tiếp hoặc suy luận rõ ràng từ chuỗi log message. TUYỆT ĐỐI KHÔNG BỊA ĐẶT (no hallucination).
2. Nếu trường nào không có thông tin trong message, gán giá trị null hoặc mảng rỗng [].
3. Nếu toàn bộ message không thể parse hoặc quá mơ hồ, đặt "is_parsable": false và ghi lý do vào "unparsed_reason".
4. Đầu ra CHỈ LÀ DUY NHẤT một chuỗi JSON hợp lệ, không kèm giải thích hay markdown backticks thừa ngoài JSON.

JSON SCHEMA:
{
  "is_parsable": boolean,
  "error_type": string | null,         // Ví dụ: "ConnectionTimeout", "AuthenticationFailed", "NullPointer", v.v.
  "error_code": string | null,         // Mã lỗi nếu có (ví dụ: "ERR_408", "503", "ECONNRESET")
  "target_component": string | null,   // Thành phần/hệ thống bị ảnh hưởng (ví dụ: "db-primary", "auth-service", "redis-cache")
  "duration_ms": number | null,        // Thời gian diễn ra sự cố/timeout theo millisecond (chuyển đổi nếu ghi theo s/ms)
  "retry_count": number | null,        // Số lần thử lại nếu được ghi nhận
  "additional_params": object,         // Các cặp key-value tham số khác trích xuất được (IP, user_id, path, ...)
  "unparsed_reason": string | null
}
```

### User Prompt
```markdown
Trích xuất chuỗi log message sau:
"""
{LOG_MESSAGE}
"""
```

---

## 🧪 2. Bộ 5 Test Cases từ Data Pack & Kỳ vọng

| STT | Log Message đầu vào | Đặc điểm test case | Đầu ra JSON kỳ vọng (Ground Truth) |
| :---: | :--- | :--- | :--- |
| **TC1** | `"ERR ConnTimeout db-primary after 30s retry=3"` | Chuẩn, có component + timeout + retry | `{"is_parsable": true, "error_type": "ConnectionTimeout", "error_code": "ERR", "target_component": "db-primary", "duration_ms": 30000, "retry_count": 3, "additional_params": {}, "unparsed_reason": null}` |
| **TC2** | `"HTTP 502 Bad Gateway while calling /api/v1/payments from 192.168.1.50"` | Có HTTP status, path, IP | `{"is_parsable": true, "error_type": "BadGateway", "error_code": "502", "target_component": "api-payments", "duration_ms": null, "retry_count": null, "additional_params": {"endpoint": "/api/v1/payments", "client_ip": "192.168.1.50"}, "unparsed_reason": null}` |
| **TC3** | `"Out of memory: Kill process 29481 (worker-pool) score 850 or sacrifice child"` | Lỗi hệ điều hành OOM | `{"is_parsable": true, "error_type": "OutOfMemory", "error_code": null, "target_component": "worker-pool", "duration_ms": null, "retry_count": null, "additional_params": {"pid": 29481, "score": 850}, "unparsed_reason": null}` |
| **TC4** | `"Service failed with unknown code"` | **Ca khó/mơ hồ**: thiếu chi tiết | `{"is_parsable": true, "error_type": "UnknownError", "error_code": null, "target_component": null, "duration_ms": null, "retry_count": null, "additional_params": {}, "unparsed_reason": "Log lacks specific error code or target component details"}` |
| **TC5** | `"###---=== CORRUPTED_LINE_BYTE_0x8921 ===---###"` | **Ca lỗi hoàn toàn**: chuỗi rác | `{"is_parsable": false, "error_type": null, "error_code": null, "target_component": null, "duration_ms": null, "retry_count": null, "additional_params": {}, "unparsed_reason": "Malformed non-text corrupted log data"}` |

---

## 📊 3. Phương pháp Đánh giá Prompt trên Quy mô Lớn (3.000 dòng log)

### Tiêu chí Đo lường (Metrics)
1. **JSON Schema Validity Rate (Tỷ lệ JSON hợp lệ)**: Tỷ lệ output parse được thành công bằng `json.loads()` và khớp Pydantic schema (Kỳ vọng: ≥ 99.5%).
2. **Field Extraction Accuracy (Độ chính xác từng trường)**: So khớp F1-score trên tập mẫu được gán nhãn thủ công (Ground Truth).
3. **Hallucination Rate (Tỷ lệ bịa đặt)**: Kiểm tra các giá trị chuỗi trích xuất (IP, component name) có phải là substring của input message hay không.

### Cơ chế Giám sát & Human-in-the-loop
- Tự động gắn cờ (Flag) yêu cầu người kiểm tra khi:
  - `is_parsable == false` hoặc có `unparsed_reason`.
  - JSON parse thất bại.
  - Trường số (`duration_ms`, `retry_count`) có giá trị âm hoặc bất thường (> 1 ngày).
  - Trích xuất ra `target_component` không nằm trong danh mục service của hệ thống.
