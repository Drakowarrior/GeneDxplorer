import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Path, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.config import config
from src.cache import cache
from src.logging_config import setup_logging, set_request_id, get_request_id
from src.utils import (
    ValidationError,
    validate_disease_name,
    validate_gene_symbol,
    validate_disease_comparison,
    sanitize_filename
)
from src.medgen import (
    configure_ncbi,
    search_medgen,
    search_medgen_by_gene,
    fetch_medgen_records_xml,
    fetch_single_medgen_record_xml,
    NCBIException,
    NCBIConnectionError,
    NCBITimeoutError,
    NCBISearchError
)
from src.parser import parse_medgen_xml
from src.analysis import (
    analyze_disease_genes,
    analyze_gene_to_disease,
    compare_diseases,
    build_disease_evidence_payload,
    build_gene_evidence_payload,
    generate_research_summary,
    export_disease_evidence_json,
    export_disease_evidence_csv,
    export_disease_gene_csv,
    export_disease_gene_json,
    generate_bar_chart,
    export_comparison_json,
    export_comparison_shared_genes_csv,
    export_comparison_unique_genes_csv,
    generate_comparison_chart,
    discover_disease_concepts,
    discover_gene_associations
)
from src.evidence import aggregator
from src.graph import (
    build_disease_knowledge_graph,
    build_gene_knowledge_graph,
    explore_graph_node,
    export_graph_json,
    export_graph_csv
)
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.similarity import (
    calculate_multi_disease_similarity,
    export_similarity_analysis_json,
    export_similarity_matrix_csv
)
from src.reporting import (
    build_disease_report,
    build_gene_report,
    build_comparison_report,
    build_graph_report,
    build_similarity_report,
    build_workspace_report,
    get_report_by_id,
    export_report_html,
    export_report_json,
    export_report_genes_csv,
    export_report_evidence_csv
)
from src.reproducibility import (
    create_analysis_snapshot,
    get_snapshot_by_id,
    build_reproducibility_manifest,
    extract_citations_from_report,
    build_reproducibility_package_files,
    export_reproducibility_package_zip,
    export_publication_evidence_csv
)

class SnapshotCreateRequest(BaseModel):
    report_data: Dict[str, Any] = Field(..., description="Research report model dict or analysis payload")
    workspace: Optional[Dict[str, Any]] = Field(None, description="Optional workspace data with notes")

class MultiSimilarityRequest(BaseModel):
    diseases: List[str] = Field(..., min_length=2, max_length=10, description="List of 2 to 10 disease names")
    max_records: Optional[int] = Field(100, ge=10, le=500, description="Maximum MedGen records to fetch per disease")

class DiseaseReportRequest(BaseModel):
    disease_name: str = Field(..., description="Target disease name")
    max_records: Optional[int] = Field(None, ge=10, le=500)

class GeneReportRequest(BaseModel):
    gene_symbol: str = Field(..., description="Target gene symbol")

class ComparisonReportRequest(BaseModel):
    disease_a: str = Field(..., description="Disease A name")
    disease_b: str = Field(..., description="Disease B name")

class GraphReportRequest(BaseModel):
    query: str = Field(..., description="Disease name or gene symbol")
    node_type: Optional[str] = Field("disease", description="Node type ('disease' or 'gene')")

class WorkspaceReportRequest(BaseModel):
    workspace: Dict[str, Any] = Field(..., description="User workspace object")



# Initialize logging configuration

setup_logging(config.LOG_LEVEL)
logger = logging.getLogger("genedxplorer.api")


# Ensure NCBI configuration is initialized at app load
configure_ncbi()

app = FastAPI(
    title="GeneDxplorer REST API",
    description=(
        "Production-grade REST API for exploring disease–gene relationships, scientific evidence, and cross-disease comparative intelligence using real NCBI MedGen data.\n\n"
        "**Scientific Definitions & Evidence Interpretations:**\n"
        "- **Reported Association:** Direct `<AssociatedGenes>` XML element annotations returned by NCBI MedGen.\n"
        "- **Record Count:** Number of analyzed MedGen disease records in which the gene was reported as directly associated.\n"
        "- **Record Percentage:** (Record Count / Records Analyzed) × 100.\n"
        "- **Jaccard Similarity:** (|GeneSet_A ∩ GeneSet_B| / |GeneSet_A ∪ GeneSet_B|) × 100.\n"
        "- **Overlap Coefficient:** (|GeneSet_A ∩ GeneSet_B| / min(|GeneSet_A|, |GeneSet_B|)) × 100.\n\n"
        "*Note: Scientific evidence and set overlap metrics do NOT establish clinical causality, risk, or diagnosis.*"
    ),
    version=config.GENEDXPLORER_VERSION
)

# ==================================================
# MIDDLEWARES
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def in_flight_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    set_request_id(req_id)
    
    start_time = time.time()
    logger.info(f"Incoming HTTP Request: {request.method} {request.url.path}")

    try:
        response: Response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"Unhandled Exception during request processing after {duration_ms}ms: {exc}", exc_info=True)
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An internal server error occurred while processing your request.",
                "code": "INTERNAL_ERROR",
                "request_id": req_id
            }
        )

    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = req_id
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    logger.info(f"Completed HTTP Response: {response.status_code} in {duration_ms}ms [req_id={req_id}]")
    return response


