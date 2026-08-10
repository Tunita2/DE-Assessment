# Xbrain Assessment — Data Engineer (AI / Knowledge Engineering) POC

This repository contains the complete implementation, artifacts, and documentation for the Data Engineer POC (Red Star Finance - POC AI Operations Assistant), developed for the **Xbrain · TechX Corp** recruitment assessment (August 2026).

---

## 📌 Project Overview

The POC addresses two core challenges faced by Red Star Finance across 5 internal systems:
1. **Part A — Data Pipeline**: Ingesting, cleaning, validating, and transforming 7 days of raw distributed application logs (`data/app_logs_7days.jsonl`) into structured data, generating analytical reports to address operational questions, and designing a production-grade AWS architecture.
2. **Part B — Mini Knowledge Base**: Constructing a curated Knowledge Base (KB) from internal SOPs & operational documents (`data/docs/`), implementing conflict resolution across document versions, establishing a 10-question evaluation benchmark, and drafting an update SOP.
3. **Assessment Part 2 — AI Proficiency**: AI work log tracking, review of an AI-generated architecture response, and robust prompt engineering for structured log extraction.

---

## 📂 Repository Structure

```
DE-Assessment/
├── .gitignore                   # Standard git ignore rules
├── README.md                    # Project overview, run instructions, technical decisions (EN)
├── AI_WORKLOG.md                # Part 2: AI Work Log tracking verified AI interactions
├── requirements.txt             # Project dependencies
├── data/                        # Dataset provided in the assessment
│   ├── app_logs_7days.jsonl     # 7 days of raw system logs (unclean)
│   └── docs/                    # 8 operational SOP & policy documents
├── reading/                     # Methodological background documentation
│   ├── 01_chunking_basics.md    # Chunking strategies & best practices
│   └── 02_rag_eval_basics.md    # Knowledge base / RAG evaluation principles
├── pipeline/                    # Part A: Log Data Pipeline
│   ├── README.md                # Pipeline documentation & data cleaning rationale
│   ├── run_pipeline.py          # Pipeline execution entrypoint
│   ├── src/                     # Data ingestion, validator, cleaner, analytics modules
│   ├── output/                  # Clean structured dataset (Parquet / SQLite) & outputs
│   └── report_answers.md        # Detailed answers to the 4 business questions
├── kb/                          # Part B: Mini Knowledge Base
│   ├── README.md                # KB design, chunking strategy & conflict resolution mechanism
│   ├── run_kb.py                # Knowledge Base query & retrieval demonstration script
│   ├── src/                     # Document parser, chunker, indexer & retriever
│   ├── index/                   # Local index artifacts (SQLite FTS / BM25 / Vector store)
│   ├── eval/                    # 10 evaluation test questions & rubric
│   └── eval_results.md          # Benchmark test run results (min. 3 test queries)
├── design/                      # Production Cloud Architecture
│   ├── aws_architecture.md      # AWS daily batch/stream architecture diagram & description
│   └── diagrams/                # Architectural diagrams (Mermaid / PNG)
├── sop/                         # Operations & Governance
│   └── kb_update_sop.md         # SOP for KB document updates, reviews, and deprecation
└── ai_proficiency/              # Part 2: AI Proficiency Artifacts
    ├── task_a_ai_review.md      # Task A: Critical review of AI flawed response
    └── task_b_prompt_design.md  # Task B: Structured extraction prompt design & benchmark
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Tunita2/DE-Assessment.git
cd DE-Assessment

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate   # On Linux/macOS
# or: .\.venv\Scripts\Activate.ps1  # On Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### 3. How to Run Each Component

#### Running Part A (Data Pipeline)
```bash
python pipeline/run_pipeline.py
```
Outputs and reports will be generated under `pipeline/output/` and detailed in `pipeline/report_answers.md`.

#### Running Part B (Knowledge Base Query & Evaluation)
```bash
python kb/run_kb.py
```
Evaluation test runs and results are recorded in `kb/eval_results.md`.

---

## 💡 Key Architectural & Technical Decisions

- **Log Storage Format**: Chose columnar format (**Apache Parquet**) for cleaned data storage to optimize analytical query throughput, partition pruning by date/service, and storage compression ratio.
- **Data Validation & Cleaning**: Explicit rule-based sanitization handling timestamp format deviations, malformed JSON lines, null levels, and deduplication.
- **Knowledge Base Strategy**: Semantic chunking preserving document headers, version metadata tagging, and deterministic priority resolution favoring the latest authoritative SOP version.
- **AI Tooling & Verification**: Every AI-assisted code generation or drafting step is systematically audited and logged in [AI_WORKLOG.md](file:///d:/DE-assessment/AI_WORKLOG.md).

---

## 👤 Author
- **Candidate**: Data Engineering Applicant
- **Assessment**: Xbrain · TechX Corp (August 2026)
- **Repository**: [https://github.com/Tunita2/DE-Assessment.git](https://github.com/Tunita2/DE-Assessment.git)
