# Xbrain Assessment — Data Engineer (AI / Knowledge Engineering) POC

Repository chứa toàn bộ code, tài liệu và artifact cho bài đánh giá Data Engineer POC tại
**Xbrain · TechX Corp** (tháng 8/2026), xây dựng xung quanh tình huống vận hành giả định của
**Công ty Tài chính Sao Đỏ** (công ty hư cấu phục vụ đề bài).

---

## ⚠️ Minh Bạch Về Quá Trình Thực Hiện

Một số điểm cần nêu rõ để người đọc/chấm hiểu đúng mức độ:

- **Toàn bộ code và thiết kế đều có sự hỗ trợ của AI** (Gemini/Claude). Mỗi lần AI tạo ra
  code hoặc nội dung đều được ghi lại trong [`AI_WORKLOG.md`](AI_WORKLOG.md) kèm đánh giá và
  cách kiểm chứng thực tế.

- **Các test case (eval questions)** trong `kb/eval/eval_questions.json` được AI sinh ra bằng
  cách đọc qua nội dung KB và file log JSONL — chưa được đối chiếu kỹ từng câu và kiểm tra
  độc lập bởi human. Điều này có nghĩa bộ benchmark có thể mang tính circular (câu hỏi được
  thiết kế biết trước KB), chưa phản ánh độc lập chất lượng retrieval trong thực tế.

- **SOP cập nhật KB** (`sop/kb_update_sop.md`) mô tả quy trình chuẩn 6 bước cho một tổ chức
  thực sự. Trong ngữ cảnh bài thi này, quy trình đó chưa được vận hành thực tế; đây là tài
  liệu thiết kế/template.

- **Kết quả benchmark 100%** của KB đạt được sau nhiều lần refactor prompt và code retriever —
  không phải lần chạy đầu tiên. Quá trình debug được ghi trong worklog.

---

## 📌 Tổng Quan Bài Làm

Bài giải gồm 3 phần chính:

1. **Phần A — Data Pipeline**: Ingest, làm sạch, validate 7 ngày log thô
   (`data/app_logs_7days.jsonl`), xuất Parquet + SQLite, trả lời 4 câu hỏi nghiệp vụ,
   thiết kế kiến trúc AWS production.

2. **Phần B — Mini Knowledge Base**: Xây dựng KB từ 8 tài liệu vận hành nội bộ (`data/docs/`),
   tích hợp conflict resolution đa phiên bản, benchmark 10 câu hỏi, viết SOP cập nhật.

3. **AI Proficiency**: Worklog 18 mục theo dõi tương tác AI, bản review lỗi thiết kế
   AI (Task A), thiết kế prompt trích xuất log (Task B) và chạy thực tế qua LLM.

---

## 📂 Cấu Trúc Repository (Thực Tế)

```
DE-Assessment/
├── README.md                    # File này
├── AI_WORKLOG.md                # Log 18 tương tác AI có kiểm chứng
├── requirements.txt             # Dependencies Python
│
├── data/                        # Dataset đề bài cung cấp
│   ├── app_logs_7days.jsonl     # ~3.000 dòng log thô (unclean)
│   └── docs/                    # 8 tài liệu vận hành SOP/GUIDE/FAQ/POL
│
├── pipeline/                    # Phần A: Log Data Pipeline
│   ├── run_pipeline.py          # Entrypoint chạy toàn bộ pipeline
│   ├── src/                     # ingest, validator, storage, analytics
│   ├── output/                  # clean_logs.parquet, clean_logs.db, quarantine_logs.jsonl
│   └── report_answers.md        # Câu trả lời 4 câu hỏi nghiệp vụ
│
├── kb/                          # Phần B: Mini Knowledge Base
│   ├── run_kb.py                # Chạy query + evaluation demo
│   ├── src/                     # chunker, indexer, retriever, evaluator
│   ├── eval/
│   │   └── eval_questions.json  # 10 câu hỏi benchmark (AI-generated — xem lưu ý trên)
│   ├── output/                  # chunks.json, knowledge_base.db (SQLite FTS5)
│   ├── tests/                   # 16 unit tests
│   └── eval_results.md          # Kết quả chạy benchmark thực tế
│
├── design/
│   └── aws_architecture.md      # Kiến trúc AWS (Lean Serverless + Phase 2)
│
├── sop/
│   └── kb_update_sop.md         # Template SOP 6 bước cập nhật KB (chưa vận hành thực tế)
│
└── ai_proficiency/
    ├── task_a_ai_review.md       # Task A: Review 7 lỗi thiết kế trong câu trả lời AI
    ├── task_b_prompt_design.md   # Task B: Prompt + 5 TC + eval framework
    ├── task_b_eval_results.md    # Kết quả thực tế (1/5 PASS, 4/5 PARTIAL — claude-sonnet-4-6)
    └── run_task_b_eval.py        # Script eval tự động (Gemini API — chưa chạy được do quota)
```

---

## 🚀 Hướng Dẫn Chạy

### Yêu cầu
- Python 3.10+

### Cài đặt
```bash
git clone https://github.com/Tunita2/DE-Assessment.git
cd DE-Assessment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
```

### Chạy Phần A — Pipeline
```bash
python pipeline/run_pipeline.py
```
Output: `pipeline/output/` (Parquet, SQLite, quarantine log). Báo cáo: `pipeline/report_answers.md`.

### Chạy Phần B — Knowledge Base
```bash
python kb/run_kb.py
```
Chạy 10 câu hỏi benchmark và ghi kết quả vào `kb/eval_results.md`.

---

## 💡 Quyết Định Kỹ Thuật Chính

| Quyết định | Lựa chọn | Lý do |
|:---|:---|:---|
| Lưu trữ log sạch | Apache Parquet (Snappy) + SQLite | Parquet cho phân tích column, SQLite cho query ad-hoc và FTS5 |
| Xử lý log lỗi | Quarantine JSONL riêng | Không làm bẩn bảng sạch, audit được, reprocess được |
| Conflict resolution KB | Semver comparison + DEPRECATED flag | Tự động, không hardcode tên file |
| KB retrieval | BM25/FTS5 lexical scoring | Phù hợp với KB nhỏ, không cần vector embedding |
| Chống hallucination (Task B) | Substring grounding check | Baseline đơn giản, có cả false-positive và false-negative — cần human review |

---

## 👤 Thông Tin

- **Ứng viên**: Data Engineering Applicant
- **Đơn vị**: Xbrain · TechX Corp (tháng 8/2026)
- **Repository**: [https://github.com/Tunita2/DE-Assessment.git](https://github.com/Tunita2/DE-Assessment.git)
