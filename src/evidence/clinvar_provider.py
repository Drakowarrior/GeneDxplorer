import time
import urllib.error
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from Bio import Entrez

from src.config import config
from src.cache import cache
from src.medgen import configure_ncbi, NCBIConnectionError, NCBISearchError
from src.evidence.base import BaseEvidenceProvider
from src.evidence.models import NormalizedEvidence

logger = logging.getLogger("genedxplorer.evidence.clinvar")


class ClinVarEvidenceProvider(BaseEvidenceProvider):
    """
    Authoritative ClinVar evidence provider using official NCBI Entrez E-utilities API.
    Retrieves variant interpretations, clinical significance, review status, and reported conditions.
    """

    @property
    def name(self) -> str:
        return "ClinVar"

    @property
    def source_type(self) -> str:
        return "Variant Interpretation Submission"

    def lookup_gene(self, gene_symbol: str) -> List[NormalizedEvidence]:
        clean_symbol = gene_symbol.strip().upper()
        if not clean_symbol:
            return []

        cache_key = f"evidence:clinvar:gene:{clean_symbol}"
        cached = cache.get("evidence_clinvar", symbol=clean_symbol)
        if cached is not None:
            return cached

        configure_ncbi()
        logger.info(f"Initiating ClinVar lookup for gene='{clean_symbol}'")

        try:
            # Step 1: ESearch ClinVar for target gene
            gene_query = f'"{clean_symbol}"[Gene]'
            max_limit = min(config.ANALYSIS_LIMIT, 50)  # Reasonable limit for discovery

            handle = Entrez.esearch(db="clinvar", term=gene_query, retmax=max_limit)
            search_res = Entrez.read(handle, validate=False)
            handle.close()

            time.sleep(config.NCBI_REQUEST_DELAY)

            id_list = search_res.get("IdList", [])
            if not id_list:
                logger.info(f"No ClinVar variant records found for gene '{clean_symbol}'")
                cache.set("evidence_clinvar", [], ttl=config.CACHE_TTL, symbol=clean_symbol)
                return []

            # Step 2: ESummary for ClinVar IDs
            ids_str = ",".join(id_list)
            handle = Entrez.esummary(db="clinvar", id=ids_str)
            summary_res = Entrez.read(handle, validate=False)
            handle.close()


            time.sleep(config.NCBI_REQUEST_DELAY)

            now_iso = datetime.now(timezone.utc).isoformat()
            evidence_list = []

            # ESummary results structure parsing
            result_dict = summary_res.get("result", {})
            uids = result_dict.get("uids", [])

            for uid in uids:
                record = result_dict.get(str(uid), {})
                if not record:
                    continue

                title = record.get("title", f"ClinVar Record {uid}")
                variation_id = str(record.get("variation_set", [{}])[0].get("variation_id", uid)) if record.get("variation_set") else str(uid)

                # Extract Clinical Significance & Review Status
                clin_sig_obj = record.get("clinical_significance", {})
                if isinstance(clin_sig_obj, dict):
                    interpretation = clin_sig_obj.get("description", "Not reported")
                    review_status = clin_sig_obj.get("review_status", "Not reported")
                else:
                    interpretation = str(clin_sig_obj) if clin_sig_obj else "Not reported"
                    review_status = "Not reported"

                # Extract Gene ID if available
                ncbi_gene_id = None
                genes_list = record.get("genes", [])
                if genes_list and isinstance(genes_list, list):
                    for g_obj in genes_list:
                        if isinstance(g_obj, dict) and g_obj.get("symbol", "").upper() == clean_symbol:
                            ncbi_gene_id = str(g_obj.get("gene_id", ""))

                # Extract Trait / Condition Set
                trait_set = record.get("trait_set", [])
                condition_names = []
                if isinstance(trait_set, list):
                    for trait in trait_set:
                        if isinstance(trait, dict):
                            t_name = trait.get("trait_name") or trait.get("name")
                            if t_name:
                                condition_names.append(t_name)

                primary_condition = condition_names[0] if condition_names else "Reported Variant Association"

                evidence_item = NormalizedEvidence(
                    source=self.name,
                    source_type=self.source_type,
                    record_id=f"VCV_{variation_id}" if variation_id else f"UID_{uid}",
                    entity_type="gene",
                    entity_identifier=clean_symbol,
                    gene_symbol=clean_symbol,
                    ncbi_gene_id=ncbi_gene_id or None,
                    disease_name=primary_condition,
                    disease_identifier=None,
                    relationship="variant submission",
                    evidence_type="ClinVar Submission",
                    interpretation=interpretation,
                    review_status=review_status,
                    variant_id=variation_id,
                    retrieved_at=now_iso,
                    provenance={
                        "clinvar_uid": str(uid),
                        "variant_title": title,
                        "all_conditions": condition_names,
                        "ncbi_database": "ClinVar"
                    },
                    source_url=f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{variation_id}/" if variation_id else f"https://www.ncbi.nlm.nih.gov/clinvar/?term={uid}"
                )
                evidence_list.append(evidence_item)

            logger.info(f"Successfully retrieved {len(evidence_list)} ClinVar records for gene '{clean_symbol}'")
            cache.set("evidence_clinvar", evidence_list, ttl=config.CACHE_TTL, symbol=clean_symbol)
            return evidence_list

        except (urllib.error.URLError, TimeoutError) as e:
            logger.error(f"ClinVar network timeout/connection error: {e}")
            raise NCBIConnectionError("Unable to connect to ClinVar E-utilities service.")
        except Exception as e:
            logger.error(f"Error in ClinVar provider for gene {clean_symbol}: {e}")
            raise NCBISearchError(f"ClinVar evidence retrieval failed: {str(e)}")

    def lookup_disease(self, disease_name: str) -> List[NormalizedEvidence]:
        clean_name = disease_name.strip()
        if not clean_name:
            return []

        cache_key = f"evidence:clinvar:disease:{clean_name}"
        cached = cache.get("evidence_clinvar_dis", disease=clean_name)
        if cached is not None:
            return cached

        configure_ncbi()
        try:
            max_limit = min(config.ANALYSIS_LIMIT, 50)
            handle = Entrez.esearch(db="clinvar", term=clean_name, retmax=max_limit)
            search_res = Entrez.read(handle, validate=False)
            handle.close()

            time.sleep(config.NCBI_REQUEST_DELAY)

            id_list = search_res.get("IdList", [])
            if not id_list:
                cache.set("evidence_clinvar_dis", [], ttl=config.CACHE_TTL, disease=clean_name)
                return []

            ids_str = ",".join(id_list)
            handle = Entrez.esummary(db="clinvar", id=ids_str)
            summary_res = Entrez.read(handle, validate=False)
            handle.close()


            time.sleep(config.NCBI_REQUEST_DELAY)

            now_iso = datetime.now(timezone.utc).isoformat()
            evidence_list = []
            result_dict = summary_res.get("result", {})
            uids = result_dict.get("uids", [])

            for uid in uids:
                record = result_dict.get(str(uid), {})
                if not record:
                    continue

                title = record.get("title", f"ClinVar Record {uid}")
                variation_id = str(record.get("variation_set", [{}])[0].get("variation_id", uid)) if record.get("variation_set") else str(uid)

                # Extract gene symbol from genes set
                g_symbol = "UNKNOWN"
                ncbi_g_id = None
                genes_list = record.get("genes", [])
                if genes_list and isinstance(genes_list, list) and len(genes_list) > 0:
                    g_obj = genes_list[0]
                    if isinstance(g_obj, dict):
                        g_symbol = g_obj.get("symbol", "UNKNOWN").upper()
                        ncbi_g_id = str(g_obj.get("gene_id", ""))

                clin_sig_obj = record.get("clinical_significance", {})
                interpretation = clin_sig_obj.get("description", "Not reported") if isinstance(clin_sig_obj, dict) else "Not reported"
                review_status = clin_sig_obj.get("review_status", "Not reported") if isinstance(clin_sig_obj, dict) else "Not reported"

                evidence_item = NormalizedEvidence(
                    source=self.name,
                    source_type=self.source_type,
                    record_id=f"VCV_{variation_id}" if variation_id else f"UID_{uid}",
                    entity_type="disease",
                    entity_identifier=clean_name,
                    gene_symbol=g_symbol,
                    ncbi_gene_id=ncbi_g_id or None,
                    disease_name=clean_name,
                    disease_identifier=None,
                    relationship="variant submission",
                    evidence_type="ClinVar Submission",
                    interpretation=interpretation,
                    review_status=review_status,
                    variant_id=variation_id,
                    retrieved_at=now_iso,
                    provenance={
                        "clinvar_uid": str(uid),
                        "variant_title": title,
                        "ncbi_database": "ClinVar"
                    },
                    source_url=f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{variation_id}/" if variation_id else f"https://www.ncbi.nlm.nih.gov/clinvar/?term={uid}"
                )
                evidence_list.append(evidence_item)

            cache.set("evidence_clinvar_dis", evidence_list, ttl=config.CACHE_TTL, disease=clean_name)
            return evidence_list

        except Exception as e:
            logger.error(f"Error in ClinVar provider for disease {clean_name}: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": "available",
            "source_type": self.source_type,
            "message": "ClinVar Entrez E-utilities provider initialized and operational."
        }
