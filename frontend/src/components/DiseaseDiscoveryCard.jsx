import React from 'react';
import { Link } from 'react-router-dom';

export function DiseaseDiscoveryCard({ disease }) {
  if (!disease) return null;

  const {
    title,
    medgen_uid,
    concept_id,
    semantic_type,
    definition,
    associated_gene_count,
    associated_genes,
  } = disease;

  return (
    <div className="card discovery-card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.35rem' }}>
          <span className="badge badge-blue">MedGen UID: {medgen_uid}</span>
          {concept_id && <span className="badge" style={{ backgroundColor: 'var(--surface-soft)', color: 'var(--text-secondary)' }}>{concept_id}</span>}
          {semantic_type && <span className="badge" style={{ backgroundColor: 'var(--surface-muted)', color: 'var(--accent)' }}>{semantic_type}</span>}
        </div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, fontFamily: 'var(--font-heading)', color: 'var(--text-primary)', margin: 0 }}>
          {title}
        </h3>
      </div>

      {definition && (
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: '1.5', flex: 1, marginBottom: '1rem' }}>
          {definition.length > 180 ? `${definition.substring(0, 180)}...` : definition}
        </p>
      )}

      {associated_genes && associated_genes.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.25rem' }}>
            Reported Genes ({associated_gene_count || associated_genes.length})
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
            {associated_genes.map((g, idx) => {
              const sym = typeof g === 'object' ? g.symbol : g;
              return (
                <Link
                  key={idx}
                  to={`/gene/${encodeURIComponent(sym)}`}
                  className="badge badge-blue"
                  style={{ textDecoration: 'none', fontSize: '0.75rem' }}
                >
                  {sym}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border)', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <Link
          to={`/disease/${encodeURIComponent(title)}`}
          className="btn-primary-sm"
          style={{ textDecoration: 'none', fontSize: '0.85rem' }}
        >
          Analyze Disease →
        </Link>
        <Link
          to={`/medgen/${medgen_uid}`}
          className="btn-secondary-sm"
          style={{ textDecoration: 'none', fontSize: '0.85rem' }}
        >
          View Evidence
        </Link>
      </div>
    </div>
  );
}

export default DiseaseDiscoveryCard;
