import React from 'react';
import { ProviderStatus } from './ProviderStatus';

export function EvidenceSourceCard({ sourceName, providerData, isChecked, onToggle }) {
  const status = providerData?.status || 'unavailable';
  const count = providerData?.count ?? (providerData?.records || []).length;
  const sourceType = providerData?.source_type || 'Scientific Database';

  return (
    <div
      onClick={onToggle}
      className="card"
      style={{
        cursor: 'pointer',
        border: isChecked ? '2px solid var(--brand-accent)' : '1px solid var(--border)',
        backgroundColor: isChecked ? 'var(--surface-soft)' : 'var(--surface)',
        transition: 'all 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <input
            type="checkbox"
            checked={isChecked}
            onChange={(e) => {
              e.stopPropagation();
              onToggle();
            }}
            style={{ width: '18px', height: '18px', cursor: 'pointer' }}
          />
          <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>{sourceName}</strong>
        </div>
        <ProviderStatus status={status} />
      </div>

      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        <div><strong>Type:</strong> {sourceType}</div>
        <div><strong>Records Retrieved:</strong> {count}</div>
      </div>
    </div>
  );
}

export default EvidenceSourceCard;
