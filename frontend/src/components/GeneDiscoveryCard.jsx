import React from 'react';
import { Link } from 'react-router-dom';

export function GeneDiscoveryCard({ gene }) {
  if (!gene) return null;

  const {
    symbol,
    ncbi_gene_id,
    candidate_records,
    verified_records,
    unique_diseases,
    diseases,
  } = gene;

  return (
    <div className="card discovery-card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.35rem' }}>
          <span className="badge badge-blue">Gene Symbol</span>
          {ncbi_gene_id && ncbi_gene_id !== 'N/A' && (
            <span className="badge" style={{ backgroundColor: 'var(--surface-soft)', color: 'var(--text-secondary)' }}>
              NCBI Gene ID: {ncbi_gene_id}
            </span>
          )}
        </div>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--accent)', margin: 0 }}>
          {symbol}
        </h3>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginBottom: '1rem', backgroundColor: 'var(--surface-soft)', padding: '0.6rem', borderRadius: '6px', textAlign: 'center' }}>
        <div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', fontFamily: 'var(--font-body)' }}>Candidate Records</span>
          <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>{candidate_records ?? 0}</strong>
        </div>
        <div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', fontFamily: 'var(--font-heading)' }}>Verified Diseases</span>
          <strong style={{ fontSize: '0.95rem', color: 'var(--accent)', fontFamily: 'var(--font-heading)' }}>{verified_records ?? 0}</strong>
        </div>
        <div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', fontFamily: 'var(--font-heading)' }}>Unique Concepts</span>
          <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>{unique_diseases ?? 0}</strong>
        </div>
      </div>

      {diseases && diseases.length > 0 && (
        <div style={{ flex: 1, marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
            Associated Diseases ({diseases.length})
          </span>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {diseases.slice(0, 4).map((d, idx) => (
              <li key={idx} style={{ fontSize: '0.85rem', marginBottom: '0.25rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                <Link to={`/disease/${encodeURIComponent(d.title)}`} className="clickable-link">
                  • {d.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border)', display: 'flex', gap: '0.5rem' }}>
        <Link
          to={`/gene/${encodeURIComponent(symbol)}`}
          className="btn-primary-sm"
          style={{ textDecoration: 'none', fontSize: '0.85rem' }}
        >
          Explore Gene →
        </Link>
      </div>
    </div>
  );
}

export default GeneDiscoveryCard;
