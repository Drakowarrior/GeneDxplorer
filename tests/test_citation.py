import pytest
from src.reproducibility.citation import (
    construct_official_ncbi_url,
    build_medgen_citation,
    build_clinvar_citation,
    extract_citations_from_report
)

def test_construct_official_ncbi_url():
    url_mg = construct_official_ncbi_url("NCBI MedGen", "medgen", "1001")
    assert url_mg == "https://www.ncbi.nlm.nih.gov/medgen/1001"

    url_cv = construct_official_ncbi_url("NCBI ClinVar", "clinvar_variation", "12345")
    assert url_cv == "https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/"

    url_gene = construct_official_ncbi_url("NCBI Gene", "gene", "348")
    assert url_gene == "https://www.ncbi.nlm.nih.gov/gene/348"


def test_build_medgen_citation():
    cit = build_medgen_citation(
        record_uid="1001",
        concept_id="C0002395",
        title="Alzheimer Disease 1",
        gene_symbol="APP",
        disease_title="Alzheimer's disease"
    )
    assert cit.source == "NCBI MedGen"
    assert cit.record_id == "1001"
    assert cit.gene_symbol == "APP"
    assert "medgen/1001" in cit.official_url
    assert cit.citation_id.startswith("CIT-MG-")


def test_build_clinvar_citation():
    cit = build_clinvar_citation(
        variation_id="12345",
        gene_symbol="APOE",
        condition_title="Alzheimer Disease",
        clinical_significance="Pathogenic",
        review_status="reviewed by expert panel"
    )
    assert cit.source == "NCBI ClinVar"
    assert cit.record_id == "12345"
    assert cit.clinical_significance == "Pathogenic"
    assert "clinvar/variation/12345" in cit.official_url
    assert cit.citation_id.startswith("CIT-CV-")


def test_extract_citations_from_report():
    dummy_report = {
        "report_metadata": {
            "query": "Alzheimer's disease",
            "retrieval_timestamp": "2026-10-07T00:00:00Z"
        },
        "evidence": [
            {
                "medgen_uid": "1001",
                "source": "NCBI MedGen",
                "gene": "APP",
                "disease_title": "Alzheimer Disease 1"
            },
            {
                "uid": "67890",
                "source": "NCBI ClinVar",
                "gene": "APOE",
                "disease_title": "Alzheimer's disease",
                "clinical_significance": "Risk factor"
            }
        ]
    }

    citations = extract_citations_from_report(dummy_report)
    assert len(citations) == 2
    sources = [c.source for c in citations]
    assert "NCBI MedGen" in sources
    assert "NCBI ClinVar" in sources
