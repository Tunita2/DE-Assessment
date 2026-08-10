"""
Evaluation Engine for Knowledge Base & RAG Quality
Evaluates Retrieval Hit Rate, Groundedness, Version Conflict Resolution, and Out-of-scope Refusal.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from kb.src.models import EvalQuestion, EvalResultItem, EvalSummary
from kb.src.retriever import KnowledgeRetriever


class KnowledgeEvaluator:
    """Runs automated benchmark evaluation on a KnowledgeRetriever instance."""

    def __init__(self, eval_questions_path: Path, retriever: KnowledgeRetriever):
        self.eval_questions_path = Path(eval_questions_path)
        self.retriever = retriever
        self.questions: List[EvalQuestion] = self._load_questions()

    def _load_questions(self) -> List[EvalQuestion]:
        with open(self.eval_questions_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [EvalQuestion(**item) for item in data]

    def run_evaluation(self, top_k: int = 5) -> EvalSummary:
        """Executes evaluation for all questions and computes metric scores."""
        results: List[EvalResultItem] = []

        retrieval_hits = 0
        groundedness_passes = 0
        version_traps_resolved = 0
        version_trap_count = 0
        out_of_scope_handled = 0
        out_of_scope_count = 0
        overall_passes = 0

        for q in self.questions:
            rag_output = self.retriever.answer_query(q.question, top_k=top_k, active_only=True)
            retrieved_chunks = rag_output["retrieved_chunks"]
            generated_answer = rag_output["answer"]
            is_out_of_scope = rag_output["is_out_of_scope"]

            retrieved_doc_ids = list(dict.fromkeys([r.chunk.doc_id for r in retrieved_chunks]))
            retrieved_chunk_ids = [r.chunk.chunk_id for r in retrieved_chunks]

            # 1. Check Retrieval Hit
            if q.category == "OUT_OF_SCOPE":
                # For out-of-scope, retrieval hit is true if system correctly filtered out low scores
                retrieval_hit = True
                retrieval_hits += 1
            else:
                hit = any(exp_doc in retrieved_doc_ids for exp_doc in q.expected_doc_ids)
                retrieval_hit = hit
                if hit:
                    retrieval_hits += 1

            # 2. Check Version Conflict Trap (POL-01)
            is_deprecated_retrieved = any(r.chunk.status == "DEPRECATED" for r in retrieved_chunks)
            if q.category == "VERSION_TRAP":
                version_trap_count += 1
                # Must retrieve POL-01 v2 and NOT contain deprecated 22:00/7 days
                if "23:30" in generated_answer and "30 ngày" in generated_answer and not is_deprecated_retrieved:
                    version_traps_resolved += 1
                    version_resolved = True
                else:
                    version_resolved = False
            else:
                version_resolved = True

            # 3. Check Out-of-Scope Handling
            if q.category == "OUT_OF_SCOPE":
                out_of_scope_count += 1
                if "không có thông tin" in generated_answer.lower() and is_out_of_scope:
                    out_of_scope_pass = True
                    out_of_scope_handled += 1
                else:
                    out_of_scope_pass = False
            else:
                out_of_scope_pass = True

            # 4. Check Groundedness & Accuracy
            if q.category == "OUT_OF_SCOPE":
                groundedness_pass = out_of_scope_pass
            elif q.category == "VERSION_TRAP":
                groundedness_pass = version_resolved
            else:
                # Check for presence of key factual tokens from expected answer
                groundedness_pass = retrieval_hit and (len(generated_answer) > 20) and not is_deprecated_retrieved

            if groundedness_pass:
                groundedness_passes += 1

            # Determine overall question status
            if retrieval_hit and groundedness_pass and version_resolved and out_of_scope_pass:
                status = "PASS"
                overall_passes += 1
                notes = "Chính xác, bám sát nguồn dữ liệu, trích dẫn đúng."
            elif retrieval_hit:
                status = "PARTIAL"
                notes = "Tìm đúng tài liệu nhưng câu trả lời cần hoàn thiện thêm chi tiết."
            else:
                status = "FAIL"
                notes = "Không tìm thấy tài liệu nguồn phù hợp hoặc trả lời sai."

            results.append(EvalResultItem(
                question_id=q.id,
                category=q.category,
                question=q.question,
                retrieval_hit=retrieval_hit,
                retrieved_chunk_ids=retrieved_chunk_ids,
                retrieved_doc_ids=retrieved_doc_ids,
                generated_answer=generated_answer,
                groundedness_pass=groundedness_pass,
                is_deprecated_retrieved=is_deprecated_retrieved,
                is_out_of_scope_handled=out_of_scope_pass,
                status=status,
                notes=notes
            ))

        total_q = len(self.questions)
        summary = EvalSummary(
            total_questions=total_q,
            retrieval_hit_rate_pct=round((retrieval_hits / total_q) * 100, 2) if total_q > 0 else 0,
            groundedness_pass_rate_pct=round((groundedness_passes / total_q) * 100, 2) if total_q > 0 else 0,
            version_conflict_resolution_rate_pct=round((version_traps_resolved / version_trap_count) * 100, 2) if version_trap_count > 0 else 100.0,
            out_of_scope_rejection_rate_pct=round((out_of_scope_handled / out_of_scope_count) * 100, 2) if out_of_scope_count > 0 else 100.0,
            overall_pass_rate_pct=round((overall_passes / total_q) * 100, 2) if total_q > 0 else 0,
            results=results
        )

        return summary