# ==================================================
# CUSTOM EXCEPTION HANDLERS
# ==================================================

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    req_id = get_request_id()
    detail = exc.detail if isinstance(exc.detail, dict) else {"error": str(exc.detail)}
    err_code = detail.get("code", f"HTTP_{exc.status_code}")
    err_msg = detail.get("error", "An error occurred.")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": err_msg,
            "code": err_code,
            "request_id": req_id,
            "query": detail.get("query")
        }
    )

@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(request: Request, exc: ValidationError):
    req_id = get_request_id()
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.message,
            "code": exc.code,
            "request_id": req_id
        }
    )

@app.exception_handler(NCBIConnectionError)
async def ncbi_connection_exception_handler(request: Request, exc: NCBIConnectionError):
    req_id = get_request_id()
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": exc.message,
            "code": exc.code,
            "request_id": req_id
        }
    )

@app.exception_handler(NCBITimeoutError)
async def ncbi_timeout_exception_handler(request: Request, exc: NCBITimeoutError):
    req_id = get_request_id()
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "error": exc.message,
            "code": exc.code,
            "request_id": req_id
        }
    )

@app.exception_handler(NCBISearchError)
async def ncbi_search_exception_handler(request: Request, exc: NCBISearchError):
    req_id = get_request_id()
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": exc.message,
            "code": exc.code,
            "request_id": req_id
        }
    )


# ==================================================
# REQUEST / RESPONSE SCHEMAS
# ==================================================

class DiseaseComparisonRequest(BaseModel):
    disease_a: str = Field(..., description="Name of first disease", json_schema_extra={"example": "Alzheimer's disease"})
    disease_b: str = Field(..., description="Name of second disease", json_schema_extra={"example": "Parkinson disease"})


# ==================================================
# WORKFLOW WITH CACHING
# ==================================================

def _execute_disease_workflow(disease_name: str):
    """
    Executes standard disease retrieval & parsing workflow with server-side caching.
    Auto-generates evidence exports in results/ directory.
    """
    clean_query = validate_disease_name(disease_name)

    cached_data = cache.get("disease_workflow", query=clean_query, limit=config.ANALYSIS_LIMIT)
    if cached_data:
        return cached_data

    total_search_results, title_count, combined_uids, search_strategy_desc = search_medgen(
        clean_query, max_limit=config.ANALYSIS_LIMIT
    )

    if not combined_uids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No matching MedGen records found.", "code": "MEDGEN_NOT_FOUND", "query": clean_query}
        )

    doc_elements = fetch_medgen_records_xml(combined_uids, batch_size=config.NCBI_BATCH_SIZE)
    records, parser_metrics = parse_medgen_xml(doc_elements)
    df_counts, analysis_payload = analyze_disease_genes(records, clean_query, total_search_results)

    evidence_payload = build_disease_evidence_payload(
        records=records,
        query_name=clean_query,
        total_search_results=total_search_results,
        search_strategy=search_strategy_desc,
        records_retrieved=len(doc_elements),
        parser_metrics=parser_metrics
    )

    disease_slug = sanitize_filename(clean_query)
    export_disease_evidence_json(evidence_payload, f"results/{disease_slug}_evidence.json")
    export_disease_evidence_csv(evidence_payload, f"results/{disease_slug}_evidence.csv")

    res = {
        "query": clean_query,
        "total_search_results": total_search_results,
        "search_strategy_desc": search_strategy_desc,
        "combined_uids": combined_uids,
        "doc_elements": doc_elements,
        "records": records,
        "parser_metrics": parser_metrics,
        "df_counts": df_counts,
        "analysis_payload": analysis_payload,
        "evidence_payload": evidence_payload
    }

    cache.set("disease_workflow", res, ttl=config.CACHE_TTL, query=clean_query, limit=config.ANALYSIS_LIMIT)
    return res


# ==================================================
# API ROUTES
# ==================================================

@app.get("/api/health", summary="Liveness Health Check", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "GeneDxplorer API",
        "version": config.GENEDXPLORER_VERSION
    }


@app.get("/api/ready", summary="Readiness Check", tags=["System"])
def readiness_check():
    return {
        "status": "ready",
        "service": "GeneDxplorer API",
        "version": config.GENEDXPLORER_VERSION,
        "config": {
            "analysis_limit": config.ANALYSIS_LIMIT,
            "ncbi_batch_size": config.NCBI_BATCH_SIZE,
            "ncbi_request_delay": config.NCBI_REQUEST_DELAY,
            "cache_ttl": config.CACHE_TTL,
            "log_level": config.LOG_LEVEL
        },
        "cache": cache.stats()
    }


