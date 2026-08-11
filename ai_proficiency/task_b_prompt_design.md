# Task B — Thiết kế Prompt Trích Xuất Dữ Liệu Có Cấu Trúc từ Log Message

**Tác giả:** Bùi Lê Tuấn  
**Ngày:** 11/08/2026

---

## 1. Prompt Hoàn Chỉnh

```
### ROLE
Bạn là hệ thống phân tích log vận hành tự động. Nhiệm vụ của bạn là đọc một
dòng message log (free-text) và trích xuất thông tin có cấu trúc theo schema
JSON bên dưới.

### INPUT
Một chuỗi văn bản tự do là nội dung trường `message` của một bản ghi log hệ
thống. Ví dụ:
  "ERR ConnTimeout db-primary after 30s retry=3"
  "Payment processed txn=t419149 amount=990000"
  "Slow login 900ms uid=u7882"

### OUTPUT SCHEMA
Trả về DUY NHẤT một JSON object hợp lệ. Không thêm giải thích, không wrap
trong markdown backtick. Schema:

{
  "event_type": string,        // "error" | "warning" | "info" | "unknown"
  "error_code": string | null, // Mã lỗi nếu có (VD: "ERR ConnTimeout", "ERR HTTP 502"), null nếu không có
  "component": string | null,  // Thành phần/service được nhắc TÊN TƯỜNG MINH trong message
                               // (VD: "db-primary", "payment-api", "ReportBuilder")
                               // KHÔNG được điền từ context bên ngoài message
  "action": string | null,     // Hành động/sự kiện chính dạng snake_case tiếng Anh
                               // (VD: "connection_timeout", "payment_processed", "login_success")
  "parameters": object,        // Các cặp key=value bắt được từ message
                               // Key là tên tham số, value LUÔN là string
                               // Ví dụ: {"retry": "3", "txn": "t419149", "uid": "u7882"}
  "parse_status": string       // "ok"           — đủ thông tin rút ra event_type + action
                               // "partial"       — rút ra được một phần, thiếu một số trường
                               // "unparseable"   — không rút ra được thông tin có nghĩa
}

### QUY TẮC BẮT BUỘC
1. KHÔNG BỊA (No hallucination): Chỉ điền giá trị rút ra trực tiếp từ nội dung
   message. Nếu không rút ra được, để null (với string) hoặc {} (với object).
   Tuyệt đối không suy diễn hay điền giá trị mặc định giả.
2. KHÔNG bổ sung thông tin ngoài message: Không được điền `component` từ tên
   service ở trường khác của log — chỉ xét văn bản message.
3. parse_status trung thực: Nếu không rút ra được ít nhất event_type và action,
   đặt parse_status = "unparseable". Nếu chỉ rút ra được một phần, đặt "partial".
4. Định dạng tuyệt đối: Chỉ trả về JSON, không có text trước hay sau.
   JSON phải hợp lệ (escape đúng, không trailing comma).

### MESSAGE CẦN PHÂN TÍCH
{{message}}
```

---

## 2. Bộ Test 5 Message (chọn từ data pack thực tế)

### TC-01 — Ca chuẩn: lỗi kết nối có đủ tham số

**Input:**
```
ERR ConnTimeout db-primary after 30s retry=3
```

**Đầu ra kỳ vọng:**
```json
{
  "event_type": "error",
  "error_code": "ERR ConnTimeout",
  "component": "db-primary",
  "action": "connection_timeout",
  "parameters": {"retry": "3"},
  "parse_status": "ok"
}
```

**Lý do chọn:** Message lỗi phổ biến nhất trong data (chiếm 39.72% tổng ERROR).
Kiểm tra bắt error_code 2-token, component và tham số key=value cùng lúc.

---

### TC-02 — Ca chuẩn: sự kiện INFO không có component trong text

**Input:**
```
Payment processed txn=t419149 amount=990000
```

