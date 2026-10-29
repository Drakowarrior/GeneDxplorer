import pytest
from src.parser import DiseaseRecord, GeneAssociation
from src.analysis import (
    analyze_disease_genes,
    analyze_gene_to_disease,
    compare_diseases
)

@pytest.fixture
def sample_parsed_records():
    r1 = DiseaseRecord(
        medgen_uid="101",
        title="Disease One",
        associated_genes=[
            GeneAssociation(symbol="GENEA", ncbi_gene_id="10"),
            GeneAssociation(symbol="GENEB", ncbi_gene_id="20")
        ]
    )
    r2 = DiseaseRecord(
        medgen_uid="102",
        title="Disease Two",
        associated_genes=[
            GeneAssociation(symbol="GENEA", ncbi_gene_id="10")
        ]
    )
    r3 = DiseaseRecord(
        medgen_uid="103",
        title="Disease Three",
        associated_genes=[
            GeneAssociation(symbol="GENEC", ncbi_gene_id="30")
        ]
    )
    return [r1, r2, r3]


def test_analyze_disease_genes_ranking(sample_parsed_records):
    df_sorted, payload = analyze_disease_genes(sample_parsed_records, "Sample Disease", total_search_results=10)
    
    assert payload["unique_genes"] == 3
    assert payload["records_analyzed"] == 3
    assert payload["records_with_genes"] == 3
    assert len(df_sorted) == 3

    # Rank 1: GENEA (count = 2)
    top_gene = df_sorted.iloc[0]
    assert top_gene["Rank"] == 1
    assert top_gene["Gene"] == "GENEA"
    assert top_gene["Record Count"] == 2
    assert top_gene["Record_Percentage"] == 66.67


def test_analyze_gene_to_disease_filtering(sample_parsed_records):
    df_diseases, payload = analyze_gene_to_disease("GENEA", sample_parsed_records, total_search_results=10)
    
    assert payload["matching_disease_count"] == 2
    assert len(df_diseases) == 2
    titles = df_diseases["title"].tolist()
    assert "Disease One" in titles
    assert "Disease Two" in titles
    assert "Disease Three" not in titles


def test_compare_diseases_overlap_metrics():
    records_a = [
        DiseaseRecord(
            medgen_uid="1", title="Disease A1",
            associated_genes=[GeneAssociation(symbol="APOE"), GeneAssociation(symbol="APP")]
        )
    ]
    records_b = [
        DiseaseRecord(
            medgen_uid="2", title="Disease B1",
            associated_genes=[GeneAssociation(symbol="APP"), GeneAssociation(symbol="PSEN1")]
        )
    ]

    res = compare_diseases("Disease A", records_a, 1, "Disease B", records_b, 1)

    assert res["shared_genes_count"] == 1  # APP
    assert res["unique_to_a_count"] == 1   # APOE
    assert res["unique_to_b_count"] == 1   # PSEN1
    assert res["combined_unique_genes_count"] == 3  # APOE, APP, PSEN1
    
    sim = res["similarity"]
    # Jaccard = 1 / 3 = 33.33%
    assert sim["jaccard_percentage"] == 33.33
    # Overlap Coeff = 1 / min(2, 2) = 50.0%
    assert sim["overlap_coefficient"] == 50.0
    # Coverage = 1 / 2 = 50.0%
    assert sim["coverage_a_percentage"] == 50.0
    assert sim["coverage_b_percentage"] == 50.0

    # Research summary generated
    assert "research_summary" in res
    assert "GeneDxplorer analyzed" in res["research_summary"]["summary"]


def test_compare_diseases_evidence_references():
    records_a = [
        DiseaseRecord(
            medgen_uid="100", title="Disease A1",
            associated_genes=[GeneAssociation(symbol="SHARED1")]
        )
    ]
    records_b = [
        DiseaseRecord(
            medgen_uid="200", title="Disease B1",
            associated_genes=[GeneAssociation(symbol="SHARED1")]
        )
    ]

    res = compare_diseases("Disease A", records_a, 1, "Disease B", records_b, 1)
    shared = res["shared_genes"][0]
    assert shared["Gene"] == "SHARED1"
    assert len(shared["evidence_a"]) == 1
    assert shared["evidence_a"][0]["medgen_uid"] == "100"
    assert len(shared["evidence_b"]) == 1
    assert shared["evidence_b"][0]["medgen_uid"] == "200"