@app.get("/api/disease/{disease_name}", summary="Disease → Gene Analysis", tags=["Disease Analysis"])
def get_disease_analysis(
    disease_name: str = Path(..., description="Disease name to analyze")
):
    res = _execute_disease_workflow(disease_name)
    df_counts = res["df_counts"]

    if df_counts.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "No reported associated genes found in retrieved MedGen records.",
                "code": "NO_DIRECT_GENES",
                "query": res["query"]
            }
        )

    genes_list = []
    top_gene_symbol = ""

    for idx, row in df_counts.iterrows():
        sym = str(row["Gene"])
        if idx == 0:
            top_gene_symbol = sym

        supporting_recs = row.get("supporting_records", []) if hasattr(row, "supporting_records") else []
        if not supporting_recs and "genes" in res["analysis_payload"]:
            for g_item in res["analysis_payload"]["genes"]:
                if g_item.get("Gene") == sym:
                    supporting_recs = g_item.get("supporting_records", [])
                    break

        genes_list.append({
            "rank": int(row["Rank"]),
            "symbol": sym,
            "ncbi_gene_id": str(row["NCBI_Gene_ID"]) if str(row["NCBI_Gene_ID"]) else "",
            "record_count": int(row["Record Count"]),
            "record_percentage": float(row["Record_Percentage"]),
            "supporting_records": supporting_recs
        })

    metrics = res["parser_metrics"]
    research_summary = generate_research_summary(
        query=res["query"],
        total_search_results=res["total_search_results"],
        records_analyzed=metrics["records_analyzed"],
        records_with_genes=metrics["records_with_genes"],
        unique_genes=res["analysis_payload"]["unique_genes"],
        top_gene_symbol=top_gene_symbol
    )

    return {
        "query": res["query"],
        "version": config.GENEDXPLORER_VERSION,
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "search_strategy": res["search_strategy_desc"],
        "records": {
            "total_available": res["total_search_results"],
            "retrieved": len(res["doc_elements"]),
            "analyzed": metrics["records_analyzed"]
        },
        "data_quality": {
            "records_with_genes": metrics["records_with_genes"],
            "records_without_genes": metrics["records_without_genes"],
            "total_relationships": metrics["total_relationships"],
            "unique_genes": res["analysis_payload"]["unique_genes"],
            "duplicate_genes_removed": metrics["duplicate_genes_removed"]
        },
        "research_summary": research_summary,
        "genes": genes_list
    }


@app.get("/api/disease/{disease_name}/evidence", summary="Disease Record-Level Evidence", tags=["Evidence & Provenance"])
def get_disease_evidence(
    disease_name: str = Path(..., description="Disease name to retrieve evidence for")
):
    res = _execute_disease_workflow(disease_name)
    return res["evidence_payload"]


@app.get("/api/disease/{disease_name}/info", summary="Disease Information", tags=["Disease Analysis"])
def get_disease_info(
    disease_name: str = Path(..., description="Disease name")
):
    res = _execute_disease_workflow(disease_name)
    records = res["records"]

    record_info_list = [
        {
            "medgen_uid": r.medgen_uid,
            "title": r.title,
            "concept_id": r.concept_id if r.concept_id else "",
            "definition": r.definition if r.definition else "",
            "semantic_type": r.semantic_type if r.semantic_type else ""
        }
        for r in records
    ]

    return {
        "query": res["query"],
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(record_info_list),
        "records": record_info_list
    }


@app.get("/api/disease/{disease_name}/genes", summary="Ranked Associated Genes", tags=["Disease Analysis"])
def get_disease_genes(
    disease_name: str = Path(..., description="Disease name")
):
    res = _execute_disease_workflow(disease_name)
    df_counts = res["df_counts"]

    if df_counts.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "No reported associated genes found in retrieved MedGen records.",
                "code": "NO_DIRECT_GENES",
                "query": res["query"]
            }
        )

    genes_list = [
        {
            "rank": int(row["Rank"]),
            "symbol": str(row["Gene"]),
            "ncbi_gene_id": str(row["NCBI_Gene_ID"]) if str(row["NCBI_Gene_ID"]) else "",
            "record_count": int(row["Record Count"]),
            "record_percentage": float(row["Record_Percentage"])
        }
        for _, row in df_counts.iterrows()
    ]

    return {
        "query": res["query"],
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "total_genes": len(genes_list),
        "genes": genes_list
    }


@app.get("/api/disease/{disease_name}/records", summary="Structured MedGen Records", tags=["Disease Analysis"])
def get_disease_records(
    disease_name: str = Path(..., description="Disease name")
):
    res = _execute_disease_workflow(disease_name)
    records = res["records"]

    formatted_records = [
        {
            "medgen_uid": r.medgen_uid,
            "title": r.title,
            "concept_id": r.concept_id if r.concept_id else "",
            "definition": r.definition if r.definition else "",
            "semantic_type": r.semantic_type if r.semantic_type else "",
            "associated_genes": [
                {
                    "symbol": g.symbol,
                    "ncbi_gene_id": g.ncbi_gene_id if g.ncbi_gene_id else "",
                    "chromosome": g.chromosome if g.chromosome else "",
                    "location": g.location if g.location else "",
                    "relationship": g.relationship,
                    "source": g.source
                }
                for g in r.associated_genes
            ]
        }
        for r in records
    ]

    return {
        "query": res["query"],
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(formatted_records),
        "records": formatted_records
    }


