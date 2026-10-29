"""
GeneDxplorer — Phase 9 Knowledge Graph Engine

Provides an evidence-backed scientific graph data model and multi-hop exploration.
Enforces strict provenance: every disease-gene edge originates directly from
structured NCBI MedGen AssociatedGenes XML annotations.

Graph limits:
- GRAPH_MAX_NODES (default: 50)
- GRAPH_MAX_EDGES (default: 100)
- GRAPH_MAX_HOPS (default: 2)
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from src.config import config
from src.medgen import search_medgen, search_medgen_by_gene, fetch_medgen_records_xml
from src.parser import parse_medgen_xml
from src.analysis import analyze_disease_genes, analyze_gene_to_disease

logger = logging.getLogger("genedxplorer.graph")

def slugify(text: str) -> str:
    """Helper to convert names into node ID safe slugs."""
    text_clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', text.strip().lower())
    return re.sub(r'_+', '_', text_clean).strip('_')

def create_disease_node_id(disease_title: str) -> str:
    return f"disease:{slugify(disease_title)}"

def create_gene_node_id(symbol: str) -> str:
    return f"gene:{symbol.strip().upper()}"

def create_record_node_id(medgen_uid: str) -> str:
    return f"record:{medgen_uid.strip()}"


def build_disease_knowledge_graph(
    disease_name: str,
    max_genes: int = 15,
    include_records: bool = True,
    max_records: int = 20
) -> Dict[str, Any]:
    """
    Build an evidence-backed knowledge graph centered on a disease.
    Disease -> Gene (direct associated gene)
    Disease -> MedGen Record -> Gene (provenance layer)
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    max_nodes = getattr(config, "GRAPH_MAX_NODES", 50)
    max_edges = getattr(config, "GRAPH_MAX_EDGES", 100)

    total_search_results, title_count, uids, strategy = search_medgen(disease_name, max_limit=max_records)
    xml_data = fetch_medgen_records_xml(uids) if uids else ""
    parsed_res = parse_medgen_xml(xml_data) if xml_data else ([], {})
    records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res


    df_genes, payload = analyze_disease_genes(records, disease_name, total_search_results)

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_node_ids = set()
    seen_edge_ids = set()

    # Primary Disease Node
    primary_disease_id = create_disease_node_id(disease_name)
    
    # Try to find representative concept_id & medgen_uid from records
    concept_id = "N/A"
    medgen_uid = "N/A"
    semantic_type = "Disease or Syndrome"
    definition = f"NCBI MedGen disease concept for '{disease_name}'"

    if records:
        first_r = records[0]
        medgen_uid = first_r.medgen_uid or "N/A"
        concept_id = first_r.concept_id or "N/A"
        semantic_type = first_r.semantic_type or semantic_type
        definition = first_r.definition or definition

    nodes.append({
        "node_id": primary_disease_id,
        "node_type": "disease",
        "title": disease_name,
        "medgen_uid": medgen_uid,
        "concept_id": concept_id,
        "semantic_type": semantic_type,
        "definition": definition,
        "source": "NCBI MedGen"
    })
    seen_node_ids.add(primary_disease_id)

    # Process Genes up to max_genes
    gene_items = payload.get("genes", [])[:max_genes]

    for item in gene_items:
        if len(nodes) >= max_nodes:
            break

        symbol = item["Gene"]
        g_id = create_gene_node_id(symbol)

        if g_id not in seen_node_ids:
            nodes.append({
                "node_id": g_id,
                "node_type": "gene",
                "symbol": symbol,
                "ncbi_gene_id": str(item.get("NCBI_Gene_ID") or "N/A"),
                "chromosome": "N/A",
                "location": "N/A",
                "source": "NCBI MedGen"
            })
            seen_node_ids.add(g_id)

        # Direct Disease -> Gene Edge
        edge_key = f"{primary_disease_id}->{g_id}:direct_associated_gene"
        if edge_key not in seen_edge_ids and len(edges) < max_edges:
            edges.append({
                "edge_id": edge_key,
                "source_node": primary_disease_id,
                "target_node": g_id,
                "relationship": "direct_associated_gene",
                "source": "NCBI MedGen",
                "medgen_uid": medgen_uid,
                "retrieved_at": now_iso,
                "evidence_type": "NCBI MedGen AssociatedGenes"
            })
            seen_edge_ids.add(edge_key)

    # Process Supporting MedGen Record Nodes if requested
    if include_records:
        for r in records[:max_records]:
            if len(nodes) >= max_nodes:
                break

            r_id = create_record_node_id(r.medgen_uid)
            if r_id not in seen_node_ids:
                nodes.append({
                    "node_id": r_id,
                    "node_type": "medgen_record",
                    "medgen_uid": r.medgen_uid,
                    "title": r.title,
                    "concept_id": r.concept_id or "N/A",
                    "semantic_type": r.semantic_type or "Disease or Syndrome",
                    "definition": r.definition or "N/A",
                    "source": "NCBI MedGen"
                })
                seen_node_ids.add(r_id)

            # Disease -> Record Edge
            d_r_edge_key = f"{primary_disease_id}->{r_id}:contains_record"
            if d_r_edge_key not in seen_edge_ids and len(edges) < max_edges:
                edges.append({
                    "edge_id": d_r_edge_key,
                    "source_node": primary_disease_id,
                    "target_node": r_id,
                    "relationship": "contains_record",
                    "source": "NCBI MedGen",
                    "medgen_uid": r.medgen_uid,
                    "retrieved_at": now_iso,
                    "evidence_type": "NCBI MedGen Record"
                })
                seen_edge_ids.add(d_r_edge_key)

            # Record -> Gene Edges for genes in this record
            for g in r.associated_genes:
                g_id = create_gene_node_id(g.symbol)
                if g_id in seen_node_ids and len(edges) < max_edges:
                    r_g_edge_key = f"{r_id}->{g_id}:direct_associated_gene"
                    if r_g_edge_key not in seen_edge_ids:
                        edges.append({
                            "edge_id": r_g_edge_key,
                            "source_node": r_id,
                            "target_node": g_id,
                            "relationship": "direct_associated_gene",
                            "source": "NCBI MedGen",
                            "medgen_uid": r.medgen_uid,
                            "retrieved_at": now_iso,
                            "evidence_type": "NCBI MedGen AssociatedGenes"
                        })
                        seen_edge_ids.add(r_g_edge_key)

    disease_nodes_count = sum(1 for n in nodes if n["node_type"] == "disease")
    gene_nodes_count = sum(1 for n in nodes if n["node_type"] == "gene")
    record_nodes_count = sum(1 for n in nodes if n["node_type"] == "medgen_record")
    direct_rels_count = sum(1 for e in edges if e["relationship"] == "direct_associated_gene")

    return {
        "query": disease_name,
        "source": "NCBI MedGen",
        "retrieved_at": now_iso,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "disease_nodes": disease_nodes_count,
            "gene_nodes": gene_nodes_count,
            "record_nodes": record_nodes_count,
            "direct_relationships": direct_rels_count
        }
    }


