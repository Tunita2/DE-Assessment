"""
Task B — Evaluation & Live LLM Test Runner
Câu 3: Đánh giá prompt trên toàn bộ data thật (3.000 dòng)
Câu 4: Chạy thử 5 test case qua Gemini API và ghi kết quả thực tế

Usage:
    set GEMINI_API_KEY=your_key_here
    py -3.13 ai_proficiency/run_task_b_eval.py
"""

import json
import re
import sqlite3
import sys
import os
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-flash-latest"
DB_PATH        = Path("pipeline/output/clean_logs.db")
OUT_PATH       = Path("ai_proficiency/task_b_eval_results.md")

# ── PROMPT TEMPLATE ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """### ROLE
Bạn là hệ thống phân tích log vận hành tự động. Nhiệm vụ của bạn là đọc một
dòng message log (free-text) và trích xuất thông tin có cấu trúc theo schema
JSON bên dưới.

### OUTPUT SCHEMA
Trả về DUY NHẤT một JSON object hợp lệ. Không thêm giải thích, không wrap
trong markdown backtick. Schema:

{
  "event_type": string,
  "error_code": string | null,
  "component": string | null,
  "action": string | null,
  "parameters": object,
  "parse_status": string
}

event_type: "error" | "warning" | "info" | "unknown"
error_code: mã lỗi nếu có (VD: "ERR ConnTimeout", "ERR HTTP 502"), null nếu không có
component: thành phần được nhắc TÊN TƯỜNG MINH trong message, null nếu không có
action: hành động chính dạng snake_case tiếng Anh
parameters: các cặp key=value bắt được, value luôn là string
parse_status: "ok" | "partial" | "unparseable"

### QUY TẮC BẮT BUỘC
1. KHÔNG BỊA: Chỉ điền giá trị rút ra trực tiếp từ message. Nếu không có, để null hoặc {}.
2. KHÔNG dùng thông tin ngoài message (không suy diễn component từ trường service).
3. parse_status trung thực: "unparseable" nếu không rút ra được event_type + action.
4. Chỉ trả về JSON thuần, không có text trước hay sau.