@app.get("/api/gene/{gene_symbol}", summary="Gene → Disease Analysis", tags=["Gene Analysis"])
def get_gene_associated_diseases(
    gene_symbol: str = Path(..., description="Gene symbol to search")
):
    clean_gene = validate_gene_symbol(gene_symbol)

    cached_res = cache.get("gene_workflow", gene=clean_gene, limit=config.ANALYSIS_LIMIT)
    if cached_res:
        return cached_res

    total_search_results, combined_uids, search_strategy_desc = search_medgen_by_gene(
        clean_gene, max_limit=config.ANALYSIS_LIMIT
    )

    if not combined_uids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"No matching MedGen records found for gene '{clean_gene}'.",
                "code": "MEDGEN_NOT_FOUND",
                "query": clean_gene
            }
        )

    doc_elements = fetch_medgen_records_xml(combined_uids, batch_size=config.NCBI_BATCH_SIZE)
    records, _ = parse_medgen_xml(doc_elements)
    df_diseases, analysis_payload = analyze_gene_to_disease(clean_gene, records, total_search_results)

    matching_count = analysis_payload["matching_disease_count"]
    if matching_count == 0 or df_diseases.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"No direct MedGen disease associations found for gene '{clean_gene}'.",
                "code": "NO_DIRECT_DISEASES",
                "query": clean_gene
            }
        )

    disease_list = [
        {
            "title": str(row["title"]),
            "medgen_uid": str(row["medgen_uid"]),
            "concept_id": str(row["concept_id"]) if str(row["concept_id"]) else "",
            "relationship": str(row["relationship"]),
            "source": str(row["source"])
        }
        for _, row in df_diseases.iterrows()
    ]

    res = {
        "gene": {
            "symbol": clean_gene,
            "ncbi_gene_id": analysis_payload["ncbi_gene_id"]
        },
        "version": config.GENEDXPLORER_VERSION,
        "source": "NCBI MedGen",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "records_examined": len(records),
        "matching_disease_count": matching_count,
        "diseases": disease_list
    }

    cache.set("gene_workflow", res, ttl=config.CACHE_TTL, gene=clean_gene, limit=config.ANALYSIS_LIMIT)
    return res


@app.get("/api/gene/{gene_symbol}/summary", summary="Compact Gene Overview Summary", tags=["Gene Analysis"])
def get_gene_summary(
    gene_symbol: str = Path(..., description="Gene symbol to get summary overview for")
):
    """
    Phase 6B dedicated endpoint returning compact overview statistics for a gene.
    """
    clean_gene = validate_gene_symbol(gene_symbol)

    cached_summary = cache.get("gene_summary_overview", gene=clean_gene, limit=config.ANALYSIS_LIMIT)
    if cached_summary:
        return cached_summary

    total_search_results, combined_uids, search_strategy_desc = search_medgen_by_gene(
        clean_gene, max_limit=config.ANALYSIS_LIMIT
    )

    if not combined_uids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"No matching MedGen records found for gene '{clean_gene}'.",
                "code": "MEDGEN_NOT_FOUND",
                "query": clean_gene
            }
        )

    doc_elements = fetch_medgen_records_xml(combined_uids, batch_size=config.NCBI_BATCH_SIZE)
    records, _ = parse_medgen_xml(doc_elements)
    df_diseases, analysis_payload = analyze_gene_to_disease(clean_gene, records, total_search_results)

    unique_disease_titles = set(r["title"] for r in analysis_payload.get("disease_records", []))

    summary_payload = {
        "symbol": clean_gene,
        "ncbi_gene_id": analysis_payload.get("ncbi_gene_id", "N/A"),
        "candidate_records": total_search_results,
        "verified_records": len(records),
        "unique_diseases": len(unique_disease_titles),
        "source": "NCBI MedGen",
        "version": config.GENEDXPLORER_VERSION
    }

    cache.set("gene_summary_overview", summary_payload, ttl=config.CACHE_TTL, gene=clean_gene, limit=config.ANALYSIS_LIMIT)
    return summary_payload


@app.get("/api/gene/{gene_symbol}/evidence", summary="Gene Record-Level Evidence", tags=["Evidence & Provenance"])
def get_gene_evidence(
    gene_symbol: str = Path(..., description="Gene symbol to search evidence for")
):
    clean_gene = validate_gene_symbol(gene_symbol)

    cached_res = cache.get("gene_evidence_workflow", gene=clean_gene, limit=config.ANALYSIS_LIMIT)
    if cached_res:
        return cached_res

    total_search_results, combined_uids, search_strategy_desc = search_medgen_by_gene(
        clean_gene, max_limit=config.ANALYSIS_LIMIT
    )

    if not combined_uids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"No matching MedGen records found for gene '{clean_gene}'.",
                "code": "MEDGEN_NOT_FOUND",
                "query": clean_gene
            }
        )

    doc_elements = fetch_medgen_records_xml(combined_uids, batch_size=config.NCBI_BATCH_SIZE)
    records, _ = parse_medgen_xml(doc_elements)
    evidence_payload = build_gene_evidence_payload(clean_gene, records, total_search_results, search_strategy_desc)

    cache.set("gene_evidence_workflow", evidence_payload, ttl=config.CACHE_TTL, gene=clean_gene, limit=config.ANALYSIS_LIMIT)
    return evidence_payload


@app.get("/api/medgen/{medgen_uid}", summary="MedGen Record Detail", tags=["Evidence & Provenance"])
def get_medgen_record_detail(
    medgen_uid: str = Path(..., description="MedGen record UID")
):
    clean_uid = medgen_uid.strip()
    if not clean_uid or not clean_uid.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid MedGen UID format. Must be a numeric identifier.", "code": "VALIDATION_ERROR"}
        )

    cached_rec = cache.get("medgen_record_detail", uid=clean_uid)
    if cached_rec:
        return cached_rec

    doc_element, _ = fetch_single_medgen_record_xml(clean_uid)
    if doc_element is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"MedGen record with UID '{clean_uid}' was not found.", "code": "RECORD_NOT_FOUND"}
        )

    records, _ = parse_medgen_xml([doc_element])
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"MedGen record with UID '{clean_uid}' could not be parsed.", "code": "RECORD_NOT_FOUND"}
        )

    r = records[0]
    rec_payload = {
        "medgen_uid": r.medgen_uid,
        "disease_title": r.title,
        "concept_id": r.concept_id if r.concept_id else None,
        "semantic_type": r.semantic_type if r.semantic_type else None,
        "definition": r.definition if r.definition else None,
        "source": "NCBI MedGen",
        "access_method": "Biopython Bio.Entrez",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "associated_genes": [
            {
                "symbol": g.symbol,
                "ncbi_gene_id": g.ncbi_gene_id if g.ncbi_gene_id else None,
                "chromosome": g.chromosome if g.chromosome else None,
                "location": g.location if g.location else None,
                "relationship": g.relationship,
                "source": g.source
            }
            for g in r.associated_genes
        ],
        "disclaimer": "This information represents structured data retrieved from NCBI MedGen and does not independently establish clinical causality or diagnostic significance."
    }

    cache.set("medgen_record_detail", rec_payload, ttl=config.CACHE_TTL, uid=clean_uid)
    return rec_payload


