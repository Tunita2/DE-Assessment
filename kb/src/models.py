"""
Data Models for Mini Knowledge Base & RAG Evaluation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """Represents an indexed chunk with rich operational metadata."""
    chunk_id: str = Field(..., description="Unique ID format: {doc_id}_{sec_id}")
    doc_id: str = Field(..., description="Document identifier, e.g., FAQ-01, POL-01")
    doc_title: str = Field(..., description="Full document title")
    chunk_type: str = Field("SECTION", description="'HEADER_SUMMARY' or 'SECTION'")
    section_id: str = Field(..., description="Section identifier/number, e.g., 'header', 'sec_01'")
    section_title: str = Field(..., description="Section heading title")
    content: str = Field(..., description="Text content of the chunk")
    version: str = Field("1.0", description="Document version string, e.g., '1.0', '2.0'")
    effective_date: str = Field(..., description="Effective date, e.g., '05/2026'")
    status: str = Field("ACTIVE", description="'ACTIVE' or 'DEPRECATED'")
    owner: str = Field("Phòng CNTT", description="Document owner/department")
    keywords: List[str] = Field(default_factory=list, description="Extracted search keywords and tags")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class RetrievalResult(BaseModel):
    """Result returned by the search / retrieval engine."""
    chunk: KnowledgeChunk
    score: float = Field(..., description="Relevance score (BM25 / Hybrid)")
    is_active: bool = Field(True, description="Whether the chunk is currently active")


class EvalQuestion(BaseModel):
    """Evaluation question definition."""
    id: str = Field(..., description="Question identifier, e.g., 'EVAL-01'")
    category: str = Field(..., description="Question archetype: DIRECT_LOOKUP, MULTI_SOURCE, VERSION_TRAP, OUT_OF_SCOPE, OVERVIEW")
    question: str = Field(..., description="User prompt / question text")
    expected_answer: str = Field(..., description="Ground truth answer summary")
    expected_doc_ids: List[str] = Field(..., description="List of target doc_ids expected to be retrieved")
    expected_section_hints: List[str] = Field(default_factory=list, description="Section hints for retrieval hit check")
    groundedness_criteria: str = Field(..., description="Criteria for assessing groundedness and lack of hallucination")


class EvalResultItem(BaseModel):
    """Result for an individual evaluation question."""
    question_id: str
    category: str
    question: str
    retrieval_hit: bool
    retrieved_chunk_ids: List[str]
    retrieved_doc_ids: List[str]
    generated_answer: str
    groundedness_pass: bool
    is_deprecated_retrieved: bool
    is_out_of_scope_handled: bool
    status: str  # "PASS", "PARTIAL", "FAIL"
    notes: str


class EvalSummary(BaseModel):
    """Overall evaluation summary metrics."""
    total_questions: int
    retrieval_hit_rate_pct: float
    groundedness_pass_rate_pct: float
    version_conflict_resolution_rate_pct: float
    out_of_scope_rejection_rate_pct: float
    overall_pass_rate_pct: float
    results: List[EvalResultItem]
