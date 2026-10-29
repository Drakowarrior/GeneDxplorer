"""
GeneDxplorer Reporting Package
Provides deterministic, reproducible scientific research report generation.
"""

from src.reporting.models import ResearchReport, ReportType
from src.reporting.builder import (
    build_disease_report,
    build_gene_report,
    build_comparison_report,
    build_graph_report,
    build_similarity_report,
    build_workspace_report,
    get_report_by_id,
    store_report_in_cache
)
from src.reporting.exporters import (
    export_report_html,
    export_report_json,
    export_report_genes_csv,
    export_report_evidence_csv
)
from src.reporting.summary import generate_deterministic_summary

__all__ = [
    "ResearchReport",
    "ReportType",
    "build_disease_report",
    "build_gene_report",
    "build_comparison_report",
    "build_graph_report",
    "build_similarity_report",
    "build_workspace_report",
    "get_report_by_id",
    "store_report_in_cache",
    "export_report_html",
    "export_report_json",
    "export_report_genes_csv",
    "export_report_evidence_csv",
    "generate_deterministic_summary",
]
