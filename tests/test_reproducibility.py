import json
import pytest
import io
import zipfile
from src.reproducibility import (
    canonicalize_snapshot_payload,
    compute_snapshot_hash,
    create_analysis_snapshot,
    get_snapshot_by_id,
    build_reproducibility_manifest,
    build_reproducibility_package_files,
    export_reproducibility_package_zip,
    export_publication_evidence_csv,
    sanitize_filename,
    validate_safe_path,
    escape_html_value,
    filter_secrets
)

def test_canonicalize_and_hash_determinism():
    payload_a = {
        "query": "Alzheimer's disease",
        "analysis_scope": {"records_analyzed": 50, "analysis_limit": 500},
        "gene_associations": [
            {"Gene": "APOE", "Record_Count": 20},
            {"Gene": "APP", "Record_Count": 15}
        ]
    }
    
    # Reverse key order in payload_b
    payload_b = {
        "gene_associations": [
            {"Record_Count": 20, "Gene": "APOE"},
            {"Record_Count": 15, "Gene": "APP"}
        ],
        "query": "Alzheimer's disease",
        "analysis_scope": {"analysis_limit": 500, "records_analyzed": 50}
    }
    
    canon_a = canonicalize_snapshot_payload(payload_a)
    canon_b = canonicalize_snapshot_payload(payload_b)
    
    assert canon_a == canon_b
    
    hash_a = compute_snapshot_hash(canon_a)
    hash_b = compute_snapshot_hash(canon_b)
    
    assert hash_a == hash_b
    assert len(hash_a) == 64


def test_create_analysis_snapshot():
    report_data = {
        "report_metadata": {
            "report_id": "REP-TEST-1001",
            "report_type": "disease",
            "query": "Cystic fibrosis",
            "source": "NCBI MedGen"
        },
        "analysis_scope": {
            "records_retrieved": 10,
            "records_analyzed": 10,
            "analysis_limit": 500,
            "search_strategy": "exact"
        },
        "gene_analysis": {
            "ranked_genes": [
                {"Gene": "CFTR", "NCBI_Gene_ID": "1080", "Record_Count": 10, "Record_Percentage": 100.0}
            ]
        },
        "evidence": [
            {"medgen_uid": "2001", "gene": "CFTR", "disease_title": "Cystic Fibrosis", "source": "NCBI MedGen"}
        ]
    }
    
    snapshot = create_analysis_snapshot(report_data)
    assert snapshot.snapshot_id.startswith("SNAP-")
    assert len(snapshot.snapshot_hash) == 64
    assert snapshot.query == "Cystic fibrosis"
    assert len(snapshot.gene_associations) == 1
    
    fetched = get_snapshot_by_id(snapshot.snapshot_id)
    assert fetched is not None
    assert fetched.snapshot_hash == snapshot.snapshot_hash


def test_build_reproducibility_manifest():
    report_data = {
        "report_metadata": {
            "report_id": "REP-TEST-1002",
            "report_type": "disease",
            "query": "Alzheimer's disease"
        },
        "analysis_scope": {"records_analyzed": 5, "analysis_limit": 500},
        "evidence": [
            {"medgen_uid": "1001", "concept_id": "C0002395", "ncbi_gene_id": "348", "gene": "APOE"}
        ]
    }
    
    snapshot = create_analysis_snapshot(report_data)
    manifest = build_reproducibility_manifest(snapshot)
    
    assert manifest.manifest_id.startswith("MAN-")
    assert manifest.query == "Alzheimer's disease"
    assert manifest.snapshot_hash == snapshot.snapshot_hash
    assert "1001" in manifest.source_record_ids
    assert "348" in manifest.gene_ids
    assert "C0002395" in manifest.disease_concepts


def test_reproducibility_package_files():
    report_data = {
        "report_metadata": {"report_id": "REP-PKG-01", "report_type": "disease", "query": "Parkinson disease"},
        "gene_analysis": {"ranked_genes": [{"Gene": "SNCA", "NCBI_Gene_ID": "6622", "Record_Count": 5, "Record_Percentage": 50.0}]},
        "evidence": [{"medgen_uid": "3001", "gene": "SNCA", "disease_title": "Parkinson Disease 1"}]
    }
    
    snapshot = create_analysis_snapshot(report_data)
    files = build_reproducibility_package_files(snapshot)
    
    required_files = [
        "manifest.json",
        "snapshot.json",
        "report.json",
        "publication_evidence.csv",
        "genes.csv",
        "evidence.csv",
        "citations.csv",
        "README.txt"
    ]
    
    for f in required_files:
        assert f in files
        assert len(files[f]) > 0


def test_zip_package_export():
    report_data = {
        "report_metadata": {"query": "ALS"},
        "gene_analysis": {"ranked_genes": [{"Gene": "SOD1", "NCBI_Gene_ID": "6647"}]}
    }
    
    snapshot = create_analysis_snapshot(report_data)
    zip_bytes = export_reproducibility_package_zip(snapshot)
    
    assert len(zip_bytes) > 0
    
    # Read zip bytes
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    namelist = zf.namelist()
    
    assert any("manifest.json" in n for n in namelist)
    assert any("publication_evidence.csv" in n for n in namelist)
    assert any("README.txt" in n for n in namelist)


def test_security_sanitization_and_secrets():
    # 1. Filename sanitization
    unsafe_name = "../../etc/passwd/report.json"
    safe_name = sanitize_filename(unsafe_name)
    assert ".." not in safe_name
    assert "/" not in safe_name
    assert safe_name == "report.json"

    # 2. Path traversal validation
    base_directory = "/tmp/safe_dir"
    assert validate_safe_path(base_directory, "/tmp/safe_dir/export.json") is True
    assert validate_safe_path(base_directory, "/tmp/other_dir/hack.json") is False

    # 3. HTML escaping
    unsafe_html = "<script>alert('xss')</script>"
    safe_html = escape_html_value(unsafe_html)
    assert "<script>" not in safe_html
    assert "&lt;script&gt;" in safe_html

    # 4. Secret redaction
    payload_with_secret = {
        "query": "Alzheimer",
        "ncbi_api_key": "SECRET_KEY_12345",
        "normal_data": "public_val"
    }
    cleaned = filter_secrets(payload_with_secret)
    assert cleaned["ncbi_api_key"] == "[REDACTED_SECRET]"
    assert cleaned["normal_data"] == "public_val"
