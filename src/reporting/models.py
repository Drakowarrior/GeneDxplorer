"""
GeneDxplorer — Phase 10 Research Report Data Models

Provides structured, serializable models for deterministic research reports.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class ReportType(str, Enum):
    DISEASE = "disease"
    GENE = "gene"
    COMPARISON = "comparison"
    SIMILARITY = "similarity"
    GRAPH = "graph"
    WORKSPACE = "workspace"

@dataclass
class ReportMetadata:
    report_id: str
    report_type: ReportType
    title: str
    generated_at: str
    software_version: str
    query: str
    source: str = "NCBI MedGen"
    retrieval_timestamp: str = ""

@dataclass
class AnalysisScope:
    records_available: int = 0
    records_retrieved: int = 0
    records_analyzed: int = 0
    analysis_limit: int = 500
    search_strategy: str = "exact_title_or_broad_fallback"

@dataclass
class DataQualityMetrics:
    records_with_genes: int = 0
    records_without_genes: int = 0
    total_relationships: int = 0
    unique_genes: int = 0
    duplicate_occurrences_removed: int = 0

@dataclass
class KnowledgeGraphSummary:
    disease_nodes: int = 0
    gene_nodes: int = 0
    record_nodes: int = 0
    direct_relationships: int = 0

@dataclass
class ResearchReport:
    metadata: ReportMetadata
    scope: AnalysisScope
    data_quality: DataQualityMetrics
    gene_analysis: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    comparison: Optional[Dict[str, Any]] = None
    similarity_matrix: Optional[Dict[str, Any]] = None
    knowledge_graph: Optional[KnowledgeGraphSummary] = None
    executive_summary: str = ""
    disclaimer: str = ""
    limitations: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report model into serializable dictionary."""
        return {
            "metadata": asdict(self.metadata),
            "scope": asdict(self.scope),
            "data_quality": asdict(self.data_quality),
            "gene_analysis": self.gene_analysis,
            "evidence": self.evidence,
            "comparison": self.comparison,
            "similarity_matrix": self.similarity_matrix,
            "knowledge_graph": asdict(self.knowledge_graph) if self.knowledge_graph else None,
            "executive_summary": self.executive_summary,
            "disclaimer": self.disclaimer,
            "limitations": self.limitations,
            "provenance": self.provenance,
        }
