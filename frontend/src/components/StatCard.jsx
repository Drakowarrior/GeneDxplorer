import React from 'react';

export function StatCard({ label, value, subtext }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value !== undefined && value !== null ? value : '-'}</div>
      {subtext && <div className="stat-sub">{subtext}</div>}
    </div>
  );
}
