"""
GeneDxplorer — Phase 10 Provenance & Scientific Safeguards

Manages audit trails, metadata tracking, and standardized scientific limitations.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from src.config import config

STANDARD_LIMITATIONS = [
    "GeneDxplorer analyzes reporting frequencies within retrieved NCBI MedGen DocumentSummary XML records.",
    "Record Percentage describes reporting frequency across analyzed MedGen records and does NOT establish biological causality, disease severity, or diagnostic certainty.",
    "Relationships are restricted to direct <AssociatedGenes> XML annotations; free-text mentions and unannotated literature are excluded.",
    "Gene-set similarity metrics (Jaccard Similarity and Overlap Coefficient) are standard mathematical set calculations and do NOT imply clinical or etiology equivalence.",
    "Analysis results depend on the specified retrieval limit (ANALYSIS_LIMIT) and current NCBI MedGen indexing state.",
]

def build_provenance_record(
    query: str,
    search_strategy: str = "exact_title_or_broad_fallback",
    retrieved_at: str = "",
    extra_sources: List[str] = None
) -> Dict[str, Any]:
    """
    Construct a complete, secure provenance payload for auditability.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    sources = ["NCBI MedGen"]
    if extra_sources:
        for s in extra_sources:
            if s and s not in sources:
                sources.append(s)

    return {
        "software_name": "GeneDxplorer — Disease-Gene Relationship Explorer",
        "software_version": config.GENEDXPLORER_VERSION,
        "query": query,
        "sources": sources,
        "search_strategy": search_strategy,
        "analysis_limit": config.ANALYSIS_LIMIT,
        "retrieved_at": retrieved_at or now_iso,
        "report_generated_at": now_iso,
        "reproducibility_note": (
            "This report is deterministically constructed from verified NCBI MedGen record annotations. "
            "Identical query parameters and cache states produce identical numerical outputs."
        )
    }

def get_standard_limitations() -> List[str]:
    """Return standard scientific limitations array."""
    return list(STANDARD_LIMITATIONS)
