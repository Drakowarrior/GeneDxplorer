import React from 'react';

export function Footer() {
  return (
    <footer style={{
      background: 'var(--surface)',
      borderTop: '1px solid var(--border)',
      padding: '2rem 1.5rem',
      marginTop: 'auto',
      color: 'var(--text-secondary)',
      fontSize: '0.85rem'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <strong style={{ color: 'var(--text-primary)', fontSize: '0.95rem', fontFamily: 'var(--font-heading)' }}>
              Disease–Gene Research Explorer
            </strong>
            <div style={{ marginTop: '0.2rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Scientific research environment using authoritative public databases.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
            <span>Sources: <strong style={{ color: 'var(--text-primary)' }}>NCBI MedGen</strong> &amp; <strong style={{ color: 'var(--text-primary)' }}>NCBI ClinVar</strong></span>
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem', fontSize: '0.775rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          Scientific Note: Reported gene associations represent structured database annotations retrieved from public sources. They do not imply clinical causality, medical diagnosis, or individual disease risk prediction.
        </div>
      </div>
    </footer>
  );
}

export default Footer;
