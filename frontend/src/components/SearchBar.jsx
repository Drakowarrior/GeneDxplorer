import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function SearchBar({ initialQuery = '', initialType = 'disease', showExamples = true }) {
  const [query, setQuery] = useState(initialQuery);
  const [searchType, setSearchType] = useState(initialType);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    // Save to localStorage (max 5 items)
    saveRecentSearch(cleanQuery, searchType);

    if (searchType === 'disease') {
      navigate(`/disease/${encodeURIComponent(cleanQuery)}`);
    } else {
      navigate(`/gene/${encodeURIComponent(cleanQuery.toUpperCase())}`);
    }
  };

  const saveRecentSearch = (q, type) => {
    try {
      const history = JSON.parse(localStorage.getItem('genedx_recent_searches') || '[]');
      const filtered = history.filter(item => !(item.query.toLowerCase() === q.toLowerCase() && item.type === type));
      const updated = [{ query: q, type, timestamp: new Date().toISOString() }, ...filtered].slice(0, 5);
      localStorage.setItem('genedx_recent_searches', JSON.stringify(updated));
    } catch (err) {
      console.warn('Could not save to localStorage:', err);
    }
  };

  const handleExampleClick = (item, type) => {
    setQuery(item);
    setSearchType(type);
    saveRecentSearch(item, type);
    if (type === 'disease') {
      navigate(`/disease/${encodeURIComponent(item)}`);
    } else {
      navigate(`/gene/${encodeURIComponent(item.toUpperCase())}`);
    }
  };

  return (
    <div className="search-box-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-group">
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className="type-select"
            aria-label="Search Type"
          >
            <option value="disease">Disease</option>
            <option value="gene">Gene Symbol</option>
          </select>
          <input
            type="text"
            className="search-input"
            placeholder={searchType === 'disease' ? "e.g., Alzheimer's disease, Cystic fibrosis, Diabetes..." : "e.g., APP, CFTR, HBB, APOE..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search Input"
          />
        </div>
        <button type="submit" className="btn-primary">
          Search
        </button>
      </form>

      {showExamples && (
        <div className="examples-bar">
          <span>Try examples:</span>
          <button type="button" className="example-chip" onClick={() => handleExampleClick("Alzheimer's disease", 'disease')}>
            Alzheimer's disease
          </button>
          <button type="button" className="example-chip" onClick={() => handleExampleClick('Cystic fibrosis', 'disease')}>
            Cystic fibrosis
          </button>
          <button type="button" className="example-chip" onClick={() => handleExampleClick('Sickle cell disease', 'disease')}>
            Sickle cell disease
          </button>
          <button type="button" className="example-chip" onClick={() => handleExampleClick('APP', 'gene')}>
            APP
          </button>
          <button type="button" className="example-chip" onClick={() => handleExampleClick('CFTR', 'gene')}>
            CFTR
          </button>
          <button type="button" className="example-chip" onClick={() => handleExampleClick('HBB', 'gene')}>
            HBB
          </button>
        </div>
      )}
    </div>
  );
}
