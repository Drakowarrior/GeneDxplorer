import pytest
from unittest.mock import patch, MagicMock
from src.reporting import (
    build_disease_report,
    build_gene_report,
    build_comparison_report,
    build_similarity_report,
    build_graph_report,
    build_workspace_report,
    generate_deterministic_summary,
    export_report_html,
    export_report_json,
    export_report_genes_csv,
    export_report_evidence_csv,
    get_report_by_id
)
from src.parser import DiseaseRecord, GeneAssociation

@pytest.fixture
def mock_disease_records():
    return [
        DiseaseRecord(
            medgen_uid="1001",
            title="Alzheimer Disease 1",
            concept_id="C0002395",
            semantic_type="Disease or Syndrome",
            definition="Neurodegenerative disorder.",
            associated_genes=[
                GeneAssociation(symbol="APOE", ncbi_gene_id="348"),
                GeneAssociation(symbol="APP", ncbi_gene_id="351")
            ]
        )
    ]

@patch("src.reporting.builder.build_disease_knowledge_graph")
@patch("src.reporting.builder.search_medgen")
@patch("src.reporting.builder.fetch_medgen_records_xml")
@patch("src.reporting.builder.parse_medgen_xml")
def test_build_disease_report(mock_parse, mock_fetch, mock_search, mock_graph, mock_disease_records):
    mock_search.return_value = (1, 1, ["1001"], "exact")
    mock_fetch.return_value = "<xml></xml>"
    mock_parse.return_value = mock_disease_records
    mock_graph.return_value = {
        "query": "Alzheimer's disease",
        "nodes": [
            {"node_id": "disease:alzheimer", "node_type": "disease", "title": "Alzheimer's disease"},
            {"node_id": "gene:APOE", "node_type": "gene", "symbol": "APOE"},
            {"node_id": "gene:APP", "node_type": "gene", "symbol": "APP"},
            {"node_id": "record:1001", "node_type": "medgen_record", "medgen_uid": "1001"}
        ],
        "edges": [
            {"edge_id": "e1", "source_node": "disease:alzheimer", "target_node": "gene:APOE"},
            {"edge_id": "e2", "source_node": "disease:alzheimer", "target_node": "gene:APP"}
        ],
        "summary": {
            "disease_nodes": 1,
            "gene_nodes": 2,
            "record_nodes": 1,
            "direct_relationships": 2
        }
    }

    report = build_disease_report("Alzheimer's disease", max_records=10)
    report_dict = report.to_dict()

    mock_graph.assert_called_once_with("Alzheimer's disease", max_genes=10, include_records=True)

    assert report_dict["metadata"]["query"] == "Alzheimer's disease"
    assert report_dict["metadata"]["report_type"] == "disease"
    assert "APOE" in report_dict["executive_summary"]
    assert "most frequently reported" in report_dict["executive_summary"]

    assert report_dict["scope"]["records_analyzed"] == 1
    assert report_dict["knowledge_graph"]["disease_nodes"] == 1
    assert report_dict["knowledge_graph"]["gene_nodes"] == 2
    assert report_dict["knowledge_graph"]["direct_relationships"] == 2
    assert len(report_dict["limitations"]) > 0
    assert "provenance" in report_dict

    # Check cache store
    cached = get_report_by_id(report_dict["metadata"]["report_id"])
    assert cached is not None
    assert cached["metadata"]["report_id"] == report_dict["metadata"]["report_id"]


def test_deterministic_summary_generation():
    summary = generate_deterministic_summary("disease", {
        "query": "Cystic fibrosis",
        "records_analyzed": 50,
        "records_with_genes": 45,
        "unique_genes": 12,
        "top_gene_symbol": "CFTR",
        "top_gene_count": 40,
        "top_gene_pct": 80.0
    })
    assert "Cystic fibrosis" in summary
    assert "50 NCBI MedGen record(s)" in summary
    assert "'CFTR' was the most frequently reported associated gene" in summary


def test_report_exporters(tmp_path):
    sample_report = {
        "metadata": {
            "report_id": "report_123",
            "report_type": "disease",
            "title": "Disease Report: Test Disease",
            "generated_at": "2026-10-07T00:00:00Z",
            "software_version": "1.0.0",
            "query": "Test Disease",
            "source": "NCBI MedGen"
        },
        "scope": {"records_analyzed": 10, "records_available": 10},
        "data_quality": {"records_with_genes": 8, "unique_genes": 3},
        "gene_analysis": [
            {"Rank": 1, "Gene": "GENE1", "NCBI_Gene_ID": "100", "Record Count": 8, "Record_Percentage": 80.0}
        ],
        "evidence": [
            {"medgen_uid": "999", "disease_title": "Test Disease", "relationship": "direct", "evidence_type": "NCBI MedGen AssociatedGenes"}
        ],
        "executive_summary": "Test executive summary text.",
        "disclaimer": "Test disclaimer.",
        "limitations": ["Test limitation 1"],
        "provenance": {"query": "Test Disease"}
    }

    html_file = export_report_html(sample_report, str(tmp_path / "test_report.html"))
    assert html_file.endswith("test_report.html")
    with open(html_file, "r") as f:
        content = f.read()
        assert "<title>Disease Report: Test Disease</title>" in content
        assert "GENE1" in content

    json_file = export_report_json(sample_report, str(tmp_path / "test_report.json"))
    assert json_file.endswith("test_report.json")

    genes_csv = export_report_genes_csv(sample_report, str(tmp_path / "test_genes.csv"))
    assert genes_csv.endswith("test_genes.csv")

    evidence_csv = export_report_evidence_csv(sample_report, str(tmp_path / "test_evidence.csv"))
    assert evidence_csv.endswith("test_evidence.csv")
