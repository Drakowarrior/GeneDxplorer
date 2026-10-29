from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from api import app
from src.evidence.models import NormalizedEvidence
from src.evidence.base import BaseEvidenceProvider
from src.evidence.medgen_provider import MedGenEvidenceProvider
from src.evidence.clinvar_provider import ClinVarEvidenceProvider
from src.evidence.aggregator import EvidenceAggregator
from src.parser import DiseaseRecord, GeneAssociation

client = TestClient(app)


def test_normalized_evidence_model():
    ev = NormalizedEvidence(
        source="ClinVar",
        source_type="Variant Interpretation Submission",
        record_id="VCV_12345",
        entity_type="gene",
        entity_identifier="APOE",
        gene_symbol="APOE",
        ncbi_gene_id="348",
        disease_name="Alzheimer disease",
        interpretation="Pathogenic",
        review_status="criteria provided, single submitter",
        variant_id="12345",
        source_url="https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/"
    )
    d = ev.to_dict()
    assert d["source"] == "ClinVar"
    assert d["record_id"] == "VCV_12345"
    assert d["interpretation"] == "Pathogenic"
    assert d["source_url"] == "https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/"


def test_medgen_provider_lookup_gene():
    sample_records = [
        DiseaseRecord(
            medgen_uid="1001",
            title="Alzheimer disease 1",
            concept_id="C0002395",
            semantic_type="Disease or Syndrome",
            associated_genes=[GeneAssociation(symbol="APOE", ncbi_gene_id="348")]
        )
    ]

    provider = MedGenEvidenceProvider()
    with patch("src.evidence.medgen_provider.search_medgen_by_gene") as mock_search, \
         patch("src.evidence.medgen_provider.fetch_medgen_records_xml") as mock_fetch, \
         patch("src.evidence.medgen_provider.parse_medgen_xml") as mock_parse:

        mock_search.return_value = (1, ["1001"], "Strategy")
        mock_fetch.return_value = [object()]
        mock_parse.return_value = (sample_records, {})

        results = provider.lookup_gene("APOE")
        assert len(results) == 1
        assert results[0].source == "NCBI MedGen"
        assert results[0].record_id == "1001"
        assert results[0].gene_symbol == "APOE"
        assert results[0].disease_name == "Alzheimer disease 1"


def test_clinvar_provider_lookup_gene():
    mock_esummary_res = {
        "result": {
            "uids": ["999"],
            "999": {
                "title": "NM_000041.4(APOE):c.388T>C",
                "variation_set": [{"variation_id": "999"}],
                "clinical_significance": {
                    "description": "Pathogenic",
                    "review_status": "criteria provided, single submitter"
                },
                "genes": [{"symbol": "APOE", "gene_id": "348"}],
                "trait_set": [{"trait_name": "Alzheimer disease 1"}]
            }
        }
    }

    provider = ClinVarEvidenceProvider()
    with patch("src.evidence.clinvar_provider.Entrez.esearch") as mock_esearch, \
         patch("src.evidence.clinvar_provider.Entrez.esummary") as mock_esummary, \
         patch("src.evidence.clinvar_provider.Entrez.read") as mock_read:

        mock_esearch.return_value = MagicMock()
        mock_esummary.return_value = MagicMock()
        mock_read.side_effect = [{"IdList": ["999"]}, mock_esummary_res]

        results = provider.lookup_gene("APOE")
        assert len(results) == 1
        assert results[0].source == "ClinVar"
        assert results[0].record_id == "VCV_999"
        assert results[0].interpretation == "Pathogenic"
        assert results[0].disease_name == "Alzheimer disease 1"


def test_evidence_aggregator_failure_isolation():
    class SuccessProvider(BaseEvidenceProvider):
        @property
        def name(self): return "SuccessProvider"
        @property
        def source_type(self): return "Test Source"
        def lookup_gene(self, gene): return [
            NormalizedEvidence(source="SuccessProvider", source_type="Test", record_id="1", entity_type="gene", entity_identifier=gene, gene_symbol=gene)
        ]
        def lookup_disease(self, disease): return []
        def health_check(self): return {"name": self.name, "status": "available"}

    class FailingProvider(BaseEvidenceProvider):
        @property
        def name(self): return "FailingProvider"
        @property
        def source_type(self): return "Failing Source"
        def lookup_gene(self, gene): raise Exception("Provider Connection Refused")
        def lookup_disease(self, disease): return []
        def health_check(self): raise Exception("Provider Down")

    agg = EvidenceAggregator()
    agg._providers = {
        "successprovider": SuccessProvider(),
        "failingprovider": FailingProvider()
    }

    with patch("src.config.config.EVIDENCE_PROVIDERS", ["successprovider", "failingprovider"]):
        res = agg.aggregate_gene_evidence("APOE")
        assert res["total_records"] == 1
        assert res["providers"]["SuccessProvider"]["status"] == "available"
        assert res["providers"]["FailingProvider"]["status"] == "unavailable"
        assert "error" in res["providers"]["FailingProvider"]


def test_api_evidence_health_endpoint():
    res = client.get("/api/evidence/health")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    assert len(data["providers"]) >= 2


def test_api_unified_gene_evidence_endpoint():
    sample_records = [
        DiseaseRecord(
            medgen_uid="2002",
            title="Cystic fibrosis",
            associated_genes=[GeneAssociation(symbol="CFTR", ncbi_gene_id="1080")]
        )
    ]
    with patch("src.evidence.medgen_provider.search_medgen_by_gene") as mock_search, \
         patch("src.evidence.medgen_provider.fetch_medgen_records_xml") as mock_fetch, \
         patch("src.evidence.medgen_provider.parse_medgen_xml") as mock_parse, \
         patch("src.evidence.clinvar_provider.Entrez.esearch") as mock_clinvar_search, \
         patch("src.evidence.clinvar_provider.Entrez.esummary") as mock_clinvar_summary, \
         patch("src.evidence.clinvar_provider.Entrez.read") as mock_clinvar_read:

        mock_search.return_value = (1, ["2002"], "Strategy")
        mock_fetch.return_value = [object()]
        mock_parse.return_value = (sample_records, {})

        mock_clinvar_search.return_value = MagicMock()
        mock_clinvar_summary.return_value = MagicMock()
        mock_clinvar_read.side_effect = [{"IdList": []}]

        res = client.get("/api/evidence/gene/CFTR")
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "CFTR"
        assert "NCBI MedGen" in data["providers"]
        assert "ClinVar" in data["providers"]
