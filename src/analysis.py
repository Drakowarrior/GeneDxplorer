import json
import os
import logging
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from src.utils import sanitize_filename, get_safe_export_path
from src.config import config
from src.cache import cache
from src.medgen import search_medgen, search_medgen_by_gene, fetch_medgen_records_xml
from src.parser import parse_medgen_xml

logger = logging.getLogger("genedxplorer.analysis")



def analyze_disease_genes(records, query_name, total_search_results):
    """
    Perform Disease -> Gene analysis on DiseaseRecord objects.
    Calculates Record Count and Record_Percentage.
    Collects supporting records for each gene association.
    Ranks genes deterministically:
      1. Record Count descending
      2. Record_Percentage descending
      3. Gene symbol ascending (alphabetical tie-breaker)
    """
    records_analyzed = len(records)
    gene_occurrences = []
    gene_supporting_records_map = {}

    for r in records:
        for g in r.associated_genes:
            symbol = g.symbol
            gene_occurrences.append({
                "Gene": symbol,
                "NCBI_Gene_ID": g.ncbi_gene_id
            })

            if symbol not in gene_supporting_records_map:
                gene_supporting_records_map[symbol] = []

            if not any(rec["medgen_uid"] == r.medgen_uid for rec in gene_supporting_records_map[symbol]):
                gene_supporting_records_map[symbol].append({
                    "medgen_uid": r.medgen_uid,
                    "title": r.title
                })

    if not gene_occurrences or records_analyzed == 0:
        empty_df = pd.DataFrame(columns=["Rank", "Gene", "NCBI_Gene_ID", "Record Count", "Record_Percentage"])
        analysis_payload = {
            "query": query_name,
            "version": config.GENEDXPLORER_VERSION,
            "records_analyzed": records_analyzed,
            "records_with_genes": 0,
            "total_relationships": 0,
            "unique_genes": 0,
            "genes": []
        }
        return empty_df, analysis_payload

    df_raw = pd.DataFrame(gene_occurrences)

    grouped = df_raw.groupby("Gene").agg(
        Record_Count=("Gene", "count"),
        NCBI_Gene_ID=("NCBI_Gene_ID", lambda ids: next((str(i) for i in ids if i), ""))
    ).reset_index()

    grouped["Record_Percentage"] = (grouped["Record_Count"] / records_analyzed * 100).round(2)
    grouped.rename(columns={"Record_Count": "Record Count"}, inplace=True)

    df_sorted = grouped.sort_values(
        by=["Record Count", "Record_Percentage", "Gene"],
        ascending=[False, False, True]
    ).reset_index(drop=True)

    df_sorted.insert(0, "Rank", range(1, len(df_sorted) + 1))

    unique_genes_count = len(df_sorted)
    records_with_genes = len(set(r.medgen_uid for r in records if r.associated_genes))
    total_relationships = len(gene_occurrences)

    genes_records_list = df_sorted.to_dict(orient="records")
    for item in genes_records_list:
        sym = item["Gene"]
        item["supporting_records"] = gene_supporting_records_map.get(sym, [])

    analysis_payload = {
        "query": query_name,
        "version": config.GENEDXPLORER_VERSION,
        "records_analyzed": records_analyzed,
        "records_with_genes": records_with_genes,
        "total_relationships": total_relationships,
        "unique_genes": unique_genes_count,
        "genes": genes_records_list
    }

    return df_sorted, analysis_payload


