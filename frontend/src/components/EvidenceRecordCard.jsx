import React from 'react';
import { useWorkspace } from '../context/WorkspaceContext';

export function EvidenceRecordCard({ record }) {
  const { isEvidenceSaved, saveEvidence } = useWorkspace();
  if (!record) return null;

  const {
    source,
    source_type,
    record_id,
    gene_symbol,
    ncbi_gene_id,
    disease_name,
    relationship,
    evidence_type,
    interpretation,
    review_status,
    retrieved_at,
    source_url,
  } = record;

  const isSaved = isEvidenceSaved(source, record_id);

  // Distinct styling by source
  const isMedGen = source === 'NCBI MedGen';
  const isClinVar = source === 'ClinVar';

  const badgeBg = isMedGen ? 'var(--surface-muted)' : isClinVar ? 'var(--surface-sage)' : 'var(--surface-soft)';
  const badgeColor = isMedGen ? 'var(--accent)' : isClinVar ? 'var(--accent-hover)' : 'var(--text-secondary)';

  return (
    <div
      className="card evidence-record-card"
      style={{
        borderLeft: `4px solid ${isMedGen ? 'var(--accent)' : isClinVar ? 'var(--accent-hover)' : 'var(--border-strong)'}`,
        marginBottom: '1rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span
              style={{
                backgroundColor: badgeBg,
                color: badgeColor,
                fontSize: '0.75rem',
                fontWeight: 600,
                fontFamily: 'var(--font-body)',
                padding: '0.2rem 0.6rem',
                borderRadius: '4px',
                textTransform: 'uppercase',
                border: '1px solid var(--border-subtle)'
              }}
            >
              {source}
            </span>
            <span className="badge" style={{ backgroundColor: 'var(--surface-soft)', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
              Record ID: {record_id}
            </span>
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, fontFamily: 'var(--font-heading)', color: 'var(--text-primary)', margin: 0 }}>
            {disease_name || 'Reported Condition'}
          </h3>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            onClick={() => saveEvidence(record)}
            className={isSaved ? 'btn-secondary-sm' : 'btn-primary-sm'}
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
          >
            {isSaved ? 'Saved Evidence' : 'Save Evidence'}
          </button>
          {source_url && (
            <a
              href={source_url}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary-sm"
              style={{ fontSize: '0.8rem', textDecoration: 'none', padding: '0.35rem 0.75rem' }}
            >
              Source Page ↗
            </a>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', backgroundColor: 'var(--surface-soft)', padding: '0.75rem', borderRadius: '6px', fontSize: '0.875rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Gene Symbol</span>
          <strong style={{ color: 'var(--brand-primary)' }}>{gene_symbol}</strong>
          {ncbi_gene_id && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.3rem' }}>(NCBI: {ncbi_gene_id})</span>}
        </div>

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Evidence Type</span>
          <span>{evidence_type || source_type}</span>
        </div>

        {interpretation && (
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Interpretation / Significance</span>
            <span
              style={{
                fontWeight: 600,
                color: interpretation.toLowerCase().includes('pathogenic') ? 'var(--danger)' : interpretation.toLowerCase().includes('benign') ? 'var(--success-text)' : 'var(--warning-text)',
              }}
            >
              {interpretation}
            </span>
          </div>
        )}

        {review_status && review_status !== 'N/A' && (
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Review Status</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{review_status}</span>
          </div>
        )}
      </div>

      <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
        <span>Relationship: <strong>{relationship || 'reported'}</strong></span>
        <span>Retrieved: {new Date(retrieved_at).toLocaleString()}</span>
      </div>
    </div>
  );
}

export default EvidenceRecordCard;
