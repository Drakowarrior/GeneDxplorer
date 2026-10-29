import os
import re

class ValidationError(ValueError):
    """Exception raised for invalid user/API input validation failures."""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


def sanitize_filename(disease_name: str) -> str:
    """
    Sanitize disease or gene name into a clean, filesystem-safe filename slug.
    Prevents path traversal attacks (e.g. '../../etc/passwd').
    Example: "Alzheimer's disease" -> "alzheimers_disease"
    """
    if not disease_name:
        return "item"

    # Strip dangerous path traversal characters and null bytes
    clean_name = str(disease_name).replace("\0", "").replace("..", "").replace("/", "_").replace("\\", "_")
    clean_name = clean_name.replace("'", "").replace("’", "")
    
    # Replace non-alphanumeric characters with underscore
    slug = "".join(c.lower() if c.isalnum() else "_" for c in clean_name)
    
    # Collapse multiple consecutive underscores
    while "__" in slug:
        slug = slug.replace("__", "_")
    
    slug = slug.strip("_")
    
    # Safety fallback if empty or starts with dot
    if not slug or slug.startswith("."):
        slug = "sanitized_item"
        
    return slug


def get_safe_export_path(base_dir: str, filename: str) -> str:
    """
    Ensure the resulting filepath strictly resides inside base_dir to prevent path traversal.
    """
    abs_base = os.path.abspath(base_dir)
    target_path = os.path.abspath(os.path.join(abs_base, filename))
    
    if not target_path.startswith(abs_base):
        raise ValidationError("Invalid export filename resulting in path traversal.", code="PATH_TRAVERSAL_ATTEMPT")
        
    return target_path


def validate_disease_name(disease_name: str) -> str:
    """
    Validate disease query input.
    """
    if not disease_name or not disease_name.strip():
        raise ValidationError("Disease query cannot be empty.", code="VALIDATION_ERROR")
    
    clean_name = disease_name.strip()
    if len(clean_name) > 200:
        raise ValidationError("Disease query is excessively long (maximum 200 characters).", code="VALIDATION_ERROR")
        
    # Disallow control characters
    if any(ord(c) < 32 for c in clean_name):
        raise ValidationError("Disease query contains invalid control characters.", code="VALIDATION_ERROR")

    return clean_name


def validate_gene_symbol(gene_symbol: str) -> str:
    """
    Validate gene symbol query input.
    """
    if not gene_symbol or not gene_symbol.strip():
        raise ValidationError("Gene symbol cannot be empty.", code="VALIDATION_ERROR")

    clean_symbol = gene_symbol.strip().upper()
    if len(clean_symbol) > 50:
        raise ValidationError("Gene symbol is excessively long (maximum 50 characters).", code="VALIDATION_ERROR")

    if any(ord(c) < 32 for c in clean_symbol):
        raise ValidationError("Gene symbol contains invalid control characters.", code="VALIDATION_ERROR")

    # Gene symbols are typically alphanumeric with hyphens/underscores/dots
    if not re.match(r"^[A-Z0-9_\-\.]+$", clean_symbol):
        raise ValidationError(f"Invalid gene symbol format: '{clean_symbol}'.", code="VALIDATION_ERROR")

    return clean_symbol


def validate_disease_comparison(disease_a: str, disease_b: str) -> tuple[str, str]:
    """
    Validate two disease queries for comparison.
    """
    clean_a = validate_disease_name(disease_a)
    clean_b = validate_disease_name(disease_b)

    if clean_a.lower() == clean_b.lower():
        raise ValidationError("Cannot compare a disease with itself.", code="VALIDATION_ERROR")

    return clean_a, clean_b
