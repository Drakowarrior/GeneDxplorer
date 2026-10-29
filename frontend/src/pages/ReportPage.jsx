import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const RECENT_REPORTS_KEY = 'genedxplorer_recent_reports';

export function saveReportToHistory(report) {
  if (!report || !report.metadata || !report.metadata.report_id) return;
  try {
    const raw = localStorage.getItem(RECENT_REPORTS_KEY);
    const existing = raw ? JSON.parse(raw) : [];

    const newItem = {
      report_id: report.metadata.report_id,
      title: report.metadata.title || report.metadata.query,
      report_type: report.metadata.report_type,
      query: report.metadata.query,
      generated_at: report.metadata.generated_at,
    };

    const filtered = existing.filter((item) => item.report_id !== newItem.report_id);
    const updated = [newItem, ...filtered].slice(0, 20); // Keep max 20

    localStorage.setItem(RECENT_REPORTS_KEY, JSON.stringify(updated));
  } catch (err) {
    console.error('Failed to save report to recent history:', err);
  }
}

export function getRecentReportHistory() {
  try {
    const raw = localStorage.getItem(RECENT_REPORTS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    return [];
  }
}

export default function ReportPage() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState(getRecentReportHistory);

  useEffect(() => {
    if (reportId) {
      loadReport();
    }
  }, [reportId]);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReport(reportId);
      setReport(data);
      saveReportToHistory(data);
      setHistory(getRecentReportHistory());
    } catch (err) {
      console.error('Error fetching report:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message={`Retrieving Research Report "${reportId}"...`} />;
  if (error) return <ErrorState error={error} onRetry={loadReport} />;
  if (!report) return null;

  const { metadata, scope, data_quality, gene_analysis, evidence, comparison, similarity_matrix, knowledge_graph, executive_summary, disclaimer, limitations, provenance } = report;

  const downloadFile = (format) => {
    const downloadUrl = `${API_BASE_URL}/api/reports/${encodeURIComponent(reportId)}/export/${format}`;
    window.open(downloadUrl, '_blank');
  };

  const handleCreateSnapshot = async () => {
    try {
      const res = await api.createSnapshotFromReport(reportId);
      if (res && res.snapshot && res.snapshot.snapshot_id) {
        navigate(`/reproducibility/${res.snapshot.snapshot_id}`);
      }
    } catch (err) {
      console.error('Error creating snapshot:', err);
      alert(`Failed to create reproducibility snapshot: ${err.message}`);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1200px' }}>
      {/* Top Navigation & History Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <Link to="/workspace" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem' }}>
          ← Back to Research Workspace
        </Link>

        {/* Download Buttons Bar */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button onClick={handleCreateSnapshot} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
            Create reproducibility snapshot
          </button>
          <button onClick={() => downloadFile('html')} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
            Download HTML
          </button>
          <button onClick={() => downloadFile('json')} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
            Download JSON
          </button>
          <button onClick={() => downloadFile('csv_genes')} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
            Download Genes CSV
          </button>
          <button onClick={() => downloadFile('csv_evidence')} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
            Download Evidence CSV
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem', alignItems: 'start' }}>
        {/* Main Report Document Container */}
        <div className="card" style={{ padding: '2rem' }}>
          {/* Header */}
          <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span className="badge badge-blue">
                Reproducible Scientific Report
              </span>
              <span className="badge badge-purple">
                {metadata.report_type} report
              </span>
            </div>

            <h1 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.85rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
              {metadata.title}
            </h1>

            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Report ID: <code style={{ color: 'var(--text-primary)', background: 'var(--surface-muted)', padding: '0.1rem 0.35rem', borderRadius: 'var(--radius-xs)' }}>{metadata.report_id}</code> &nbsp;•&nbsp; Generated: {new Date(metadata.generated_at).toLocaleString()}
            </div>
          </div>

          {/* Metadata Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={metaCardStyle}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block', fontWeight: 600 }}>QUERY TERM</span>
              <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>{metadata.query}</strong>
            </div>

            <div style={metaCardStyle}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block', fontWeight: 600 }}>SOURCE DATABASE</span>
              <strong style={{ color: 'var(--primary)', fontSize: '0.95rem' }}>{metadata.source}</strong>
            </div>

            <div style={metaCardStyle}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block', fontWeight: 600 }}>RECORDS ANALYZED</span>
              <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>{scope.records_analyzed}</strong>
            </div>

            <div style={metaCardStyle}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block', fontWeight: 600 }}>SOFTWARE VERSION</span>
              <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>v{metadata.software_version}</strong>
            </div>
          </div>

          {/* 1. Executive Summary */}
          <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--surface-muted)' }}>
            <h3 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 700 }}>1. Executive Summary</h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, fontWeight: 500 }}>
              {executive_summary}
            </p>
          </div>

          {/* 2. Dataset Scope & Data Quality */}
          <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--surface)' }}>
            <h3 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 700 }}>2. Dataset Scope &amp; Data Quality</h3>
            <table className="data-table" style={{ width: '100%', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.5rem' }}>Metric</th>
                  <th style={{ padding: '0.5rem' }}>Value</th>
                  <th style={{ padding: '0.5rem' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ padding: '0.5rem' }}>Total Search Matches Available</td>
                  <td style={{ padding: '0.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{scope.records_available}</td>
                  <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>NCBI MedGen query index count</td>
                </tr>
                <tr>
                  <td style={{ padding: '0.5rem' }}>Records Retrieved &amp; Analyzed</td>
                  <td style={{ padding: '0.5rem', fontWeight: 'bold', color: 'var(--primary)' }}>{scope.records_analyzed}</td>
                  <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>Examined DocumentSummary XML records</td>
                </tr>
                <tr>
                  <td style={{ padding: '0.5rem' }}>Records with Direct Gene Annotations</td>
                  <td style={{ padding: '0.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{data_quality.records_with_genes}</td>
                  <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>Structured &lt;AssociatedGenes&gt; XML nodes</td>
                </tr>
                <tr>
                  <td style={{ padding: '0.5rem' }}>Unique Reported Associated Genes</td>
                  <td style={{ padding: '0.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{data_quality.unique_genes}</td>
                  <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>Deduplicated gene symbols</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 3. Gene Analysis Section */}
          {gene_analysis && gene_analysis.length > 0 && (
            <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--surface)' }}>
              <h3 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 700 }}>3. Top Reported Associated Genes ({gene_analysis.length})</h3>
              <div className="table-container">
                <table className="data-table" style={{ width: '100%', fontSize: '0.85rem' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '0.5rem' }}>Rank</th>
                      <th style={{ padding: '0.5rem' }}>Gene Symbol</th>
                      <th style={{ padding: '0.5rem' }}>NCBI Gene ID</th>
                      <th style={{ padding: '0.5rem', textAlign: 'center' }}>Record Count</th>
                      <th style={{ padding: '0.5rem', textAlign: 'center' }}>Record %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gene_analysis.slice(0, 20).map((g, idx) => (
                      <tr key={idx}>
                        <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>#{g.Rank || idx + 1}</td>
                        <td style={{ padding: '0.5rem', fontWeight: 'bold', color: 'var(--primary)' }}>{g.Gene || g.symbol}</td>
                        <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{g.NCBI_Gene_ID || g.ncbi_gene_id || 'N/A'}</td>
                        <td style={{ padding: '0.5rem', textAlign: 'center', fontWeight: 'bold' }}>{g['Record Count'] || g.Record_Count || 0}</td>
                        <td style={{ padding: '0.5rem', textAlign: 'center', color: 'var(--text-primary)' }}>{g.Record_Percentage || 0}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. Evidence Section */}
          {evidence && evidence.length > 0 && (
            <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--surface)' }}>
              <h3 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 700 }}>4. Supporting Evidence Provenance ({evidence.length})</h3>
              <div className="table-container" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table className="data-table" style={{ width: '100%', fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '0.5rem' }}>MedGen UID</th>
                      <th style={{ padding: '0.5rem' }}>Disease Title / Concept</th>
                      <th style={{ padding: '0.5rem' }}>Relationship</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidence.slice(0, 15).map((e, idx) => (
                      <tr key={idx}>
                        <td style={{ padding: '0.4rem', fontFamily: 'monospace', color: 'var(--primary)' }}>{e.medgen_uid || e.record_id || 'N/A'}</td>
                        <td style={{ padding: '0.4rem' }}>{e.disease_title || e.title || e.disease_name || 'Record'}</td>
                        <td style={{ padding: '0.4rem' }}><span className="badge badge-blue">{e.relationship || 'direct'}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 5. Scientific Limitations */}
          <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--surface-muted)' }}>
            <h3 style={{ margin: '0 0 0.75rem 0', color: 'var(--warning)', fontSize: '1.05rem', fontWeight: 700 }}>5. Scientific Limitations &amp; Audit Trail</h3>
            <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0, lineHeight: 1.6 }}>
              {limitations.map((item, idx) => (
                <li key={idx} style={{ marginBottom: '0.35rem' }}>{item}</li>
              ))}
            </ul>
          </div>

          {/* Disclaimer */}
          <div className="disclaimer-callout">
            <h3>Non-Clinical Interpretation Disclaimer</h3>
            <p>{disclaimer}</p>
          </div>
        </div>

        {/* Right Sidebar: Recent Report History */}
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem', fontSize: '1rem' }}>Recent Reports ({history.length})</h3>

          {history.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
              No recent reports stored in local session.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', maxHeight: '500px', overflowY: 'auto' }}>
              {history.map((item) => (
                <Link
                  key={item.report_id}
                  to={`/report/${item.report_id}`}
                  style={{
                    display: 'block',
                    background: item.report_id === reportId ? 'var(--surface-sage)' : 'var(--surface-muted)',
                    border: '1px solid ' + (item.report_id === reportId ? 'var(--primary)' : 'var(--border)'),
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.65rem',
                    textDecoration: 'none',
                    transition: 'var(--transition-fast)'
                  }}
                >
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                    {item.report_type} • {new Date(item.generated_at).toLocaleDateString()}
                  </div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.85rem', marginTop: '0.2rem' }}>
                    {item.title}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const metaCardStyle = {
  background: 'var(--surface-muted)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  padding: '0.75rem',
  fontSize: '0.85rem'
};
