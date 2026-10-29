import React from 'react';

export function AboutPage() {
  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1000px' }}>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h1 className="page-title">About the Research Explorer</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
          Disease–Gene Relationship Explorer &amp; Biological Evidence Environment
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="card">
          <h3 style={titleStyle}>1. Purpose &amp; Overview</h3>
          <p style={textStyle}>
            The <strong>Disease–Gene Research Explorer</strong> is an open scientific research platform designed to systematically retrieve, parse, and analyze reported human gene-disease relationships using live data from trusted sources including <strong>NCBI MedGen</strong> and <strong>NCBI ClinVar</strong>.
          </p>
          <p style={{ ...textStyle, marginBottom: 0 }}>
            It applies strict XML-based direct gene extraction, record-level deduplication, deterministic reporting metrics, and reproducible evidence snapshots.
          </p>
        </div>

        <div className="card">
          <h3 style={titleStyle}>2. Data Source &amp; Retrieval Methodology</h3>
          <div className="table-container">
            <table className="data-table">
              <tbody>
                <tr>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 600, width: '220px' }}>Primary Data Sources:</td>
                  <td style={{ color: 'var(--primary)', fontWeight: 600 }}>NCBI MedGen &amp; NCBI ClinVar</td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Retrieval Engine:</td>
                  <td style={{ color: 'var(--text-secondary)' }}>Biopython <code>Bio.Entrez</code> E-utilities API</td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Extraction Rule:</td>
                  <td style={{ color: 'var(--text-secondary)' }}>Direct <code>&lt;AssociatedGenes&gt;</code> XML nodes and verified ClinVar variant classifications. Text-mining is strictly excluded.</td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Reproducibility:</td>
                  <td style={{ color: 'var(--text-secondary)' }}>Immutable analysis snapshots with canonical 64-character SHA-256 integrity hashes.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h3 style={titleStyle}>3. Key Scientific Metrics Defined</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.25rem' }}>
            <div style={{ background: 'var(--surface-soft)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.35rem', fontWeight: 700 }}>Record Count</h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>
                The number of distinct, analyzed NCBI MedGen records in which a gene was reported as directly associated with the disease.
              </p>
            </div>
            <div style={{ background: 'var(--surface-soft)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.35rem', fontWeight: 700 }}>Record Percentage</h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>
                <code>(Record Count / Records Analyzed) × 100</code>. Represents reporting frequency across analyzed records.
              </p>
            </div>
            <div style={{ background: 'var(--surface-soft)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.35rem', fontWeight: 700 }}>Jaccard Gene-Set Similarity</h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', margin: 0 }}>
                Mathematical set overlap: <code>|A ∩ B| / |A ∪ B| × 100</code>. Measures gene profile similarity between two analyzed diseases.
              </p>
            </div>
          </div>
        </div>

        <div className="disclaimer-callout">
          <h3>Scientific Limitations &amp; Non-Clinical Disclaimer</h3>
          <p style={{ marginBottom: '0.5rem' }}>
            This application is a research demonstration and biological data exploration environment. All association counts and similarity percentages describe reporting frequency in public NCBI metadata.
          </p>
          <p>
            <strong>Notice:</strong> This application does NOT establish biological causality, disease severity, mutation risk, or clinical diagnostic significance.
          </p>
        </div>
      </div>
    </div>
  );
}

const titleStyle = {
  margin: '0 0 1rem 0',
  color: 'var(--text-primary)',
  fontSize: '1.25rem',
  fontWeight: 700
};

const textStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.95rem',
  lineHeight: 1.6,
  marginBottom: '0.75rem'
};

export default AboutPage;