@app.post("/api/disease/compare", summary="Disease Comparison & Cross-Disease Intelligence", tags=["Disease Comparison"])
def compare_two_diseases(payload: DiseaseComparisonRequest):
    disease_a, disease_b = validate_disease_comparison(payload.disease_a, payload.disease_b)

    cache_key_str = f"{disease_a}__vs__{disease_b}"
    cached_res = cache.get("compare_workflow", pair=cache_key_str, limit=config.ANALYSIS_LIMIT)
    if cached_res:
        return cached_res

    res_a = _execute_disease_workflow(disease_a)
    res_b = _execute_disease_workflow(disease_b)

    comparison_res = compare_diseases(
        res_a["query"], res_a["records"], res_a["total_search_results"],
        res_b["query"], res_b["records"], res_b["total_search_results"]
    )

    slug_a = sanitize_filename(disease_a)
    slug_b = sanitize_filename(disease_b)
    prefix = f"{slug_a}_vs_{slug_b}"

    # Auto-generate Phase 6B comparison export files
    export_comparison_json(comparison_res, f"results/{prefix}_comparison.json")
    export_comparison_shared_genes_csv(comparison_res, f"results/{prefix}_shared_genes.csv")
    export_comparison_unique_genes_csv(comparison_res, f"results/{prefix}_unique_genes.csv")
    generate_comparison_chart(comparison_res, f"results/{prefix}_comparison.png")

    cache.set("compare_workflow", comparison_res, ttl=config.CACHE_TTL, pair=cache_key_str, limit=config.ANALYSIS_LIMIT)
    return comparison_res


@app.get("/api/discover/diseases", summary="Scientific Discovery: Search MedGen Disease Concepts", tags=["Discovery"])
def discover_diseases_endpoint(
    q: str = Query(..., description="Disease search term (e.g., Alzheimer, cystic fibrosis)"),
    limit: int = Query(25, ge=1, le=50, description="Maximum number of concepts to retrieve")
):
    clean_q = q.strip()
    if not clean_q or len(clean_q) < 2:
        return {
            "query": clean_q,
            "source": "NCBI MedGen",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "total_matches": 0,
            "results": []
        }
    try:
        return discover_disease_concepts(clean_q, limit=limit)
    except NCBIException as ne:
        raise ne
    except Exception as exc:
        logger.error(f"Error in discover_diseases_endpoint for q='{clean_q}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute disease discovery search: {str(exc)}"
        )


@app.get("/api/discover/genes", summary="Scientific Discovery: Search Gene Symbol Associations", tags=["Discovery"])
def discover_genes_endpoint(
    q: str = Query(..., description="Gene symbol search term (e.g., APOE, CFTR)"),
    limit: int = Query(25, ge=1, le=50, description="Maximum number of records to examine")
):
    clean_q = q.strip()
    if not clean_q:
        return {
            "query": clean_q,
            "source": "NCBI MedGen",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "results": []
        }
    try:
        return discover_gene_associations(clean_q, limit=limit)
    except NCBIException as ne:
        raise ne
    except Exception as exc:
        logger.error(f"Error in discover_genes_endpoint for q='{clean_q}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute gene discovery search: {str(exc)}"
        )


@app.get("/api/evidence/health", summary="Evidence Providers Health & Status", tags=["Evidence Providers"])
def evidence_health_endpoint():
    """Returns availability status of all registered evidence providers (MedGen, ClinVar)."""
    return aggregator.get_health()


@app.get("/api/evidence/gene/{gene_symbol}", summary="Unified Multi-Source Gene Evidence", tags=["Evidence Providers"])
def unified_gene_evidence_endpoint(
    gene_symbol: str = Path(..., description="Target gene symbol (e.g. APOE, CFTR)")
):
    """Retrieve normalized evidence from all enabled evidence providers for a gene."""
    symbol = validate_gene_symbol(gene_symbol)
    try:
        return aggregator.aggregate_gene_evidence(symbol)
    except Exception as exc:
        logger.error(f"Error in unified_gene_evidence_endpoint for gene='{symbol}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve unified evidence for gene '{symbol}': {str(exc)}"
        )


# ==================================================
# PHASE 9: KNOWLEDGE GRAPH & SIMILARITY ENDPOINTS
# ==================================================