**Đầu ra kỳ vọng:**
```json
{
  "event_type": "info",
  "error_code": null,
  "component": null,
  "action": "payment_processed",
  "parameters": {"txn": "t419149", "amount": "990000"},
  "parse_status": "ok"
}
```

**Lý do chọn:** Kiểm tra quy tắc chống hallucination — mô hình không được tự suy
diễn `component = "payment-api"` từ context bên ngoài message.

---

### TC-03 — Ca chuẩn: WARN không có prefix rõ ràng

**Input:**
```
Report row mismatch expected=843 got=759
```

**Đầu ra kỳ vọng:**
```json
{
  "event_type": "warning",
  "error_code": null,
  "component": null,
  "action": "row_mismatch",
  "parameters": {"expected": "843", "got": "759"},
  "parse_status": "ok"
}
```

**Lý do chọn:** Không có từ khoá ERR/WARN/INFO — kiểm tra mô hình suy luận
event_type từ ngữ nghĩa ("mismatch" → warning).

---

### TC-04 — Ca khó: lỗi HTTP 3-token + path có ký tự đặc biệt

**Input:**
```
ERR HTTP 502 upstream=payment-api path=/checkout
```

**Đầu ra kỳ vọng:**
```json
{
  "event_type": "error",
  "error_code": "ERR HTTP 502",
  "component": "payment-api",
  "action": "http_upstream_error",
  "parameters": {"upstream": "payment-api", "path": "/checkout"},
  "parse_status": "ok"
}
```

**Lý do chọn (ca khó):** `error_code` gồm 3 token ("ERR HTTP 502"). `component`
và `parameters.upstream` có cùng giá trị — phải điền cả hai đúng chỗ. `path`
chứa `/` dễ gây lỗi JSON nếu mô hình không escape đúng.

---

### TC-05 — Ca mơ hồ: message hợp lệ nhưng không có tham số

**Input:**
```
Daily report job started
```

**Đầu ra kỳ vọng:**
```json
{
  "event_type": "info",
  "error_code": null,
  "component": null,
  "action": "report_job_started",
  "parameters": {},
  "parse_status": "partial"
}
```

**Lý do chọn (ca mơ hồ):** Không có tham số, không có component tường minh. Kiểm
tra mô hình có bịa thêm parameters không và có đặt đúng `parse_status = "partial"`
(rút ra được event_type + action nhưng thiếu chi tiết) không.

---

## 3. Cách Đánh Giá Prompt khi Chạy trên 3.000 Dòng Thật

### 3.1 Tiêu chí đo (Metrics)

| Tiêu chí | Cách đo | Ngưỡng chấp nhận |
|:---|:---|:---|
| **JSON Validity Rate** | % output parse được bằng `json.loads()` | ≥ 98% |
| **Schema Compliance** | % JSON có đủ 6 field đúng kiểu | ≥ 95% |
| **parse_status Accuracy** | F1 trên ~100 dòng human-label (3 class) | ≥ 0.85 |
| **Parameter Recall** | % key=value trong message được bắt đúng | ≥ 90% |
| **Hallucination Rate** | % case có field điền giá trị không có trong text | ≤ 2% |

### 3.2 Phát hiện Bịa / Hallucination (automated)

Với mỗi record output, chạy kiểm tra ngược:

```python
def check_hallucination(message: str, output: dict) -> list[str]:
    """Trả về danh sách flag — nếu rỗng là không phát hiện hallucination."""
    flags = []
    # 1. Kiểm tra từng parameter: giá trị có xuất hiện trong message không?
    for k, v in output.get("parameters", {}).items():
        if v and v not in message:
            flags.append(f"parameter '{k}={v}' not found in message")
    # 2. Component phải xuất hiện tường minh trong message text
    comp = output.get("component")
    if comp and comp not in message:
        flags.append(f"component '{comp}' not grounded in message text")
    # 3. error_code phải là substring của message
    ec = output.get("error_code")
    if ec and ec not in message:
        flags.append(f"error_code '{ec}' not found in message")
    return flags
```

