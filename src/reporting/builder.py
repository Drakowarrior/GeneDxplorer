"""
GeneDxplorer — Phase 10 Research Report Builder

Constructs deterministic ResearchReport instances from existing analysis, graph,
similarity, and workspace data models.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.config import config
from src.cache import cache
from src.medgen import search_medgen, search_medgen_by_gene, fetch_medgen_records_xml
from src.parser import parse_medgen_xml
from src.analysis import (
    analyze_disease_genes,
    analyze_gene_to_disease,
    compare_diseases,
    build_disease_evidence_payload,
    build_gene_evidence_payload
)
from src.graph import build_disease_knowledge_graph, build_gene_knowledge_graph
from src.similarity import calculate_multi_disease_similarity
from src.reporting.models import (
    ResearchReport,
    ReportMetadata,
    ReportType,
    AnalysisScope,
    DataQualityMetrics,
    KnowledgeGraphSummary
)
from src.reporting.provenance import build_provenance_record, get_standard_limitations
from src.reporting.summary import generate_deterministic_summary

logger = logging.getLogger("genedxplorer.reporting")

REPORT_CACHE_PREFIX = "report_store:"

def store_report_in_cache(report: ResearchReport) -> None:
    """Store report in cache under its report_id."""
    key = f"{REPORT_CACHE_PREFIX}{report.metadata.report_id}"
    cache.set(key, report.to_dict(), ttl=config.CACHE_TTL * 2)

def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored report by report_id."""
    key = f"{REPORT_CACHE_PREFIX}{report_id}"
    return cache.get(key)


def build_disease_report(disease_name: str, max_records: Optional[int] = None) -> ResearchReport:
    """Build a deterministic ResearchReport for a disease."""
    clean_name = disease_name.strip()
    limit = max_records or config.ANALYSIS_LIMIT
    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"report_d_{uuid.uuid4().hex[:12]}"

    # Fetch records or use cache
    total_search_results, title_count, uids, strategy = search_medgen(clean_name, max_limit=limit)
    xml_data = fetch_medgen_records_xml(uids) if uids else ""
    parsed_res = parse_medgen_xml(xml_data) if xml_data else ([], {})
    records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res


    df_genes, payload = analyze_disease_genes(records, clean_name, total_search_results)
    evidence_payload = build_disease_evidence_payload(records, clean_name, total_search_results, strategy, len(uids), {})

    top_gene_symbol = None
    top_gene_count = None
    top_gene_pct = None
    if payload.get("genes"):
        first_g = payload["genes"][0]
        top_gene_symbol = first_g.get("Gene")
        top_gene_count = first_g.get("Record Count")
        top_gene_pct = first_g.get("Record_Percentage")

    summary_text = generate_deterministic_summary("disease", {
        "query": clean_name,
        "records_analyzed": payload.get("records_analyzed", 0),
        "records_with_genes": payload.get("records_with_genes", 0),
        "unique_genes": payload.get("unique_genes", 0),
        "top_gene_symbol": top_gene_symbol,
        "top_gene_count": top_gene_count,
        "top_gene_pct": top_gene_pct
    })

    metadata = ReportMetadata(
        report_id=report_id,
        report_type=ReportType.DISEASE,
        title=f"Disease Research Report: {clean_name}",
        generated_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        query=clean_name,
        source="NCBI MedGen",
        retrieval_timestamp=now_iso
    )

    scope = AnalysisScope(
        records_available=total_search_results,
        records_retrieved=len(uids),
        records_analyzed=payload.get("records_analyzed", 0),
        analysis_limit=limit,
        search_strategy=strategy
    )

    quality = DataQualityMetrics(
        records_with_genes=payload.get("records_with_genes", 0),
        records_without_genes=payload.get("records_analyzed", 0) - payload.get("records_with_genes", 0),
        total_relationships=payload.get("total_relationships", 0),
        unique_genes=payload.get("unique_genes", 0)
    )

    # Optional Graph Summary
    graph_data = build_disease_knowledge_graph(clean_name, max_genes=10, include_records=True)
    kg_summary = KnowledgeGraphSummary(
        disease_nodes=graph_data.get("summary", {}).get("disease_nodes", 1),
        gene_nodes=graph_data.get("summary", {}).get("gene_nodes", 0),
        record_nodes=graph_data.get("summary", {}).get("record_nodes", 0),
        direct_relationships=graph_data.get("summary", {}).get("direct_relationships", 0)
    )

    report = ResearchReport(
        metadata=metadata,
        scope=scope,
        data_quality=quality,
        gene_analysis=payload.get("genes", []),
        evidence=evidence_payload.get("evidence", []),
        knowledge_graph=kg_summary,
        executive_summary=summary_text,
        disclaimer=(
            "This report is generated deterministically from directAssociatedGenes annotations in NCBI MedGen. "
            "Reporting frequencies describe data presence in MedGen records and do NOT establish disease causality, severity, or diagnosis."
        ),
        limitations=get_standard_limitations(),
        provenance=build_provenance_record(clean_name, strategy, now_iso)
    )

    store_report_in_cache(report)
    return report


