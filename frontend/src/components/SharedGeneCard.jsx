import React from 'react';
import { Link } from 'react-router-dom';

export function SharedGeneCard({ gene, diseaseA, diseaseB }) {
  if (!gene) return null;

  const symbol = gene.symbol || gene.Gene;
  const geneId = gene.ncbi_gene_id || gene.NCBI_Gene_ID || 'N/A';
  const countA = gene.count_a ?? gene.Count_A ?? 0;
  const pctA = gene.percentage_a ?? gene.Percentage_A ?? 0;
  const countB = gene.count_b ?? gene.Count_B ?? 0;
  const pctB = gene.percentage_b ?? gene.Percentage_B ?? 0;
  const evidenceA = gene.evidence_a || [];
  const evidenceB = gene.evidence_b || [];

  return (
    <div className="shared-gene-card" style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1rem', marginBottom: '1rem', backgroundColor: 'var(--bg-card)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <Link to={`/gene/${encodeURIComponent(symbol)}`} style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--brand-primary)', textDecoration: 'none' }}>
            {symbol}
          </Link>
          <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            NCBI Gene ID: {geneId}
          </span>
        </div>
        <span className="badge badge-green">Shared Reported Gene</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginTop: '0.5rem' }}>
        {/* Disease A Stats & Evidence */}
        <div style={{ padding: '0.75rem', borderRadius: '6px', backgroundColor: 'rgba(79, 70, 229, 0.05)', border: '1px solid rgba(79, 70, 229, 0.2)' }}>
          <div style={{ fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{diseaseA}</div>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            <strong>{countA}</strong> record(s) ({pctA}%)
          </div>
          {evidenceA.length > 0 && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Evidence Records:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.2rem' }}>
                {evidenceA.map((rec) => (
                  <Link key={rec.medgen_uid} to={`/medgen/${rec.medgen_uid}`} className="badge badge-blue" style={{ fontSize: '0.75rem', textDecoration: 'none' }}>
                    UID {rec.medgen_uid}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Disease B Stats & Evidence */}
        <div style={{ padding: '0.75rem', borderRadius: '6px', backgroundColor: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <div style={{ fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{diseaseB}</div>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            <strong>{countB}</strong> record(s) ({pctB}%)
          </div>
          {evidenceB.length > 0 && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Evidence Records:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.2rem' }}>
                {evidenceB.map((rec) => (
                  <Link key={rec.medgen_uid} to={`/medgen/${rec.medgen_uid}`} className="badge badge-green" style={{ fontSize: '0.75rem', textDecoration: 'none' }}>
                    UID {rec.medgen_uid}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SharedGeneCard;
