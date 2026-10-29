import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';

export function Home() {
  const [recentSearches, setRecentSearches] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadRecentSearches();
  }, []);

  const loadRecentSearches = () => {
    try {
      const history = JSON.parse(localStorage.getItem('genedx_recent_searches') || '[]');
      setRecentSearches(history);
    } catch (e) {
      setRecentSearches([]);
    }
  };

  const clearHistory = () => {
    localStorage.removeItem('genedx_recent_searches');
    setRecentSearches([]);
  };

  const handleRecentClick = (item) => {
    if (item.type === 'disease') {
      navigate(`/disease/${encodeURIComponent(item.query)}`);
    } else {
      navigate(`/gene/${encodeURIComponent(item.query.toUpperCase())}`);
    }
  };

  return (
    <div>
      {/* Scientific & Modern Centered Hero Section */}
      <section className="hero-section">
        <div className="hero-overlay" />
        <div className="hero-content">
          <div className="hero-eyebrow">
            NCBI Structured Biological Evidence
          </div>

          <h1 className="hero-headline">
            Disease–Gene Research Explorer
          </h1>

          <p className="hero-description">
            Explore reported disease–gene associations using structured NCBI MedGen and ClinVar evidence. Inspect source records, compare reported gene sets, and create reproducible research reports.
          </p>

          {/* Primary Search Interface */}
          <div style={{ maxWidth: '720px', margin: '0 auto' }}>
            <SearchBar showExamples={true} />
          </div>
        </div>
      </section>

      {/* Main Exploration Content */}
      <div className="container" style={{ padding: '3rem 1.5rem 4rem', maxWidth: '1100px' }}>
        {/* Local Search History */}
        {recentSearches.length > 0 && (
          <div className="card" style={{
            maxWidth: '820px',
            margin: '0 auto 2.75rem',
            background: 'var(--surface)',
            border: '1px solid var(--border-subtle)',
            padding: '1.25rem 1.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{
                fontWeight: 600,
                fontSize: '0.775rem',
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                fontFamily: 'var(--font-heading)'
              }}>
                Recent Searches
              </span>
              <button
                type="button"
                onClick={clearHistory}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontFamily: 'var(--font-body)'
                }}
              >
                Clear
              </button>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
              {recentSearches.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleRecentClick(item)}
                  style={{
                    background: 'var(--surface-muted)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.25rem 0.65rem',
                    fontSize: '0.825rem',
                    fontWeight: 500,
                    fontFamily: 'var(--font-body)',
                    cursor: 'pointer',
                    transition: 'var(--transition-fast)'
                  }}
                >
                  {item.query} <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>({item.type})</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Core Exploration Modules */}
        <div style={{ marginBottom: '3.5rem' }}>
          <div style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
            <h2 style={{
              color: 'var(--text-primary)',
              fontSize: '1.35rem',
              fontWeight: 700,
              margin: '0 0 0.35rem 0',
              fontFamily: 'var(--font-heading)',
              letterSpacing: '-0.015em'
            }}>
              Core Exploration Modules
            </h2>
            <p style={{
              color: 'var(--text-secondary)',
              fontSize: '0.95rem',
              margin: 0,
              fontFamily: 'var(--font-body)'
            }}>
              Structured tools for genetic annotation retrieval, pairwise overlap analysis, and evidence synthesis.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
            <div className="card" style={featureCardStyle}>
              <div>
                <h3 style={featureTitleStyle}>Diseases &amp; Genes</h3>
                <p style={featureTextStyle}>
                  Investigate reported associated genes and reporting frequencies across analyzed database records.
                </p>
              </div>
              <Link to="/discover" style={featureLinkStyle}>
                Explore concepts →
              </Link>
            </div>

            <div className="card" style={featureCardStyle}>
              <div>
                <h3 style={featureTitleStyle}>Evidence Records</h3>
                <p style={featureTextStyle}>
                  Trace findings directly back to original NCBI MedGen and NCBI ClinVar source records.
                </p>
              </div>
              <Link to="/evidence" style={featureLinkStyle}>
                Review evidence →
              </Link>
            </div>

            <div className="card" style={featureCardStyle}>
              <div>
                <h3 style={featureTitleStyle}>Compare Diseases</h3>
                <p style={featureTextStyle}>
                  Compare gene sets between diseases to calculate mathematical Jaccard set similarity and overlap.
                </p>
              </div>
              <Link to="/compare" style={featureLinkStyle}>
                Run comparison →
              </Link>
            </div>

            <div className="card" style={featureCardStyle}>
              <div>
                <h3 style={featureTitleStyle}>Research Reports</h3>
                <p style={featureTextStyle}>
                  Generate structured research reports with frozen reproducibility snapshots and exports.
                </p>
              </div>
              <Link to="/workspace" style={featureLinkStyle}>
                Open workspace →
              </Link>
            </div>
          </div>
        </div>

        {/* Authoritative Public Sources Section */}
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.5rem',
          textAlign: 'left',
          boxShadow: 'var(--shadow-xs)'
        }}>
          <div style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            fontWeight: 600,
            fontFamily: 'var(--font-heading)',
            marginBottom: '0.4rem'
          }}>
            Authoritative Public Sources
          </div>
          <p style={{
            fontSize: '0.9rem',
            color: 'var(--text-secondary)',
            margin: '0 0 1rem 0',
            lineHeight: 1.5,
            fontFamily: 'var(--font-body)'
          }}>
            Data is retrieved live or from cached snapshots of official National Center for Biotechnology Information (NCBI) repositories.
          </p>
          <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
            <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.925rem', fontFamily: 'var(--font-heading)' }}>
              NCBI MedGen <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.85rem', fontFamily: 'var(--font-body)' }}>(Medical Genetics)</span>
            </div>
            <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.925rem', fontFamily: 'var(--font-heading)' }}>
              NCBI ClinVar <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.85rem', fontFamily: 'var(--font-body)' }}>(Genomic Variation &amp; Phenotypes)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const featureCardStyle = {
  background: 'var(--surface)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 'var(--radius-lg)',
  padding: '1.4rem',
  boxShadow: 'var(--shadow-xs)',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  minHeight: '175px',
  transition: 'var(--transition-normal)'
};

const featureTitleStyle = {
  margin: '0 0 0.5rem 0',
  color: 'var(--text-primary)',
  fontSize: '1.1rem',
  fontWeight: 600,
  fontFamily: 'var(--font-heading)',
  letterSpacing: '-0.01em'
};

const featureTextStyle = {
  margin: '0 0 1.25rem 0',
  color: 'var(--text-secondary)',
  fontSize: '0.9rem',
  lineHeight: 1.55,
  fontFamily: 'var(--font-body)'
};

const featureLinkStyle = {
  color: 'var(--accent)',
  fontSize: '0.875rem',
  fontWeight: 600,
  fontFamily: 'var(--font-body)',
  textDecoration: 'none',
  marginTop: 'auto',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem'
};

export default Home;
