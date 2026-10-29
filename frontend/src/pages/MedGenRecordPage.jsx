import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { useWorkspace } from '../context/WorkspaceContext';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export default function MedGenRecordPage() {
  const { medgenUid } = useParams();
  const { isRecordSaved, saveRecord } = useWorkspace();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRecord = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMedGenRecord(medgenUid);
      setRecord(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecord();
  }, [medgenUid]);

  if (loading) {
    return (
      <div className="medgen-page-wrapper">
        <LoadingState message="Loading MedGen record..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="medgen-page-wrapper">
        <Link to="/" className="back-link">← Back to Explorer</Link>
        <ErrorState error={error} onRetry={fetchRecord} />
      </div>
    );
  }

  if (!record) {
    return (
      <div className="medgen-page-wrapper">
        <Link to="/" className="back-link">← Back to Explorer</Link>
        <ErrorState error={{ message: `MedGen record ${medgenUid} not found.`, status: 404 }} onRetry={fetchRecord} />
      </div>
    );
  }

  const genes = record.associated_genes || [];
  const isSaved = isRecordSaved(record.medgen_uid);
  const ncbiUrl = `https://www.ncbi.nlm.nih.gov/medgen/${record.medgen_uid}`;

  const formattedDate = record.retrieved_at
    ? new Date(record.retrieved_at).toLocaleDateString('en-GB', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : 'N/A';

  return (
    <div className="medgen-page-wrapper">
      {/* ── Back nav ── */}
      <div className="medgen-back-row">
        <Link to="/" className="back-link">← Back to Explorer</Link>
      </div>

      {/* ── Record Header ── */}
      <div className="medgen-header-section">
        <div className="medgen-header-main">
          <div>
            <div className="medgen-eyebrow">NCBI MEDGEN RECORD &nbsp;·&nbsp; UID {record.medgen_uid}</div>
            <h1 className="medgen-title">{record.disease_title}</h1>
          </div>
          <button
            onClick={() => saveRecord(record)}
            className={isSaved ? 'btn-secondary' : 'btn-primary'}
          >
            {isSaved ? 'Saved' : 'Save record'}
          </button>
        </div>
      </div>

      {/* ── Record Metadata ── */}
      <section className="medgen-section">
        <h2 className="medgen-section-title">Record information</h2>
        <div className="medgen-meta-grid">
          {record.concept_id && (
            <div className="medgen-meta-row">
              <span className="medgen-meta-label">Concept ID</span>
              <span className="medgen-meta-value">{record.concept_id}</span>
            </div>
          )}
          {record.semantic_type && (
            <div className="medgen-meta-row">
              <span className="medgen-meta-label">Semantic type</span>
              <span className="medgen-meta-value">{record.semantic_type}</span>
            </div>
          )}
          <div className="medgen-meta-row">
            <span className="medgen-meta-label">Source</span>
            <span className="medgen-meta-value">{record.source || 'NCBI MedGen'}</span>
          </div>
          <div className="medgen-meta-row">
            <span className="medgen-meta-label">Retrieved</span>
            <span className="medgen-meta-value">{formattedDate}</span>
          </div>
        </div>
      </section>

      {/* ── Definition ── */}
      {record.definition && (
        <section className="medgen-section">
          <h2 className="medgen-section-title">Definition</h2>
          <p className="medgen-definition-text">{record.definition}</p>
        </section>
      )}

      {/* ── Associated Genes ── */}
      <section className="medgen-section">
        <div className="medgen-section-header-row">
          <div>
            <h2 className="medgen-section-title">
              Direct associated genes
              <span className="medgen-count-badge">{genes.length}</span>
            </h2>
            <p className="medgen-section-desc">
              Genes extracted directly from structured NCBI MedGen{' '}
              <code className="medgen-code">&lt;AssociatedGenes&gt;</code> XML elements.
            </p>
          </div>
        </div>

        {genes.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Gene symbol</th>
                  <th>NCBI Gene ID</th>
                  <th>Chromosome</th>
                  <th>Cytogenetic location</th>
                  <th>Relationship</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {genes.map((g, index) => (
                  <tr key={index}>
                    <td style={{ color: 'var(--text-muted)', fontWeight: 500 }}>{index + 1}</td>
                    <td>
                      <span className="medgen-gene-symbol">{g.symbol}</span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{g.ncbi_gene_id || '—'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{g.chromosome || '—'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{g.location || '—'}</td>
                    <td>
                      <span className="badge badge-cyan" style={{ textTransform: 'uppercase', fontSize: '0.7rem' }}>
                        {g.relationship || 'direct'}
                      </span>
                    </td>
                    <td>
                      <Link to={`/gene/${g.symbol}`} className="medgen-explore-link">
                        Explore gene →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="medgen-empty-notice">
            No direct associated genes were reported for this NCBI MedGen record.
          </div>
        )}
      </section>

      {/* ── Source ── */}
      <section className="medgen-section">
        <h2 className="medgen-section-title">Source</h2>
        <div className="medgen-source-box">
          <div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
              NCBI MedGen
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              UID {record.medgen_uid}
              {record.concept_id && <span> &nbsp;·&nbsp; Concept {record.concept_id}</span>}
            </div>
          </div>
          <a
            href={ncbiUrl}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
            style={{ whiteSpace: 'nowrap', textDecoration: 'none', fontSize: '0.875rem' }}
          >
            View source on NCBI ↗
          </a>
        </div>
      </section>

      {/* ── Scientific Disclaimer ── */}
      <section className="medgen-section">
        <div className="medgen-disclaimer">
          <div className="medgen-disclaimer-title">Scientific interpretation</div>
          <p className="medgen-disclaimer-text">
            {record.disclaimer ||
              'This information represents structured data retrieved from NCBI MedGen and does not independently establish clinical causality or diagnostic significance. Reported gene associations reflect structured XML annotations in NCBI MedGen records and should not be interpreted as confirmed causal or diagnostic findings.'}
          </p>
        </div>
      </section>
    </div>
  );
}