@app.get("/api/graph/disease/{disease_name}", summary="Knowledge Graph: Disease-Centric Network", tags=["Knowledge Graph"])
def disease_knowledge_graph_endpoint(
    disease_name: str = Path(..., description="Target disease name"),
    max_genes: int = Query(15, ge=1, le=50, description="Maximum gene nodes to include"),
    include_records: bool = Query(True, description="Whether to include MedGen record nodes")
):
    """Return bounded evidence-backed knowledge graph centered on a disease."""
    clean_name = validate_disease_name(disease_name)
    cache_key = f"graph_disease:{clean_name.lower()}:{max_genes}:{include_records}"
    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"Cache hit for disease knowledge graph: '{clean_name}'")
        return cached_val

    try:
        graph = build_disease_knowledge_graph(
            disease_name=clean_name,
            max_genes=max_genes,
            include_records=include_records
        )
        cache.set(cache_key, graph, ttl=config.CACHE_TTL)
        return graph
    except NCBIException as ne:
        raise ne
    except Exception as exc:
        logger.error(f"Error building disease knowledge graph for '{clean_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build knowledge graph for disease '{clean_name}': {str(exc)}"
        )


@app.get("/api/graph/gene/{gene_symbol}", summary="Knowledge Graph: Gene-Centric Network", tags=["Knowledge Graph"])
def gene_knowledge_graph_endpoint(
    gene_symbol: str = Path(..., description="Target gene symbol"),
    max_diseases: int = Query(15, ge=1, le=50, description="Maximum disease nodes to include"),
    include_records: bool = Query(True, description="Whether to include MedGen record nodes")
):
    """Return bounded evidence-backed knowledge graph centered on a gene."""
    symbol = validate_gene_symbol(gene_symbol)
    cache_key = f"graph_gene:{symbol.lower()}:{max_diseases}:{include_records}"
    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"Cache hit for gene knowledge graph: '{symbol}'")
        return cached_val

    try:
        graph = build_gene_knowledge_graph(
            gene_symbol=symbol,
            max_diseases=max_diseases,
            include_records=include_records
        )
        cache.set(cache_key, graph, ttl=config.CACHE_TTL)
        return graph
    except NCBIException as ne:
        raise ne
    except Exception as exc:
        logger.error(f"Error building gene knowledge graph for '{symbol}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build knowledge graph for gene '{symbol}': {str(exc)}"
        )


@app.get("/api/graph/explore/{node_type}/{node_id}", summary="Knowledge Graph: Bounded Multi-Hop Node Expansion", tags=["Knowledge Graph"])
def explore_graph_node_endpoint(
    node_type: str = Path(..., description="Node type ('disease', 'gene', 'medgen_record')"),
    node_id: str = Path(..., description="Unique node ID (e.g. disease:alzheimer_s_disease, gene:APOE, record:100)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum neighbors to expand")
):
    """Explore and expand graph node (bounded 1st/2nd hop)."""
    valid_types = ["disease", "gene", "medgen_record"]
    clean_type = node_type.strip().lower()
    if clean_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid node_type '{node_type}'. Must be one of {valid_types}"
        )
    if not node_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="node_id cannot be empty"
        )

    try:
        return explore_graph_node(clean_type, node_id, limit=limit)
    except Exception as exc:
        logger.error(f"Error exploring graph node type='{clean_type}', id='{node_id}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explore node '{node_id}': {str(exc)}"
        )


@app.post("/api/similarity/matrix", summary="Multi-Disease Gene-Set Similarity Matrix", tags=["Cross-Disease Comparison"])
def multi_disease_similarity_endpoint(req: MultiSimilarityRequest):
    """Compute pairwise Jaccard similarity matrix and gene overlap for 2 to 10 diseases."""
    if not req.diseases or len(req.diseases) < 2 or len(req.diseases) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Between 2 and 10 unique diseases must be provided for multi-disease similarity analysis."
        )

    validated_diseases = []
    for d in req.diseases:
        clean_d = validate_disease_name(d)
        if clean_d not in validated_diseases:
            validated_diseases.append(clean_d)

    if len(validated_diseases) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 distinct disease names must be provided after validation."
        )

    sorted_key = ",".join(sorted([d.lower() for d in validated_diseases]))
    cache_key = f"multi_similarity:{sorted_key}:{req.max_records}"
    cached_val = cache.get(cache_key)
    if cached_val:
        logger.info(f"Cache hit for multi-disease similarity matrix: {validated_diseases}")
        return cached_val

    try:
        result = calculate_multi_disease_similarity(
            disease_names=validated_diseases,
            max_records=req.max_records or 100
        )
        cache.set(cache_key, result, ttl=config.CACHE_TTL)
        return result
    except NCBIException as ne:
        raise ne
    except Exception as exc:
        logger.error(f"Error calculating multi-disease similarity matrix: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute similarity matrix: {str(exc)}"
        )


# ==================================================
# PHASE 10: RESEARCH REPORT ENDPOINTS
# ==================================================

@app.post("/api/reports/disease", summary="Generate Disease Research Report", tags=["Research Reports"])
def generate_disease_report_endpoint(req: DiseaseReportRequest):
    """Generate a deterministic, reproducible disease research report."""
    clean_name = validate_disease_name(req.disease_name)
    try:
        report = build_disease_report(clean_name, req.max_records)
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Error generating disease report for '{clean_name}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate disease report: {str(exc)}"
        )


@app.post("/api/reports/gene", summary="Generate Gene Research Report", tags=["Research Reports"])
def generate_gene_report_endpoint(req: GeneReportRequest):
    """Generate a deterministic, reproducible gene research report."""
    symbol = validate_gene_symbol(req.gene_symbol)
    try:
        report = build_gene_report(symbol)
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Error generating gene report for '{symbol}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate gene report: {str(exc)}"
        )


