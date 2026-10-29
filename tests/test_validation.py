import pytest
from src.utils import (
    sanitize_filename,
    get_safe_export_path,
    validate_disease_name,
    validate_gene_symbol,
    validate_disease_comparison,
    ValidationError
)

def test_sanitize_filename_prevents_path_traversal():
    assert sanitize_filename("../../etc/passwd") == "etc_passwd"
    assert sanitize_filename("Alzheimer's disease") == "alzheimers_disease"
    assert sanitize_filename("../..") == "sanitized_item"

def test_get_safe_export_path_prevents_escaping():
    base = "results"
    safe = get_safe_export_path(base, "test.csv")
    assert safe.endswith("results/test.csv")
    
    with pytest.raises(ValidationError):
        get_safe_export_path("results", "../../etc/passwd")

def test_validate_disease_name():
    assert validate_disease_name("Alzheimer's disease") == "Alzheimer's disease"
    with pytest.raises(ValidationError):
        validate_disease_name("")
    with pytest.raises(ValidationError):
        validate_disease_name("a" * 201)

def test_validate_gene_symbol():
    assert validate_gene_symbol("app") == "APP"
    assert validate_gene_symbol("CFTR-1") == "CFTR-1"
    with pytest.raises(ValidationError):
        validate_gene_symbol("")
    with pytest.raises(ValidationError):
        validate_gene_symbol("INVALID SYMBOL WITH SPACES!")

def test_validate_disease_comparison():
    da, db = validate_disease_comparison("Alzheimer's disease", "Parkinson disease")
    assert da == "Alzheimer's disease"
    assert db == "Parkinson disease"

    with pytest.raises(ValidationError):
        validate_disease_comparison("Alzheimer's disease", "alzheimer's disease")
