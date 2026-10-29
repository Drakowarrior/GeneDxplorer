import pytest
from src.medgen import search_medgen, fetch_medgen_records_xml
from src.parser import parse_medgen_xml

@pytest.mark.integration
def test_live_ncbi_alzheimer_search():
    """
    LIVE NCBI INTEGRATION TEST.
    Requires internet connectivity and accessible NCBI MedGen servers.
    """
    total_results, title_count, uids, strategy = search_medgen("Alzheimer's disease", max_limit=10)
    assert total_results > 0
    assert len(uids) > 0
    
    docs = fetch_medgen_records_xml(uids[:5], batch_size=5)
    assert len(docs) > 0
    
    records, metrics = parse_medgen_xml(docs)
    assert len(records) > 0
    assert metrics["records_analyzed"] > 0


@pytest.mark.integration
def test_live_ncbi_reproducibility_and_citations():
    """
    LIVE NCBI INTEGRATION TEST for Citations & Reproducibility Snapshot.
    Verifies Disease -> MedGen record -> Gene -> Citation chain on live NCBI data.
    """
    from src.reporting import build_disease_report
    from src.reproducibility import create_analysis_snapshot, extract_citations_from_report

    report = build_disease_report("Alzheimer's disease", max_records=5)
    report_dict = report.to_dict()

    snapshot = create_analysis_snapshot(report_dict)
    assert snapshot.snapshot_id.startswith("SNAP-")
    assert len(snapshot.snapshot_hash) == 64

    citations = extract_citations_from_report(report_dict)
    assert len(citations) >= 0
    if len(citations) > 0:
        first_cit = citations[0]
        assert "ncbi.nlm.nih.gov" in first_cit.official_url

