import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { getSearchHistory, addSearchHistory, clearSearchHistory } from '../utils/searchHistory';
import { DiseaseDiscoveryCard } from '../components/DiseaseDiscoveryCard';
import { GeneDiscoveryCard } from '../components/GeneDiscoveryCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export function DiscoverPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('disease'); // 'disease' or 'gene'
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Search History State
  const [history, setHistory] = useState(getSearchHistory);

  // Quick Examples list
  const quickExamples = [
    { name: "Alzheimer's disease", type: 'disease' },
    { name: "Cystic fibrosis", type: 'disease' },
    { name: "Sickle cell disease", type: 'disease' },
    { name: "Parkinson disease", type: 'disease' },
    { name: "APOE", type: 'gene' },
    { name: "CFTR", type: 'gene' },
  ];

  // Debounce input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Execute Discovery Search when debounced query changes
  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      executeDiscoverySearch(debouncedQuery, activeTab);
    } else {
      setResults(null);
      setLoading(false);
      setError(null);
    }
  }, [debouncedQuery, activeTab]);

  const executeDiscoverySearch = async (queryTerm, mode) => {
    setLoading(true);
    setError(null);
    try {
      if (mode === 'disease') {
        const res = await api.discoverDiseases(queryTerm, 25);
        setResults(res.results || []);
      } else {
        const res = await api.discoverGenes(queryTerm, 25);
        setResults(res.results || []);
      }

      // Record search in history
      const updatedHistory = addSearchHistory(queryTerm, mode);
      setHistory(updatedHistory);
    } catch (err) {
      setError(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    const empty = clearSearchHistory();
    setHistory(empty);
  };

  const handleSelectExample = (name, type) => {
    setActiveTab(type);
    setSearchQuery(name);
  };

  return (
    <div className="discover-page">
      {/* Header Banner */}
      <div className="page-header" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 className="page-title">Explore</h1>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem', maxWidth: '750px' }}>
              Find diseases, genes, and record-level evidence to investigate from trusted public databases.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
            <span className="badge badge-blue">Source: NCBI MedGen</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Access: Biopython Bio.Entrez</span>
          </div>
        </div>
      </div>

      {/* Exploration Mode Tabs & Search Input Box */}
      <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        {/* Mode Selector Tabs */}
        <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem', marginBottom: '1.25rem' }}>
          <button
            onClick={() => {
              setActiveTab('disease');
              setSearchQuery('');
              setResults(null);
            }}
            className={`btn-tab ${activeTab === 'disease' ? 'active' : ''}`}
            style={{
              padding: '0.5rem 1.25rem',
              fontSize: '0.9rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: activeTab === 'disease' ? '1px solid var(--primary)' : '1px solid var(--border)',
              cursor: 'pointer',
              backgroundColor: activeTab === 'disease' ? 'var(--primary)' : 'var(--surface)',
              color: activeTab === 'disease' ? '#ffffff' : 'var(--text-secondary)',
            }}
          >
            Disease Explorer
          </button>
          <button
            onClick={() => {
              setActiveTab('gene');
              setSearchQuery('');
              setResults(null);
            }}
            className={`btn-tab ${activeTab === 'gene' ? 'active' : ''}`}
            style={{
              padding: '0.5rem 1.25rem',
              fontSize: '0.9rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: activeTab === 'gene' ? '1px solid var(--primary)' : '1px solid var(--border)',
              cursor: 'pointer',
              backgroundColor: activeTab === 'gene' ? 'var(--primary)' : 'var(--surface)',
              color: activeTab === 'gene' ? '#ffffff' : 'var(--text-secondary)',
            }}
          >
            Gene Explorer
          </button>
        </div>

        {/* Input Search Field */}
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            {activeTab === 'disease' ? 'Search MedGen Disease Concepts' : 'Search Gene Symbol Associations'}
          </label>
          <input
            type="text"
            className="search-input"
            placeholder={activeTab === 'disease' ? 'Search MedGen diseases (e.g. Alzheimer, cystic fibrosis, Parkinson...)' : 'Search gene symbol (e.g. APOE, CFTR, APP, BRCA1...)'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.65rem 0.95rem',
              fontSize: '0.95rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-strong)',
            }}
          />
        </div>

        {/* Quick Example Suggestions */}
        <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Quick Examples:</span>
          {quickExamples.map((ex, i) => (
            <button
              key={i}
              onClick={() => handleSelectExample(ex.name, ex.type)}
              style={{
                background: 'var(--surface-muted)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.2rem 0.6rem',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              {ex.name} ({ex.type})
            </button>
          ))}
        </div>
      </div>

      {/* Recently Explored Searches (Client-Side History) */}
      {history && history.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem', padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Recently Explored Searches
            </span>
            <button
              onClick={handleClearHistory}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600 }}
            >
              Clear
            </button>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {history.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectExample(item.query, item.type)}
                style={{
                  padding: '0.25rem 0.65rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-strong)',
                  backgroundColor: 'var(--surface-muted)',
                  fontSize: '0.825rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  cursor: 'pointer',
                }}
              >
                <span>{item.query}</span>
                <span className={`badge ${item.type === 'disease' ? 'badge-blue' : ''}`} style={{ fontSize: '0.7rem', padding: '0.1rem 0.35rem' }}>
                  {item.type}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search Results Display Area */}
      {loading && <LoadingState message={`Retrieving MedGen discovery results for "${debouncedQuery}"...`} />}
      {error && <ErrorState error={error} onRetry={() => executeDiscoverySearch(debouncedQuery, activeTab)} />}

      {!loading && !error && results !== null && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Discovery Results ({results.length})
            </h2>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Live query matches for "{debouncedQuery}"
            </span>
          </div>

          {results.length > 0 ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
              {activeTab === 'disease'
                ? results.map((d) => <DiseaseDiscoveryCard key={d.medgen_uid} disease={d} />)
                : results.map((g, idx) => <GeneDiscoveryCard key={g.symbol || idx} gene={g} />)}
            </div>
          ) : (
            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                No MedGen concepts matched your search.
              </h3>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Try adjusting your search terms or selecting a quick example above.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Initial Landing State when no query is entered */}
      {!loading && !error && results === null && (
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center', backgroundColor: 'var(--surface-soft)' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--brand-primary)', marginBottom: '0.5rem' }}>
            Start Scientific Discovery
          </h3>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 1.5rem', lineHeight: '1.6' }}>
            Enter a disease concept or gene symbol in the search box above to retrieve live structured record summaries and reported gene associations from NCBI MedGen.
          </p>
        </div>
      )}

      {/* Scientific Safeguards Callout */}
      <div className="disclaimer-callout" style={{ marginTop: '2.5rem' }}>
        <h3>Discovery Safeguards & Scientific Interpretation</h3>
        <p>
          Discovery search results represent live structured data retrieved from NCBI MedGen.
          All reported gene associations originate from official <code>&lt;AssociatedGenes&gt;</code> XML elements.
          Discovery search results and search suggestions do not constitute clinical causality, diagnostic prediction, or medical recommendations.
        </p>
      </div>
    </div>
  );
}

export default DiscoverPage;