@app.post("/api/reports/comparison", summary="Generate Disease Comparison Report", tags=["Research Reports"])
def generate_comparison_report_endpoint(req: ComparisonReportRequest):
    """Generate a deterministic disease comparison research report."""
    clean_a, clean_b = validate_disease_comparison(req.disease_a, req.disease_b)
    try:
        report = build_comparison_report(clean_a, clean_b)
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Error generating comparison report for '{clean_a}' vs '{clean_b}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comparison report: {str(exc)}"
        )


@app.post("/api/reports/similarity", summary="Generate Multi-Disease Similarity Report", tags=["Research Reports"])
def generate_similarity_report_endpoint(req: MultiSimilarityRequest):
    """Generate a deterministic multi-disease similarity matrix research report."""
    if not req.diseases or len(req.diseases) < 2 or len(req.diseases) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Between 2 and 10 diseases required."
        )
    validated = [validate_disease_name(d) for d in req.diseases]
    try:
        report = build_similarity_report(validated)
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Error generating similarity report: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate similarity report: {str(exc)}"
        )


@app.post("/api/reports/graph", summary="Generate Knowledge Graph Report", tags=["Research Reports"])
def generate_graph_report_endpoint(req: GraphReportRequest):
    """Generate a deterministic knowledge graph research report."""
    try:
        report = build_graph_report(req.query, req.node_type or "disease")
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Error generating graph report for '{req.query}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate graph report: {str(exc)}"
        )


@app.post("/api/reports/workspace", summary="Generate Research Workspace Integrated Report", tags=["Research Reports"])
def generate_workspace_report_endpoint(req: WorkspaceReportRequest):
    """Generate a deterministic report summarizing saved Research Workspace findings."""
    try:
        report = build_workspace_report(req.workspace)
        return report.to_dict()
    except Exception as exc:
        logger.error(f"Error generating workspace report: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workspace report: {str(exc)}"
        )


@app.get("/api/reports/{report_id}", summary="Get Stored Research Report by ID", tags=["Research Reports"])
def get_report_endpoint(report_id: str = Path(..., description="Unique report ID")):
    """Retrieve stored report object from cache."""
    stored = get_report_by_id(report_id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found or expired."
        )
    return stored


@app.get("/api/reports/{report_id}/export/{format}", summary="Export Research Report File", tags=["Research Reports"])
def export_report_endpoint(
    report_id: str = Path(..., description="Unique report ID"),
    format: str = Path(..., description="Export format ('html', 'json', 'csv_genes', 'csv_evidence')")
):
    """Export stored report into standalone HTML, JSON, or CSV file."""
    stored = get_report_by_id(report_id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found or expired."
        )

    fmt = format.strip().lower()
    slug = sanitize_filename(stored.get("metadata", {}).get("query", "report"))

    if fmt == "html":
        file_path = export_report_html(stored, f"results/{slug}_research_report.html")
        return FileResponse(file_path, media_type="text/html", filename=os.path.basename(file_path))
    elif fmt == "json":
        file_path = export_report_json(stored, f"results/{slug}_research_report.json")
        return FileResponse(file_path, media_type="application/json", filename=os.path.basename(file_path))
    elif fmt == "csv_genes":
        file_path = export_report_genes_csv(stored, f"results/{slug}_report_genes.csv")
        return FileResponse(file_path, media_type="text/csv", filename=os.path.basename(file_path))
    elif fmt == "csv_evidence":
        file_path = export_report_evidence_csv(stored, f"results/{slug}_report_evidence.csv")
        return FileResponse(file_path, media_type="text/csv", filename=os.path.basename(file_path))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{format}'. Must be one of 'html', 'json', 'csv_genes', 'csv_evidence'."
        )


# ==============================================================================
# PHASE 11 — REPRODUCIBILITY, CITATION & PUBLICATION EVIDENCE ENDPOINTS
# ==============================================================================

@app.post("/api/reproducibility/snapshot", summary="Create Analysis Snapshot", tags=["Research Reproducibility"])
def create_snapshot_endpoint(req: SnapshotCreateRequest):
    """
    Create an immutable AnalysisSnapshot with a canonical SHA-256 hash.
    """
    try:
        snapshot = create_analysis_snapshot(req.report_data, req.workspace)
        manifest = build_reproducibility_manifest(snapshot)
        return {
            "snapshot": snapshot.model_dump(),
            "manifest": manifest.model_dump()
        }
    except Exception as exc:
        logger.error(f"Error creating snapshot: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis snapshot: {str(exc)}"
        )


@app.post("/api/reproducibility/report/{report_id}", summary="Create Snapshot from Existing Report ID", tags=["Research Reproducibility"])
def create_snapshot_from_report_endpoint(report_id: str = Path(..., description="Unique report ID")):
    """
    Generate an immutable reproducibility snapshot and manifest directly from an existing report ID.
    Reuses existing cached report data without extra NCBI queries.
    """
    stored = get_report_by_id(report_id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found or expired."
        )
    
    snapshot = create_analysis_snapshot(stored)
    manifest = build_reproducibility_manifest(snapshot)
    return {
        "snapshot": snapshot.model_dump(),
        "manifest": manifest.model_dump()
    }


