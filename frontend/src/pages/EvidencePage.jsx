import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { EvidenceSourceCard } from '../components/EvidenceSourceCard';
import { EvidenceRecordCard } from '../components/EvidenceRecordCard';
import { ScientificInterpretationNotice } from '../components/ScientificInterpretationNotice';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export function EvidencePage() {
  const [geneSymbol, setGeneSymbol] = useState('APOE');
  const [searchedSymbol, setSearchedSymbol] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [healthData, setHealthData] = useState(null);

  // Source filters
  const [enabledSources, setEnabledSources] = useState({
    'NCBI MedGen': true,
    ClinVar: true,
  });

  useEffect(() => {
    loadHealth();
  }, []);

  const loadHealth = async () => {
    try {
      const res = await api.getEvidenceHealth();
      setHealthData(res);
    } catch (err) {
      console.warn('Failed to load evidence health status:', err);
    }
  };

  const handleSearch = async (symbolToSearch = geneSymbol) => {
    const clean = symbolToSearch.trim().toUpperCase();
    if (!clean) return;

    setSearchedSymbol(clean);
    setLoading(true);
    setError(null);

    try {
      const res = await api.getUnifiedGeneEvidence(clean);
      setEvidenceData(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSourceFilter = (sourceName) => {
    setEnabledSources((prev) => ({
      ...prev,
      [sourceName]: !prev[sourceName],
    }));
  };

  // Extract all records from active providers matching enabled filter
  const providersObj = evidenceData?.providers || {};
  let allRecords = [];

  Object.keys(providersObj).forEach((sourceName) => {
    if (enabledSources[sourceName]) {
      const pData = providersObj[sourceName];
      if (pData && Array.isArray(pData.records)) {
        allRecords = [...allRecords, ...pData.records];
      }
    }
  });

  const exportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(evidenceData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `unified_evidence_${searchedSymbol || 'gene'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const exportCSV = () => {
    const rows = [
      ['Source', 'Record_ID', 'Gene_Symbol', 'NCBI_Gene_ID', 'Condition_Disease', 'Evidence_Type', 'Interpretation', 'Review_Status', 'Retrieved_At', 'Source_URL']
    ];

    allRecords.forEach((r) => {
      rows.push([
        r.source,
        r.record_id,
        r.gene_symbol,
        r.ncbi_gene_id || '',
        r.disease_name || '',
        r.evidence_type || '',
        r.interpretation || '',
        r.review_status || '',
        r.retrieved_at,
        r.source_url || ''
      ]);
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map((e) => e.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', csvContent);
    downloadAnchor.setAttribute('download', `unified_evidence_${searchedSymbol || 'gene'}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="evidence-page">
      {/* Header Banner */}
      <div className="page-header">
        <h1 className="page-title">Evidence</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Trace biological findings back to NCBI MedGen and NCBI ClinVar source records.
        </p>
      </div>

      {/* Provider Health & Status Bar */}
      {healthData && healthData.providers && (
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Evidence Sources
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            {healthData.providers.map((p, idx) => (
              <EvidenceSourceCard
                key={idx}
                sourceName={p.name}
                providerData={{
                  status: p.status,
                  source_type: p.source_type,
                  count: providersObj[p.name]?.count ?? 0,
                }}
                isChecked={!!enabledSources[p.name]}
                onToggle={() => toggleSourceFilter(p.name)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Gene Search Input */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'end' }}
        >
          <div style={{ flex: 1, minWidth: '240px' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Target Gene Symbol
            </label>
            <input
              type="text"
              className="search-input"
              value={geneSymbol}
              onChange={(e) => setGeneSymbol(e.target.value)}
              placeholder="e.g. APOE, CFTR, APP, BRCA1"
              style={{ width: '100%', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', background: 'var(--surface)', color: 'var(--text-primary)', padding: '0.6rem 0.9rem' }}
            />
          </div>

          <button type="submit" className="btn-primary" style={{ padding: '0.65rem 1.5rem', fontSize: '0.9rem' }}>
            Explore evidence
          </button>
        </form>
      </div>

      {/* Loading & Error States */}
      {loading && <LoadingState message={`Retrieving multi-source evidence for gene "${searchedSymbol}"...`} />}
      {error && <ErrorState error={error} onRetry={() => handleSearch()} />}

      {/* Unified Evidence Results */}
      {!loading && !error && evidenceData && (
        <div>
          {/* Header Action Bar */}
          <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>
                Unified Evidence for Gene: <span style={{ color: 'var(--accent)' }}>{searchedSymbol}</span>
              </h2>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Showing {allRecords.length} records from selected providers ({Object.keys(enabledSources).filter(k => enabledSources[k]).join(', ')})
              </span>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={exportJSON} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
                Export JSON
              </button>
              <button onClick={exportCSV} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
                Export CSV
              </button>
            </div>
          </div>

          <ScientificInterpretationNotice />

          {/* Evidence Records List */}
          {allRecords.length > 0 ? (
            <div>
              {allRecords.map((record, idx) => (
                <EvidenceRecordCard key={idx} record={record} />
              ))}
            </div>
          ) : (
            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No evidence records found matching your selected source filters.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default EvidencePage;