def build_gene_report(gene_symbol: str) -> ResearchReport:
    """Build a deterministic ResearchReport for a gene."""
    symbol = gene_symbol.strip().upper()
    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"report_g_{uuid.uuid4().hex[:12]}"

    total_search_results, uids, strategy = search_medgen_by_gene(symbol, max_limit=config.ANALYSIS_LIMIT)
    xml_data = fetch_medgen_records_xml(uids) if uids else ""
    parsed_res = parse_medgen_xml(xml_data) if xml_data else ([], {})
    records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res

    df_diseases, payload = analyze_gene_to_disease(symbol, records, total_search_results)
    evidence_payload = build_gene_evidence_payload(symbol, records, total_search_results, strategy)

    matching_count = payload.get("matching_disease_count", 0)
    unique_diseases = len(set(d["title"] for d in payload.get("disease_records", [])))

    summary_text = generate_deterministic_summary("gene", {
        "gene_symbol": symbol,
        "ncbi_gene_id": payload.get("ncbi_gene_id", "N/A"),
        "records_examined": payload.get("records_examined", 0),
        "matching_disease_count": matching_count,
        "unique_diseases": unique_diseases
    })

    metadata = ReportMetadata(
        report_id=report_id,
        report_type=ReportType.GENE,
        title=f"Gene Research Report: {symbol}",
        generated_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        query=symbol,
        source="NCBI MedGen",
        retrieval_timestamp=now_iso
    )

    scope = AnalysisScope(
        records_available=total_search_results,
        records_retrieved=len(uids),
        records_analyzed=payload.get("records_examined", 0),
        analysis_limit=config.ANALYSIS_LIMIT,
        search_strategy=strategy
    )

    quality = DataQualityMetrics(
        records_with_genes=matching_count,
        records_without_genes=payload.get("records_examined", 0) - matching_count,
        total_relationships=matching_count,
        unique_genes=1
    )

    graph_data = build_gene_knowledge_graph(symbol, max_diseases=10, include_records=True)
    kg_summary = KnowledgeGraphSummary(
        disease_nodes=graph_data.get("summary", {}).get("disease_nodes", 0),
        gene_nodes=1,
        record_nodes=graph_data.get("summary", {}).get("record_nodes", 0),
        direct_relationships=graph_data.get("summary", {}).get("direct_relationships", 0)
    )

    report = ResearchReport(
        metadata=metadata,
        scope=scope,
        data_quality=quality,
        gene_analysis=[{"Gene": symbol, "NCBI_Gene_ID": payload.get("ncbi_gene_id"), "Matching_Diseases": matching_count}],
        evidence=evidence_payload.get("evidence", []),
        knowledge_graph=kg_summary,
        executive_summary=summary_text,
        disclaimer="Gene association reports describe reported MedGen annotations and do not imply clinical causality.",
        limitations=get_standard_limitations(),
        provenance=build_provenance_record(symbol, strategy, now_iso)
    )

    store_report_in_cache(report)
    return report


