import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.config import config
from src.cache import cache
from src.evidence.base import BaseEvidenceProvider
from src.evidence.models import NormalizedEvidence
from src.medgen import (
    search_medgen,
    search_medgen_by_gene,
    fetch_medgen_records_xml,
    NCBIException
)
from src.parser import parse_medgen_xml

logger = logging.getLogger("genedxplorer.evidence.medgen")

class MedGenEvidenceProvider(BaseEvidenceProvider):
    """
    Evidence provider for NCBI MedGen record-level disease-gene annotations.
    """

    @property
    def name(self) -> str:
        return "NCBI MedGen"

    @property
    def source_type(self) -> str:
        return "Record-level Literature Annotation"

    def lookup_gene(self, gene_symbol: str) -> List[NormalizedEvidence]:
        clean_symbol = gene_symbol.strip().upper()
        if not clean_symbol:
            return []

        cache_key = f"evidence:medgen:gene:{clean_symbol}"
        cached = cache.get("evidence_medgen", symbol=clean_symbol)
        if cached is not None:
            return cached

        try:
            total_matches, uids, strategy = search_medgen_by_gene(clean_symbol, max_limit=config.ANALYSIS_LIMIT)
            xml_docs = fetch_medgen_records_xml(uids)
            parsed_res = parse_medgen_xml(xml_docs)
            records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res

            now_iso = datetime.now(timezone.utc).isoformat()
            evidence_list = []

            for rec in records:
                for g in rec.associated_genes:
                    if g.symbol.upper() == clean_symbol:
                        item = NormalizedEvidence(
                            source=self.name,
                            source_type=self.source_type,
                            record_id=rec.medgen_uid,
                            entity_type="gene",
                            entity_identifier=clean_symbol,
                            gene_symbol=clean_symbol,
                            ncbi_gene_id=g.ncbi_gene_id or None,
                            disease_name=rec.title,
                            disease_identifier=rec.concept_id or None,
                            relationship=g.relationship or "reported associated",
                            evidence_type="MedGen Record Annotation",
                            interpretation=None,
                            retrieved_at=now_iso,
                            provenance={
                                "medgen_uid": rec.medgen_uid,
                                "concept_id": rec.concept_id,
                                "semantic_type": rec.semantic_type,
                                "chromosome": g.chromosome,
                                "location": g.location,
                                "ncbi_database": "MedGen"
                            },
                            source_url=f"https://www.ncbi.nlm.nih.gov/medgen/{rec.medgen_uid}"
                        )
                        evidence_list.append(item)

            cache.set("evidence_medgen", evidence_list, ttl=config.CACHE_TTL, symbol=clean_symbol)
            return evidence_list

        except NCBIException as e:
            logger.error(f"MedGen evidence lookup failed for gene {clean_symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in MedGen provider for gene {clean_symbol}: {e}")
            raise

    def lookup_disease(self, disease_name: str) -> List[NormalizedEvidence]:
        clean_name = disease_name.strip()
        if not clean_name:
            return []

        cache_key = f"evidence:medgen:disease:{clean_name}"
        cached = cache.get("evidence_medgen_dis", disease=clean_name)
        if cached is not None:
            return cached

        try:
            total_matches, title_count, uids, strategy = search_medgen(clean_name, max_limit=config.ANALYSIS_LIMIT)
            xml_docs = fetch_medgen_records_xml(uids)
            parsed_res = parse_medgen_xml(xml_docs)
            records = parsed_res[0] if isinstance(parsed_res, tuple) else parsed_res

            now_iso = datetime.now(timezone.utc).isoformat()
            evidence_list = []

            for rec in records:
                for g in rec.associated_genes:
                    item = NormalizedEvidence(
                        source=self.name,
                        source_type=self.source_type,
                        record_id=rec.medgen_uid,
                        entity_type="disease",
                        entity_identifier=clean_name,
                        gene_symbol=g.symbol.upper(),
                        ncbi_gene_id=g.ncbi_gene_id or None,
                        disease_name=rec.title,
                        disease_identifier=rec.concept_id or None,
                        relationship=g.relationship or "reported associated",
                        evidence_type="MedGen Record Annotation",
                        interpretation=None,
                        retrieved_at=now_iso,
                        provenance={
                            "medgen_uid": rec.medgen_uid,
                            "concept_id": rec.concept_id,
                            "semantic_type": rec.semantic_type,
                            "chromosome": g.chromosome,
                            "location": g.location,
                            "ncbi_database": "MedGen"
                        },
                        source_url=f"https://www.ncbi.nlm.nih.gov/medgen/{rec.medgen_uid}"
                    )
                    evidence_list.append(item)

            cache.set("evidence_medgen_dis", evidence_list, ttl=config.CACHE_TTL, disease=clean_name)
            return evidence_list

        except Exception as e:
            logger.error(f"Error in MedGen provider for disease {clean_name}: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": "available",
            "source_type": self.source_type,
            "message": "NCBI MedGen provider initialized and operational."
        }
