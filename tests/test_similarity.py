import pytest
from unittest.mock import patch
from src.similarity import calculate_multi_disease_similarity
from src.parser import DiseaseRecord, GeneAssociation

@pytest.fixture
def mock_disease_a_records():
    return [
        DiseaseRecord(
            medgen_uid="101",
            title="Disease Alpha",
            associated_genes=[
                GeneAssociation(symbol="GENE1", ncbi_gene_id="1010"),
                GeneAssociation(symbol="GENE2", ncbi_gene_id="1020"),
                GeneAssociation(symbol="GENE3", ncbi_gene_id="1030")
            ]
        )
    ]

@pytest.fixture
def mock_disease_b_records():
    return [
        DiseaseRecord(
            medgen_uid="201",
            title="Disease Beta",
            associated_genes=[
                GeneAssociation(symbol="GENE2", ncbi_gene_id="1020"),
                GeneAssociation(symbol="GENE4", ncbi_gene_id="1040")
            ]
        )
    ]

@pytest.fixture
def mock_disease_c_records():
    return [
        DiseaseRecord(
            medgen_uid="301",
            title="Disease Gamma",
            associated_genes=[
                GeneAssociation(symbol="GENE5", ncbi_gene_id="1050")
            ]
        )
    ]


@patch("src.similarity.search_medgen")
@patch("src.similarity.fetch_medgen_records_xml")
@patch("src.similarity.parse_medgen_xml")
def test_calculate_multi_disease_similarity(
    mock_parse, mock_fetch, mock_search,
    mock_disease_a_records, mock_disease_b_records, mock_disease_c_records
):
    def side_effect_search(d_name, *args, **kwargs):
        if "Alpha" in d_name:
            return (1, 1, ["101"], "exact")
        elif "Beta" in d_name:
            return (1, 1, ["201"], "exact")
        else:
            return (1, 1, ["301"], "exact")

    def side_effect_parse(xml):
        if "101" in xml:
            return mock_disease_a_records
        elif "201" in xml:
            return mock_disease_b_records
        else:
            return mock_disease_c_records

    mock_search.side_effect = side_effect_search
    mock_fetch.side_effect = lambda uids: f"<xml>{uids[0]}</xml>"
    mock_parse.side_effect = side_effect_parse

    result = calculate_multi_disease_similarity(
        ["Disease Alpha", "Disease Beta", "Disease Gamma"],
        max_records=50
    )

    assert result["disease_count"] == 3
    assert len(result["matrix"]) == 3
    assert len(result["ranked_pairs"]) == 3 # (Alpha,Beta), (Alpha,Gamma), (Beta,Gamma)

    # Check pair Alpha vs Beta (shared: GENE2, union: GENE1, GENE2, GENE3, GENE4 -> Jaccard = 1/4 = 25%)
    alpha_beta_pair = next(p for p in result["ranked_pairs"] if "Alpha" in p["disease_a"] and "Beta" in p["disease_b"])
    assert alpha_beta_pair["shared_gene_count"] == 1
    assert alpha_beta_pair["union_gene_count"] == 4
    assert alpha_beta_pair["jaccard_similarity"] == 25.0


def test_calculate_multi_disease_similarity_validation():
    with pytest.raises(ValueError):
        calculate_multi_disease_similarity(["Single Disease"])