### MESSAGE CẦN PHÂN TÍCH
"""

# ── 5 TEST CASES ─────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "TC-01",
        "message": "ERR ConnTimeout db-primary after 30s retry=3",
        "expected": {
            "event_type": "error",
            "error_code": "ERR ConnTimeout",
            "component": "db-primary",
            "action": "connection_timeout",
            "parameters": {"retry": "3"},
            "parse_status": "ok",
        },
    },
    {
        "id": "TC-02",
        "message": "Payment processed txn=t419149 amount=990000",
        "expected": {
            "event_type": "info",
            "error_code": None,
            "component": None,
            "action": "payment_processed",
            "parameters": {"txn": "t419149", "amount": "990000"},
            "parse_status": "ok",
        },
    },
    {
        "id": "TC-03",
        "message": "Report row mismatch expected=843 got=759",
        "expected": {
            "event_type": "warning",
            "error_code": None,
            "component": None,
            "action": "row_mismatch",
            "parameters": {"expected": "843", "got": "759"},
            "parse_status": "ok",
        },
    },
    {
        "id": "TC-04",
        "message": "ERR HTTP 502 upstream=payment-api path=/checkout",
        "expected": {
            "event_type": "error",
            "error_code": "ERR HTTP 502",
            "component": "payment-api",
            "action": "http_upstream_error",
            "parameters": {"upstream": "payment-api", "path": "/checkout"},
            "parse_status": "ok",
        },
    },
    {
        "id": "TC-05",
        "message": "Daily report job started",
        "expected": {
            "event_type": "info",
            "error_code": None,
            "component": None,
            "action": "report_job_started",
            "parameters": {},
            "parse_status": "partial",
        },
    },
]

REQUIRED_FIELDS = {"event_type", "error_code", "component", "action", "parameters", "parse_status"}
VALID_EVENT_TYPES = {"error", "warning", "info", "unknown"}
VALID_PARSE_STATUS = {"ok", "partial", "unparseable"}


# ── HALLUCINATION CHECKER ────────────────────────────────────────────────────
def check_hallucination(message: str, output: dict) -> list:
    """
    Baseline hallucination checker — substring match only.

    Known limitations:
    - False negative: inferred keys are NOT caught if the VALUE still appears in message.
      Example: model adds 'timeout=30s' from 'after 30s' — value "30s" is in message
      so this passes, but key "timeout" was inferred, not from a key=value pair.
    - False positive: if model normalises value format (e.g. '990000' -> '990,000',
      or case mismatch 'payment-api' vs 'Payment-API'), this flags as hallucination
      even though the information came from the message.

    Flags from this function are signals for human review, NOT definitive proof of
    hallucination. Always verify flagged records manually before drawing conclusions.
    """
    flags = []
    for k, v in output.get("parameters", {}).items():
        if v and str(v) not in message:
            flags.append(f"parameter '{k}={v}' not found in message")
    comp = output.get("component")
    if comp and comp not in message:
        flags.append(f"component '{comp}' not grounded in message text")
    ec = output.get("error_code")
    if ec and ec not in message:
        flags.append(f"error_code '{ec}' not found in message")
    return flags


# ── SCHEMA VALIDATOR ─────────────────────────────────────────────────────────
def validate_schema(output: dict) -> list:
    issues = []
    missing = REQUIRED_FIELDS - set(output.keys())
    if missing:
        issues.append(f"missing fields: {missing}")
    if output.get("event_type") not in VALID_EVENT_TYPES:
        issues.append(f"invalid event_type: {output.get('event_type')}")
    if output.get("parse_status") not in VALID_PARSE_STATUS:
        issues.append(f"invalid parse_status: {output.get('parse_status')}")
    if not isinstance(output.get("parameters", {}), dict):
        issues.append("parameters must be object")
    return issues


# ── GEMINI CALLER ─────────────────────────────────────────────────────────────
def call_gemini(message: str) -> tuple[dict | None, str]:
    """Returns (parsed_dict_or_None, raw_text)"""
    if not GEMINI_API_KEY:
        return None, "ERROR: GEMINI_API_KEY not set"
    try:
        import urllib.request
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        )
        body = json.dumps({
            "contents": [{"parts": [{"text": SYSTEM_PROMPT + message}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 512},
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strategy 1: strip markdown fences
        raw_clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        # Strategy 2: extract first {...} block (handles text before/after JSON)
        match = re.search(r'\{[\s\S]+\}', raw_clean)
        if match:
            raw_clean = match.group(0)
        return json.loads(raw_clean), raw_clean
    except Exception as e:
        return None, f"ERROR: {e}"


# ── EVAL ON FULL DATA ────────────────────────────────────────────────────────
def evaluate_on_data_sample(sample_size: int = 200) -> dict:
    """
    Run câu 3: evaluate prompt quality metrics on real data sample.
    Do not call LLM for all 3000 rows (cost/time) — sample 200 randomly.
    Metrics computed on schema/hallucination checks only (no LLM ground truth).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        f"SELECT message FROM cleaned_logs ORDER BY RANDOM() LIMIT {sample_size}"
    )
    messages = [row[0] for row in cur.fetchall()]
    conn.close()

    print(f"\n⏳ Câu 3: Đang chạy Gemini trên {sample_size} dòng log ngẫu nhiên...")

    json_valid = 0
    schema_ok = 0
    hallucination_flags = 0
    parse_status_counts = {"ok": 0, "partial": 0, "unparseable": 0, "other": 0}
    flagged_records = []

    for i, msg in enumerate(messages, 1):
        if i % 20 == 0:
            print(f"   {i}/{sample_size}...")
        parsed, raw = call_gemini(msg)
        time.sleep(1.5)  # rate limit — gemini-flash-latest has low RPM

        if parsed is None:
            continue

        json_valid += 1
        schema_issues = validate_schema(parsed)
        if not schema_issues:
            schema_ok += 1

        flags = check_hallucination(msg, parsed)
        if flags:
            hallucination_flags += 1
            flagged_records.append({"message": msg, "output": parsed, "flags": flags})

        ps = parsed.get("parse_status", "other")
        parse_status_counts[ps if ps in parse_status_counts else "other"] += 1

    total = len(messages)
    return {
        "total_sampled": total,
        "json_validity_rate": f"{json_valid/total*100:.1f}%",
        "schema_compliance_rate": f"{schema_ok/total*100:.1f}%",
        "hallucination_rate": f"{hallucination_flags/total*100:.1f}%",
        "parse_status_dist": parse_status_counts,
        "flagged_samples": flagged_records[:5],  # show up to 5
    }