def build_gene_knowledge_graph(
    gene_symbol: str,
    max_diseases: int = 15,
    include_records: bool = True
) -> Dict[str, Any]:
    """
    Build an evidence-backed knowledge graph centered on a gene.
    Gene -> Directly associated diseases -> Supporting MedGen records
    """
    symbol = gene_symbol.strip().upper()
    now_iso = datetime.now(timezone.utc).isoformat()
    max_nodes = getattr(config, "GRAPH_MAX_NODES", 50)
    max_edges = getattr(config, "GRAPH_MAX_EDGES", 100)

    total_search_results, uids, strategy = search_medgen_by_gene(symbol, max_limit=config.ANALYSIS_LIMIT)
    xml_data = fetch_medgen_records_xml(uids) if uids else ""
    parsed_res = parse_medgen_xml(xml_data) if xml_data else ([], {})
    records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res


    df_diseases, payload = analyze_gene_to_disease(symbol, records, total_search_results)

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_node_ids = set()
    seen_edge_ids = set()

    # Primary Gene Node
    primary_gene_id = create_gene_node_id(symbol)
    ncbi_gene_id = payload.get("ncbi_gene_id", "N/A")

    nodes.append({
        "node_id": primary_gene_id,
        "node_type": "gene",
        "symbol": symbol,
        "ncbi_gene_id": str(ncbi_gene_id),
        "chromosome": "N/A",
        "location": "N/A",
        "source": "NCBI MedGen"
    })
    seen_node_ids.add(primary_gene_id)

    disease_records = payload.get("disease_records", [])[:max_diseases]

    for item in disease_records:
        if len(nodes) >= max_nodes:
            break

        d_title = item["title"]
        d_id = create_disease_node_id(d_title)

        if d_id not in seen_node_ids:
            nodes.append({
                "node_id": d_id,
                "node_type": "disease",
                "title": d_title,
                "medgen_uid": item.get("medgen_uid", "N/A"),
                "concept_id": item.get("concept_id", "N/A"),
                "semantic_type": item.get("semantic_type", "Disease or Syndrome"),
                "definition": item.get("definition", f"NCBI MedGen record for '{d_title}'"),
                "source": "NCBI MedGen"
            })
            seen_node_ids.add(d_id)

        # Gene -> Disease Edge
        g_d_edge_key = f"{primary_gene_id}->{d_id}:direct_associated_gene"
        if g_d_edge_key not in seen_edge_ids and len(edges) < max_edges:
            edges.append({
                "edge_id": g_d_edge_key,
                "source_node": primary_gene_id,
                "target_node": d_id,
                "relationship": "direct_associated_gene",
                "source": "NCBI MedGen",
                "medgen_uid": item.get("medgen_uid", "N/A"),
                "retrieved_at": now_iso,
                "evidence_type": "NCBI MedGen AssociatedGenes"
            })
            seen_edge_ids.add(g_d_edge_key)

        if include_records and item.get("medgen_uid"):
            m_uid = item["medgen_uid"]
            r_id = create_record_node_id(m_uid)
            if r_id not in seen_node_ids and len(nodes) < max_nodes:
                nodes.append({
                    "node_id": r_id,
                    "node_type": "medgen_record",
                    "medgen_uid": m_uid,
                    "title": d_title,
                    "concept_id": item.get("concept_id", "N/A"),
                    "semantic_type": "Disease or Syndrome",
                    "definition": item.get("definition", "N/A"),
                    "source": "NCBI MedGen"
                })
                seen_node_ids.add(r_id)

            if r_id in seen_node_ids and len(edges) < max_edges:
                r_edge_key = f"{r_id}->{primary_gene_id}:direct_associated_gene"
                if r_edge_key not in seen_edge_ids:
                    edges.append({
                        "edge_id": r_edge_key,
                        "source_node": r_id,
                        "target_node": primary_gene_id,
                        "relationship": "direct_associated_gene",
                        "source": "NCBI MedGen",
                        "medgen_uid": m_uid,
                        "retrieved_at": now_iso,
                        "evidence_type": "NCBI MedGen AssociatedGenes"
                    })
                    seen_edge_ids.add(r_edge_key)

    disease_nodes_count = sum(1 for n in nodes if n["node_type"] == "disease")
    gene_nodes_count = sum(1 for n in nodes if n["node_type"] == "gene")
    record_nodes_count = sum(1 for n in nodes if n["node_type"] == "medgen_record")
    direct_rels_count = sum(1 for e in edges if e["relationship"] == "direct_associated_gene")

    return {
        "query": symbol,
        "source": "NCBI MedGen",
        "retrieved_at": now_iso,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "disease_nodes": disease_nodes_count,
            "gene_nodes": gene_nodes_count,
            "record_nodes": record_nodes_count,
            "direct_relationships": direct_rels_count
        }
    }


