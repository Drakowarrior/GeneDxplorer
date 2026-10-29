from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from api import app
from src.parser import DiseaseRecord, GeneAssociation
from src.analysis import discover_disease_concepts, discover_gene_associations

client = TestClient(app)

@pytest.fixture
def mock_discovery_ncbi():
    sample_records = [
        DiseaseRecord(
            medgen_uid="777",
            title="Alzheimer disease 1",
            concept_id="C0002395",
            semantic_type="Disease or Syndrome",
            definition="A progressive neurodegenerative disease.",
            associated_genes=[
                GeneAssociation(symbol="APOE", ncbi_gene_id="348", chromosome="19", location="19q13.32")
            ]
        )
    ]
    with patch("src.analysis.search_medgen") as mock_search_d, \
         patch("src.analysis.search_medgen_by_gene") as mock_search_g, \
         patch("src.analysis.fetch_medgen_records_xml") as mock_fetch, \
         patch("src.analysis.parse_medgen_xml") as mock_parse:

        mock_search_d.return_value = (5, 1, ["777"], "Mock Strategy")
        mock_search_g.return_value = (5, ["777"], "Mock Gene Strategy")
        mock_fetch.return_value = [object()]
        mock_parse.return_value = sample_records
        yield


def test_discover_disease_concepts_unit(mock_discovery_ncbi):
    res = discover_disease_concepts("Alzheimer", limit=10)
    assert res["query"] == "Alzheimer"
    assert res["source"] == "NCBI MedGen"
    assert len(res["results"]) == 1
    assert res["results"][0]["medgen_uid"] == "777"
    assert res["results"][0]["title"] == "Alzheimer disease 1"
    assert res["results"][0]["associated_gene_count"] == 1


def test_discover_gene_associations_unit(mock_discovery_ncbi):
    res = discover_gene_associations("APOE", limit=10)
    assert res["query"] == "APOE"
    assert len(res["results"]) == 1
    assert res["results"][0]["symbol"] == "APOE"
    assert res["results"][0]["ncbi_gene_id"] == "348"
    assert res["results"][0]["verified_records"] == 1


def test_api_discover_diseases_endpoint(mock_discovery_ncbi):
    res = client.get("/api/discover/diseases?q=Alzheimer")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "Alzheimer"
    assert "results" in data
    assert len(data["results"]) > 0


def test_api_discover_genes_endpoint(mock_discovery_ncbi):
    res = client.get("/api/discover/genes?q=APOE")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "APOE"
    assert "results" in data
    assert len(data["results"]) > 0


def test_api_discover_empty_query():
    # Empty query string tests
    res_d = client.get("/api/discover/diseases?q=")
    assert res_d.status_code == 200
    data_d = res_d.json()
    assert data_d["query"] == ""
    assert data_d["results"] == []

    res_g = client.get("/api/discover/genes?q=")
    assert res_g.status_code == 200
    data_g = res_g.json()
    assert data_g["query"] == ""
    assert data_g["results"] == []

    # Whitespace-only query tests
    res_d_ws = client.get("/api/discover/diseases?q=%20%20")
    assert res_d_ws.status_code == 200
    assert res_d_ws.json()["query"] == ""
    assert res_d_ws.json()["results"] == []

    res_g_ws = client.get("/api/discover/genes?q=%20%20")
    assert res_g_ws.status_code == 200
    assert res_g_ws.json()["query"] == ""
    assert res_g_ws.json()["results"] == []

    # Short query (< 2 characters) for disease discovery returns empty results without external call
    res_d_short = client.get("/api/discover/diseases?q=a")
    assert res_d_short.status_code == 200
    assert res_d_short.json()["query"] == "a"
    assert res_d_short.json()["results"] == []

