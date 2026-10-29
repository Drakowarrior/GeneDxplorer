import React from 'react';

export function ProviderStatus({ status, enabled = true }) {
  if (!enabled) {
    return (
      <span className="badge" style={{ backgroundColor: 'var(--surface-muted)', color: 'var(--text-muted)' }}>
        Disabled
      </span>
    );
  }

  if (status === 'available') {
    return (
      <span className="badge badge-green">
        Available
      </span>
    );
  }

  if (status === 'unavailable' || status === 'error') {
    return (
      <span className="badge badge-danger">
        Unavailable
      </span>
    );
  }

  return (
    <span className="badge badge-warning">
      {status || 'Unknown'}
    </span>
  );
}

export default ProviderStatus;

