import json
import csv
import io
import zipfile
from typing import Dict, Any, Union
from datetime import datetime, timezone

from src.config import config
from src.reproducibility.models import AnalysisSnapshot
from src.reproducibility.manifest import build_reproducibility_manifest
from src.reproducibility.citation import extract_citations_from_report, construct_official_ncbi_url
from src.reproducibility.validators import sanitize_filename

def export_publication_evidence_csv(snapshot: AnalysisSnapshot) -> str:
    """
    Generate publication-ready evidence table CSV.
    Columns: Finding, Gene, NCBI_Gene_ID, Disease, Evidence_Source, Record_ID, Evidence_Type, Source_URL, Retrieved_At, Software_Version
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Finding",
        "Gene",
        "NCBI_Gene_ID",
        "Disease",
        "Evidence_Source",
        "Record_ID",
        "Evidence_Type",
        "Source_URL",
        "Retrieved_At",
        "Software_Version"
    ])
    
    query = snapshot.query or "Analysis"
    software_ver = snapshot.software_version or config.GENEDXPLORER_VERSION
    retrieved_at = snapshot.created_at
    
    # 1. From evidence
    if snapshot.evidence:
        for ev in snapshot.evidence:
            gene = ev.get("gene") or ev.get("symbol") or "N/A"
            ncbi_gene_id = ev.get("ncbi_gene_id") or "N/A"
            disease = ev.get("disease_title") or ev.get("disease") or query
            source = ev.get("source") or ev.get("evidence_source") or "NCBI MedGen"
            uid = ev.get("medgen_uid") or ev.get("uid") or ev.get("record_id") or "N/A"
            ev_type = ev.get("relationship") or ev.get("evidence_type") or "Direct AssociatedGene"
            url = construct_official_ncbi_url(source, "medgen", str(uid)) if uid != "N/A" else "N/A"
            
            writer.writerow([
                f"Reported association: {gene} in {disease}",
                gene,
                ncbi_gene_id,
                disease,
                source,
                uid,
                ev_type,
                url,
                retrieved_at,
                software_ver
            ])
            
    # 2. From gene_associations if no raw evidence list
    elif snapshot.gene_associations:
        for g in snapshot.gene_associations:
            gene = g.get("Gene") or g.get("symbol") or "N/A"
            ncbi_gene_id = g.get("NCBI_Gene_ID") or g.get("ncbi_gene_id") or "N/A"
            count = g.get("Record_Count") or g.get("count") or "N/A"
            pct = g.get("Record_Percentage") or g.get("percentage") or "N/A"
            
            writer.writerow([
                f"Ranked gene association ({count} records, {pct}%)",
                gene,
                ncbi_gene_id,
                query,
                snapshot.source,
                "Multiple MedGen Records",
                "Reported Frequency",
                construct_official_ncbi_url(snapshot.source, "gene", str(ncbi_gene_id)) if ncbi_gene_id != "N/A" else "N/A",
                retrieved_at,
                software_ver
            ])
            
    return output.getvalue()

def build_reproducibility_readme(snapshot: AnalysisSnapshot, manifest_dict: Dict[str, Any]) -> str:
    """
    Generate plaintext scientific README explaining analysis parameters, snapshot hash, data sources, and interpretation rules.
    """
    return f"""GENEDXPLORER SCIENTIFIC REPRODUCIBILITY PACKAGE
======================================================================
Analysis Query:        {snapshot.query}
Report Type:           {snapshot.report_type}
Snapshot ID:           {snapshot.snapshot_id}
Snapshot SHA-256 Hash: {snapshot.snapshot_hash}
Software Version:      {snapshot.software_version}
Generated At:          {snapshot.created_at}
Retrieval Timestamp:   {manifest_dict.get('retrieval_timestamp')}

1. DATA SOURCES & PROVIDERS
----------------------------------------------------------------------
Primary Data Sources:  {', '.join(manifest_dict.get('source_providers', ['NCBI MedGen']))}
Search Strategy:       {snapshot.search_strategy}
Records Available:     {manifest_dict.get('records_available', 'N/A')}
Records Analyzed:      {manifest_dict.get('records_analyzed', 'N/A')}
Analysis Limit:        {manifest_dict.get('analysis_limit', config.ANALYSIS_LIMIT)}

2. PACKAGE CONTENTS
----------------------------------------------------------------------
- manifest.json:             Execution metadata, schema versions, environment properties
- snapshot.json:             Immutable frozen scientific analysis payload
- report.json:               Structured research report model
- publication_evidence.csv:  Normalized publication-ready evidence table
- genes.csv:                 Ranked reported gene frequencies and IDs
- evidence.csv:              Record-level evidence list
- citations.csv:             Structured citations with official NCBI source links
- README.txt:                Package guide and scientific interpretation rules