def build_disease_evidence_payload(records, query_name, total_search_results, search_strategy, records_retrieved, parser_metrics):
    now_iso = datetime.now(timezone.utc).isoformat()

    evidence_records = []
    unique_supporting_uids = set()

    for r in records:
        if r.associated_genes:
            unique_supporting_uids.add(r.medgen_uid)
            evidence_records.append({
                "medgen_uid": r.medgen_uid,
                "disease_title": r.title,
                "concept_id": r.concept_id if r.concept_id else None,
                "semantic_type": r.semantic_type if r.semantic_type else None,
                "definition": r.definition if r.definition else None,
                "genes": [
                    {
                        "symbol": g.symbol,
                        "ncbi_gene_id": g.ncbi_gene_id if g.ncbi_gene_id else None,
                        "chromosome": g.chromosome if g.chromosome else None,
                        "location": g.location if g.location else None,
                        "relationship": g.relationship,
                        "source": g.source
                    }
                    for g in r.associated_genes
                ]
            })

    unique_genes_set = set(g.symbol for r in records for g in r.associated_genes)

    return {
        "query": query_name,
        "version": config.GENEDXPLORER_VERSION,
        "source": "NCBI MedGen",
        "access_method": "Biopython Bio.Entrez",
        "retrieved_at": now_iso,
        "search_strategy": search_strategy,
        "records_available": total_search_results,
        "records_retrieved": records_retrieved,
        "records_analyzed": len(records),
        "analysis_limit": config.ANALYSIS_LIMIT,
        "data_quality_metrics": {
            "records_examined": len(records),
            "records_with_genes": parser_metrics.get("records_with_genes", len(unique_supporting_uids)),
            "records_without_genes": parser_metrics.get("records_without_genes", len(records) - len(unique_supporting_uids)),
            "total_verified_relationships": parser_metrics.get("total_relationships", sum(len(r.associated_genes) for r in records)),
            "unique_genes": len(unique_genes_set),
            "unique_supporting_records": len(unique_supporting_uids),
            "duplicate_relationships_removed": parser_metrics.get("duplicate_genes_removed", 0)
        },
        "evidence": evidence_records
    }


def build_gene_evidence_payload(gene_symbol, records, total_search_results, search_strategy):
    target_gene = gene_symbol.strip().upper()
    now_iso = datetime.now(timezone.utc).isoformat()

    evidence_records = []
    ncbi_gene_id = None

    for r in records:
        for g in r.associated_genes:
            if g.symbol.upper() == target_gene:
                if not ncbi_gene_id and g.ncbi_gene_id:
                    ncbi_gene_id = g.ncbi_gene_id

                evidence_records.append({
                    "medgen_uid": r.medgen_uid,
                    "disease_title": r.title,
                    "concept_id": r.concept_id if r.concept_id else None,
                    "semantic_type": r.semantic_type if r.semantic_type else None,
                    "definition": r.definition if r.definition else None,
                    "gene_symbol": target_gene,
                    "ncbi_gene_id": g.ncbi_gene_id or ncbi_gene_id or "N/A",
                    "relationship": "direct",
                    "source": "NCBI MedGen"
                })
                break

    return {
        "gene": {
            "symbol": target_gene,
            "ncbi_gene_id": ncbi_gene_id or "N/A"
        },
        "version": config.GENEDXPLORER_VERSION,
        "source": "NCBI MedGen",
        "access_method": "Biopython Bio.Entrez",
        "retrieved_at": now_iso,
        "search_strategy": search_strategy,
        "records_examined": len(records),
        "matching_disease_count": len(evidence_records),
        "evidence": evidence_records
    }


def generate_research_summary(query, total_search_results, records_analyzed, records_with_genes, unique_genes, top_gene_symbol):
    top_gene_clause = f" '{top_gene_symbol}' was the most frequently reported gene among the analyzed records." if top_gene_symbol else ""
    summary_text = (
        f"GeneDxplorer analyzed {records_analyzed} NCBI MedGen records matching '{query}' "
        f"(out of {total_search_results} total records available). {records_with_genes} records contained "
        f"structured direct gene annotations, resulting in {unique_genes} unique reported associated genes.{top_gene_clause}"
    )
    disclaimer_text = (
        "These frequencies describe reporting within the analyzed MedGen records and do not establish "
        "causality, disease severity, clinical risk, or medical diagnosis."
    )

    return {
        "summary": summary_text,
        "disclaimer": disclaimer_text
    }


