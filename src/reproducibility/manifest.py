import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.config import config
from src.reproducibility.models import AnalysisSnapshot, ReproducibilityManifest

def build_reproducibility_manifest(snapshot: AnalysisSnapshot) -> ReproducibilityManifest:
    """
    Construct a ReproducibilityManifest from an AnalysisSnapshot.
    Excludes personal data or machine-identifying telemetry.
    """
    params = snapshot.parameters or {}
    prov = snapshot.provenance or {}
    
    # Extract source record UIDs / ClinVar variation IDs
    source_record_ids = set()
    for ev in snapshot.evidence:
        uid = ev.get("medgen_uid") or ev.get("uid") or ev.get("record_id")
        if uid:
            source_record_ids.add(str(uid))
    for rec in snapshot.records:
        uid = rec.get("medgen_uid") or rec.get("uid")
        if uid:
            source_record_ids.add(str(uid))
            
    # Extract gene IDs
    gene_ids = set()
    for g in snapshot.gene_associations:
        gid = g.get("ncbi_gene_id") or g.get("NCBI_Gene_ID") or g.get("gene_id")
        if gid:
            gene_ids.add(str(gid))
    for ev in snapshot.evidence:
        gid = ev.get("ncbi_gene_id") or ev.get("NCBI_Gene_ID") or ev.get("gene_id")
        if gid:
            gene_ids.add(str(gid))
            
    # Extract disease concepts
    disease_concepts = set()
    for ev in snapshot.evidence:
        cid = ev.get("concept_id")
        if cid:
            disease_concepts.add(str(cid))
            
    manifest_id = f"MAN-{snapshot.snapshot_hash[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    retrieval_ts = (
        prov.get("retrieval_timestamp") or
        snapshot.created_at
    )
    
    return ReproducibilityManifest(
        manifest_id=manifest_id,
        created_at=now_iso,
        software_version=config.GENEDXPLORER_VERSION,
        analysis_schema_version=config.ANALYSIS_SCHEMA_VERSION,
        snapshot_schema_version=config.SNAPSHOT_SCHEMA_VERSION,
        report_id=snapshot.report_id,
        report_type=snapshot.report_type,
        query=snapshot.query,
        search_strategy=snapshot.search_strategy,
        source_providers=config.EVIDENCE_PROVIDERS,
        records_available=params.get("records_available", len(source_record_ids)),
        records_retrieved=params.get("records_retrieved", len(source_record_ids)),
        records_analyzed=params.get("records_analyzed", len(source_record_ids)),
        analysis_limit=params.get("analysis_limit", config.ANALYSIS_LIMIT),
        retrieval_timestamp=retrieval_ts,
        analysis_parameters={
            "analysis_limit": params.get("analysis_limit", config.ANALYSIS_LIMIT),
            "search_strategy": snapshot.search_strategy,
            "max_records": params.get("max_records", config.ANALYSIS_LIMIT)
        },
        source_record_ids=sorted(list(source_record_ids)),
        gene_ids=sorted(list(gene_ids)),
        disease_concepts=sorted(list(disease_concepts)),
        calculation_method="Deterministic MedGen XML parsing, frequency calculation, and set-theoretic Jaccard overlap",
        export_formats=["json", "csv", "zip", "publication_csv"],
        snapshot_hash=snapshot.snapshot_hash,
        python_version=sys.version.split()[0],
        platform=sys.platform
    )