@app.get("/api/reproducibility/snapshot/{snapshot_id}", summary="Get Snapshot by ID", tags=["Research Reproducibility"])
def get_snapshot_endpoint(snapshot_id: str = Path(..., description="Unique snapshot ID")):
    """
    Retrieve an immutable AnalysisSnapshot by ID.
    """
    snapshot = get_snapshot_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found or expired."
        )
    return snapshot.model_dump()


@app.get("/api/reproducibility/snapshot/{snapshot_id}/manifest", summary="Get Reproducibility Manifest", tags=["Research Reproducibility"])
def get_snapshot_manifest_endpoint(snapshot_id: str = Path(..., description="Unique snapshot ID")):
    """
    Retrieve the ReproducibilityManifest for a snapshot.
    """
    snapshot = get_snapshot_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found or expired."
        )
    manifest = build_reproducibility_manifest(snapshot)
    return manifest.model_dump()


@app.get("/api/reproducibility/snapshot/{snapshot_id}/citations", summary="Get Structured Citations", tags=["Research Reproducibility"])
def get_snapshot_citations_endpoint(snapshot_id: str = Path(..., description="Unique snapshot ID")):
    """
    Retrieve structured MedGen and ClinVar citations with official NCBI source URLs.
    """
    snapshot = get_snapshot_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found or expired."
        )
    citations = extract_citations_from_report(snapshot.model_dump())
    return [c.model_dump() for c in citations]


@app.get("/api/reproducibility/snapshot/{snapshot_id}/export/{format}", summary="Export Reproducibility Files or ZIP Package", tags=["Research Reproducibility"])
def export_snapshot_package_endpoint(
    snapshot_id: str = Path(..., description="Unique snapshot ID"),
    format: str = Path(..., description="Export format: 'zip', 'json', 'csv', 'publication_csv', 'manifest', 'readme'")
):
    """
    Export snapshot as a complete ZIP reproducibility package or individual manifest/CSV files.
    """
    snapshot = get_snapshot_by_id(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found or expired."
        )

    fmt = format.strip().lower()
    slug = sanitize_filename(snapshot.query or snapshot_id).lower()

    if fmt == "zip":
        zip_bytes = export_reproducibility_package_zip(snapshot)
        filename = f"{slug}_reproducibility_package.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif fmt == "publication_csv" or fmt == "csv":
        csv_str = export_publication_evidence_csv(snapshot)
        filename = f"{slug}_publication_evidence.csv"
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif fmt == "json":
        return snapshot.model_dump()
    elif fmt == "manifest":
        manifest = build_reproducibility_manifest(snapshot)
        return manifest.model_dump()
    elif fmt == "readme":
        files = build_reproducibility_package_files(snapshot)
        return Response(content=files["README.txt"], media_type="text/plain")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{format}'. Supported: 'zip', 'json', 'csv', 'publication_csv', 'manifest', 'readme'."
        )


# ==============================================================================
# PRODUCTION STATIC FRONTEND SERVING & SPA ROUTING
# ==============================================================================

def find_static_dir() -> Optional[str]:
    """
    Locates production static frontend directory if built.
    Checks:
    1. STATIC_DIR environment variable
    2. /app/static (standard in Docker container)
    3. ./static (relative to project root)
    4. ./frontend/dist (local build directory)
    Returns absolute path if directory exists and contains index.html, else None.
    """
    candidates = []
    env_dir = os.environ.get("STATIC_DIR", "").strip()
    if env_dir:
        candidates.append(env_dir)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(base_dir, "static"),
        "/app/static",
        os.path.join(base_dir, "frontend", "dist"),
    ])

    for c in candidates:
        abs_c = os.path.abspath(c)
        if os.path.isdir(abs_c) and os.path.isfile(os.path.join(abs_c, "index.html")):
            return abs_c
    return None


def setup_static_routes(target_app: FastAPI, static_dir: Optional[str] = None) -> Optional[str]:
    """
    Configures production static file serving and SPA fallback for React frontend.
    Only active if static directory exists with index.html.
    Returns the resolved static directory if configured, or None.
    """
    candidate = static_dir or find_static_dir()
    if not candidate or not os.path.isdir(candidate) or not os.path.isfile(os.path.join(candidate, "index.html")):
        logger.info("Static frontend build not found; running in API-only mode.")
        return None

    resolved_dir = os.path.abspath(candidate)

    logger.info(f"Serving production frontend from: {resolved_dir}")

    # Mount /assets if assets subfolder exists
    assets_dir = os.path.join(resolved_dir, "assets")
    if os.path.isdir(assets_dir):
        target_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_html = os.path.join(resolved_dir, "index.html")

    @target_app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(index_html, media_type="text/html")

    @target_app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_fallback(full_path: str):
        # 1. Never serve HTML for API routes or docs
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API endpoint '/{full_path}' not found."
            )

        # 2. Check if a static file directly exists in static root (e.g., /background.png, /favicon.ico)
        target_path = os.path.abspath(os.path.join(resolved_dir, full_path))
        if target_path.startswith(resolved_dir) and os.path.isfile(target_path):
            return FileResponse(target_path)

        # 3. Missing static assets with file extensions should return 404, not index.html
        _, ext = os.path.splitext(full_path)
        if ext:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset '/{full_path}' not found."
            )

        # 4. Client-side SPA routes (e.g. /about, /discover, /disease/Alzheimer, etc.)
        return FileResponse(index_html, media_type="text/html")

    return resolved_dir


# Initialize production static routes on primary app instance
setup_static_routes(app)







