import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from src.config import config
from src.evidence.base import BaseEvidenceProvider
from src.evidence.medgen_provider import MedGenEvidenceProvider
from src.evidence.clinvar_provider import ClinVarEvidenceProvider
from src.evidence.models import NormalizedEvidence

logger = logging.getLogger("genedxplorer.evidence.aggregator")


class EvidenceAggregator:
    """
    Central Evidence Aggregator orchestrating multi-source evidence retrieval.
    Provides provider failure isolation, normalization, and deduplication.
    """

    def __init__(self):
        self._providers: Dict[str, BaseEvidenceProvider] = {}
        # Register standard built-in providers
        self.register_provider("medgen", MedGenEvidenceProvider())
        self.register_provider("clinvar", ClinVarEvidenceProvider())

    def register_provider(self, key: str, provider: BaseEvidenceProvider):
        """Register a new evidence provider instance."""
        self._providers[key.lower()] = provider
        logger.debug(f"Registered evidence provider '{provider.name}' under key '{key}'")

    def get_enabled_providers(self) -> List[BaseEvidenceProvider]:
        """Return list of active provider instances configured in EVIDENCE_PROVIDERS."""
        enabled = []
        for key in config.EVIDENCE_PROVIDERS:
            p_key = key.lower()
            if p_key in self._providers:
                enabled.append(self._providers[p_key])
            else:
                logger.warning(f"Configured evidence provider key '{key}' is not registered.")
        return enabled

    def get_health(self) -> Dict[str, Any]:
        """Check health and availability of all registered providers."""
        now_iso = datetime.now(timezone.utc).isoformat()
        provider_reports = []

        for p_key, provider in self._providers.items():
            is_configured = p_key in [k.lower() for k in config.EVIDENCE_PROVIDERS]
            try:
                report = provider.health_check()
                report["enabled"] = is_configured
                provider_reports.append(report)
            except Exception as e:
                logger.error(f"Provider health check failed for '{provider.name}': {e}")
                provider_reports.append({
                    "name": provider.name,
                    "status": "unavailable",
                    "source_type": provider.source_type,
                    "enabled": is_configured,
                    "message": f"Provider health check error: {str(e)}"
                })

        return {
            "service": "GeneDxplorer Evidence Providers",
            "retrieved_at": now_iso,
            "providers": provider_reports
        }

    def aggregate_gene_evidence(self, gene_symbol: str) -> Dict[str, Any]:
        """
        Aggregate normalized evidence records across enabled providers for a gene.
        Isolated error handling ensures failure of one provider does not impact others.
        """
        clean_symbol = gene_symbol.strip().upper()
        now_iso = datetime.now(timezone.utc).isoformat()
        active_providers = self.get_enabled_providers()

        provider_results: Dict[str, Any] = {}
        total_records_count = 0

        for provider in active_providers:
            try:
                logger.info(f"Querying provider '{provider.name}' for gene '{clean_symbol}'")
                records: List[NormalizedEvidence] = provider.lookup_gene(clean_symbol)

                # Deduplicate identical records by (source, record_id)
                seen_keys = set()
                unique_records = []
                for rec in records:
                    dedupe_key = (rec.source, rec.record_id, rec.disease_name)
                    if dedupe_key not in seen_keys:
                        seen_keys.add(dedupe_key)
                        unique_records.append(rec.to_dict())

                provider_results[provider.name] = {
                    "status": "available",
                    "source_type": provider.source_type,
                    "count": len(unique_records),
                    "records": unique_records
                }
                total_records_count += len(unique_records)

            except Exception as e:
                logger.error(f"Provider failure isolated: Provider '{provider.name}' failed for gene '{clean_symbol}': {e}")
                provider_results[provider.name] = {
                    "status": "unavailable",
                    "source_type": provider.source_type,
                    "count": 0,
                    "records": [],
                    "error": str(e)
                }

        return {
            "query": clean_symbol,
            "retrieved_at": now_iso,
            "total_records": total_records_count,
            "providers": provider_results
        }


# Global Singleton Aggregator Instance
aggregator = EvidenceAggregator()