3. REPRODUCIBILITY INSTRUCTIONS
----------------------------------------------------------------------
To verify or reproduce this analysis:
1. Verify that the SHA-256 hash of snapshot.json matches {snapshot.snapshot_hash}.
2. Run GeneDxplorer v{snapshot.software_version} with query '{snapshot.query}' and analysis limit {manifest_dict.get('analysis_limit', config.ANALYSIS_LIMIT)}.
3. Compare exported snapshot hashes to verify data integrity.

4. SCIENTIFIC INTERPRETATION RULES & DISCLAIMERS
----------------------------------------------------------------------
- Reported Associated Genes: Genes reported in structured <AssociatedGenes> sections of analyzed MedGen records.
- Reporting Frequency: Describes presence in analyzed records, not clinical severity or disease risk.
- Mathematical Overlap: Set-theoretic overlap (Jaccard similarity) represents set similarity between record sets, not clinical or diagnostic similarity.
- Non-Causal: Presence in MedGen or ClinVar records does not establish biological causality or clinical diagnosis.

======================================================================
Generated by GeneDxplorer Scientific Reporting Engine
"""

def build_reproducibility_package_files(snapshot: AnalysisSnapshot) -> Dict[str, str]:
    """
    Build dictionary of package files (filename -> string content).
    """
    manifest = build_reproducibility_manifest(snapshot)
    manifest_dict = manifest.model_dump()
    citations = extract_citations_from_report(snapshot.model_dump())
    
    # 1. manifest.json
    manifest_json = json.dumps(manifest_dict, indent=2)
    
    # 2. snapshot.json
    snapshot_json = json.dumps(snapshot.model_dump(), indent=2)
    
    # 3. report.json
    report_json = json.dumps(snapshot.analysis_results, indent=2)
    
    # 4. publication_evidence.csv
    pub_csv = export_publication_evidence_csv(snapshot)
    
    # 5. genes.csv
    genes_io = io.StringIO()
    g_writer = csv.writer(genes_io)
    g_writer.writerow(["Rank", "Gene", "NCBI_Gene_ID", "Record_Count", "Record_Percentage", "Source"])
    for idx, g in enumerate(snapshot.gene_associations, 1):
        g_writer.writerow([
            g.get("Rank") or idx,
            g.get("Gene") or g.get("symbol") or "N/A",
            g.get("NCBI_Gene_ID") or g.get("ncbi_gene_id") or "N/A",
            g.get("Record_Count") or g.get("count") or 0,
            g.get("Record_Percentage") or g.get("percentage") or 0.0,
            snapshot.source
        ])
    genes_csv = genes_io.getvalue()
    
    # 6. evidence.csv
    ev_io = io.StringIO()
    ev_writer = csv.writer(ev_io)
    ev_writer.writerow(["Disease", "Gene", "MedGen_UID", "Disease_Title", "Relationship", "Source", "Retrieved_At"])
    for ev in snapshot.evidence:
        ev_writer.writerow([
            snapshot.query,
            ev.get("gene") or ev.get("symbol") or "N/A",
            ev.get("medgen_uid") or ev.get("uid") or "N/A",
            ev.get("disease_title") or ev.get("disease") or snapshot.query,
            ev.get("relationship") or ev.get("evidence_type") or "direct",
            ev.get("source") or snapshot.source,
            snapshot.created_at
        ])
    evidence_csv = ev_io.getvalue()
    
    # 7. citations.csv
    cit_io = io.StringIO()
    c_writer = csv.writer(cit_io)
    c_writer.writerow(["Citation_ID", "Source", "Record_ID", "Title", "Evidence_Type", "Gene_Symbol", "Disease_Title", "Official_URL", "Retrieved_At"])
    for c in citations:
        c_writer.writerow([
            c.citation_id,
            c.source,
            c.record_id,
            c.title or "",
            c.evidence_type,
            c.gene_symbol or "",
            c.disease_title or "",
            c.official_url,
            c.retrieved_at
        ])
    citations_csv = cit_io.getvalue()
    
    # 8. README.txt
    readme_txt = build_reproducibility_readme(snapshot, manifest_dict)
    
    return {
        "manifest.json": manifest_json,
        "snapshot.json": snapshot_json,
        "report.json": report_json,
        "publication_evidence.csv": pub_csv,
        "genes.csv": genes_csv,
        "evidence.csv": evidence_csv,
        "citations.csv": citations_csv,
        "README.txt": readme_txt
    }

def export_reproducibility_package_zip(snapshot: AnalysisSnapshot) -> bytes:
    """
    Generate in-memory ZIP archive containing the complete scientific reproducibility package.
    """
    files = build_reproducibility_package_files(snapshot)
    slug = sanitize_filename(snapshot.query or snapshot.snapshot_id).lower()
    pkg_folder = f"{slug}_reproducibility_package"
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            archive_path = f"{pkg_folder}/{fname}"
            zf.writestr(archive_path, content)
            
    return zip_buffer.getvalue()
