import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useWorkspace } from '../context/WorkspaceContext';
import { useNavigate } from 'react-router-dom';

const PRESET_GROUPS = [
  {
    name: "Neurodegenerative Diseases",
    diseases: ["Alzheimer's disease", "Parkinson's disease", "Amyotrophic lateral sclerosis", "Frontotemporal dementia"]
  },
  {
    name: "Metabolic & Endocrine Disorders",
    diseases: ["Type 2 Diabetes Mellitus", "Obesity", "Metabolic Syndrome", "Nonalcoholic Fatty Liver Disease"]
  },
  {
    name: "Cardiovascular Conditions",
    diseases: ["Coronary Artery Disease", "Hypertension", "Atrial Fibrillation", "Heart Failure"]
  }
];

export default function SimilarityPage() {
  const navigate = useNavigate();
  const { isSimilaritySaved, saveSimilarity, removeSimilarity } = useWorkspace();

  const [diseaseInputs, setDiseaseInputs] = useState([
    "Alzheimer's disease",
    "Parkinson's disease",
    "Amyotrophic lateral sclerosis"
  ]);
  const [newInput, setNewInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [similarityData, setSimilarityData] = useState(null);
  const [selectedPair, setSelectedPair] = useState(null);

  const handleAddDisease = (e) => {
    e.preventDefault();
    if (!newInput.trim()) return;
    if (diseaseInputs.length >= 10) {
      setError('Maximum 10 diseases supported per comparison matrix.');
      return;
    }
    const clean = newInput.trim();
    if (diseaseInputs.some((d) => d.toLowerCase() === clean.toLowerCase())) {
      setError(`Disease '${clean}' is already included.`);
      return;
    }
    setDiseaseInputs([...diseaseInputs, clean]);
    setNewInput('');
    setError(null);
  };

  const handleRemoveDisease = (idx) => {
    if (diseaseInputs.length <= 2) {
      setError('Minimum 2 diseases are required for a matrix comparison.');
      return;
    }
    setDiseaseInputs(diseaseInputs.filter((_, i) => i !== idx));
    setError(null);
  };

  const handleLoadPreset = (preset) => {
    setDiseaseInputs(preset.diseases);
    setError(null);
    runMatrixAnalysis(preset.diseases);
  };

  const runMatrixAnalysis = async (diseasesToCompare = diseaseInputs) => {
    if (diseasesToCompare.length < 2 || diseasesToCompare.length > 10) {
      setError('Please select between 2 and 10 diseases.');
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedPair(null);

    try {
      const data = await api.getMultiDiseaseSimilarity(diseasesToCompare);
      setSimilarityData(data);
      if (data.ranked_pairs && data.ranked_pairs.length > 0) {
        setSelectedPair(data.ranked_pairs[0]);
      }
    } catch (err) {
      console.error('Error fetching similarity matrix:', err);
      setError(err.message || 'Failed to compute similarity matrix.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runMatrixAnalysis();
  }, []);

  const exportCSV = () => {
    if (!similarityData) return;
    const matrix = similarityData.matrix;
    const diseases = similarityData.diseases.map(d => d.disease_name);
    
    const rows = [['Disease', ...diseases]];
    matrix.forEach(row => {
      if (!row || !row.length) return;
      const rName = row[0].disease_a;
      const cellVals = row.map(c => `${c.jaccard_similarity}%`);
      rows.push([rName, ...cellVals]);
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
    const a = document.createElement('a');
    a.href = csvContent;
    a.download = `multi_disease_similarity_matrix.csv`;
    a.click();
  };

  const exportJSON = () => {
    if (!similarityData) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(similarityData, null, 2));
    const a = document.createElement('a');
    a.href = dataStr;
    a.download = `multi_disease_similarity_analysis.json`;
    a.click();
  };

  const getHeatmapColor = (pct, isDiagonal) => {
    if (isDiagonal) return 'var(--surface-muted)';
    if (pct === 0) return 'var(--surface)';
    if (pct < 5) return '#E8EFE9';
    if (pct < 15) return '#C8D8CA';
    if (pct < 30) return '#9CB5A0';
    return '#526B59';
  };

  const handleGenerateReport = async () => {
    setLoading(true);
    try {
      const report = await api.generateSimilarityReport(diseaseInputs);
      if (report && report.metadata && report.metadata.report_id) {
        window.location.href = `/report/${report.metadata.report_id}`;
      }
    } catch (err) {
      console.error('Failed to generate similarity report:', err);
      setError('Failed to generate similarity research report.');
    } finally {
      setLoading(false);
    }
  };

  const matrixTitle = similarityData ? `${similarityData.disease_count}-Disease Gene-Set Similarity Matrix` : '';
  const isSaved = isSimilaritySaved(matrixTitle);

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1400px' }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: '1.5rem' }}>
        <h1 className="page-title">
          Gene Overlap Matrix
        </h1>
        <p className="page-description">
          Calculate pairwise Jaccard set similarity and shared reported genes across 2–10 diseases.
        </p>
      </div>

      {/* Input Selector & Presets */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3 className="card-title">Selected Diseases ({diseaseInputs.length}/10)</h3>
          
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>Presets:</span>
            {PRESET_GROUPS.map((preset) => (
              <button
                key={preset.name}
                onClick={() => handleLoadPreset(preset)}
                style={{
                  background: 'var(--surface-muted)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.25rem 0.6rem',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                {preset.name}
              </button>
            ))}
          </div>
        </div>

        {/* Chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
          {diseaseInputs.map((disease, idx) => (
            <div
              key={idx}
              style={{
                background: 'var(--surface-muted)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.25rem 0.65rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: 'var(--text-primary)',
                fontSize: '0.825rem'
              }}
            >
              <span>{disease}</span>
              <button
                onClick={() => handleRemoveDisease(idx)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.9rem', lineHeight: 1 }}
                title="Remove disease"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        {/* Add input form */}
        <form onSubmit={handleAddDisease} style={{ display: 'flex', gap: '0.5rem', maxWidth: '640px', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Add disease name (e.g., Epilepsy, Autism)"
            value={newInput}
            onChange={(e) => setNewInput(e.target.value)}
            className="input-field"
            style={{ flex: 1, minWidth: '220px' }}
          />
          <button
            type="submit"
            className="btn-secondary"
            style={{ padding: '0.45rem 1rem' }}
          >
            Add Disease
          </button>
          
          <button
            type="button"
            onClick={() => runMatrixAnalysis()}
            disabled={loading}
            className="btn-primary"
            style={{ padding: '0.45rem 1.25rem' }}
          >
            {loading ? 'Analyzing...' : 'Generate Matrix'}
          </button>
        </form>

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: '0.75rem' }}>{error}</div>
        )}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
          <div className="spinner" />
          Calculating pairwise Jaccard gene-set similarity across NCBI MedGen records...
        </div>
      )}

      {/* Results View */}
      {!loading && similarityData && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '1.5rem', alignItems: 'start' }}>
          {/* Matrix & Heatmap */}
          <div>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <h2 className="card-title">Pairwise Gene-Set Similarity Heatmap</h2>
                
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button onClick={handleGenerateReport} className="btn-primary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>
                    Generate report
                  </button>
                  <button onClick={exportCSV} className="btn-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>Export CSV</button>
                  <button onClick={exportJSON} className="btn-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>Export JSON</button>
                  <button
                    onClick={() => isSaved ? removeSimilarity(matrixTitle) : saveSimilarity({ title: matrixTitle, ...similarityData })}
                    className="btn-secondary"
                    style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                  >
                    {isSaved ? 'Remove Matrix' : 'Save to Workspace'}
                  </button>
                </div>
              </div>

              {/* Heatmap Grid Table */}
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ minWidth: '130px' }}>Disease</th>
                      {similarityData.diseases.map((d, i) => (
                        <th key={i} style={{ textAlign: 'center', minWidth: '100px' }}>
                          {d.disease_name.length > 18 ? d.disease_name.substring(0, 16) + '...' : d.disease_name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {similarityData.matrix.map((row, rIdx) => (
                      <tr key={rIdx}>
                        <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {similarityData.diseases[rIdx]?.disease_name}
                        </td>
                        {row.map((cell, cIdx) => {
                          const isDiag = rIdx === cIdx;
                          const cellBg = getHeatmapColor(cell.jaccard_similarity, isDiag);
                          const isSelected = selectedPair && (
                            (selectedPair.disease_a === cell.disease_a && selectedPair.disease_b === cell.disease_b) ||
                            (selectedPair.disease_a === cell.disease_b && selectedPair.disease_b === cell.disease_a)
                          );
                          const isDarkBg = !isDiag && cell.jaccard_similarity >= 30;

                          return (
                            <td
                              key={cIdx}
                              onClick={() => {
                                const matched = similarityData.ranked_pairs.find(
                                  p => (p.disease_a === cell.disease_a && p.disease_b === cell.disease_b) ||
                                       (p.disease_a === cell.disease_b && p.disease_b === cell.disease_a)
                                );
                                if (matched) setSelectedPair(matched);
                              }}
                              style={{
                                padding: '0.65rem 0.4rem',
                                textAlign: 'center',
                                background: cellBg,
                                color: isDarkBg ? '#ffffff' : 'var(--text-primary)',
                                fontWeight: isDiag ? 'normal' : '600',
                                border: isSelected ? '2px solid var(--primary)' : '1px solid var(--border)',
                                cursor: isDiag ? 'default' : 'pointer',
                                transition: 'var(--transition-fast)'
                              }}
                            >
                              {cell.jaccard_similarity}%
                              <span style={{ display: 'block', fontSize: '0.7rem', opacity: isDarkBg ? 0.9 : 0.75, fontWeight: 'normal' }}>
                                ({cell.shared_gene_count} genes)
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Ranked Pairs Table */}
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: '1rem' }}>Ranked Disease Pairs by Jaccard Gene-Set Similarity</h3>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Disease A</th>
                      <th>Disease B</th>
                      <th style={{ textAlign: 'center' }}>Shared Genes</th>
                      <th style={{ textAlign: 'center' }}>Jaccard Similarity</th>
                      <th style={{ textAlign: 'center' }}>Overlap Coeff</th>
                    </tr>
                  </thead>
                  <tbody>
                    {similarityData.ranked_pairs.map((pair, idx) => {
                      const isSelected = selectedPair && selectedPair.disease_a === pair.disease_a && selectedPair.disease_b === pair.disease_b;
                      return (
                        <tr
                          key={idx}
                          onClick={() => setSelectedPair(pair)}
                          style={{
                            background: isSelected ? 'var(--surface-muted)' : 'transparent',
                            cursor: 'pointer'
                          }}
                        >
                          <td style={{ color: 'var(--text-muted)' }}>#{idx + 1}</td>
                          <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{pair.disease_a}</td>
                          <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{pair.disease_b}</td>
                          <td style={{ textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>{pair.shared_gene_count}</td>
                          <td style={{ textAlign: 'center', color: 'var(--primary)', fontWeight: 'bold' }}>{pair.jaccard_similarity}%</td>
                          <td style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>{pair.overlap_coefficient}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Inspector Drawer: Shared Genes Detail for Selected Pair */}
          {selectedPair && (
            <div className="card" style={{ position: 'sticky', top: '5rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem', letterSpacing: '0.04em' }}>
                Selected Pair Evidence Explorer
              </div>
              <h3 className="card-title" style={{ fontSize: '1.05rem', marginBottom: '0.75rem' }}>
                {selectedPair.disease_a} vs {selectedPair.disease_b}
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: 'var(--surface-muted)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.8rem', border: '1px solid var(--border)' }}>
                <div><span style={{ color: 'var(--text-muted)' }}>Jaccard: </span><strong style={{ color: 'var(--primary)' }}>{selectedPair.jaccard_similarity}%</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Overlap: </span><strong style={{ color: 'var(--text-primary)' }}>{selectedPair.overlap_coefficient}%</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Shared: </span><strong style={{ color: 'var(--text-primary)' }}>{selectedPair.shared_gene_count}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Union: </span><strong style={{ color: 'var(--text-primary)' }}>{selectedPair.union_gene_count}</strong></div>
              </div>

              <h4 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600 }}>
                Shared Reported Associated Genes ({selectedPair.shared_genes?.length || 0})
              </h4>

              {(!selectedPair.shared_genes || selectedPair.shared_genes.length === 0) ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic', padding: '1rem 0' }}>
                  No shared reported genes found in the analyzed MedGen records for this pair.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '420px', overflowY: 'auto' }}>
                  {selectedPair.shared_genes.map((g, gIdx) => (
                    <div key={gIdx} style={{ background: 'var(--surface-muted)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '0.65rem', fontSize: '0.8rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <strong style={{ color: 'var(--primary)', fontSize: '0.9rem' }}>{g.gene_symbol}</strong>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>NCBI: {g.ncbi_gene_id}</span>
                      </div>

                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.4rem' }}>
                        Freq in A: <strong>{g.frequency_in_a}</strong> ({g.percentage_in_a}%) | Freq in B: <strong>{g.frequency_in_b}</strong> ({g.percentage_in_b}%)
                      </div>

                      <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.35rem' }}>
                        <button
                          onClick={() => navigate(`/gene/${g.gene_symbol}`)}
                          className="btn-secondary-sm"
                          style={{ fontSize: '0.725rem', padding: '0.2rem 0.5rem', minHeight: '26px' }}
                        >
                          Gene Page
                        </button>
                        <button
                          onClick={() => navigate(`/graph?gene=${g.gene_symbol}`)}
                          className="btn-secondary-sm"
                          style={{ fontSize: '0.725rem', padding: '0.2rem 0.5rem', minHeight: '26px' }}
                        >
                          Network Graph
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Non-Clinical Disclaimer */}
      <div className="disclaimer-callout" style={{ marginTop: '2rem' }}>
        <h3>Scientific Terminology &amp; Interpretation Disclaimer</h3>
        <p>
          The pairwise metrics displayed above (Jaccard Similarity, Overlap Coefficient, and Gene Coverages) are strictly standard mathematical gene-set overlap calculations derived from direct AssociatedGenes annotations in NCBI MedGen. They describe reporting overlap in the analyzed record sets and do NOT imply clinical similarity, shared etiology, diagnostic equivalence, or medical prediction.
        </p>
      </div>
    </div>
  );
}