def explore_graph_node(node_type: str, node_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Bounded multi-hop exploration.
    Expands selected node to show its 1st and 2nd hop evidence-backed connections.
    """
    node_type = node_type.strip().lower()
    if node_type not in ["disease", "gene", "medgen_record"]:
        raise ValueError(f"Invalid node_type '{node_type}'. Must be one of 'disease', 'gene', 'medgen_record'.")

    if node_type == "disease":
        # Extract title from node_id if formatted like "disease:alzheimer_s_disease" or use clean id
        parts = node_id.split(":", 1)
        disease_name = parts[1] if len(parts) > 1 else parts[0]
        # Replace underscores if slugified
        disease_name = disease_name.replace("_", " ")
        return build_disease_knowledge_graph(disease_name, max_genes=limit)

    elif node_type == "gene":
        parts = node_id.split(":", 1)
        gene_symbol = parts[1] if len(parts) > 1 else parts[0]
        return build_gene_knowledge_graph(gene_symbol, max_diseases=limit)

    elif node_type == "medgen_record":
        parts = node_id.split(":", 1)
        medgen_uid = parts[1] if len(parts) > 1 else parts[0]

        xml_data = fetch_medgen_records_xml([medgen_uid]) if medgen_uid else ""
        parsed_res = parse_medgen_xml(xml_data) if xml_data else ([], {})
        records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res


        if not records:
            return {
                "query": medgen_uid,
                "source": "NCBI MedGen",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "nodes": [],
                "edges": [],
                "summary": {"disease_nodes": 0, "gene_nodes": 0, "record_nodes": 0, "direct_relationships": 0}
            }

        rec = records[0]
        now_iso = datetime.now(timezone.utc).isoformat()
        r_id = create_record_node_id(rec.medgen_uid)
        d_id = create_disease_node_id(rec.title)

        nodes = [
            {
                "node_id": r_id,
                "node_type": "medgen_record",
                "medgen_uid": rec.medgen_uid,
                "title": rec.title,
                "concept_id": rec.concept_id or "N/A",
                "semantic_type": rec.semantic_type or "Disease or Syndrome",
                "definition": rec.definition or "N/A",
                "source": "NCBI MedGen"
            },
            {
                "node_id": d_id,
                "node_type": "disease",
                "title": rec.title,
                "medgen_uid": rec.medgen_uid,
                "concept_id": rec.concept_id or "N/A",
                "semantic_type": rec.semantic_type or "Disease or Syndrome",
                "definition": rec.definition or "N/A",
                "source": "NCBI MedGen"
            }
        ]

        edges = [
            {
                "edge_id": f"{d_id}->{r_id}:contains_record",
                "source_node": d_id,
                "target_node": r_id,
                "relationship": "contains_record",
                "source": "NCBI MedGen",
                "medgen_uid": rec.medgen_uid,
                "retrieved_at": now_iso,
                "evidence_type": "NCBI MedGen Record"
            }
        ]

        for g in rec.associated_genes[:limit]:
            g_id = create_gene_node_id(g.symbol)
            nodes.append({
                "node_id": g_id,
                "node_type": "gene",
                "symbol": g.symbol,
                "ncbi_gene_id": str(g.ncbi_gene_id or "N/A"),
                "chromosome": "N/A",
                "location": "N/A",
                "source": "NCBI MedGen"
            })
            edges.append({
                "edge_id": f"{r_id}->{g_id}:direct_associated_gene",
                "source_node": r_id,
                "target_node": g_id,
                "relationship": "direct_associated_gene",
                "source": "NCBI MedGen",
                "medgen_uid": rec.medgen_uid,
                "retrieved_at": now_iso,
                "evidence_type": "NCBI MedGen AssociatedGenes"
            })

        return {
            "query": medgen_uid,
            "source": "NCBI MedGen",
            "retrieved_at": now_iso,
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "disease_nodes": 1,
                "gene_nodes": len(rec.associated_genes[:limit]),
                "record_nodes": 1,
                "direct_relationships": len(rec.associated_genes[:limit])
            }
        }


def export_graph_json(graph_payload: Dict[str, Any], output_path: str) -> str:
    """Export knowledge graph to JSON file."""
    import os
    import json
    from src.utils import get_safe_export_path

    safe_path = get_safe_export_path(os.path.dirname(output_path) or "results", os.path.basename(output_path))
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        json.dump(graph_payload, f, indent=2, ensure_ascii=False)
    logger.info(f"Exported Knowledge Graph JSON to {safe_path}")
    return safe_path


def export_graph_csv(graph_payload: Dict[str, Any], nodes_csv_path: str, edges_csv_path: str) -> tuple:
    """Export knowledge graph nodes and edges to separate CSV files."""
    import os
    import pandas as pd
    from src.utils import get_safe_export_path

    safe_nodes_path = get_safe_export_path(os.path.dirname(nodes_csv_path) or "results", os.path.basename(nodes_csv_path))
    safe_edges_path = get_safe_export_path(os.path.dirname(edges_csv_path) or "results", os.path.basename(edges_csv_path))
    os.makedirs(os.path.dirname(safe_nodes_path), exist_ok=True)
    os.makedirs(os.path.dirname(safe_edges_path), exist_ok=True)

    df_nodes = pd.DataFrame(graph_payload.get("nodes", []))
    df_edges = pd.DataFrame(graph_payload.get("edges", []))

    df_nodes.to_csv(safe_nodes_path, index=False)
    df_edges.to_csv(safe_edges_path, index=False)
    logger.info(f"Exported Knowledge Graph Nodes CSV to {safe_nodes_path} and Edges CSV to {safe_edges_path}")
    return safe_nodes_path, safe_edges_path