Mọi record có `flags != []` đều được đưa vào hàng đợi human review.

### 3.3 Khi nào cần người kiểm tra (Human-in-the-loop)

Ưu tiên theo thứ tự:

1. **Bắt buộc:** Mọi record bị flag hallucination (dữ liệu sai cấu trúc gây sai
   phân tích downstream).
2. **Nên xem:** `parse_status = "unparseable"` — xác định thật sự không parse
   được hay prompt đang fail với format mới.
3. **Nên xem:** `parse_status = "partial"` bất thường cao (> 15% trong một batch)
   — có thể xuất hiện message pattern mới chưa được ví dụ trong prompt.
4. **Sampling định kỳ:** 50–100 record ngẫu nhiên mỗi batch để duy trì ground
   truth và phát hiện model drift khi LLM provider cập nhật model.

---

## 4. Kết Quả Chạy Thực Tế (Bonus — 5 Test Case)

> **Công cụ:** claude-sonnet-4-6 (TechOpenClaw proxy, OpenAI-compatible API)
> **Temperature:** 0 · **Script:** `scratch/run_5tc_claude.py`
> **Kết quả:** 1/5 ✅ PASS · 4/5 🔶 PARTIAL · 0/5 🚨 HALLUCINATION

Chi tiết đầy đủ: [`task_b_eval_results.md`](task_b_eval_results.md)

### Tóm tắt

| TC | Input | Verdict | Mismatch chính |
|:---:|:---|:---:|:---|
| TC-01 | `ERR ConnTimeout db-primary after 30s retry=3` | 🔶 PARTIAL | `error_code` bị rút gọn ("ConnTimeout" thay vì "ERR ConnTimeout"), `action` quá ngắn |
| TC-02 | `Payment processed txn=t419149 amount=990000` | ✅ PASS | — |
| TC-03 | `Report row mismatch expected=843 got=759` | 🔶 PARTIAL | `event_type = "error"` thay vì `"warning"`, parameter values là integer thay vì string |
| TC-04 | `ERR HTTP 502 upstream=payment-api path=/checkout` | 🔶 PARTIAL | `error_code = "502"` (bỏ "ERR HTTP"), thêm `protocol=HTTP` không phải key=value |
| TC-05 | `Daily report job started` | 🔶 PARTIAL | `action` khác convention, `parse_status = "ok"` thay vì `"partial"` |

### Phát hiện quan trọng từ kết quả thực tế

**1. TC-02 PASS** xác nhận quy tắc chống hallucination hoạt động: `component = null`,
model không suy diễn "payment-api" từ trường `service` bên ngoài message.

**2. Underspecification của prompt** gây 4/5 PARTIAL:
- `error_code`: Prompt không chỉ rõ giữ nguyên prefix "ERR" → model tự rút gọn.
- `action`: Không quy định độ dài hay convention (verb-first vs noun-first).
- `parameters` type: Mặc dù đã ghi "value luôn là string" nhưng model vẫn trả integer.
- `parse_status = "partial"`: Định nghĩa chưa đủ cụ thể — model hiểu "partial" là "thiếu 1 field quan trọng" thay vì "thiếu parameters".

**3. Hallucination checker có false-negative:** `timeout=30s` (TC-01) và `protocol=HTTP`
(TC-04) được thêm vào parameters dù không phải dạng key=value trong message. Checker
chỉ verify value xuất hiện trong text chứ không verify key=value pattern — cần nâng cấp.

**4. JSON Validity Rate = 100%** — tất cả 5 response đều parse được bằng `json.loads()`.

---

**Prompt cần cải thiện:** Thêm ràng buộc tường minh về `error_code` format,
`action` convention (2–4 từ, past-participle), type enforcement cho `parameters`,
và ví dụ phân biệt `parse_status = "ok"` vs `"partial"`.






