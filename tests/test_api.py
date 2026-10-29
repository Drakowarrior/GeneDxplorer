from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from api import app
from src.parser import DiseaseRecord, GeneAssociation

client = TestClient(app)

@pytest.fixture
def mock_ncbi_disease_workflow():
    sample_records = [
        DiseaseRecord(
            medgen_uid="123",
            title="Mock Disease",
            associated_genes=[
                GeneAssociation(symbol="MOCKGENE1", ncbi_gene_id="111"),
                GeneAssociation(symbol="MOCKGENE2", ncbi_gene_id="222")
            ]
        )
    ]
    with patch("api.search_medgen") as mock_search, \
         patch("api.fetch_medgen_records_xml") as mock_fetch, \
         patch("api.parse_medgen_xml") as mock_parse:
        
        mock_search.return_value = (10, 1, ["123"], "Mock strategy")
        mock_fetch.return_value = [object()]
        mock_parse.return_value = (sample_records, {
            "records_analyzed": 1,
            "records_with_genes": 1,
            "records_without_genes": 0,
            "total_relationships": 2,
            "duplicate_genes_removed": 0
        })
        yield


def test_api_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_ready_endpoint():
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "config" in data
    assert "cache" in data


def test_api_disease_analysis(mock_ncbi_disease_workflow):
    res = client.get("/api/disease/Mock Disease")
    assert res.status_code == 200
    data = res.json()

    assert data["query"] == "Mock Disease"
    assert "records" in data
    assert "data_quality" in data
    assert "research_summary" in data
    assert len(data["genes"]) == 2
    assert data["genes"][0]["symbol"] == "MOCKGENE1"

    # Check security & correlation headers
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"


def test_api_disease_evidence(mock_ncbi_disease_workflow):
    res = client.get("/api/disease/Mock Disease/evidence")
    assert res.status_code == 200
    data = res.json()

    assert data["query"] == "Mock Disease"
    assert "data_quality_metrics" in data
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["medgen_uid"] == "123"
    assert data["evidence"][0]["genes"][0]["symbol"] == "MOCKGENE1"


def test_api_gene_evidence():
    sample_records = [
        DiseaseRecord(
            medgen_uid="1853",
            title="Alzheimer disease",
            associated_genes=[GeneAssociation(symbol="APP", ncbi_gene_id="351")]
        )
    ]
    with patch("api.search_medgen_by_gene") as mock_search, \
         patch("api.fetch_medgen_records_xml") as mock_fetch, \
         patch("api.parse_medgen_xml") as mock_parse:
        
        mock_search.return_value = (5, ["1853"], "Gene search strategy")
        mock_fetch.return_value = [object()]
        mock_parse.return_value = (sample_records, {})

        res = client.get("/api/gene/APP/evidence")
        assert res.status_code == 200
        data = res.json()

        assert data["gene"]["symbol"] == "APP"
        assert data["gene"]["ncbi_gene_id"] == "351"
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["disease_title"] == "Alzheimer disease"


def test_api_gene_summary():
    sample_records = [
        DiseaseRecord(
            medgen_uid="1853",
            title="Alzheimer disease",
            associated_genes=[GeneAssociation(symbol="APP", ncbi_gene_id="351")]
        )
    ]
    with patch("api.search_medgen_by_gene") as mock_search, \
         patch("api.fetch_medgen_records_xml") as mock_fetch, \
         patch("api.parse_medgen_xml") as mock_parse:
        
        mock_search.return_value = (17, ["1853"], "Gene search strategy")
        mock_fetch.return_value = [object()]
        mock_parse.return_value = (sample_records, {})

        res = client.get("/api/gene/APP/summary")
        assert res.status_code == 200
        data = res.json()

        assert data["symbol"] == "APP"
        assert data["ncbi_gene_id"] == "351"
        assert data["candidate_records"] == 17
        assert data["verified_records"] == 1
        assert data["unique_diseases"] == 1


def test_api_medgen_record_detail():
    sample_record = DiseaseRecord(
        medgen_uid="1853",
        title="Alzheimer disease",
        concept_id="C0002395",
        semantic_type="Disease or Syndrome",
        definition="A neurodegenerative condition...",
        associated_genes=[GeneAssociation(symbol="APP", ncbi_gene_id="351")]
    )
    with patch("api.fetch_single_medgen_record_xml") as mock_fetch, \
         patch("api.parse_medgen_xml") as mock_parse:
        
        mock_fetch.return_value = (object(), "1853")
        mock_parse.return_value = ([sample_record], {})

        res = client.get("/api/medgen/1853")
        assert res.status_code == 200
        data = res.json()

        assert data["medgen_uid"] == "1853"
        assert data["disease_title"] == "Alzheimer disease"
        assert data["concept_id"] == "C0002395"
        assert len(data["associated_genes"]) == 1


def test_api_medgen_record_detail_404():
    with patch("api.fetch_single_medgen_record_xml") as mock_fetch:
        mock_fetch.return_value = (None, "99999999")

        res = client.get("/api/medgen/99999999")
        assert res.status_code == 404
        data = res.json()
        assert data["code"] == "RECORD_NOT_FOUND"


def test_api_validation_error_empty_disease():
    res = client.get("/api/disease/   ")
    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "error" in data
    assert "request_id" in data


def test_api_same_disease_comparison_validation():
    res = client.post("/api/disease/compare", json={
        "disease_a": "Alzheimer's disease",
        "disease_b": "alzheimer's disease"
    })
    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "Cannot compare a disease with itself" in data["error"]
