from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any

@dataclass
class NormalizedEvidence:
    """
    Normalized internal evidence model across all scientific evidence providers.
    Maintains strict provenance, source attribution, and non-clinical metadata.
    """
    source: str                             # e.g., "NCBI MedGen", "ClinVar"
    source_type: str                        # e.g., "Record-level Annotation", "Variant Submission"
    record_id: str                          # e.g., MedGen UID, ClinVar RCV/Variation ID
    entity_type: str                        # e.g., "gene", "disease", "variant"
    entity_identifier: str                  # Primary identifier (Symbol, UID, VCV)
    gene_symbol: str                        # Gene Symbol (e.g., APOE, CFTR)
    ncbi_gene_id: Optional[str] = None      # NCBI Gene ID (e.g., 348)
    disease_name: Optional[str] = None      # Reported Condition / Disease Title
    disease_identifier: Optional[str] = None # Concept ID / MedGen UID
    relationship: Optional[str] = None      # e.g., "reported associated", "germline variant"
    evidence_type: Optional[str] = None     # e.g., "MedGen Record", "ClinVar Submission"
    interpretation: Optional[str] = None    # Clinical significance (e.g., "Pathogenic")
    review_status: Optional[str] = None     # ClinVar review status
    variant_id: Optional[str] = None        # ClinVar Variation ID
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance: Dict[str, Any] = field(default_factory=dict)
    source_url: Optional[str] = None         # Direct link to authoritative source page

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to standard dictionary for API serialization."""
        return asdict(self)
