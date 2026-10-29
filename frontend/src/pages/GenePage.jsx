import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useWorkspace } from '../context/WorkspaceContext';
import { StatCard } from '../components/StatCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { SearchBar } from '../components/SearchBar';

export function GenePage() {
  const { geneSymbol } = useParams();
  const navigate = useNavigate();
  const { isGeneSaved, saveGene } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [geneData, setGeneData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      const rep = await api.generateGeneReport(geneSymbol);
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
  const [diseaseSearch, setDiseaseSearch] = useState('');


  useEffect(() => {
    if (geneSymbol) {
      loadData();
    }
  }, [geneSymbol]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [res, summaryRes] = await Promise.all([
        api.getGeneDiseases(geneSymbol),
        api.getGeneSummary(geneSymbol).catch(() => null)
      ]);
      setGeneData(res);
      setSummaryData(summaryRes);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message={`Searching NCBI MedGen for gene "${geneSymbol}"...`} />;
  if (error) return <ErrorState error={error} onRetry={loadData} />;
  if (!geneData) return null;

  const { gene, source, retrieved_at, records_examined, matching_disease_count, diseases } = geneData;
  const formattedDate = retrieved_at ? new Date(retrieved_at).toLocaleString() : 'N/A';

  const candidateRecords = summaryData?.candidate_records ?? records_examined;
  const uniqueDiseasesCount = summaryData?.unique_diseases ?? new Set(diseases.map(d => d.title)).size;
  const isSaved = isGeneSaved(gene.symbol);

  const filteredDiseases = diseases.filter((d) => {
    const q = diseaseSearch.toLowerCase().trim();
    if (!q) return true;
    return (
      d.title.toLowerCase().includes(q) ||
      (d.medgen_uid && d.medgen_uid.toLowerCase().includes(q)) ||
      (d.concept_id && d.concept_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <SearchBar initialQuery={gene.symbol} initialType="gene" showExamples={false} />
      </div>

      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Gene: {gene.symbol}</h1>
          <div className="meta-bar">
            <div className="meta-item">
              <strong>NCBI Gene ID:</strong> {gene.ncbi_gene_id || 'N/A'}
            </div>
            <div className="meta-item">
              <strong>Source:</strong> {source}
            </div>
            <div className="meta-item">
              <strong>Retrieved:</strong> {formattedDate}
            </div>
            <div className="meta-item">
              <span className="badge badge-blue">Gene → Multi-Disease Explorer</span>
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
            to={`/graph?gene=${encodeURIComponent(gene.symbol)}`}
            className="btn-secondary"
          >
            Explore Network
          </Link>
          <button
            onClick={() =>
              saveGene({
                symbol: gene.symbol,
                ncbi_gene_id: gene.ncbi_gene_id,
                candidate_records: candidateRecords,
                verified_diseases_count: matching_disease_count,
              })
            }
            className="btn-secondary"
          >
            {isSaved ? 'Saved' : 'Save to Workspace'}
          </button>
        </div>

      </div>

      {/* Summary Statistics Grid */}
      <div className="stats-grid">
        <StatCard label="Candidate MedGen Records" value={candidateRecords} subtext="Total initial search matches" />
        <StatCard label="Verified Disease Records" value={matching_disease_count} subtext="Direct AssociatedGenes matches" />
        <StatCard label="Unique Disease Concepts" value={uniqueDiseasesCount} subtext="Distinct disease titles" />
      </div>

      {/* Gene Overview & Coverage Section */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 className="card-title">Gene Overview &amp; Evidence Coverage</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5, margin: '0 0 1rem 0' }}>
          Gene <strong>{gene.symbol}</strong> (NCBI Gene ID: {gene.ncbi_gene_id || 'N/A'}) was evaluated across {candidateRecords} NCBI MedGen records, identifying {matching_disease_count} verified disease record associations with {uniqueDiseasesCount} unique disease concepts.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          <div style={{ background: 'var(--surface-muted)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block' }}>EVIDENCE SOURCE</span>
            <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>NCBI MedGen AssociatedGenes</strong>
          </div>

          <div style={{ background: 'var(--surface-muted)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block' }}>RETRIEVAL TIMESTAMP</span>
            <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>{formattedDate}</strong>
          </div>

          <div style={{ background: 'var(--surface-muted)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block' }}>ASSOCIATION STATUS</span>
            <span className="badge badge-blue">Direct XML Provenance</span>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header-flex" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <div className="card-title">Verified Disease Associations ({filteredDiseases.length})</div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>
              Relationships verified strictly through official <code>AssociatedGenes</code> XML structure. Free-text mentions excluded.
            </p>
          </div>

          <div style={{ minWidth: '220px' }}>
            <input
              type="text"
              placeholder="Filter diseases by title, UID..."
              value={diseaseSearch}
              onChange={(e) => setDiseaseSearch(e.target.value)}
              style={{ width: '100%', padding: '0.45rem 0.75rem', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)', fontSize: '0.875rem' }}
            />
          </div>
        </div>

        {filteredDiseases.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Disease Title</th>
                  <th>MedGen UID</th>
                  <th>Concept ID</th>
                  <th>Relationship</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDiseases.map((d, idx) => (
                  <tr key={d.medgen_uid || idx}>
                    <td>{idx + 1}</td>
                    <td>
                      <Link to={`/disease/${encodeURIComponent(d.title)}`} className="clickable-link">
                        {d.title}
                      </Link>
                    </td>
                    <td>
                      <Link to={`/medgen/${d.medgen_uid}`} style={{ fontWeight: 600, color: 'var(--primary)', textDecoration: 'none' }}>
                        {d.medgen_uid}
                      </Link>
                    </td>
                    <td>{d.concept_id || 'N/A'}</td>
                    <td>
                      <span className="badge badge-blue">{d.relationship}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Link to={`/disease/${encodeURIComponent(d.title)}`} style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: 600 }}>
                          Analyze Disease →
                        </Link>
                        <Link to={`/medgen/${d.medgen_uid}`} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                          Record Detail →
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No matching associated disease records found.
          </div>
        )}
      </div>

      {/* Explore Further Toolbar */}
      <div className="card" style={{ marginTop: '1.5rem', backgroundColor: 'var(--surface-muted)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Research &amp; Multi-Hop Exploration</h4>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Interactive knowledge network graph &amp; multi-disease matrix tools</span>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <Link to={`/graph?gene=${encodeURIComponent(gene.symbol)}`} className="btn-primary" style={{ textDecoration: 'none', fontSize: '0.875rem' }}>
            Open Gene Network Graph
          </Link>
          <Link to="/similarity" className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.875rem' }}>
            Multi-Disease Matrix
          </Link>
          <Link to="/workspace" className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.875rem' }}>
            Research Workspace
          </Link>
        </div>
      </div>


      <div className="disclaimer-callout" style={{ marginTop: '1.5rem' }}>
        <h3>Scientific Interpretation Disclaimer</h3>
        <p>
          These are disease–gene relationships reported in NCBI MedGen. Their presence does not by itself establish clinical causality or diagnostic significance.
        </p>
      </div>
    </div>
  );
}

export default GenePage;

