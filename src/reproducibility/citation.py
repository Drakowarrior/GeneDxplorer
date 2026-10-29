from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import hashlib
from src.reproducibility.models import CitationRecord

def construct_official_ncbi_url(source_name: str, record_type: str, id_val: str) -> str:
    """
    Construct official NCBI source navigation URLs strictly from verified NCBI identifiers.
    Never create fake URLs or use third-party citation sites.
    """
    if not id_val:
        return "https://www.ncbi.nlm.nih.gov/"
    
    clean_id = str(id_val).strip()
    s_lower = source_name.lower()
    r_lower = record_type.lower()
    
    if "clinvar" in s_lower or "clinvar" in r_lower:
        return f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{clean_id}/"
    elif "gene" in r_lower and clean_id.isdigit():
        return f"https://www.ncbi.nlm.nih.gov/gene/{clean_id}"
    elif "medgen" in s_lower or "medgen" in r_lower or clean_id.isdigit():
        return f"https://www.ncbi.nlm.nih.gov/medgen/{clean_id}"
    else:
        return f"https://www.ncbi.nlm.nih.gov/medgen/{clean_id}"

def build_medgen_citation(
    record_uid: str,
    concept_id: Optional[str] = None,
    title: Optional[str] = None,
    gene_symbol: Optional[str] = None,
    disease_title: Optional[str] = None,
    retrieved_at: Optional[str] = None
) -> CitationRecord:
    """
    Generate a structured CitationRecord for an NCBI MedGen record.
    """
    uid_str = str(record_uid).strip()
    c_id = f"medgen_{uid_str}"
    if gene_symbol:
        c_id += f"_{gene_symbol}"
    
    cit_hash = hashlib.md5(c_id.encode('utf-8')).hexdigest()[:10]
    
    official_url = construct_official_ncbi_url("NCBI MedGen", "medgen_uid", uid_str)
    now_iso = retrieved_at or datetime.now(timezone.utc).isoformat()
    
    return CitationRecord(
        citation_id=f"CIT-MG-{cit_hash}",
        source="NCBI MedGen",
        record_id=uid_str,
        title=title or disease_title or f"MedGen UID {uid_str}",
        evidence_type="NCBI MedGen AssociatedGenes XML",
        gene_symbol=gene_symbol,
        disease_title=disease_title or title,
        official_url=official_url,
        retrieved_at=now_iso
    )

def build_clinvar_citation(
    variation_id: str,
    gene_symbol: Optional[str] = None,
    condition_title: Optional[str] = None,
    clinical_significance: Optional[str] = None,
    review_status: Optional[str] = None,
    retrieved_at: Optional[str] = None
) -> CitationRecord:
    """
    Generate a structured CitationRecord for an NCBI ClinVar record.
    """
    v_id = str(variation_id).strip()
    cit_hash = hashlib.md5(f"clinvar_{v_id}".encode('utf-8')).hexdigest()[:10]
    official_url = construct_official_ncbi_url("NCBI ClinVar", "clinvar_variation", v_id)
    now_iso = retrieved_at or datetime.now(timezone.utc).isoformat()
    
    return CitationRecord(
        citation_id=f"CIT-CV-{cit_hash}",
        source="NCBI ClinVar",
        record_id=v_id,
        title=condition_title or f"ClinVar Variation {v_id}",
        evidence_type="NCBI ClinVar Variant Classification",
        gene_symbol=gene_symbol,
        disease_title=condition_title,
        clinical_significance=clinical_significance or "Not specified",
        review_status=review_status or "Not specified",
        official_url=official_url,
        retrieved_at=now_iso
    )

def extract_citations_from_report(report_data: Dict[str, Any]) -> List[CitationRecord]:
    """
    Extract deterministic structured citations from a ResearchReport model dict or analysis payload.
    Sorts deterministically by source, gene_symbol, record_id.
    """
    citations: List[CitationRecord] = []
    seen = set()
    
    retrieved_at = (
        report_data.get("report_metadata", {}).get("retrieval_timestamp") or
        report_data.get("retrieved_at") or
        datetime.now(timezone.utc).isoformat()
    )
    
    # 1. From supporting_records / evidence in report
    evidence_list = (
        report_data.get("evidence", []) or
        report_data.get("supporting_records", [])
    )
    
    for ev in evidence_list:
        if isinstance(ev, dict):
            uid = ev.get("medgen_uid") or ev.get("uid") or ev.get("record_id")
            source = ev.get("source") or ev.get("evidence_source") or "NCBI MedGen"
            gene = ev.get("gene") or ev.get("symbol") or ev.get("gene_symbol")
            d_title = ev.get("disease_title") or ev.get("disease") or ev.get("title")
            
            if uid:
                key = (source, str(uid), str(gene))
                if key not in seen:
                    seen.add(key)
                    if "clinvar" in str(source).lower():
                        cit = build_clinvar_citation(
                            variation_id=str(uid),
                            gene_symbol=gene,
                            condition_title=d_title,
                            clinical_significance=ev.get("clinical_significance"),
                            review_status=ev.get("review_status"),
                            retrieved_at=retrieved_at
                        )
                    else:
                        cit = build_medgen_citation(
                            record_uid=str(uid),
                            concept_id=ev.get("concept_id"),
                            title=d_title,
                            gene_symbol=gene,
                            disease_title=d_title,
                            retrieved_at=retrieved_at
                        )
                    citations.append(cit)
                    
    # Sort deterministically
    citations.sort(key=lambda c: (c.source, c.gene_symbol or "", c.record_id))
    return citations
