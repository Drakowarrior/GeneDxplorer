import React from 'react';

export function EvidenceCitation({ citation }) {
  if (!citation) return null;

  const {
    source,
    record_id,
    official_url,
    title,
    disease_title,
    evidence_type,
    gene_symbol,
    clinical_significance,
    review_status,
    retrieved_at
  } = citation;

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '0.85rem 1rem',
      margin: '0.5rem 0',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      boxShadow: 'var(--shadow-xs)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            background: 'var(--surface-muted)',
            color: 'var(--accent)',
            fontSize: '0.75rem',
            fontWeight: 600,
            fontFamily: 'var(--font-body)',
            padding: '0.2rem 0.6rem',
            borderRadius: 'var(--radius-sm)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            border: '1px solid var(--border-subtle)'
          }}>
            {source || 'NCBI Source'}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600, fontFamily: 'var(--font-body)' }}>
            ID: {record_id}
          </span>
        </div>

        {official_url && (
          <a
            href={official_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: 'var(--surface-muted)',
              color: 'var(--accent)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.25rem 0.65rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              fontFamily: 'var(--font-body)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              transition: 'var(--transition-fast)'
            }}
          >
            View NCBI Record ↗
          </a>
        )}
      </div>

      <div style={{ fontSize: '0.925rem', color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'var(--font-heading)' }}>
        {title || disease_title || 'Structured Evidence Record'}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', fontSize: '0.825rem', color: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}>
        <div>Evidence Type: <strong style={{ color: 'var(--text-primary)' }}>{evidence_type || 'Direct Annotation'}</strong></div>
        {gene_symbol && <div>Gene Symbol: <strong style={{ color: 'var(--accent)' }}>{gene_symbol}</strong></div>}
        {clinical_significance && <div>Significance: <strong style={{ color: 'var(--warning-text)' }}>{clinical_significance}</strong></div>}
        {review_status && <div>Review Status: <strong style={{ color: 'var(--text-secondary)' }}>{review_status}</strong></div>}
        {retrieved_at && <div>Retrieved: <span style={{ color: 'var(--text-muted)' }}>{new Date(retrieved_at).toLocaleDateString()}</span></div>}
      </div>
    </div>
  );
}

export default EvidenceCitation;
