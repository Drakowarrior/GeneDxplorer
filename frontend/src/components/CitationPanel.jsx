import React, { useState } from 'react';
import { EvidenceCitation } from './EvidenceCitation';

export function CitationPanel({ citations = [] }) {
  const [filterSource, setFilterSource] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  if (!citations || citations.length === 0) {
    return (
      <div style={{ padding: '1.5rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        No citations recorded for this dataset scope.
      </div>
    );
  }

  const sources = Array.from(new Set(citations.map((c) => c.source)));

  const filteredCitations = citations.filter((c) => {
    if (filterSource !== 'all' && c.source !== filterSource) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchGene = c.gene_symbol && c.gene_symbol.toLowerCase().includes(q);
      const matchTitle = c.title && c.title.toLowerCase().includes(q);
      const matchId = c.record_id && String(c.record_id).includes(q);
      return matchGene || matchTitle || matchId;
    }
    return true;
  });

  return (
    <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
        <div>
          <h4 style={{ margin: 0, color: 'var(--surface-soft)', fontSize: '1rem', fontWeight: 700 }}>
            Source Record Citations ({filteredCitations.length} / {citations.length})
          </h4>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Traceable NCBI MedGen and ClinVar source record links
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            style={{
              background: 'var(--text-primary)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '6px',
              padding: '0.35rem 0.6rem',
              color: 'var(--surface-soft)',
              fontSize: '0.8rem'
            }}
          >
            <option value="all">All Sources ({citations.length})</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by gene, title, or UID..."
            style={{
              background: 'var(--text-primary)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '6px',
              padding: '0.35rem 0.65rem',
              color: 'var(--surface-soft)',
              fontSize: '0.8rem',
              width: '200px'
            }}
          />
        </div>
      </div>

      <div style={{ maxHeight: '500px', overflowY: 'auto', paddingRight: '0.25rem' }}>
        {filteredCitations.map((cit, idx) => (
          <EvidenceCitation key={cit.citation_id || idx} citation={cit} />
        ))}
      </div>
    </div>
  );
}

export default CitationPanel;