def build_comparison_report(disease_a: str, disease_b: str) -> ResearchReport:
    """Build a deterministic ResearchReport for pairwise disease comparison."""
    clean_a = disease_a.strip()
    clean_b = disease_b.strip()
    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"report_c_{uuid.uuid4().hex[:12]}"

    total_a, title_count_a, uids_a, strat_a = search_medgen(clean_a, max_limit=config.ANALYSIS_LIMIT)
    xml_a = fetch_medgen_records_xml(uids_a) if uids_a else ""
    parsed_a = parse_medgen_xml(xml_a) if xml_a else ([], {})
    recs_a = parsed_a[0] if isinstance(parsed_a, tuple) else parsed_a

    total_b, title_count_b, uids_b, strat_b = search_medgen(clean_b, max_limit=config.ANALYSIS_LIMIT)
    xml_b = fetch_medgen_records_xml(uids_b) if uids_b else ""
    parsed_b = parse_medgen_xml(xml_b) if xml_b else ([], {})
    recs_b = parsed_b[0] if isinstance(parsed_b, tuple) else parsed_b

    comp_payload = compare_diseases(clean_a, recs_a, total_a, clean_b, recs_b, total_b)



    summary_text = generate_deterministic_summary("comparison", {
        "disease_a": clean_a,
        "disease_b": clean_b,
        "genes_count_a": comp_payload["disease_a_metrics"]["unique_genes"],
        "genes_count_b": comp_payload["disease_b_metrics"]["unique_genes"],
        "shared_count": comp_payload["metrics"]["shared_genes_count"],
        "jaccard_pct": comp_payload["metrics"]["jaccard_similarity_pct"],
        "overlap_coeff_pct": comp_payload["metrics"]["overlap_coefficient_pct"]
    })

    metadata = ReportMetadata(
        report_id=report_id,
        report_type=ReportType.COMPARISON,
        title=f"Disease Comparison Report: {clean_a} vs {clean_b}",
        generated_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        query=f"{clean_a} vs {clean_b}",
        source="NCBI MedGen",
        retrieval_timestamp=now_iso
    )

    scope = AnalysisScope(
        records_available=total_a + total_b,
        records_retrieved=len(uids_a) + len(uids_b),
        records_analyzed=len(recs_a) + len(recs_b),
        analysis_limit=config.ANALYSIS_LIMIT
    )

    quality = DataQualityMetrics(
        records_with_genes=comp_payload["disease_a_metrics"]["records_with_genes"] + comp_payload["disease_b_metrics"]["records_with_genes"],
        records_without_genes=(len(recs_a) + len(recs_b)) - (comp_payload["disease_a_metrics"]["records_with_genes"] + comp_payload["disease_b_metrics"]["records_with_genes"]),
        total_relationships=len(comp_payload.get("shared_genes", [])) + len(comp_payload.get("unique_to_a", [])) + len(comp_payload.get("unique_to_b", [])),
        unique_genes=comp_payload["metrics"]["union_genes_count"]
    )

    report = ResearchReport(
        metadata=metadata,
        scope=scope,
        data_quality=quality,
        comparison=comp_payload,
        executive_summary=summary_text,
        disclaimer="Jaccard set similarity describes reporting overlap in MedGen and is NOT clinical similarity.",
        limitations=get_standard_limitations(),
        provenance=build_provenance_record(f"{clean_a} vs {clean_b}", "pairwise_comparison", now_iso)
    )

    store_report_in_cache(report)
    return report


def build_similarity_report(disease_names: List[str]) -> ResearchReport:
    """Build a deterministic ResearchReport for a multi-disease similarity matrix."""
    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"report_s_{uuid.uuid4().hex[:12]}"

    sim_payload = calculate_multi_disease_similarity(disease_names, max_records=100)
    top_pair = sim_payload.get("ranked_pairs", [None])[0] if sim_payload.get("ranked_pairs") else None

    summary_text = generate_deterministic_summary("similarity", {
        "disease_count": sim_payload.get("disease_count", 0),
        "top_pair": top_pair
    })

    metadata = ReportMetadata(
        report_id=report_id,
        report_type=ReportType.SIMILARITY,
        title=f"Multi-Disease Similarity Matrix Report ({sim_payload.get('disease_count', 0)} Diseases)",
        generated_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        query=", ".join(disease_names),
        source="NCBI MedGen",
        retrieval_timestamp=now_iso
    )

    scope = AnalysisScope(
        records_available=sum(d.get("records_analyzed", 0) for d in sim_payload.get("diseases", [])),
        records_analyzed=sum(d.get("records_analyzed", 0) for d in sim_payload.get("diseases", [])),
        analysis_limit=100
    )

    quality = DataQualityMetrics(
        unique_genes=sum(d.get("unique_genes", 0) for d in sim_payload.get("diseases", []))
    )

    report = ResearchReport(
        metadata=metadata,
        scope=scope,
        data_quality=quality,
        similarity_matrix=sim_payload,
        executive_summary=summary_text,
        disclaimer="Multi-disease similarity matrix metrics represent standard set overlap of reported MedGen annotations.",
        limitations=get_standard_limitations(),
        provenance=build_provenance_record(", ".join(disease_names), "multi_disease_similarity", now_iso)
    )

    store_report_in_cache(report)
    return report


