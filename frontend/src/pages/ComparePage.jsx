import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useWorkspace } from '../context/WorkspaceContext';
import { StatCard } from '../components/StatCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import SharedGeneCard from '../components/SharedGeneCard';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  LabelList
} from 'recharts';

export function ComparePage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialA = searchParams.get('a') || "Alzheimer's disease";
  const initialB = searchParams.get('b') || 'Parkinson disease';

  const [diseaseA, setDiseaseA] = useState(initialA);
  const [diseaseB, setDiseaseB] = useState(initialB);
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      const rep = await api.generateComparisonReport(diseaseA, diseaseB);
      if (rep && rep.metadata && rep.metadata.report_id) {
        navigate(`/report/${rep.metadata.report_id}`);
      }
    } catch (err) {
      console.error('Error generating report:', err);
      alert(`Failed to generate report: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    if (initialA && initialB) {
      handleCompare(initialA, initialB);
    }
  }, []);

  const handleCompare = async (a = diseaseA, b = diseaseB) => {
    const cleanA = a.trim();
    const cleanB = b.trim();
    if (!cleanA || !cleanB) return;

    setSearchParams({ a: cleanA, b: cleanB });
    setLoading(true);
    setError(null);

    try {
      const res = await api.compareDiseases(cleanA, cleanB);
      setComparison(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e) => {
    e.preventDefault();
    handleCompare();
  };

  const { isComparisonSaved, saveComparison } = useWorkspace();

  const disA = comparison?.disease_a?.query || comparison?.disease_a || diseaseA;
  const disB = comparison?.disease_b?.query || comparison?.disease_b || diseaseB;
  const isSaved = comparison ? isComparisonSaved(disA, disB) : false;

  const overlapChartData = comparison ? [
    { name: `Unique to\n${disA}`, count: comparison.unique_to_a_count ?? comparison.unique_to_a.length, color: 'var(--accent)' },
    { name: 'Shared Genes', count: comparison.shared_genes_count ?? comparison.shared_genes.length, color: 'var(--warning)' },
    { name: `Unique to\n${disB}`, count: comparison.unique_to_b_count ?? comparison.unique_to_b.length, color: 'var(--accent-hover)' }
  ] : [];

  const sharedFreqData = comparison?.shared_genes?.map((sg) => ({
    symbol: sg.symbol || sg.Gene,
    [disA]: sg.count_a ?? sg.Count_A ?? 0,
    [disB]: sg.count_b ?? sg.Count_B ?? 0
  })) || [];

  return (
    <div className="container">
      {/* Header Banner */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title">Compare Diseases</h1>
          <p style={{ color: 'var(--text-muted)', margin: 0 }}>
            Compare reported gene sets between two diseases to identify shared genes and mathematical set overlap.
          </p>
        </div>

        {comparison && (
          <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={handleGenerateReport}
              disabled={generatingReport}
              className="btn-primary"
            >
              {generatingReport ? 'Generating...' : 'Generate report'}
            </button>
            <button
              onClick={() => saveComparison(comparison)}
              className="btn-secondary"
            >
              {isSaved ? 'Saved' : 'Save Comparison'}
            </button>
          </div>
        )}
      </div>

      {/* Comparison Search Input Card */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <form onSubmit={onSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              First Disease (Disease A)
            </label>
            <input
              type="text"
              className="search-input"
              value={diseaseA}
              onChange={(e) => setDiseaseA(e.target.value)}
              placeholder="e.g. Alzheimer's disease"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Second Disease (Disease B)
            </label>
            <input
              type="text"
              className="search-input"
              value={diseaseB}
              onChange={(e) => setDiseaseB(e.target.value)}
              placeholder="e.g. Parkinson disease"
            />
          </div>

          <div>
            <button type="submit" className="btn-primary" style={{ padding: '0.65rem 1.5rem', width: '100%' }}>
              Compare Diseases
            </button>
          </div>
        </form>
      </div>

      {loading && <LoadingState message={`Comparing "${diseaseA}" and "${diseaseB}"...`} />}
      {error && <ErrorState error={error} onRetry={() => handleCompare()} />}

      {!loading && !error && comparison && (
        <div>
          {/* Primary Statistics Grid */}
          <div className="stats-grid">
            <StatCard
              label={`${disA} Genes`}
              value={comparison.disease_a?.unique_genes ?? comparison.genes_a?.length}
              subtext={`${comparison.records_analyzed_a ?? comparison.disease_a?.records_analyzed} records analyzed`}
            />
            <StatCard
              label={`${disB} Genes`}
              value={comparison.disease_b?.unique_genes ?? comparison.genes_b?.length}
              subtext={`${comparison.records_analyzed_b ?? comparison.disease_b?.records_analyzed} records analyzed`}
            />
            <StatCard
              label="Shared Reported Genes"
              value={comparison.similarity?.shared_count ?? comparison.shared_genes.length}
              subtext="Present in both gene sets"
            />
            <StatCard
              label="Jaccard Gene-Set Similarity"
              value={`${comparison.similarity?.jaccard_percentage ?? 0}%`}
              subtext={`Overlap Coeff: ${comparison.similarity?.overlap_coefficient ?? 0}%`}
            />
          </div>

          {/* Research Comparison Summary Card */}
          {comparison.research_summary && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-title" style={{ marginBottom: '0.5rem' }}>Scientific Comparison Summary</div>
              <p style={{ fontSize: '1rem', lineHeight: '1.6', color: 'var(--text-primary)', margin: 0 }}>
                {comparison.research_summary.summary}
              </p>
              <p style={{ fontSize: '0.875rem', fontStyle: 'italic', color: 'var(--text-muted)', marginTop: '0.55rem', margin: 0 }}>
                {comparison.research_summary.disclaimer}
              </p>
            </div>
          )}

          {/* Set Overlap Metrics Summary Card */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-title">Set Overlap Metrics Breakdown</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
              <div style={{ padding: '0.85rem', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--surface-soft)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Jaccard Similarity</span>
                <strong style={{ fontSize: '1.3rem', color: 'var(--primary)' }}>{comparison.similarity?.jaccard_percentage}%</strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>|A ∩ B| / |A ∪ B|</span>
              </div>

              <div style={{ padding: '0.85rem', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--surface-soft)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Overlap Coefficient</span>
                <strong style={{ fontSize: '1.3rem', color: 'var(--warning)' }}>{comparison.similarity?.overlap_coefficient}%</strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>|A ∩ B| / min(|A|, |B|)</span>
              </div>

              <div style={{ padding: '0.85rem', border: '1px solid var(--border-subtle)', borderRadius: '8px', background: 'var(--surface-soft)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>{disA} Coverage</span>
                <strong style={{ fontSize: '1.3rem', color: 'var(--accent)' }}>{comparison.similarity?.coverage_a_percentage ?? 0}%</strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>Shared / {disA} unique</span>
              </div>

              <div style={{ padding: '0.85rem', border: '1px solid var(--border-subtle)', borderRadius: '8px', background: 'var(--surface-soft)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>{disB} Coverage</span>
                <strong style={{ fontSize: '1.3rem', color: 'var(--accent-hover)' }}>{comparison.similarity?.coverage_b_percentage ?? 0}%</strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>Shared / {disB} unique</span>
              </div>
            </div>
          </div>

          {/* Overlap Visualization Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div className="card">
              <div className="card-title">Gene-Set Overlap Breakdown</div>
              <div style={{ width: '100%', height: 260, marginTop: '1rem' }}>
                <ResponsiveContainer>
                  <BarChart data={overlapChartData} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fontWeight: 600 }} />
                    <YAxis label={{ value: 'Direct Genes', angle: -90, position: 'insideLeft', offset: 0 }} allowDecimals={false} />
                    <Tooltip formatter={(val) => [`${val} genes`, 'Gene Count']} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={40}>
                      {overlapChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                      <LabelList dataKey="count" position="top" style={{ fontSize: 12, fontWeight: 700, fill: 'var(--text-primary)' }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {sharedFreqData.length > 0 && (
              <div className="card">
                <div className="card-title">Shared Gene Record Counts</div>
                <div style={{ width: '100%', height: 260, marginTop: '1rem' }}>
                  <ResponsiveContainer>
                    <BarChart data={sharedFreqData} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                      <XAxis dataKey="symbol" tick={{ fontSize: 11, fontWeight: 600 }} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey={disA} fill="var(--accent)" name={disA} radius={[4, 4, 0, 0]} />
                      <Bar dataKey={disB} fill="var(--accent-hover)" name={disB} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          {/* Shared Genes Cards & Evidence */}
          <div className="card" style={{ marginBottom: '2rem' }}>
            <div className="card-title">Shared Reported Genes ({comparison.shared_genes.length})</div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Genes directly annotated in NCBI MedGen records for both {disA} and {disB}. Click any MedGen UID tag to view supporting record details.
            </p>

            {comparison.shared_genes.length > 0 ? (
              <div>
                {comparison.shared_genes.map((sg) => (
                  <SharedGeneCard key={sg.symbol || sg.Gene} gene={sg} diseaseA={disA} diseaseB={disB} />
                ))}
              </div>
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No shared reported genes were found in the analyzed MedGen records.
              </div>
            )}
          </div>

          {/* Unique Genes Columns */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div className="card">
              <div className="card-title" style={{ color: 'var(--primary)', marginBottom: '0.75rem' }}>
                Unique to {disA} ({comparison.unique_to_a.length})
              </div>
              {comparison.unique_to_a.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {comparison.unique_to_a.map((u) => (
                    <Link
                      key={u.symbol || u.Gene}
                      to={`/gene/${encodeURIComponent(u.symbol || u.Gene)}`}
                      className="badge badge-blue"
                      style={{ textDecoration: 'none' }}
                      title={`${u.record_count || u.Record_Count} MedGen records`}
                    >
                      {u.symbol || u.Gene} ({u.record_count || u.Record_Count})
                    </Link>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>None</p>
              )}
            </div>

            <div className="card">
              <div className="card-title" style={{ color: 'var(--accent-hover)', marginBottom: '0.75rem' }}>
                Unique to {disB} ({comparison.unique_to_b.length})
              </div>
              {comparison.unique_to_b.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {comparison.unique_to_b.map((u) => (
                    <Link
                      key={u.symbol || u.Gene}
                      to={`/gene/${encodeURIComponent(u.symbol || u.Gene)}`}
                      className="badge badge-green"
                      style={{ textDecoration: 'none' }}
                      title={`${u.record_count || u.Record_Count} MedGen records`}
                    >
                      {u.symbol || u.Gene} ({u.record_count || u.Record_Count})
                    </Link>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>None</p>
              )}
            </div>
          </div>

          {/* Scientific Disclaimer Box */}
          <div className="disclaimer-callout">
            <h3>Gene-Set Similarity Scientific Disclaimer</h3>
            <p>
              Jaccard similarity measures mathematical set overlap between analyzed NCBI MedGen records (<code>|A ∩ B| / |A ∪ B|</code>).
              It does not represent clinical similarity, disease severity, shared pathology, or diagnostic prediction.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComparePage;