# ── TC RUNNER ────────────────────────────────────────────────────────────────
def run_test_cases() -> list:
    print("\n⏳ Câu 4: Đang chạy 5 test cases qua Gemini...")
    results = []
    for tc in TEST_CASES:
        parsed, raw = call_gemini(tc["message"])
        time.sleep(2.0)  # rate limit

        if parsed is None:
            verdict = "❌ LLM call failed"
            details = raw
        else:
            schema_issues = validate_schema(parsed)
            hal_flags = check_hallucination(tc["message"], parsed)
            exp = tc["expected"]

            field_matches = {}
            for f in REQUIRED_FIELDS:
                field_matches[f] = parsed.get(f) == exp.get(f)

            all_match = all(field_matches.values())
            verdict = "✅ PASS" if (all_match and not hal_flags) else "⚠️ PARTIAL" if not hal_flags else "❌ HALLUCINATION"
            details = {
                "raw_output": raw,
                "field_match": field_matches,
                "schema_issues": schema_issues,
                "hallucination_flags": hal_flags,
            }

        results.append({
            "id": tc["id"],
            "message": tc["message"],
            "verdict": verdict,
            "details": details,
        })
        print(f"   {tc['id']}: {verdict}")
    return results


# ── REPORT WRITER ─────────────────────────────────────────────────────────────
def write_report(tc_results: list, eval_stats: dict):
    lines = [
        "# Task B — Kết Quả Chạy Thực Tế (Gemini API)\n",
        f"> **Model:** {GEMINI_MODEL} · **Temperature:** 0  \n",
        f"> **Ngày chạy:** {time.strftime('%d/%m/%Y %H:%M')}\n",
        "\n---\n",
        "## Câu 4 — Kết Quả 5 Test Case\n",
    ]

    for r in tc_results:
        lines.append(f"\n### {r['id']} — {r['verdict']}\n")
        lines.append(f"**Input:** `{r['message']}`\n")
        if isinstance(r["details"], dict):
            lines.append("\n**Output thực tế từ Gemini:**\n")
            lines.append("```json\n" + r["details"].get("raw_output", "") + "\n```\n")
            fm = r["details"].get("field_match", {})
            matches = [f for f, v in fm.items() if v]
            misses  = [f for f, v in fm.items() if not v]
            if matches:
                lines.append(f"✅ Khớp: `{'`, `'.join(matches)}`  \n")
            if misses:
                lines.append(f"⚠️ Không khớp: `{'`, `'.join(misses)}`  \n")
            if r["details"].get("hallucination_flags"):
                lines.append(f"🚨 Hallucination: {r['details']['hallucination_flags']}  \n")
        else:
            lines.append(f"\n```\n{r['details']}\n```\n")

    lines += [
        "\n---\n",
        "## Câu 3 — Đánh Giá Trên Data Thật\n",
        f"**Sample:** {eval_stats['total_sampled']} dòng log ngẫu nhiên từ `cleaned_logs.db`\n\n",
        "| Tiêu chí | Kết quả |\n|:---|:---|\n",
        f"| JSON Validity Rate | {eval_stats['json_validity_rate']} |\n",
        f"| Schema Compliance Rate | {eval_stats['schema_compliance_rate']} |\n",
        f"| Hallucination Rate | {eval_stats['hallucination_rate']} |\n",
        f"| parse_status ok | {eval_stats['parse_status_dist']['ok']} |\n",
        f"| parse_status partial | {eval_stats['parse_status_dist']['partial']} |\n",
        f"| parse_status unparseable | {eval_stats['parse_status_dist']['unparseable']} |\n",
        "\n### Ví dụ các record bị flag hallucination\n",
    ]
    for sample in eval_stats.get("flagged_samples", []):
        lines.append(f"\n**Message:** `{sample['message']}`  \n")
        lines.append(f"**Flags:** {sample['flags']}  \n")
        lines.append("```json\n" + json.dumps(sample["output"], ensure_ascii=False, indent=2) + "\n```\n")

    OUT_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"\n✓ Đã ghi báo cáo: {OUT_PATH}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ Chưa set GEMINI_API_KEY. Chạy: $env:GEMINI_API_KEY='your_key'")
        sys.exit(1)

    # Câu 4: chạy 5 test case
    tc_results = run_test_cases()

    # Câu 3: evaluate trên sample data thật
    eval_stats = evaluate_on_data_sample(sample_size=30)  # 30 dòng để tiết kiệm quota

    # Ghi báo cáo
    write_report(tc_results, eval_stats)

    print("\n✨ Hoàn tất!")