def build_graph_report(disease_name_or_symbol: str, node_type: str = "disease") -> ResearchReport:
    """Build a deterministic ResearchReport for a Knowledge Graph."""
    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"report_k_{uuid.uuid4().hex[:12]}"

    if node_type.lower() == "gene":
        graph_data = build_gene_knowledge_graph(disease_name_or_symbol)
    else:
        graph_data = build_disease_knowledge_graph(disease_name_or_symbol)

    summary_text = generate_deterministic_summary("graph", {
        "query": disease_name_or_symbol,
        "disease_nodes": graph_data.get("summary", {}).get("disease_nodes", 0),
        "gene_nodes": graph_data.get("summary", {}).get("gene_nodes", 0),
        "record_nodes": graph_data.get("summary", {}).get("record_nodes", 0),
        "direct_rels": graph_data.get("summary", {}).get("direct_relationships", 0)
    })

    metadata = ReportMetadata(
        report_id=report_id,
        report_type=ReportType.GRAPH,
        title=f"Knowledge Graph Research Report: {disease_name_or_symbol}",
        generated_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        query=disease_name_or_symbol,
        source="NCBI MedGen",
        retrieval_timestamp=now_iso
    )

    kg_summary = KnowledgeGraphSummary(
        disease_nodes=graph_data.get("summary", {}).get("disease_nodes", 0),
        gene_nodes=graph_data.get("summary", {}).get("gene_nodes", 0),
        record_nodes=graph_data.get("summary", {}).get("record_nodes", 0),
        direct_relationships=graph_data.get("summary", {}).get("direct_relationships", 0)
    )

    report = ResearchReport(
        metadata=metadata,
        scope=AnalysisScope(),
        data_quality=DataQualityMetrics(total_relationships=graph_data.get("summary", {}).get("direct_relationships", 0)),
        knowledge_graph=kg_summary,
        evidence=graph_data.get("edges", []),
        executive_summary=summary_text,
        disclaimer="Knowledge graph connections represent reported annotations in NCBI MedGen.",
        limitations=get_standard_limitations(),
        provenance=build_provenance_record(disease_name_or_symbol, "knowledge_graph", now_iso)
    )

    store_report_in_cache(report)
    return report


def build_workspace_report(workspace_payload: Dict[str, Any]) -> ResearchReport:
    """Build a deterministic ResearchReport for selected/saved Research Workspace findings."""
    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = f"report_w_{uuid.uuid4().hex[:12]}"

    diseases = workspace_payload.get("diseases", [])
    genes = workspace_payload.get("genes", [])
    comparisons = workspace_payload.get("comparisons", [])
    records = workspace_payload.get("records", [])
    graph_nodes = workspace_payload.get("graph_nodes", [])
    graph_edges = workspace_payload.get("graph_edges", [])
    similarity_matrices = workspace_payload.get("similarity_matrices", [])
    notes = workspace_payload.get("notes", [])

    summary_text = generate_deterministic_summary("workspace", {
        "saved_diseases_count": len(diseases),
        "saved_genes_count": len(genes),
        "saved_comparisons_count": len(comparisons),
        "saved_records_count": len(records),
        "saved_nodes_count": len(graph_nodes),
        "saved_edges_count": len(graph_edges),
        "saved_matrices_count": len(similarity_matrices),
        "notes_count": len(notes)
    })

    metadata = ReportMetadata(
        report_id=report_id,
        report_type=ReportType.WORKSPACE,
        title="Research Workspace Integrated Report",
        generated_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        query="Research Workspace",
        source="NCBI MedGen",
        retrieval_timestamp=now_iso
    )

    scope = AnalysisScope(
        records_analyzed=len(records) + len(diseases) + len(genes)
    )

    quality = DataQualityMetrics(
        unique_genes=len(genes)
    )

    report = ResearchReport(
        metadata=metadata,
        scope=scope,
        data_quality=quality,
        gene_analysis=genes,
        evidence=records,
        comparison={"comparisons": comparisons, "similarity_matrices": similarity_matrices, "notes": notes},
        executive_summary=summary_text,
        disclaimer="Workspace report summarizes items saved locally by the user during exploration.",
        limitations=get_standard_limitations(),
        provenance=build_provenance_record("Research Workspace", "user_workspace_export", now_iso)
    )

    store_report_in_cache(report)
    return report
