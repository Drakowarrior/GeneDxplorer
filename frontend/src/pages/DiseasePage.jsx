import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useWorkspace } from '../context/WorkspaceContext';
import { StatCard } from '../components/StatCard';
import { GeneTable } from '../components/GeneTable';
import { GeneChart } from '../components/GeneChart';
import { DiseaseOverview } from '../components/DiseaseOverview';
import { DataQuality } from '../components/DataQuality';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { SearchBar } from '../components/SearchBar';
import { DiscoveryGraph } from '../components/DiscoveryGraph';
import MedGenRecordCard from '../components/MedGenRecordCard';

export function DiseasePage() {
  const { diseaseName } = useParams();
  const navigate = useNavigate();
  const { isDiseaseSaved, saveDisease } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      const rep = await api.generateDiseaseReport(diseaseName);
      if (rep && rep.metadata && rep.metadata.report_id) {
        navigate(`/report/${rep.metadata.report_id}`);
      }
    } catch (err) {
      console.error('Error generating report:', err);
      alert(`Failed to generate report: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const [analysis, setAnalysis] = useState(null);

  const [info, setInfo] = useState(null);
  const [recordsData, setRecordsData] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);

  // Evidence filtering state
  const [evidenceSearch, setEvidenceSearch] = useState('');
  const [selectedGeneFilter, setSelectedGeneFilter] = useState('');
  const [expandedUid, setExpandedUid] = useState(null);

  useEffect(() => {
    if (diseaseName) {
      loadData();
    }
  }, [diseaseName]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analysisRes, infoRes, recordsRes, evidenceRes] = await Promise.all([
        api.getDiseaseAnalysis(diseaseName),
        api.getDiseaseInfo(diseaseName).catch(() => null),
        api.getDiseaseRecords(diseaseName).catch(() => null),
        api.getDiseaseEvidence(diseaseName).catch(() => null)
      ]);

      setAnalysis(analysisRes);
      setInfo(infoRes);
      setRecordsData(recordsRes);
      setEvidenceData(evidenceRes);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message={`Retrieving MedGen records for "${diseaseName}"...`} />;
  if (error) return <ErrorState error={error} onRetry={loadData} />;
  if (!analysis) return null;

  const query = analysis?.query || diseaseName;
  const source = analysis?.source || 'NCBI MedGen';
  const retrieved_at = analysis?.retrieved_at;
  const records = analysis?.records || { total_available: 0, retrieved: 0, analyzed: 0 };
  const data_quality = analysis?.data_quality || { records_with_genes: 0, records_without_genes: 0, total_relationships: 0, unique_genes: 0, duplicate_genes_removed: 0 };
  const genes = analysis?.genes || [];
  const research_summary = analysis?.research_summary;

  const formattedDate = retrieved_at ? new Date(retrieved_at).toLocaleString() : 'N/A';
  const isSaved = isDiseaseSaved(query);

  // Filter evidence list dynamically
  const rawEvidence = evidenceData?.evidence || [];
  const filteredEvidence = rawEvidence.filter((rec) => {
    if (!rec) return false;
    const searchLower = (evidenceSearch || '').toLowerCase().trim();
    const uidMatch = (rec.medgen_uid || '').toLowerCase().includes(searchLower);
    const titleMatch = (rec.disease_title || '').toLowerCase().includes(searchLower);
    const geneMatch = Array.isArray(rec.genes) && rec.genes.some((g) => (g?.symbol || '').toLowerCase().includes(searchLower));

    const passesSearch = !searchLower || uidMatch || titleMatch || geneMatch;

    const passesGeneFilter =
      !selectedGeneFilter ||
      (Array.isArray(rec.genes) && rec.genes.some((g) => (g?.symbol || '').toUpperCase() === selectedGeneFilter.toUpperCase()));

    return passesSearch && passesGeneFilter;
  });

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <SearchBar initialQuery={query} initialType="disease" showExamples={false} />
      </div>

      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">{query}</h1>
          <div className="meta-bar">
            <div className="meta-item">
              <strong>Source:</strong> {source}
            </div>
            <div className="meta-item">
              <strong>Retrieved:</strong> {formattedDate}
            </div>
            <div className="meta-item">
              <span className="badge badge-blue">Disease → Gene Analysis</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            className="btn-primary"
          >
            {generatingReport ? 'Generating...' : 'Generate report'}
          </button>
          <Link
            to={`/graph?disease=${encodeURIComponent(query)}`}
            className="btn-secondary"
          >
            Explore Network
          </Link>
          <button
            onClick={() => saveDisease(analysis)}
            className="btn-secondary"
          >
            {isSaved ? 'Saved' : 'Save to Workspace'}
          </button>
        </div>

      </div>

      {/* Primary Statistics Grid */}
      <div className="stats-grid">
        <StatCard label="Total Matches Available" value={records.total_available} subtext="NCBI MedGen count" />
        <StatCard label="Records Analyzed" value={records.analyzed} subtext={`Retrieved: ${records.retrieved}`} />
        <StatCard
          label="Records With Direct Genes"
          value={data_quality.records_with_genes}
          subtext={`${((data_quality.records_with_genes / records.analyzed) * 100).toFixed(1)}% of analyzed`}
        />
        <StatCard
          label="Unique Genes"
          value={data_quality.unique_genes}
          subtext={`${data_quality.total_relationships} total relationships`}
        />
      </div>

      {/* 1. Disease Overview */}
      <DiseaseOverview info={info} query={query} />

      {/* 2. Data Quality Card */}
      <DataQuality dataQuality={data_quality} records={records} />

      {/* 3. Research Summary Section */}
      {research_summary && (
        <div className="card research-summary-card" style={{ marginTop: '1.5rem' }}>
          <div className="card-title">Scientific Research Summary</div>
          <p className="summary-paragraph" style={{ fontSize: '1rem', lineHeight: '1.6', color: 'var(--text-primary)' }}>
            {research_summary.summary}
          </p>
          <p className="summary-disclaimer" style={{ fontSize: '0.875rem', fontStyle: 'italic', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
            {research_summary.disclaimer}
          </p>
        </div>
      )}

      {/* 4. Top Genes Chart */}
      <GeneChart genes={genes} diseaseName={query} />

      {/* 5. Discovery Relationship Explorer Graph */}
      <DiscoveryGraph diseaseName={query} genes={genes} relatedDiseases={(rawEvidence || []).map(r => ({ title: r?.disease_title || '' }))} />

      {/* 6. Explore Reported Genes Section */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-title">Explore Reported Genes</div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Select any reported gene to explore all verified NCBI MedGen disease concepts associated with that gene symbol.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {genes.map((g) => (
            <Link
              key={g.symbol}
              to={`/gene/${encodeURIComponent(g.symbol)}`}
              className="badge badge-blue"
              style={{ textDecoration: 'none', padding: '0.35rem 0.65rem', fontSize: '0.825rem' }}
            >
              {g.symbol} ({g.record_count} records)
            </Link>
          ))}
        </div>
      </div>

      {/* 7. Explore Related Diseases Section */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-title">Explore Related Diseases</div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Diseases identified through shared reported genes in the analyzed MedGen records.
          <br />
          <em>Note: Relatedness is based strictly on mathematical gene-set overlap, not clinical similarity or diagnosis.</em>
        </p>

        {rawEvidence && rawEvidence.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {Array.from(new Set((rawEvidence || []).map(r => r?.disease_title).filter(t => t && t.toLowerCase() !== query.toLowerCase())))
              .slice(0, 4)
              .map((relTitle, idx) => (
                <div key={idx} style={{ padding: '0.875rem', backgroundColor: 'var(--surface-muted)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{relTitle}</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Shared reported gene annotations in dataset</span>
                  </div>
                  <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
                    <Link
                      to={`/compare?a=${encodeURIComponent(query)}&b=${encodeURIComponent(relTitle)}`}
                      className="btn-secondary-sm"
                      style={{ fontSize: '0.8rem', textDecoration: 'none' }}
                    >
                      Compare →
                    </Link>
                    <Link
                      to={`/disease/${encodeURIComponent(relTitle)}`}
                      className="btn-primary-sm"
                      style={{ fontSize: '0.8rem', textDecoration: 'none' }}
                    >
                      Analyze →
                    </Link>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            No distinct related disease concepts found in this record set. Use the Compare tool to select another disease.
          </p>
        )}
      </div>

      {/* 8. Explore Further Toolbar */}
      <div className="card" style={{ marginTop: '1.5rem', backgroundColor: 'var(--surface-muted)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Explore Further</h4>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Continue your scientific analysis workflow</span>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <Link to={`/compare?a=${encodeURIComponent(query)}`} className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.875rem' }}>
            Compare Disease
          </Link>
          <Link to="/workspace" className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.875rem' }}>
            Open Workspace
          </Link>
        </div>
      </div>

      {/* 9. Ranked Gene Table with Clickable Supporting Records */}
      <div style={{ marginTop: '1.5rem' }}>
        <GeneTable
          genes={genes}
          onSelectGene={(symbol) => {
            setSelectedGeneFilter(selectedGeneFilter === symbol ? '' : symbol);
          }}
          selectedGene={selectedGeneFilter}
        />
      </div>


      {/* 6. Scientific Evidence & Supporting Records Section */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header-flex" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div className="card-title">Evidence & Supporting MedGen Records ({filteredEvidence.length})</div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>
              Showing verified record-level MedGen evidence supporting direct gene associations.
            </p>
          </div>

          {/* Export / Download Buttons */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <a
              href={`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/disease/${encodeURIComponent(query)}`}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary-sm"
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', textDecoration: 'none', color: 'var(--text-primary)', background: 'var(--surface)' }}
            >
              JSON API Data
            </a>
            <a
              href={`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/disease/${encodeURIComponent(query)}/evidence`}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary-sm"
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', textDecoration: 'none', color: 'var(--text-primary)', background: 'var(--surface)' }}
            >
              Evidence JSON
            </a>
          </div>
        </div>

        {/* Evidence Search & Filter Toolbar */}
        <div className="evidence-toolbar" style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '240px' }}>
            <input
              type="text"
              placeholder="Search evidence by gene (e.g. APOE, APP) or MedGen UID..."
              value={evidenceSearch}
              onChange={(e) => setEvidenceSearch(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', fontSize: '0.9rem', background: 'var(--surface)', color: 'var(--text-primary)' }}
            />
          </div>

          {selectedGeneFilter && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="badge badge-blue">Filtering Gene: {selectedGeneFilter}</span>
              <button
                onClick={() => setSelectedGeneFilter('')}
                style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600 }}
              >
                Clear Filter
              </button>
            </div>
          )}
        </div>

        {/* Evidence Cards List */}
        <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredEvidence.length > 0 ? (
            filteredEvidence.map((rec) => (
              <MedGenRecordCard key={rec.medgen_uid} record={rec} />
            ))
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No matching MedGen evidence records found for the current search/filter.
            </div>
          )}
        </div>
      </div>

      {/* 7. All MedGen Records Analyzed Section */}
      {recordsData && recordsData.records && recordsData.records.length > 0 && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <div className="card-title">All MedGen Records Analyzed ({recordsData.records.length})</div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Complete list of retrieved MedGen records. Click any row to expand definition details or view full record page.
          </p>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>MedGen UID</th>
                  <th>Disease Title</th>
                  <th>Direct Associated Genes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recordsData.records.map((r) => {
                  const isExpanded = expandedUid === r.medgen_uid;
                  return (
                    <React.Fragment key={r.medgen_uid}>
                      <tr
                        onClick={() => setExpandedUid(isExpanded ? null : r.medgen_uid)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td>
                          <span style={{ fontWeight: 600, color: 'var(--brand-primary)' }}>{r.medgen_uid}</span>
                        </td>
                        <td>
                          <span style={{ fontWeight: 500 }}>{r.title}</span>
                          {r.concept_id && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                              ({r.concept_id})
                            </span>
                          )}
                        </td>
                        <td>
                          {r.associated_genes && r.associated_genes.length > 0 ? (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                              {r.associated_genes.map((g) => (
                                <Link
                                  key={g.symbol}
                                  to={`/gene/${encodeURIComponent(g.symbol)}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="badge badge-blue"
                                  style={{ textDecoration: 'none' }}
                                >
                                  {g.symbol}
                                </Link>
                              ))}
                            </div>
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.85rem' }}>
                              None reported
                            </span>
                          )}
                        </td>
                        <td>
                          <Link
                            to={`/medgen/${r.medgen_uid}`}
                            onClick={(e) => e.stopPropagation()}
                            style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}
                          >
                            Full Detail →
                          </Link>
                        </td>
                      </tr>
                      {isExpanded && r.definition && (
                        <tr>
                          <td colSpan={4} style={{ backgroundColor: 'var(--surface-soft)', padding: '1rem 1.25rem' }}>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                              MedGen Definition ({r.medgen_uid}):
                            </div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                              {r.definition}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default DiseasePage;
