import pytest
from unittest.mock import patch, MagicMock
from src.graph import (
    build_disease_knowledge_graph,
    build_gene_knowledge_graph,
    explore_graph_node,
    slugify,
    create_disease_node_id,
    create_gene_node_id,
    create_record_node_id
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
            definition="A progressive neurodegenerative disorder.",
            associated_genes=[
                GeneAssociation(symbol="APOE", ncbi_gene_id="348"),
                GeneAssociation(symbol="APP", ncbi_gene_id="351")
            ]
        ),
        DiseaseRecord(
            medgen_uid="1002",
            title="Alzheimer Disease 2",
            concept_id="C0002395",
            semantic_type="Disease or Syndrome",
            definition="Subtype of Alzheimer disease.",
            associated_genes=[
                GeneAssociation(symbol="APOE", ncbi_gene_id="348"),
                GeneAssociation(symbol="PSEN1", ncbi_gene_id="5663")
            ]
        )

    ]

@patch("src.graph.search_medgen")
@patch("src.graph.fetch_medgen_records_xml")
@patch("src.graph.parse_medgen_xml")
def test_build_disease_knowledge_graph(mock_parse, mock_fetch, mock_search, mock_disease_records):
    mock_search.return_value = (2, 2, ["1001", "1002"], "exact")
    mock_fetch.return_value = "<xml></xml>"
    mock_parse.return_value = mock_disease_records

    graph = build_disease_knowledge_graph("Alzheimer's disease", max_genes=10, include_records=True)

    assert graph["query"] == "Alzheimer's disease"
    assert "nodes" in graph
    assert "edges" in graph
    assert graph["summary"]["disease_nodes"] >= 1
    assert graph["summary"]["gene_nodes"] == 3 # APOE, APP, PSEN1

    # Verify nodes
    node_types = {n["node_type"] for n in graph["nodes"]}
    assert "disease" in node_types
    assert "gene" in node_types
    assert "medgen_record" in node_types

    # Verify direct edge relationship & provenance
    direct_edges = [e for e in graph["edges"] if e["relationship"] == "direct_associated_gene"]
    assert len(direct_edges) > 0
    for e in direct_edges:
        assert e["source"] == "NCBI MedGen"
        assert e["evidence_type"] == "NCBI MedGen AssociatedGenes"


@patch("src.graph.search_medgen_by_gene")
@patch("src.graph.fetch_medgen_records_xml")
@patch("src.graph.parse_medgen_xml")
def test_build_gene_knowledge_graph(mock_parse, mock_fetch, mock_search, mock_disease_records):
    mock_search.return_value = (["1001", "1002"], 2, "gene_symbol")
    mock_fetch.return_value = "<xml></xml>"
    mock_parse.return_value = mock_disease_records

    graph = build_gene_knowledge_graph("APOE", max_diseases=10, include_records=True)

    assert graph["query"] == "APOE"
    gene_nodes = [n for n in graph["nodes"] if n["node_type"] == "gene"]
    assert len(gene_nodes) == 1
    assert gene_nodes[0]["symbol"] == "APOE"


def test_explore_graph_node_invalid_type():
    with pytest.raises(ValueError):
        explore_graph_node("invalid_type", "node_123")