def analyze_gene_to_disease(gene_symbol, records, total_search_results):
    target_gene = gene_symbol.strip().upper()
    matching_diseases = []
    ncbi_gene_id = ""

    for r in records:
        for g in r.associated_genes:
            if g.symbol.upper() == target_gene:
                if not ncbi_gene_id and g.ncbi_gene_id:
                    ncbi_gene_id = g.ncbi_gene_id

                matching_diseases.append({
                    "medgen_uid": r.medgen_uid,
                    "title": r.title,
                    "concept_id": r.concept_id,
                    "gene_symbol": target_gene,
                    "ncbi_gene_id": g.ncbi_gene_id or ncbi_gene_id or "N/A",
                    "relationship": "direct",
                    "source": "NCBI MedGen"
                })
                break

    df_diseases = pd.DataFrame(matching_diseases)
    if not df_diseases.empty:
        df_diseases = df_diseases.sort_values(by="title", ascending=True).reset_index(drop=True)
        df_diseases.insert(0, "Rank", range(1, len(df_diseases) + 1))

    analysis_payload = {
        "gene_symbol": target_gene,
        "ncbi_gene_id": ncbi_gene_id or "N/A",
        "version": config.GENEDXPLORER_VERSION,
        "total_search_results": total_search_results,
        "records_examined": len(records),
        "matching_disease_count": len(matching_diseases),
        "disease_records": matching_diseases
    }

    return df_diseases, analysis_payload


def compare_diseases(
    disease_a_name,
    records_a,
    total_search_results_a,
    disease_b_name,
    records_b,
    total_search_results_b
):
    """
    Perform Disease Comparison between Disease A and Disease B with Phase 6B Cross-Disease Intelligence.
    Calculates:
      - Shared genes, record counts & percentage in both diseases
      - Concise record evidence references for A and B
      - Unique genes in A & unique genes in B with evidence
      - Jaccard Similarity = |A ∩ B| / |A ∪ B| * 100
      - Overlap Coefficient = |A ∩ B| / min(|A|, |B|) * 100
      - Disease A Coverage = |A ∩ B| / |A| * 100
      - Disease B Coverage = |A ∩ B| / |B| * 100
      - Dynamic Scientific Comparison Summary
    """
    df_a, payload_a = analyze_disease_genes(records_a, disease_a_name, total_search_results_a)
    df_b, payload_b = analyze_disease_genes(records_b, disease_b_name, total_search_results_b)

    genes_a_dict = {}
    for item in payload_a.get("genes", []):
        genes_a_dict[item["Gene"]] = {
            "NCBI_Gene_ID": item["NCBI_Gene_ID"],
            "Record_Count": item["Record Count"],
            "Record_Percentage": item["Record_Percentage"],
            "supporting_records": item.get("supporting_records", [])
        }

    genes_b_dict = {}
    for item in payload_b.get("genes", []):
        genes_b_dict[item["Gene"]] = {
            "NCBI_Gene_ID": item["NCBI_Gene_ID"],
            "Record_Count": item["Record Count"],
            "Record_Percentage": item["Record_Percentage"],
            "supporting_records": item.get("supporting_records", [])
        }

    set_a = set(genes_a_dict.keys())
    set_b = set(genes_b_dict.keys())

    shared_set = set_a.intersection(set_b)
    unique_a_set = set_a.difference(set_b)
    unique_b_set = set_b.difference(set_a)
    union_set = set_a.union(set_b)

    # Calculate Set Overlap Metrics
    if union_set:
        jaccard_similarity = len(shared_set) / len(union_set)
        jaccard_pct = round(jaccard_similarity * 100, 2)
    else:
        jaccard_similarity = 0.0
        jaccard_pct = 0.0

    min_size = min(len(set_a), len(set_b)) if set_a and set_b else 0
    overlap_coeff = (len(shared_set) / min_size * 100) if min_size > 0 else 0.0
    overlap_coeff_pct = round(overlap_coeff, 2)

    coverage_a_pct = round((len(shared_set) / len(set_a) * 100), 2) if set_a else 0.0
    coverage_b_pct = round((len(shared_set) / len(set_b) * 100), 2) if set_b else 0.0

    # Build Shared Genes list with Phase 6A evidence references
    shared_genes = []
    for g in sorted(list(shared_set)):
        gid = genes_a_dict[g]["NCBI_Gene_ID"] or genes_b_dict[g]["NCBI_Gene_ID"] or ""
        shared_genes.append({
            "Gene": g,
            "NCBI_Gene_ID": gid,
            "Count_A": genes_a_dict[g]["Record_Count"],
            "Percentage_A": genes_a_dict[g]["Record_Percentage"],
            "Count_B": genes_b_dict[g]["Record_Count"],
            "Percentage_B": genes_b_dict[g]["Record_Percentage"],
            "evidence_a": genes_a_dict[g]["supporting_records"],
            "evidence_b": genes_b_dict[g]["supporting_records"]
        })
    shared_genes.sort(key=lambda x: (-(x["Count_A"] + x["Count_B"]), x["Gene"]))

    # Build Unique to A list
    unique_a = []
    for g in sorted(list(unique_a_set)):
        unique_a.append({
            "Gene": g,
            "NCBI_Gene_ID": genes_a_dict[g]["NCBI_Gene_ID"],
            "Record_Count": genes_a_dict[g]["Record_Count"],
            "Record_Percentage": genes_a_dict[g]["Record_Percentage"],
            "evidence": genes_a_dict[g]["supporting_records"]
        })
    unique_a.sort(key=lambda x: (-x["Record_Count"], x["Gene"]))

    # Build Unique to B list
    unique_b = []
    for g in sorted(list(unique_b_set)):
        unique_b.append({
            "Gene": g,
            "NCBI_Gene_ID": genes_b_dict[g]["NCBI_Gene_ID"],
            "Record_Count": genes_b_dict[g]["Record_Count"],
            "Record_Percentage": genes_b_dict[g]["Record_Percentage"],
            "evidence": genes_b_dict[g]["supporting_records"]
        })
    unique_b.sort(key=lambda x: (-x["Record_Count"], x["Gene"]))

    # Deterministic Scientific Summary
    summary_text = (
        f"GeneDxplorer analyzed {len(records_a)} MedGen records for '{disease_a_name}' and {len(records_b)} records for '{disease_b_name}'. "
        f"The analyzed datasets contained {len(set_a)} and {len(set_b)} unique reported associated genes respectively. "
        f"{len(shared_set)} gene(s) were shared between the two analyzed gene sets, producing a Jaccard similarity of {jaccard_pct}% "
        f"and an Overlap coefficient of {overlap_coeff_pct}%."
    )
    disclaimer_text = (
        "The similarity metrics represent mathematical overlap between the analyzed gene sets "
        "and should not be interpreted as clinical, diagnostic, or biological similarity."
    )

    comparison_payload = {
        "disease_a": {
            "query": disease_a_name,
            "records_available": total_search_results_a,
            "records_analyzed": len(records_a),
            "unique_genes": len(set_a)
        },
        "disease_b": {
            "query": disease_b_name,
            "records_available": total_search_results_b,
            "records_analyzed": len(records_b),
            "unique_genes": len(set_b)
        },
        "version": config.GENEDXPLORER_VERSION,
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "shared_genes_count": len(shared_set),
        "unique_to_a_count": len(unique_a),
        "unique_to_b_count": len(unique_b),
        "combined_unique_genes_count": len(union_set),
        "similarity": {
            "shared_count": len(shared_set),
            "union_count": len(union_set),
            "jaccard_percentage": jaccard_pct,
            "overlap_coefficient": overlap_coeff_pct,
            "coverage_a_percentage": coverage_a_pct,
            "coverage_b_percentage": coverage_b_pct
        },
        "research_summary": {
            "summary": summary_text,
            "disclaimer": disclaimer_text
        },
        "shared_genes": shared_genes,
        "unique_to_a": unique_a,
        "unique_to_b": unique_b
    }

    return comparison_payload


