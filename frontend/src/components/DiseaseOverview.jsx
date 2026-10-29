import React from 'react';

export function DiseaseOverview({ info, query }) {
  if (!info || !info.records || info.records.length === 0) {
    return null;
  }

  // Primary record (usually first or exact title match)
  const primary = info.records[0];

  return (
    <div className="card">
      <div className="card-title">Disease Overview (NCBI MedGen)</div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Preferred Title</span>
          <div style={{ fontWeight: 600, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{primary.title || query}</div>
        </div>
        <div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>MedGen UID</span>
          <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--brand-primary)' }}>{primary.medgen_uid || 'Not available'}</div>
        </div>
        <div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Concept ID</span>
          <div style={{ fontWeight: 500, fontSize: '0.95rem' }}>{primary.concept_id || 'Not available'}</div>
        </div>
        <div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Semantic Type</span>
          <div>
            <span className="badge badge-blue">{primary.semantic_type || 'Disease or Syndrome'}</span>
          </div>
        </div>
      </div>

      {primary.definition ? (
        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>MedGen Definition</span>
          <p style={{ marginTop: '0.25rem', color: 'var(--text-secondary)', fontSize: '0.925rem', lineHeight: '1.6' }}>
            {primary.definition}
          </p>
        </div>
      ) : (
        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.875rem', fontStyle: 'italic' }}>
          Definition not available in MedGen data.
        </div>
      )}
    </div>
  );
}
