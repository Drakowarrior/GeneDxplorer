"""
GeneDxplorer — Phase 9 Multi-Disease Similarity Matrix Engine

Computes pairwise gene-set similarity across 2 to 10 diseases using verified NCBI MedGen records.
Metrics calculated:
- Jaccard Similarity: |A ∩ B| / |A ∪ B| * 100
- Overlap Coefficient: |A ∩ B| / min(|A|, |B|) * 100
- Coverage A & B: |A ∩ B| / |A| * 100 & |A ∩ B| / |B| * 100
- Shared Gene Details & Supporting Record Provenance

Note: These are standard set-theoretic overlap metrics. They describe reporting overlap
in analyzed MedGen records and do NOT imply clinical, diagnostic, or etiology similarity.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.config import config
from src.medgen import search_medgen, fetch_medgen_records_xml
from src.parser import parse_medgen_xml
from src.analysis import analyze_disease_genes

logger = logging.getLogger("genedxplorer.similarity")


def calculate_multi_disease_similarity(
    disease_names: List[str],
    max_records: int = 100
) -> Dict[str, Any]:
    """
    Calculate pairwise gene-set similarity matrix for 2-10 diseases.
    """
    # Clean and validate input names
    cleaned_names = [d.strip() for d in disease_names if d and d.strip()]
    # Deduplicate while preserving order
    unique_names = []
    for d in cleaned_names:
        if d not in unique_names:
            unique_names.append(d)

    if len(unique_names) < 2 or len(unique_names) > 10:
        raise ValueError(f"Multi-disease similarity requires between 2 and 10 unique diseases. Got: {len(unique_names)}")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Step 1: Fetch and analyze gene sets for each disease
    disease_data: Dict[str, Dict[str, Any]] = {}

    for d_name in unique_names:
        total_search_results, title_count, uids, strategy = search_medgen(d_name, max_limit=max_records)
        xml_data = fetch_medgen_records_xml(uids) if uids else ""
        parsed_res = parse_medgen_xml(xml_data) if xml_data else ([], {})
        records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res


        df_genes, payload = analyze_disease_genes(records, d_name, total_search_results)

        genes_dict = {}
        for item in payload.get("genes", []):
            genes_dict[item["Gene"]] = {
                "ncbi_gene_id": str(item.get("NCBI_Gene_ID") or "N/A"),
                "record_count": item.get("Record Count", 0),
                "record_percentage": item.get("Record_Percentage", 0.0),
                "supporting_records": item.get("supporting_records", [])
            }

        disease_data[d_name] = {
            "query": d_name,
            "total_records_analyzed": len(records),
            "unique_genes_count": len(genes_dict),
            "gene_set": set(genes_dict.keys()),
            "genes_dict": genes_dict
        }

    # Step 2: Compute pairwise matrices and comparisons
    n = len(unique_names)
    matrix: List[List[Dict[str, Any]]] = []
    ranked_pairs: List[Dict[str, Any]] = []

    for i in range(n):
        row = []
        name_a = unique_names[i]
        data_a = disease_data[name_a]
        set_a = data_a["gene_set"]

        for j in range(n):
            name_b = unique_names[j]
            data_b = disease_data[name_b]
            set_b = data_b["gene_set"]

            shared_set = set_a.intersection(set_b)
            union_set = set_a.union(set_b)

            if union_set:
                jaccard = round((len(shared_set) / len(union_set)) * 100, 2)
            else:
                jaccard = 100.0 if i == j else 0.0

            min_size = min(len(set_a), len(set_b)) if set_a and set_b else 0
            overlap_coeff = round((len(shared_set) / min_size * 100), 2) if min_size > 0 else (100.0 if i == j else 0.0)

            cov_a = round((len(shared_set) / len(set_a) * 100), 2) if set_a else (100.0 if i == j else 0.0)
            cov_b = round((len(shared_set) / len(set_b) * 100), 2) if set_b else (100.0 if i == j else 0.0)

            cell_data = {
                "disease_a": name_a,
                "disease_b": name_b,
                "jaccard_similarity": jaccard,
                "overlap_coefficient": overlap_coeff,
                "shared_gene_count": len(shared_set),
                "union_gene_count": len(union_set),
                "coverage_a": cov_a,
                "coverage_b": cov_b
            }
            row.append(cell_data)

            # Record upper triangle pairs for ranked pair list
            if i < j:
                # Build detailed shared genes info
                shared_genes_list = []
                for sym in sorted(list(shared_set)):
                    info_a = data_a["genes_dict"].get(sym, {})
                    info_b = data_b["genes_dict"].get(sym, {})
                    ncbi_id = info_a.get("ncbi_gene_id") or info_b.get("ncbi_gene_id") or "N/A"

                    shared_genes_list.append({
                        "gene_symbol": sym,
                        "ncbi_gene_id": ncbi_id,
                        "frequency_in_a": info_a.get("record_count", 0),
                        "percentage_in_a": info_a.get("record_percentage", 0.0),
                        "frequency_in_b": info_b.get("record_count", 0),
                        "percentage_in_b": info_b.get("record_percentage", 0.0),
                        "supporting_records_a": info_a.get("supporting_records", []),
                        "supporting_records_b": info_b.get("supporting_records", [])
                    })

                pair_record = {
                    "disease_a": name_a,
                    "disease_b": name_b,
                    "jaccard_similarity": jaccard,
                    "overlap_coefficient": overlap_coeff,
                    "shared_gene_count": len(shared_set),
                    "union_gene_count": len(union_set),
                    "gene_count_a": len(set_a),
                    "gene_count_b": len(set_b),
                    "coverage_a": cov_a,
                    "coverage_b": cov_b,
                    "shared_genes": shared_genes_list
                }
                ranked_pairs.append(pair_record)

        matrix.append(row)

    # Sort ranked pairs by Jaccard similarity descending
    ranked_pairs.sort(key=lambda x: x["jaccard_similarity"], reverse=True)

    summary_diseases = []
    for name in unique_names:
        info = disease_data[name]
        summary_diseases.append({
            "disease_name": name,
            "records_analyzed": info["total_records_analyzed"],
            "unique_genes": info["unique_genes_count"]
        })

    return {
        "version": config.GENEDXPLORER_VERSION,
        "source": "NCBI MedGen",
        "retrieved_at": now_iso,
        "disease_count": len(unique_names),
        "diseases": summary_diseases,
        "matrix": matrix,
        "ranked_pairs": ranked_pairs,
        "disclaimer": (
            "Gene-set similarity metrics (Jaccard Similarity and Overlap Coefficient) are standard mathematical overlap "
            "calculations based on reported associated genes in NCBI MedGen. They describe reporting similarity in the analyzed "
            "records and do NOT imply clinical, diagnostic, or therapeutic equivalence."
        )
    }


def export_similarity_analysis_json(similarity_payload: Dict[str, Any], output_path: str) -> str:
    """Export multi-disease similarity analysis payload to JSON."""
    import os
    import json
    from src.utils import get_safe_export_path

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        json.dump(similarity_payload, f, indent=2, ensure_ascii=False)
    logger.info(f"Exported Similarity Analysis JSON to {safe_path}")
    return safe_path


def export_similarity_matrix_csv(similarity_payload: Dict[str, Any], output_path: str) -> str:
    """Export pairwise Jaccard similarity matrix to CSV."""
    import os
    import pandas as pd
    from src.utils import get_safe_export_path

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)

    matrix_data = similarity_payload.get("matrix", [])
    disease_names = [d["disease_name"] for d in similarity_payload.get("diseases", [])]

    # Build 2D table of Jaccard percentages
    grid = {}
    for row in matrix_data:
        if not row:
            continue
        d_a = row[0]["disease_a"]
        grid[d_a] = {}
        for cell in row:
            grid[d_a][cell["disease_b"]] = f"{cell['jaccard_similarity']}%"

    df_matrix = pd.DataFrame.from_dict(grid, orient="index")
    df_matrix.to_csv(safe_path)
    logger.info(f"Exported Similarity Matrix CSV to {safe_path}")
    return safe_path