# ==================================================
# EXPORT & VISUALIZATION HELPERS
# ==================================================

def export_disease_gene_csv(df_top, output_path):
    if df_top.empty:
        return

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    df_csv = df_top.head(10).copy()
    df_csv.rename(columns={"Record Count": "Record_Count"}, inplace=True)

    try:
        df_csv.to_csv(safe_path, index=False)
        logger.info(f"Exported CSV to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save CSV file: {e}")


def export_disease_gene_json(
    query,
    search_strategy,
    total_search_results,
    records_retrieved,
    records_analyzed,
    records_with_genes,
    unique_genes,
    records,
    output_path
):
    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    metadata_payload = {
        "query": query,
        "version": config.GENEDXPLORER_VERSION,
        "database": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "search_strategy": search_strategy,
        "total_search_results": total_search_results,
        "records_retrieved": records_retrieved,
        "records_analyzed": records_analyzed,
        "records_with_genes": records_with_genes,
        "unique_genes": unique_genes,
        "gene_extraction_rule": "Direct AssociatedGenes Element Annotations",
        "records": [
            {
                "medgen_uid": r.medgen_uid,
                "title": r.title,
                "concept_id": r.concept_id,
                "definition": r.definition,
                "semantic_type": r.semantic_type,
                "associated_genes": [
                    {
                        "symbol": g.symbol,
                        "ncbi_gene_id": g.ncbi_gene_id,
                        "chromosome": g.chromosome,
                        "location": g.location,
                        "relationship": g.relationship,
                        "source": g.source
                    }
                    for g in r.associated_genes
                ]
            }
            for r in records
        ]
    }

    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(metadata_payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported JSON metadata to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save JSON metadata: {e}")


def export_disease_evidence_json(evidence_payload, output_path):
    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(evidence_payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported Evidence JSON to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Evidence JSON: {e}")


def export_disease_evidence_csv(evidence_payload, output_path):
    evidence_items = evidence_payload.get("evidence", [])
    if not evidence_items:
        return

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    rows = []
    query = evidence_payload.get("query", "")
    retrieved_at = evidence_payload.get("retrieved_at", "")

    for rec in evidence_items:
        uid = rec.get("medgen_uid", "")
        title = rec.get("disease_title", "")
        for g in rec.get("genes", []):
            rows.append({
                "Disease": query,
                "MedGen_UID": uid,
                "Disease_Title": title,
                "Gene": g.get("symbol", ""),
                "NCBI_Gene_ID": g.get("ncbi_gene_id", "") or "N/A",
                "Relationship": g.get("relationship", "direct"),
                "Source": g.get("source", "NCBI MedGen"),
                "Retrieved_At": retrieved_at
            })

    if not rows:
        return

    df_ev = pd.DataFrame(rows)
    try:
        df_ev.to_csv(safe_path, index=False)
        logger.info(f"Exported Evidence CSV to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Evidence CSV: {e}")


def generate_bar_chart(df_top, disease_name, output_path):
    if df_top.empty:
        return

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    df_plot = df_top.head(10).copy()
    df_plot = df_plot.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df_plot["Gene"], df_plot["Record Count"], color="#2b5c8f", edgecolor="#1e3d59", height=0.6)

    ax.set_xlabel("Number of MedGen Records", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_ylabel("Gene", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_title(f"Top Reported Genes Associated With {disease_name.title()}", fontsize=14, fontweight="bold", pad=15)

    max_count = int(df_plot["Record Count"].max())
    ax.set_xticks(range(0, max_count + 2))

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.08,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)}",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color="#1e3d59"
        )

    ax.grid(axis="x", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()

    try:
        plt.savefig(safe_path, dpi=300)
        plt.close(fig)
        logger.info(f"Generated chart at {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save bar chart: {e}")


def export_gene_disease_csv(df_diseases, gene_symbol, output_path):
    if df_diseases.empty:
        return

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    df_csv = df_diseases.copy()
    df_csv.rename(columns={
        "title": "Disease_Title",
        "medgen_uid": "MedGen_UID",
        "concept_id": "Concept_ID",
        "gene_symbol": "Gene_Symbol",
        "ncbi_gene_id": "NCBI_Gene_ID"
    }, inplace=True)

    cols = [c for c in ["Rank", "Disease_Title", "MedGen_UID", "Concept_ID", "Gene_Symbol", "NCBI_Gene_ID"] if c in df_csv.columns]

    try:
        df_csv[cols].to_csv(safe_path, index=False)
        logger.info(f"Exported Gene->Disease CSV to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Gene -> Disease CSV: {e}")


def export_gene_disease_json(analysis_payload, output_path):
    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    payload = dict(analysis_payload)
    payload["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    payload["database"] = "NCBI MedGen"
    payload["version"] = config.GENEDXPLORER_VERSION

    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported Gene->Disease JSON to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Gene -> Disease JSON: {e}")


def export_comparison_json(comparison_payload, output_path):
    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    payload = dict(comparison_payload)
    payload["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    payload["database"] = "NCBI MedGen"
    payload["version"] = config.GENEDXPLORER_VERSION

    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported Comparison JSON to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Comparison JSON: {e}")


def export_comparison_shared_genes_csv(comparison_payload, output_path):
    """
    Phase 6B Shared Genes CSV export.
    Columns: Gene,NCBI_Gene_ID,Disease_A,Disease_A_Record_Count,Disease_A_Percentage,Disease_B,Disease_B_Record_Count,Disease_B_Percentage,Jaccard_Percentage,Source
    """
    shared_genes = comparison_payload.get("shared_genes", [])
    if not shared_genes:
        return

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    disease_a = comparison_payload.get("disease_a", {}).get("query", comparison_payload.get("disease_a", ""))
    disease_b = comparison_payload.get("disease_b", {}).get("query", comparison_payload.get("disease_b", ""))
    jaccard_pct = comparison_payload.get("similarity", {}).get("jaccard_percentage", 0.0)

    rows = []
    for sg in shared_genes:
        rows.append({
            "Gene": sg.get("Gene", ""),
            "NCBI_Gene_ID": sg.get("NCBI_Gene_ID", "") or "N/A",
            "Disease_A": disease_a,
            "Disease_A_Record_Count": sg.get("Count_A", 0),
            "Disease_A_Percentage": sg.get("Percentage_A", 0.0),
            "Disease_B": disease_b,
            "Disease_B_Record_Count": sg.get("Count_B", 0),
            "Disease_B_Percentage": sg.get("Percentage_B", 0.0),
            "Jaccard_Percentage": jaccard_pct,
            "Source": "NCBI MedGen"
        })

    df_shared = pd.DataFrame(rows)
    try:
        df_shared.to_csv(safe_path, index=False)
        logger.info(f"Exported Shared Genes CSV to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Shared Genes CSV: {e}")


# Legacy alias compatibility
export_comparison_csv = export_comparison_shared_genes_csv


def export_comparison_unique_genes_csv(comparison_payload, output_path):
    """
    Phase 6B Unique Genes CSV export.
    Columns: Gene,NCBI_Gene_ID,Category,Disease,Record_Count,Record_Percentage,Source
    """
    unique_a = comparison_payload.get("unique_to_a", [])
    unique_b = comparison_payload.get("unique_to_b", [])

    if not unique_a and not unique_b:
        return

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    disease_a = comparison_payload.get("disease_a", {}).get("query", comparison_payload.get("disease_a", ""))
    disease_b = comparison_payload.get("disease_b", {}).get("query", comparison_payload.get("disease_b", ""))

    rows = []
    for ua in unique_a:
        rows.append({
            "Gene": ua.get("Gene", ""),
            "NCBI_Gene_ID": ua.get("NCBI_Gene_ID", "") or "N/A",
            "Category": "unique_to_A",
            "Disease": disease_a,
            "Record_Count": ua.get("Record_Count", 0),
            "Record_Percentage": ua.get("Record_Percentage", 0.0),
            "Source": "NCBI MedGen"
        })

    for ub in unique_b:
        rows.append({
            "Gene": ub.get("Gene", ""),
            "NCBI_Gene_ID": ub.get("NCBI_Gene_ID", "") or "N/A",
            "Category": "unique_to_B",
            "Disease": disease_b,
            "Record_Count": ub.get("Record_Count", 0),
            "Record_Percentage": ub.get("Record_Percentage", 0.0),
            "Source": "NCBI MedGen"
        })

    df_unique = pd.DataFrame(rows)
    try:
        df_unique.to_csv(safe_path, index=False)
        logger.info(f"Exported Unique Genes CSV to {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save Unique Genes CSV: {e}")


def generate_comparison_chart(comparison_payload, output_path):
    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    disease_a = comparison_payload.get("disease_a", {}).get("query", comparison_payload.get("disease_a", "Disease A"))
    disease_b = comparison_payload.get("disease_b", {}).get("query", comparison_payload.get("disease_b", "Disease B"))
    unique_a = comparison_payload.get("unique_to_a_count", 0)
    shared = comparison_payload.get("shared_genes_count", 0)
    unique_b = comparison_payload.get("unique_to_b_count", 0)
    jaccard_pct = comparison_payload.get("similarity", {}).get("jaccard_percentage", 0.0)

    categories = [f"Unique to\n{disease_a}", "Shared Genes", f"Unique to\n{disease_b}"]
    counts = [unique_a, shared, unique_b]
    colors = ["#2b5c8f", "#d97706", "#059669"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, counts, color=colors, edgecolor="#1e3d59", width=0.5)

    ax.set_ylabel("Number of Direct Genes", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_title(f"Gene-Set Overlap: {disease_a} vs {disease_b}\nJaccard Similarity: {jaccard_pct}%", fontsize=13, fontweight="bold", pad=15)

    max_c = max(counts) if counts else 1
    ax.set_ylim(0, max_c + max(2, int(max_c * 0.2)))

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.1,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold"
        )

    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()

    try:
        plt.savefig(safe_path, dpi=300)
        plt.close(fig)
        logger.info(f"Generated comparison chart at {safe_path}")
    except Exception as e:
        logger.warning(f"Could not save comparison chart: {e}")


def discover_disease_concepts(query_name: str, limit: int = 25) -> dict:
    """
    Lightweight discovery search for MedGen disease concepts.
    Uses caching and retrieves up to `limit` records.
    """
    clean_query = query_name.strip()
    if not clean_query:
        return {
            "query": "",
            "source": "NCBI MedGen",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "total_matches": 0,
            "results": []
        }

    cached = cache.get("discover_disease", query=clean_query, limit=limit)
    if cached:
        return cached

    total_matches, title_count, combined_uids, strategy = search_medgen(clean_query, max_limit=limit)
    xml_docs = fetch_medgen_records_xml(combined_uids, batch_size=limit)
    parsed_res = parse_medgen_xml(xml_docs)
    records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res

    results = []
    for r in records:
        results.append({
            "medgen_uid": r.medgen_uid,
            "title": r.title,
            "concept_id": r.concept_id or None,
            "semantic_type": r.semantic_type or None,
            "definition": r.definition or None,
            "associated_gene_count": len(r.associated_genes),
            "associated_genes": [
                {
                    "symbol": g.symbol,
                    "ncbi_gene_id": g.ncbi_gene_id,
                    "chromosome": g.chromosome,
                    "location": g.location
                }
                for g in r.associated_genes
            ],
            "source": "NCBI MedGen"
        })

    payload = {
        "query": clean_query,
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "total_matches": total_matches,
        "results": results
    }

    cache.set("discover_disease", payload, query=clean_query, limit=limit)
    return payload


def discover_gene_associations(gene_symbol: str, limit: int = 25) -> dict:
    """
    Lightweight discovery search for gene symbol associations.
    Uses caching and retrieves up to `limit` records.
    """
    clean_symbol = gene_symbol.strip()
    if not clean_symbol:
        return {
            "query": "",
            "source": "NCBI MedGen",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "results": []
        }

    cached = cache.get("discover_gene", symbol=clean_symbol, limit=limit)
    if cached:
        return cached

    total_matches, combined_uids, strategy = search_medgen_by_gene(clean_symbol, max_limit=limit)
    xml_docs = fetch_medgen_records_xml(combined_uids, batch_size=limit)
    parsed_res = parse_medgen_xml(xml_docs)
    records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res

    target_upper = clean_symbol.upper()
    matching_diseases = []
    ncbi_gene_id = None

    for r in records:
        direct_match = False
        for g in r.associated_genes:
            if g.symbol.upper() == target_upper:
                direct_match = True
                if g.ncbi_gene_id and not ncbi_gene_id:
                    ncbi_gene_id = g.ncbi_gene_id
        if direct_match:
            matching_diseases.append({
                "title": r.title,
                "medgen_uid": r.medgen_uid,
                "concept_id": r.concept_id,
                "semantic_type": r.semantic_type,
                "associated_gene_count": len(r.associated_genes)
            })

    unique_titles = list(set(d["title"] for d in matching_diseases))

    results = [
        {
            "symbol": target_upper,
            "ncbi_gene_id": ncbi_gene_id or "N/A",
            "candidate_records": total_matches,
            "verified_records": len(matching_diseases),
            "unique_diseases": len(unique_titles),
            "diseases": matching_diseases
        }
    ]

    payload = {
        "query": clean_symbol,
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "results": results
    }

    cache.set("discover_gene", payload, symbol=clean_symbol, limit=limit)
    return payload


