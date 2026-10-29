from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET


@dataclass
class GeneAssociation:
    """
    Data model representing a direct gene association for a MedGen record.
    """
    symbol: str
    ncbi_gene_id: str = ""
    chromosome: str = ""
    location: str = ""
    relationship: str = "direct"
    source: str = "NCBI MedGen"


@dataclass
class DiseaseRecord:
    """
    Data model representing a structured MedGen disease record.
    """
    medgen_uid: str
    title: str
    concept_id: str = ""
    definition: str = ""
    semantic_type: str = ""
    associated_genes: List[GeneAssociation] = field(default_factory=list)


def parse_medgen_xml(doc_elements):
    """
    Parse a list of ElementTree DocumentSummary XML elements.
    Extracts structured DiseaseRecord objects and direct Associated Genes ONLY.
    Applies record-level deduplication to ensure each gene counts at most once per record.

    Returns:
      - records (List[DiseaseRecord]): Parsed disease records
      - metrics (dict): Parsing and data quality metrics
    """
    records = []
    
    total_raw_gene_nodes = 0
    total_dedup_gene_nodes = 0
    records_with_genes_count = 0
    records_without_genes_count = 0

    for doc in doc_elements:
        uid = str(doc.get("uid", "")).strip()
        title = str(doc.findtext("Title") or "Unknown Title").strip()
        concept_id = str(doc.findtext("ConceptId") or "").strip()
        definition = str(doc.findtext("Definition") or "").strip()
        semantic_type = str(doc.findtext("SemanticType") or "").strip()

        # Direct AssociatedGenes extraction ONLY
        raw_genes_found = []

        for assoc_node in doc.findall(".//AssociatedGenes"):
            for gene_elem in assoc_node:
                symbol = (
                    gene_elem.findtext("GeneSymbol")
                    or gene_elem.findtext("Symbol")
                    or gene_elem.text
                )
                gene_id = (
                    gene_elem.get("gene_id")
                    or gene_elem.get("id")
                    or gene_elem.findtext("GeneID")
                )
                chrom = (
                    gene_elem.get("chromosome")
                    or gene_elem.findtext("Chromosome")
                )
                loc = (
                    gene_elem.get("cytogen_loc")
                    or gene_elem.get("location")
                    or gene_elem.findtext("Location")
                )

                if symbol:
                    sym_clean = str(symbol).strip()
                    if sym_clean and sym_clean.lower() not in ["none", "null", "n/a", "unknown"]:
                        raw_genes_found.append(
                            GeneAssociation(
                                symbol=sym_clean,
                                ncbi_gene_id=str(gene_id).strip() if gene_id else "",
                                chromosome=str(chrom).strip() if chrom else "",
                                location=str(loc).strip() if loc else "",
                                relationship="direct",
                                source="NCBI MedGen"
                            )
                        )

        total_raw_gene_nodes += len(raw_genes_found)

        # Record-level deduplication: preserve unique gene symbols per record
        seen_symbols = set()
        dedup_genes = []
        for g in raw_genes_found:
            if g.symbol not in seen_symbols:
                seen_symbols.add(g.symbol)
                dedup_genes.append(g)

        total_dedup_gene_nodes += len(dedup_genes)

        if dedup_genes:
            records_with_genes_count += 1
        else:
            records_without_genes_count += 1

        disease_rec = DiseaseRecord(
            medgen_uid=uid,
            title=title,
            concept_id=concept_id,
            definition=definition,
            semantic_type=semantic_type,
            associated_genes=dedup_genes
        )
        records.append(disease_rec)

    duplicate_genes_removed = total_raw_gene_nodes - total_dedup_gene_nodes

    metrics = {
        "records_analyzed": len(records),
        "records_with_genes": records_with_genes_count,
        "records_without_genes": records_without_genes_count,
        "total_relationships": total_dedup_gene_nodes,
        "duplicate_genes_removed": duplicate_genes_removed
    }

    return records, metrics
