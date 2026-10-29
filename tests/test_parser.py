import pytest
from src.parser import parse_medgen_xml, DiseaseRecord, GeneAssociation

def test_parse_single_record_multiple_genes(xml_single_record):
    records, metrics = parse_medgen_xml(xml_single_record)
    assert len(records) == 1
    assert metrics["records_analyzed"] == 1
    assert metrics["records_with_genes"] == 1
    assert metrics["records_without_genes"] == 0
    assert metrics["duplicate_genes_removed"] == 0

    rec = records[0]
    assert rec.medgen_uid == "123456"
    assert rec.title == "Alzheimer disease 1"
    assert rec.concept_id == "C0750900"
    assert len(rec.associated_genes) == 1
    
    gene = rec.associated_genes[0]
    assert gene.symbol == "APP"
    assert gene.ncbi_gene_id == "351"
    assert gene.chromosome == "21"
    assert gene.location == "21q21.3"


def test_parse_duplicate_gene_in_record_and_multiple_records(xml_multiple_records):
    records, metrics = parse_medgen_xml(xml_multiple_records)
    assert len(records) == 3
    assert metrics["records_analyzed"] == 3
    assert metrics["records_with_genes"] == 2
    assert metrics["records_without_genes"] == 1
    assert metrics["duplicate_genes_removed"] == 1  # 1 duplicate CFTR removed in record 100001

    # Record 100001 should have CFTR and TGFB1 (2 unique genes)
    rec1 = records[0]
    assert len(rec1.associated_genes) == 2
    symbols = [g.symbol for g in rec1.associated_genes]
    assert "CFTR" in symbols
    assert "TGFB1" in symbols

    # Record 100002 should have CFTR
    rec2 = records[1]
    assert len(rec2.associated_genes) == 1
    assert rec2.associated_genes[0].symbol == "CFTR"

    # Record 100003 has no genes
    rec3 = records[2]
    assert len(rec3.associated_genes) == 0


def test_parse_malformed_xml(xml_malformed):
    records, metrics = parse_medgen_xml(xml_malformed)
    assert len(records) == 1
    rec = records[0]
    # 'NONE' and empty symbols should be filtered out
    assert len(rec.associated_genes) == 0
    assert metrics["records_without_genes"] == 1
