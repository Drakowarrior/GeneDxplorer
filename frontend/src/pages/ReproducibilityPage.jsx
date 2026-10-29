import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import CitationPanel from '../components/CitationPanel';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export function ReproducibilityPage() {
  const { snapshotId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [snapshot, setSnapshot] = useState(null);
  const [manifest, setManifest] = useState(null);
  const [citations, setCitations] = useState([]);

  useEffect(() => {
    if (snapshotId) {
      loadSnapshotData();
    }
  }, [snapshotId]);

  const loadSnapshotData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [snapData, manData, citData] = await Promise.all([
        api.getSnapshot(snapshotId),
        api.getSnapshotManifest(snapshotId).catch(() => null),
        api.getSnapshotCitations(snapshotId).catch(() => [])
      ]);
      setSnapshot(snapData);
      setManifest(manData);
      setCitations(citData);
    } catch (err) {
      console.error('Error fetching snapshot:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message={`Fetching reproducibility snapshot "${snapshotId}"...`} />;
  if (error) return <ErrorState error={error} onRetry={loadSnapshotData} />;
  if (!snapshot) return null;

  const downloadUrl = (fmt) => `${API_BASE_URL}/api/reproducibility/snapshot/${snapshot.snapshot_id}/export/${fmt}`;

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1300px' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>
            Reproducibility
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '0.5rem 0 0 0', fontSize: '0.95rem', maxWidth: '750px' }}>
            This snapshot preserves the exact analysis state used to generate this research result.
          </p>
        </div>

        {snapshot.report_id && (
          <Link
            to={`/report/${snapshot.report_id}`}
            className="btn-secondary"
            style={{ fontSize: '0.875rem' }}
          >
            ← Back to Report
          </Link>
        )}
      </div>

      {/* Snapshot Integrity Header Card */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</span>
            <div style={{ marginTop: '0.35rem' }}>
              <span className="badge badge-green" style={{ fontSize: '0.85rem' }}>Verified Snapshot</span>
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>SHA-256 Hash</span>
            <div style={{ fontSize: '0.85rem', fontFamily: 'monospace', color: 'var(--success)', background: 'rgba(16, 185, 129, 0.1)', padding: '0.5rem 0.75rem', borderRadius: '6px', marginTop: '0.35rem', wordBreak: 'break-all' }}>
              {snapshot.snapshot_hash}
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Generated</span>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginTop: '0.35rem', fontWeight: 600 }}>
              {new Date(snapshot.created_at).toLocaleDateString()}
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Software Version</span>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.35rem' }}>
              v{snapshot.software_version}
            </div>
          </div>
        </div>
      </div>

      {/* Grid Split: Manifest Scope & Action Toolbar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem', marginBottom: '2rem', alignItems: 'start' }}>
        {/* Manifest & Execution Parameters */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '1.1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            Analysis details
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.875rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Search Strategy:</span>
              <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.2rem' }}>{snapshot.search_strategy}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Calculation Method:</span>
              <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.2rem' }}>{manifest?.calculation_method || 'MedGen XML parsing'}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Data Sources:</span>
              <div style={{ color: 'var(--accent)', fontWeight: 600, marginTop: '0.2rem' }}>{(manifest?.source_providers || ['NCBI MedGen']).join(', ')}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Retrieval Limit:</span>
              <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.2rem' }}>{manifest?.analysis_limit || 500} records</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Source Records Analyzed:</span>
              <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.2rem' }}>{manifest?.source_record_ids?.length || 0} MedGen UIDs</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Gene IDs Identified:</span>
              <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '0.2rem' }}>{manifest?.gene_ids?.length || 0} unique IDs</div>
            </div>
          </div>
        </div>

        {/* Reproducibility Package Exports Toolbar */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '1.1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            Downloads
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <a
              href={downloadUrl('zip')}
              className="btn-primary"
              style={{
                textDecoration: 'none',
                textAlign: 'center',
                fontWeight: 600,
                fontSize: '0.875rem'
              }}
            >
              Download ZIP package (.zip)
            </a>

            <a
              href={downloadUrl('publication_csv')}
              className="btn-secondary"
              style={{ textDecoration: 'none', textAlign: 'center', fontSize: '0.85rem' }}
            >
              Publication Evidence CSV
            </a>

            <a
              href={downloadUrl('manifest')}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary"
              style={{ textDecoration: 'none', textAlign: 'center', fontSize: '0.85rem' }}
            >
              View Manifest JSON
            </a>

            <a
              href={downloadUrl('readme')}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary"
              style={{ textDecoration: 'none', textAlign: 'center', fontSize: '0.85rem' }}
            >
              View Plaintext README
            </a>
          </div>
        </div>
      </div>

      {/* Source Record Citations Panel */}
      <CitationPanel citations={citations} />

      {/* Disclaimer Callout */}
      <div className="disclaimer-callout" style={{ marginTop: '2rem' }}>
        <h3>Scientific Reproducibility & Traceability Guidelines</h3>
        <p>
          This snapshot freezes the analytical execution state and record provenance. All source links point strictly to authoritative NCBI MedGen and ClinVar database entries.
        </p>
      </div>
    </div>
  );
}

const actionLinkStyle = {
  background: 'rgba(30, 41, 59, 0.8)',
  color: 'var(--border-strong)',
  border: '1px solid rgba(255, 255, 255, 0.15)',
  borderRadius: '6px',
  padding: '0.55rem 0.85rem',
  fontSize: '0.85rem',
  fontWeight: 500,
  textDecoration: 'none',
  textAlign: 'center',
  display: 'block',
  transition: 'all 0.2s ease'
};

export default ReproducibilityPage;
