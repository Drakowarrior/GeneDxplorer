import React from 'react';

export function LoadingState({ message = 'Retrieving MedGen data...' }) {
  return (
    <div className="card loading-box">
      <div className="spinner"></div>
      <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
        {message}
      </div>
      <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Connecting live to NCBI MedGen E-utilities...
      </div>
    </div>
  );
}
