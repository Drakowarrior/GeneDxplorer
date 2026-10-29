import pytest
import xml.etree.ElementTree as ET
from src.parser import DiseaseRecord, GeneAssociation

# Sample XML Fixtures representing actual NCBI MedGen DocumentSummary structures
SAMPLE_MEDGEN_XML_SINGLE_RECORD = """
<eSummaryResult>
  <DocumentSummarySet>
    <DocumentSummary uid="123456">
      <Title>Alzheimer disease 1</Title>
      <ConceptId>C0750900</ConceptId>
      <Definition>A subtype of familial Alzheimer disease caused by mutation in the APP gene.</Definition>
      <SemanticType>Disease or Syndrome</SemanticType>
      <AssociatedGenes>
        <Gene>
          <GeneSymbol>APP</GeneSymbol>
          <GeneID>351</GeneID>
          <Chromosome>21</Chromosome>
          <Location>21q21.3</Location>
        </Gene>
      </AssociatedGenes>
    </DocumentSummary>
  </DocumentSummarySet>
</eSummaryResult>
"""

SAMPLE_MEDGEN_XML_MULTIPLE_GENES_AND_DUPLICATES = """
<eSummaryResult>
  <DocumentSummarySet>
    <DocumentSummary uid="100001">
      <Title>Cystic Fibrosis</Title>
      <ConceptId>C0010674</ConceptId>
      <Definition>An autosomal recessive disorder caused by mutations in CFTR.</Definition>
      <SemanticType>Disease or Syndrome</SemanticType>
      <AssociatedGenes>
        <Gene>
          <GeneSymbol>CFTR</GeneSymbol>
          <GeneID>1080</GeneID>
          <Chromosome>7</Chromosome>
          <Location>7q31.2</Location>
        </Gene>
        <!-- Duplicate gene node within same record -->
        <Gene>
          <GeneSymbol>CFTR</GeneSymbol>
          <GeneID>1080</GeneID>
          <Chromosome>7</Chromosome>
          <Location>7q31.2</Location>
        </Gene>
        <Gene>
          <GeneSymbol>TGFB1</GeneSymbol>
          <GeneID>7040</GeneID>
          <Chromosome>19</Chromosome>
          <Location>19q13.2</Location>
        </Gene>
      </AssociatedGenes>
    </DocumentSummary>
    <DocumentSummary uid="100002">
      <Title>CFTR-related disorder</Title>
      <ConceptId>C1844621</ConceptId>
      <Definition>Spectrum of conditions associated with CFTR variants.</Definition>
      <SemanticType>Disease or Syndrome</SemanticType>
      <AssociatedGenes>
        <Gene>
          <GeneSymbol>CFTR</GeneSymbol>
          <GeneID>1080</GeneID>
          <Chromosome>7</Chromosome>
          <Location>7q31.2</Location>
        </Gene>
      </AssociatedGenes>
    </DocumentSummary>
    <DocumentSummary uid="100003">
      <Title>Unclassified Genetic Syndrome</Title>
      <ConceptId>C9999999</ConceptId>
      <Definition>Condition with no direct gene reported.</Definition>
      <SemanticType>Finding</SemanticType>
    </DocumentSummary>
  </DocumentSummarySet>
</eSummaryResult>
"""

SAMPLE_MEDGEN_XML_MALFORMED = """
<eSummaryResult>
  <DocumentSummarySet>
    <DocumentSummary uid="999">
      <Title>Partial Record</Title>
      <AssociatedGenes>
        <Gene>
          <GeneSymbol>NONE</GeneSymbol>
        </Gene>
        <Gene>
          <Symbol></Symbol>
        </Gene>
      </AssociatedGenes>
    </DocumentSummary>
  </DocumentSummarySet>
</eSummaryResult>
"""

@pytest.fixture
def xml_single_record():
    root = ET.fromstring(SAMPLE_MEDGEN_XML_SINGLE_RECORD)
    return root.findall(".//DocumentSummary")

@pytest.fixture
def xml_multiple_records():
    root = ET.fromstring(SAMPLE_MEDGEN_XML_MULTIPLE_GENES_AND_DUPLICATES)
    return root.findall(".//DocumentSummary")

@pytest.fixture
def xml_malformed():
    root = ET.fromstring(SAMPLE_MEDGEN_XML_MALFORMED)
    return root.findall(".//DocumentSummary")
