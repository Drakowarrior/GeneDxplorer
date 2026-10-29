"""
GeneDxplorer — Phase 10 Deterministic Summary Generator

Generates precise, scientifically auditable natural language summaries directly from
numerical and structural data variables. NO LLM or generative AI is used.
"""

from typing import Dict, Any, List, Optional

def generate_disease_summary(
    query: str,
    records_analyzed: int,
    records_with_genes: int,
    unique_genes: int,
    top_gene_symbol: Optional[str] = None,
    top_gene_count: Optional[int] = None,
    top_gene_pct: Optional[float] = None
) -> str:
    """
    Generate deterministic disease research summary.
    """
    top_gene_clause = ""
    if top_gene_symbol and top_gene_count is not None and top_gene_pct is not None:
        top_gene_clause = (
            f" Among the analyzed records, '{top_gene_symbol}' was the most frequently reported associated gene, "
            f"appearing in {top_gene_count} record(s) ({top_gene_pct}%)."
        )

    summary = (
        f"GeneDxplorer analyzed {records_analyzed} NCBI MedGen record(s) matching '{query}'. "
        f"{records_with_genes} record(s) contained structured direct gene annotations, "
        f"yielding {unique_genes} unique reported associated gene(s).{top_gene_clause}"
    )
    return summary


def generate_gene_summary(
    gene_symbol: str,
    ncbi_gene_id: str,
    records_examined: int,
    matching_disease_count: int,
    unique_diseases: int
) -> str:
    """
    Generate deterministic gene research summary.
    """
    id_str = f" (NCBI Gene ID: {ncbi_gene_id})" if ncbi_gene_id and ncbi_gene_id != "N/A" else ""
    summary = (
        f"GeneDxplorer evaluated gene '{gene_symbol}'{id_str} across {records_examined} NCBI MedGen record(s). "
        f"Identified {matching_disease_count} verified record association(s) across {unique_diseases} unique disease concept(s) "
        f"where '{gene_symbol}' was directly reported in structured AssociatedGenes annotations."
    )
    return summary


def generate_comparison_summary(
    disease_a: str,
    disease_b: str,
    genes_count_a: int,
    genes_count_b: int,
    shared_count: int,
    jaccard_pct: float,
    overlap_coeff_pct: float
) -> str:
    """
    Generate deterministic disease comparison summary.
    """
    summary = (
        f"GeneDxplorer compared analyzed gene sets for '{disease_a}' ({genes_count_a} gene(s)) and '{disease_b}' ({genes_count_b} gene(s)). "
        f"The comparison identified {shared_count} shared reported associated gene(s), resulting in a Jaccard gene-set similarity "
        f"of {jaccard_pct}% and an Overlap Coefficient of {overlap_coeff_pct}%."
    )
    return summary


def generate_similarity_matrix_summary(
    disease_count: int,
    top_pair: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate deterministic multi-disease similarity matrix summary.
    """
    top_clause = ""
    if top_pair:
        top_clause = (
            f" Among the analyzed pairs, '{top_pair.get('disease_a')}' and '{top_pair.get('disease_b')}' "
            f"exhibited the highest Jaccard gene-set overlap ({top_pair.get('jaccard_similarity')}%, {top_pair.get('shared_gene_count')} shared gene(s))."
        )

    summary = (
        f"GeneDxplorer computed a pairwise Jaccard gene-set similarity matrix across {disease_count} diseases.{top_clause} "
        f"These metrics represent standard set-theoretic overlap of reported MedGen annotations."
    )
    return summary


def generate_graph_summary(
    query: str,
    disease_nodes: int,
    gene_nodes: int,
    record_nodes: int,
    direct_rels: int
) -> str:
    """
    Generate deterministic knowledge graph summary.
    """
    summary = (
        f"GeneDxplorer constructed an evidence-backed knowledge graph centered on '{query}' containing "
        f"{disease_nodes} disease node(s), {gene_nodes} gene node(s), {record_nodes} MedGen record node(s), "
        f"and {direct_rels} direct evidence-backed relationship edge(s) sourced from NCBI MedGen AssociatedGenes XML annotations."
    )
    return summary


def generate_workspace_summary(
    saved_diseases_count: int,
    saved_genes_count: int,
    saved_comparisons_count: int,
    saved_records_count: int,
    saved_nodes_count: int,
    saved_edges_count: int,
    saved_matrices_count: int,
    notes_count: int
) -> str:
    """
    Generate deterministic workspace summary.
    """
    summary = (
        f"GeneDxplorer Research Workspace report summarizing {saved_diseases_count} saved disease(s), "
        f"{saved_genes_count} saved gene(s), {saved_comparisons_count} saved comparison(s), "
        f"{saved_records_count} saved MedGen record(s), {saved_nodes_count} graph node(s), "
        f"{saved_edges_count} graph edge(s), {saved_matrices_count} similarity matrix(es), "
        f"and {notes_count} user research note(s)."
    )
    return summary


def generate_deterministic_summary(report_type: str, data: Dict[str, Any]) -> str:
    """
    General entry point for deterministic summary generation.
    """
    t = report_type.strip().lower()
    if t == "disease":
        return generate_disease_summary(
            query=data.get("query", "Unknown"),
            records_analyzed=data.get("records_analyzed", 0),
            records_with_genes=data.get("records_with_genes", 0),
            unique_genes=data.get("unique_genes", 0),
            top_gene_symbol=data.get("top_gene_symbol"),
            top_gene_count=data.get("top_gene_count"),
            top_gene_pct=data.get("top_gene_pct")
        )
    elif t == "gene":
        return generate_gene_summary(
            gene_symbol=data.get("gene_symbol", "Unknown"),
            ncbi_gene_id=data.get("ncbi_gene_id", "N/A"),
            records_examined=data.get("records_examined", 0),
            matching_disease_count=data.get("matching_disease_count", 0),
            unique_diseases=data.get("unique_diseases", 0)
        )
    elif t == "comparison":
        return generate_comparison_summary(
            disease_a=data.get("disease_a", "Disease A"),
            disease_b=data.get("disease_b", "Disease B"),
            genes_count_a=data.get("genes_count_a", 0),
            genes_count_b=data.get("genes_count_b", 0),
            shared_count=data.get("shared_count", 0),
            jaccard_pct=data.get("jaccard_pct", 0.0),
            overlap_coeff_pct=data.get("overlap_coeff_pct", 0.0)
        )
    elif t == "similarity":
        return generate_similarity_matrix_summary(
            disease_count=data.get("disease_count", 0),
            top_pair=data.get("top_pair")
        )
    elif t == "graph":
        return generate_graph_summary(
            query=data.get("query", "Unknown"),
            disease_nodes=data.get("disease_nodes", 0),
            gene_nodes=data.get("gene_nodes", 0),
            record_nodes=data.get("record_nodes", 0),
            direct_rels=data.get("direct_rels", 0)
        )
    elif t == "workspace":
        return generate_workspace_summary(
            saved_diseases_count=data.get("saved_diseases_count", 0),
            saved_genes_count=data.get("saved_genes_count", 0),
            saved_comparisons_count=data.get("saved_comparisons_count", 0),
            saved_records_count=data.get("saved_records_count", 0),
            saved_nodes_count=data.get("saved_nodes_count", 0),
            saved_edges_count=data.get("saved_edges_count", 0),
            saved_matrices_count=data.get("saved_matrices_count", 0),
            notes_count=data.get("notes_count", 0)
        )
    return "GeneDxplorer scientific research report generated from verified NCBI MedGen records."
