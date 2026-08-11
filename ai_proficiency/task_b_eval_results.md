# Task B — Câu 4: Kết Quả 5 Test Case

> **Model:** gemini-flash-latest (Google AI) · **Temperature:** 0  
> **Ngày chạy:** 11/08/2026  
> **Script:** `ai_proficiency/run_task_b_eval.py` + `scratch/run_5tc.py`

---

## Trạng thái thực tế

Quá trình chạy thực tế gặp 2 vấn đề kỹ thuật được ghi nhận trung thực:

**Vấn đề 1 — Model migration:** `gemini-2.0-flash` và `gemini-2.5-flash` đã được
migrate sang Interactions API mới, không còn dùng được với endpoint
`generateContent` cũ (HTTP 404). Đã tìm được model còn hoạt động:
`gemini-flash-latest`.

**Vấn đề 2 — Quota exhausted:** Quá trình debug model (thử nhiều tên model, 3 lần
chạy 100+ request/lần) đã tiêu hết daily quota của API key trước khi 5 TC thực sự
được chạy thành công. Mọi lần gọi API sau đó đều trả về HTTP 429 Too Many Requests.

**Điều đã xác nhận hoạt động:**
- API key hợp lệ, `gemini-flash-latest` phản hồi đúng (test "say hi" thành công).
- Lần đầu chạy 5 TC, model ĐÃ trả về response (không phải 404) nhưng JSON parse
  fail vì prompt tiếng Việt có ký tự `//` trong schema description khiến model
  bao gồm comments không hợp lệ vào output JSON.
- Fix: chuyển sang English prompt + regex extract `{...}` block → đã sửa đúng về
  kỹ thuật, nhưng không còn quota để xác nhận.

---

## Kết Quả Kỳ Vọng (dựa trên thiết kế prompt — chưa xác nhận bằng LLM thực)

> **Lưu ý:** Các output dưới đây là đầu ra kỳ vọng theo thiết kế, không phải output
> thực tế từ Gemini do quota hết. Script đầy đủ tại `run_task_b_eval.py`.

---

### TC-01 — Kỳ vọng ✅ PASS

**Input:** `ERR ConnTimeout db-primary after 30s retry=3`

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

---

### TC-02 — Kỳ vọng ✅ PASS (kiểm tra chống hallucination)

**Input:** `Payment processed txn=t419149 amount=990000`

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

*Điểm cần kiểm tra: `component` phải là `null` — không được suy diễn "payment-api" từ context ngoài message.*

---

### TC-03 — Kỳ vọng ✅ PASS (inference từ ngữ nghĩa)

**Input:** `Report row mismatch expected=843 got=759`

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

*Không có prefix WARN/ERR — model phải suy luận `warning` từ ngữ nghĩa "mismatch".*

---

### TC-04 — Kỳ vọng ✅ PASS (ca khó)

**Input:** `ERR HTTP 502 upstream=payment-api path=/checkout`

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

*`error_code` 3-token, `component` và `upstream` cùng giá trị, `path=/checkout` có ký tự đặc biệt.*

---

### TC-05 — Kỳ vọng ✅ PASS (ca mơ hồ)

**Input:** `Daily report job started`

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

*Không có tham số — `parse_status = "partial"` đúng. Kiểm tra không bịa thêm parameters.*

---

## Câu 3 — Đánh Giá Trên Data Thật

Script đo metrics đã hoàn thiện trong `run_task_b_eval.py` với các tiêu chí:

| Tiêu chí | Cách đo | Ngưỡng kỳ vọng |
|:---|:---|:---|
| JSON Validity Rate | `json.loads()` thành công | ≥ 98% |
| Schema Compliance | Đủ 6 field đúng kiểu | ≥ 95% |
| Hallucination Rate | `check_hallucination()` flag | ≤ 2% |
| parse_status Accuracy | So với 30-dòng human-label | ≥ 0.85 F1 |

**Không thể chạy thực tế do quota hết.** Kết quả sẽ được bổ sung khi quota reset (thường 24h với free tier).

---

## Bài Học Kỹ Thuật

1. **Model versioning:** Các model mới (gemini-2.5+) đã migrate sang Interactions API — cần kiểm tra endpoint tương thích trước khi hardcode model name.
2. **Quota management trong debug:** Nên chạy test với 1–2 request trước khi scale lên 100+ để không lãng phí quota.
3. **Prompt language:** English prompt cho JSON output ít bị lỗi `//` comment hơn prompt tiếng Việt có ký tự đặc biệt trong schema description.
4. **JSON extraction:** Regex `{[\s\S]+}` để extract JSON block từ free-text response ổn định hơn strip markdown fence đơn thuần.
