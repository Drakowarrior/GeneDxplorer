import React from 'react';

export default function GraphLegend({
  filterType,
  setFilterType,
  searchQuery,
  setSearchQuery,
  nodeCounts,
  onResetView
}) {
  return (
    <div className="graph-legend-container" style={{
      background: 'var(--surface)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      padding: '1rem 1.25rem',
      color: 'var(--text-primary)',
      marginBottom: '1rem',
      boxShadow: 'var(--shadow-xs)'
    }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        {/* Node Type Badges / Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#40576f', display: 'inline-block' }}></span>
            <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>Disease Node</strong> ({nodeCounts?.disease || 0})
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#526b85', display: 'inline-block' }}></span>
            <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>Gene Node</strong> ({nodeCounts?.gene || 0})
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#7c899c', display: 'inline-block' }}></span>
            <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>MedGen Record</strong> ({nodeCounts?.record || 0})
          </div>
          <div style={{ borderLeft: '1px solid var(--border-subtle)', height: '20px', margin: '0 0.2rem' }}></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <span style={{ width: '20px', height: '2px', background: '#526b85', display: 'inline-block' }}></span> Direct Evidence
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <span style={{ width: '20px', height: '2px', background: '#dfe5ee', borderTop: '2px dashed #7c899c', display: 'inline-block' }}></span> 2nd-Hop Overlap
          </div>
        </div>

        {/* Filter Controls & Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Filter nodes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.4rem 0.75rem',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              fontFamily: 'var(--font-body)',
              outline: 'none',
              minWidth: '160px'
            }}
          />

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.4rem 0.75rem',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              fontFamily: 'var(--font-body)',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Node Types</option>
            <option value="disease">Diseases Only</option>
            <option value="gene">Genes Only</option>
            <option value="medgen_record">MedGen Records Only</option>
          </select>

          <button
            onClick={onResetView}
            className="btn-secondary"
            style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }}
          >
            Reset Graph View
          </button>
        </div>
      </div>
    </div>
  );
}
