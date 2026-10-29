import os
import sys
import time
import urllib.error
import xml.etree.ElementTree as ET
import logging
from Bio import Entrez
from src.config import config

logger = logging.getLogger("genedxplorer.medgen")


class NCBIException(Exception):
    """Base exception for NCBI MedGen operations."""
    def __init__(self, message: str, code: str = "NCBI_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class NCBIConnectionError(NCBIException):
    """Raised when network connectivity to NCBI fails."""
    def __init__(self, message: str = "Unable to connect to NCBI MedGen service."):
        super().__init__(message, code="MEDGEN_UNAVAILABLE")


class NCBITimeoutError(NCBIException):
    """Raised when an NCBI request times out."""
    def __init__(self, message: str = "NCBI MedGen request timed out."):
        super().__init__(message, code="NCBI_TIMEOUT")


class NCBISearchError(NCBIException):
    """Raised when NCBI search execution fails."""
    def __init__(self, message: str):
        super().__init__(message, code="NCBI_SEARCH_ERROR")


def configure_ncbi(email=None, api_key=None):
    """
    Configure NCBI Entrez credentials using config / environment variables / non-interactive fallback.
    Credentials are never exposed in logs or responses.
    """
    if not email:
        email = config.NCBI_EMAIL or os.environ.get("NCBI_EMAIL", "").strip()

    if not email or "@" not in email or "." not in email:
        email = "genedxplorer.user@ncbi.nlm.nih.gov"

    Entrez.email = email

    if not api_key:
        api_key = config.NCBI_API_KEY or os.environ.get("NCBI_API_KEY", "").strip()

    if api_key:
        Entrez.api_key = api_key
        logger.debug("NCBI API key configured.")
    else:
        logger.debug("No NCBI API key provided; operating with standard 3 req/sec limit.")


def search_medgen(disease_name: str, max_limit: int = 500) -> tuple[int, int, list, str]:
    """
    Search NCBI MedGen database for a disease using title prioritization and standard term fallback.
    Includes retry with exponential backoff.
    Raises NCBIConnectionError or NCBISearchError on persistent failure (NO sys.exit).
    Returns:
      - total_search_results (int)
      - title_count (int)
      - combined_uids (list)
      - search_strategy_desc (str)
    """
    configure_ncbi()
    logger.info(f"Initiating MedGen disease search for query='{disease_name}' (limit={max_limit})")

    max_retries = 3
    delay = config.NCBI_REQUEST_DELAY

    for attempt in range(1, max_retries + 1):
        try:
            # Step 1: Attempt title query
            title_query = f'"{disease_name}"[title]'
            handle = Entrez.esearch(db="medgen", term=title_query, retmax=max_limit)
            res_title = Entrez.read(handle)
            handle.close()

            time.sleep(delay)  # Pacing delay

            title_count = int(res_title.get("Count", 0))
            title_uids = res_title.get("IdList", [])

            # Step 2: Attempt standard term query
            handle = Entrez.esearch(db="medgen", term=disease_name, retmax=max_limit)
            res_std = Entrez.read(handle)
            handle.close()

            time.sleep(delay)  # Pacing delay

            std_count = int(res_std.get("Count", 0))
            std_uids = res_std.get("IdList", [])

            total_search_results = max(title_count, std_count)

            combined_uids = list(title_uids)
            for uid in std_uids:
                if uid not in combined_uids:
                    combined_uids.append(uid)

            combined_uids = combined_uids[:max_limit]
            search_strategy_desc = (
                f"Prioritized exact title search ('\"{disease_name}\"[title]', {title_count} matches) "
                f"supplemented by general search ({std_count} total matches)."
            )

            logger.info(f"MedGen search successful: total_available={total_search_results}, combined_uids={len(combined_uids)}")
            return total_search_results, title_count, combined_uids, search_strategy_desc

        except (urllib.error.URLError, TimeoutError) as e:
            logger.warning(f"NCBI MedGen connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
            else:
                logger.error(f"NCBI MedGen connection failed permanently after {max_retries} retries.")
                raise NCBIConnectionError("Unable to connect to NCBI MedGen service after multiple retries.")
        except Exception as e:
            logger.error(f"NCBI MedGen search failed with exception: {e}")
            raise NCBISearchError(f"NCBI MedGen search failed: {str(e)}")


def search_medgen_by_gene(gene_symbol: str, max_limit: int = 500) -> tuple[int, list, str]:
    """
    Search NCBI MedGen database for disease records associated with a gene symbol.
    Includes retry with exponential backoff.
    Raises NCBIConnectionError or NCBISearchError on persistent failure (NO sys.exit).
    Returns:
      - total_search_results (int)
      - combined_uids (list)
      - search_strategy_desc (str)
    """
    configure_ncbi()
    logger.info(f"Initiating MedGen gene search for symbol='{gene_symbol}' (limit={max_limit})")

    max_retries = 3
    delay = config.NCBI_REQUEST_DELAY

    for attempt in range(1, max_retries + 1):
        try:
            # Step 1: Specific Gene tag query
            gene_query = f'"{gene_symbol}"[Gene]'
            handle = Entrez.esearch(db="medgen", term=gene_query, retmax=max_limit)
            res_gene = Entrez.read(handle)
            handle.close()

            time.sleep(delay)

            gene_count = int(res_gene.get("Count", 0))
            gene_uids = res_gene.get("IdList", [])

            # Step 2: Fallback query
            handle = Entrez.esearch(db="medgen", term=gene_symbol, retmax=max_limit)
            res_std = Entrez.read(handle)
            handle.close()

            time.sleep(delay)

            std_count = int(res_std.get("Count", 0))
            std_uids = res_std.get("IdList", [])

            total_search_results = max(gene_count, std_count)

            combined_uids = list(gene_uids)
            for uid in std_uids:
                if uid not in combined_uids:
                    combined_uids.append(uid)

            combined_uids = combined_uids[:max_limit]
            search_strategy_desc = (
                f"Targeted gene field search ('\"{gene_symbol}\"[Gene]', {gene_count} matches) "
                f"supplemented by general term search ({std_count} total matches)."
            )

            logger.info(f"MedGen gene search successful: total_available={total_search_results}, combined_uids={len(combined_uids)}")
            return total_search_results, combined_uids, search_strategy_desc

        except (urllib.error.URLError, TimeoutError) as e:
            logger.warning(f"NCBI MedGen gene search attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
            else:
                logger.error(f"NCBI MedGen gene search failed permanently after {max_retries} retries.")
                raise NCBIConnectionError("Unable to connect to NCBI MedGen service after multiple retries.")
        except Exception as e:
            logger.error(f"NCBI MedGen gene search failed: {e}")
            raise NCBISearchError(f"NCBI MedGen gene search failed: {str(e)}")


def fetch_medgen_records_xml(uids: list[str], batch_size: int = None, delay: float = None) -> list[ET.Element]:
    """
    Fetch structured MedGen XML summaries for UIDs using pagination/batching.
    Includes retry with exponential backoff and rate pacing.
    Returns list of ElementTree DocumentSummary XML elements.
    """
    if not uids:
        return []

    configure_ncbi()

    batch_sz = batch_size or config.NCBI_BATCH_SIZE
    delay_sz = delay if delay is not None else config.NCBI_REQUEST_DELAY

    all_doc_elements = []
    total_uids = len(uids)
    logger.info(f"Fetching MedGen XML records for {total_uids} UIDs in batches of {batch_sz}")

    for i in range(0, total_uids, batch_sz):
        chunk = uids[i:i + batch_sz]
        chunk_ids_str = ",".join(chunk)

        max_retries = 3
        success = False
        raw_xml_bytes = None

        for attempt in range(1, max_retries + 1):
            try:
                handle = Entrez.esummary(db="medgen", id=chunk_ids_str, retmode="xml")
                raw_xml_bytes = handle.read()
                handle.close()
                success = True
                break
            except (urllib.error.URLError, TimeoutError, Exception) as e:
                logger.warning(f"Fetch batch {i // batch_sz + 1} attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(1.0 * attempt)
                else:
                    logger.error(f"Failed to fetch XML batch starting at index {i} after {max_retries} attempts.")

        if success and raw_xml_bytes:
            try:
                root = ET.fromstring(raw_xml_bytes)
                docs = root.findall(".//DocumentSummary")
                all_doc_elements.extend(docs)
                logger.debug(f"Successfully parsed batch starting at index {i} ({len(docs)} DocumentSummary elements)")
            except ET.ParseError as pe:
                logger.error(f"XML parse error in batch starting at index {i}: {pe}")

        time.sleep(delay_sz)

    logger.info(f"Completed MedGen XML fetch: retrieved {len(all_doc_elements)} DocumentSummary elements total.")
    return all_doc_elements


def fetch_single_medgen_record_xml(medgen_uid: str) -> tuple[ET.Element | None, str]:
    """
    Fetch single structured MedGen XML summary element for a specific medgen_uid.
    Returns (doc_element, medgen_uid).
    """
    clean_uid = str(medgen_uid).strip()
    if not clean_uid or not clean_uid.isdigit():
        return None, clean_uid

    docs = fetch_medgen_records_xml([clean_uid], batch_size=1)
    if docs:
        return docs[0], clean_uid
    return None, clean_uid

