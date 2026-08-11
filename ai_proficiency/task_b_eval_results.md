# Task B — Câu 4: Kết Quả 5 Test Case Thực Tế

> **Model:** claude-sonnet-4-6 (TechOpenClaw proxy) · **Temperature:** 0
> **Ngày:** 11/08/2026 19:48 · **Script:** `scratch/run_5tc_claude.py`

---

**Tổng kết: 1/5 ✅ PASS · 4/5 🔶 PARTIAL · 0/5 🚨 HALLUCINATION**

---

### TC-01 — 🔶 PARTIAL

**Input:** `ERR ConnTimeout db-primary after 30s retry=3`

**Output từ LLM:**
```json
{"event_type": "error", "error_code": "ConnTimeout", "component": "db-primary", "action": "connect", "parameters": {"timeout": "30s", "retry": "3"}, "parse_status": "ok"}
```

**Expected:**
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

⚠️ **Field không khớp:** `error_code`, `action`, `parameters`

**Nhận xét:**
- `error_code`: Model bỏ prefix "ERR", chỉ giữ "ConnTimeout" → prompt chưa chỉ rõ phải giữ toàn bộ chuỗi error code.
- `action`: "connect" quá ngắn, thiếu ngữ nghĩa so với "connection_timeout" → prompt không định nghĩa độ chi tiết của action.
- `parameters`: Model thêm `timeout=30s` dù "after 30s" trong message KHÔNG ở dạng `key=value` → đây là **false-negative của hallucination checker** — checker chỉ kiểm tra value ("30s") có trong message không, nhưng key "timeout" là do model suy diễn.

---

### TC-02 — ✅ PASS

**Input:** `Payment processed txn=t419149 amount=990000`

**Output từ LLM:**
```json
{"event_type": "info", "error_code": null, "component": null, "action": "payment_processed", "parameters": {"txn": "t419149", "amount": "990000"}, "parse_status": "ok"}
```

**Expected:**
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

✅ Tất cả field khớp, không hallucination.

**Nhận xét quan trọng:** `component = null` — model KHÔNG suy diễn "payment-api" từ context
bên ngoài message. Quy tắc chống hallucination hoạt động đúng ở TC này.

---

### TC-03 — 🔶 PARTIAL

**Input:** `Report row mismatch expected=843 got=759`

**Output từ LLM:**
```json
{"event_type": "error", "error_code": null, "component": null, "action": "validate_report_row_count", "parameters": {"expected": 843, "got": 759}, "parse_status": "ok"}
```

**Expected:**
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

⚠️ **Field không khớp:** `event_type`, `action`, `parameters`

**Nhận xét:**
- `event_type`: Model trả về "error" thay vì "warning" — ngữ nghĩa "mismatch" mang tính cảnh báo (data không nhất quán) nhưng chưa đến mức lỗi nghiêm trọng. Prompt cần ví dụ cụ thể hơn về phân biệt warning vs error.
- `action`: "validate_report_row_count" quá dài và chi tiết hơn mức cần → cần chỉ định trong prompt "ngắn gọn 2–3 từ".
- `parameters`: Giá trị `843`, `759` là integer thay vì string → prompt đã ghi "values always string" nhưng model không tuân thủ → cần thêm ví dụ tường minh.

---

### TC-04 — 🔶 PARTIAL

**Input:** `ERR HTTP 502 upstream=payment-api path=/checkout`

**Output từ LLM:**
```json
{"event_type": "error", "error_code": "502", "component": "payment-api", "action": "http_request", "parameters": {"protocol": "HTTP", "upstream": "payment-api", "path": "/checkout"}, "parse_status": "ok"}
```

**Expected:**
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

⚠️ **Field không khớp:** `error_code`, `action`, `parameters`

**Nhận xét:**
- `error_code`: Chỉ lấy "502" thay vì toàn bộ "ERR HTTP 502" → cùng vấn đề TC-01, model tự rút gọn error code.
- `action`: "http_request" không đủ ngữ nghĩa so với "http_upstream_error".
- `parameters`: Thêm `protocol=HTTP` dù "HTTP" không ở dạng key=value trong message → **false-negative** của hallucination checker (value "HTTP" có trong message nên không bị flag).
- **Điểm đáng chú ý:** `component = "payment-api"` đúng — model đọc đúng từ `upstream=payment-api`.

---

### TC-05 — 🔶 PARTIAL

**Input:** `Daily report job started`

**Output từ LLM:**
```json
{"event_type": "info", "error_code": null, "component": null, "action": "start_daily_report_job", "parameters": {}, "parse_status": "ok"}
```

**Expected:**
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

⚠️ **Field không khớp:** `action`, `parse_status`

**Nhận xét:**
- `action`: "start_daily_report_job" vs "report_job_started" — đây là vấn đề **chủ quan của action naming**. Cả hai đều có nghĩa hợp lý; chỉ khác về convention (verb-first vs noun-first). Đây là underspecification của prompt.
- `parse_status`: Model trả về "ok" thay vì "partial" — model lập luận rằng message đủ để xác định event_type + action nên là "ok". Định nghĩa "partial" trong prompt cần rõ hơn: ví dụ "partial = có action/event_type nhưng thiếu parameters để chẩn đoán đầy đủ".

---

## Tổng Kết Phân Tích

### Các điểm prompt cần cải thiện (dựa trên kết quả thực tế)

| Vấn đề | Tần suất | Cải thiện đề xuất |
|:---|:---|:---|
| `error_code` bị rút gọn (bỏ prefix "ERR") | TC-01, TC-04 | Thêm ví dụ: "Giữ nguyên toàn bộ error prefix: 'ERR ConnTimeout', không chỉ 'ConnTimeout'" |
| `action` không nhất quán về độ dài/format | TC-01, TC-03, TC-04, TC-05 | Thêm ràng buộc: "2–4 từ, dùng past-participle hoặc noun phrase" |
| `parameters` giá trị là integer thay vì string | TC-03 | Thêm ví dụ tường minh: `{"expected": "843"}` không phải `{"expected": 843}` |
| `parse_status = "ok"` khi nên là "partial" | TC-05 | Làm rõ: "'partial' = đủ event_type+action nhưng KHÔNG có parameters" |
| Hallucination checker: false-negative | TC-01, TC-04 | Nâng cấp: kiểm tra `key=value` pattern, không chỉ value substring |
| Hallucination checker: false-positive | Tiềm năng | Nếu model normalize format (`990000`→`990,000`), sẽ flag nhầm |

> **Lưu ý về hallucination checker:** Đây là baseline đơn giản dùng substring match.
> Flags là **tín hiệu gợi ý cho human review**, không phải bằng chứng chắc chắn.
> False-negative: inferred keys (`timeout`, `protocol`) không bị bắt vì value vẫn có trong message.
> False-positive: format normalization khác có thể bị flag nhầm. Luôn cần người xác nhận thủ công.

### Điểm đáng ghi nhận

- **TC-02 PASS hoàn toàn** — đặc biệt là `component = null` chứng minh quy tắc
  "không suy diễn từ context ngoài" hoạt động.
- **Không có HALLUCINATION flag** — giá trị được điền đều có thể trace ngược về
  message text, dù checker có false-negative với inferred keys.
- **JSON format**: Tất cả 5 output đều là valid JSON, `json.loads()` thành công 100%.
