from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.evidence.models import NormalizedEvidence

class BaseEvidenceProvider(ABC):
    """
    Abstract Base Class for Scientific Evidence Providers.
    All evidence providers (MedGen, ClinVar, etc.) must implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider display name (e.g. 'NCBI MedGen', 'ClinVar')."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Source evidence type classification."""
        pass

    @abstractmethod
    def lookup_gene(self, gene_symbol: str) -> List[NormalizedEvidence]:
        """Retrieve normalized evidence records for a target gene symbol."""
        pass

    @abstractmethod
    def lookup_disease(self, disease_name: str) -> List[NormalizedEvidence]:
        """Retrieve normalized evidence records for a target disease query."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check provider availability and connectivity.
        Returns dictionary with status ('available' | 'unavailable' | 'degraded').
        """
        pass
