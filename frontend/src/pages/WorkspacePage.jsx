import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { StatCard } from '../components/StatCard';
import { api } from '../api/client';

export function WorkspacePage() {
  const {
    workspace,
    removeDisease,
    removeGene,
    removeRecord,
    removeComparison,
    removeEvidence,
    addNote,
    deleteNote,
    clearWorkspace,
    exportWorkspaceJSON,
    exportWorkspaceCSV,
  } = useWorkspace();

  const [newNoteText, setNewNoteText] = useState('');
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState(null);

  const handleGenerateWorkspaceReport = async () => {
    setGeneratingReport(true);
    setReportError(null);
    try {
      const report = await api.generateWorkspaceReport(workspace);
      if (report && report.metadata && report.metadata.report_id) {
        window.location.href = `/report/${report.metadata.report_id}`;
      }
    } catch (err) {
      console.error('Failed to generate workspace report:', err);
      setReportError('Failed to generate workspace research report.');
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleAddNote = (e) => {
    e.preventDefault();
    if (!newNoteText.trim()) return;
    addNote(newNoteText);
    setNewNoteText('');
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear your entire Research Workspace? This action cannot be undone.')) {
      clearWorkspace();
    }
  };

  const savedEvidenceList = workspace.evidence || [];

  const totalFindings =
    workspace.diseases.length +
    workspace.genes.length +
    workspace.comparisons.length +
    workspace.records.length +
    savedEvidenceList.length +
    workspace.notes.length;


  return (
    <div className="container">
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title">Research Workspace</h1>
          <p style={{ color: 'var(--text-muted)', margin: 0, maxWidth: '750px' }}>
            Your saved disease, gene, comparison, evidence findings, and research notes.
          </p>
          {reportError && (
            <div style={{ color: 'var(--danger)', marginTop: '0.5rem', fontSize: '0.85rem' }}>{reportError}</div>
          )}
        </div>

        {/* Action Toolbar */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            onClick={handleGenerateWorkspaceReport}
            disabled={generatingReport || totalFindings === 0}
            className="btn-primary"
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.85rem' }}
          >
            {generatingReport ? 'Generating...' : 'Generate research report'}
          </button>
          <button
            onClick={exportWorkspaceJSON}
            disabled={totalFindings === 0}
            className="btn-secondary"
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.85rem' }}
          >
            Export JSON
          </button>
          <button
            onClick={exportWorkspaceCSV}
            disabled={totalFindings === 0}
            className="btn-secondary"
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.85rem' }}
          >
            Export CSV
          </button>
          <button
            onClick={handleClearAll}
            disabled={totalFindings === 0}
            className="btn-danger"
            style={{ padding: '0.55rem 1.15rem', fontSize: '0.85rem' }}
          >
            Clear Workspace
          </button>
        </div>
      </div>

      {/* Workspace Statistics Dashboard */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Workspace Item Counts
        </div>
        <div className="stats-grid">
          <StatCard label="Total Saved Findings" value={totalFindings} subtext="Combined workspace items" />
          <StatCard label="Diseases Saved" value={workspace.diseases.length} subtext="Analyzed disease queries" />
          <StatCard label="Genes Saved" value={workspace.genes.length} subtext="NCBI gene profiles" />
          <StatCard label="Comparisons Saved" value={workspace.comparisons.length} subtext="Cross-disease analyses" />
          <StatCard label="MedGen Records Saved" value={workspace.records.length} subtext="Direct record snapshots" />
          <StatCard label="Research Notes" value={workspace.notes.length} subtext="User-created notes" />
        </div>
      </div>

      {/* 1. Saved Diseases */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">Saved Diseases ({workspace.diseases.length})</div>
        </div>

        {workspace.diseases.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Disease Query</th>
                  <th>Records (Analyzed / Total)</th>
                  <th>Records w/ Genes</th>
                  <th>Unique Genes</th>
                  <th>Top Reported Genes</th>
                  <th>Saved Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workspace.diseases.map((d, i) => (
                  <tr key={i}>
                    <td>
                      <Link to={`/disease/${encodeURIComponent(d.query)}`} style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {d.query}
                      </Link>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Source: {d.source}</div>
                    </td>
                    <td>{d.records_analyzed} / {d.records_available}</td>
                    <td>{d.records_with_genes}</td>
                    <td>{d.unique_genes}</td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                        {d.top_genes && d.top_genes.length > 0 ? (
                          d.top_genes.map((g) => (
                            <Link
                              key={g.symbol}
                              to={`/gene/${encodeURIComponent(g.symbol)}`}
                              className="badge badge-blue"
                              style={{ textDecoration: 'none', fontSize: '0.75rem' }}
                            >
                              {g.symbol} ({g.count})
                            </Link>
                          ))
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(d.saved_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <Link to={`/disease/${encodeURIComponent(d.query)}`} className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}>
                          View →
                        </Link>
                        <button
                          onClick={() => removeDisease(d.query)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No diseases saved to workspace yet. Explore a disease and click <strong>"Save to Workspace"</strong>.
          </div>
        )}
      </div>

      {/* 2. Saved Genes */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">Saved Genes ({workspace.genes.length})</div>
        </div>

        {workspace.genes.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Gene Symbol</th>
                  <th>NCBI Gene ID</th>
                  <th>Candidate Records Examined</th>
                  <th>Verified Disease Records</th>
                  <th>Saved Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workspace.genes.map((g, i) => (
                  <tr key={i}>
                    <td>
                      <Link to={`/gene/${encodeURIComponent(g.symbol)}`} style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                        {g.symbol}
                      </Link>
                    </td>
                    <td>{g.ncbi_gene_id || 'N/A'}</td>
                    <td>{g.candidate_records}</td>
                    <td>{g.verified_diseases_count}</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(g.saved_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <Link to={`/gene/${encodeURIComponent(g.symbol)}`} className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}>
                          View →
                        </Link>
                        <button
                          onClick={() => removeGene(g.symbol)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No genes saved to workspace yet. Search a gene and click <strong>"Save to Workspace"</strong>.
          </div>
        )}
      </div>

      {/* 3. Saved Comparisons */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">Saved Comparisons ({workspace.comparisons.length})</div>
        </div>

        {workspace.comparisons.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Diseases Compared</th>
                  <th>Records (A / B)</th>
                  <th>Shared Genes</th>
                  <th>Unique Genes (A / B)</th>
                  <th>Jaccard Similarity</th>
                  <th>Overlap Coeff</th>
                  <th>Saved Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workspace.comparisons.map((c, i) => (
                  <tr key={i}>
                    <td>
                      <div style={{ fontWeight: 600 }}>
                        {c.disease_a} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>vs</span> {c.disease_b}
                      </div>
                    </td>
                    <td>{c.records_analyzed_a} / {c.records_analyzed_b}</td>
                    <td>
                      <span className="badge badge-blue">{c.shared_genes_count} shared</span>
                    </td>
                    <td>{c.unique_genes_a} / {c.unique_genes_b}</td>
                    <td>
                      <strong style={{ color: 'var(--primary)' }}>{c.jaccard_percentage}%</strong>
                    </td>
                    <td>{c.overlap_coefficient}%</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(c.saved_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <Link
                          to={`/compare?a=${encodeURIComponent(c.disease_a)}&b=${encodeURIComponent(c.disease_b)}`}
                          className="btn-secondary"
                          style={{ textDecoration: 'none', fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}
                        >
                          View →
                        </Link>
                        <button
                          onClick={() => removeComparison(c.disease_a, c.disease_b)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No comparisons saved to workspace yet. Run a disease comparison and click <strong>"Save Comparison"</strong>.
          </div>
        )}
      </div>

      {/* 4. Saved MedGen Records */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">Saved MedGen Records ({workspace.records.length})</div>
        </div>

        {workspace.records.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>MedGen UID</th>
                  <th>Disease Title</th>
                  <th>Concept ID</th>
                  <th>Semantic Type</th>
                  <th>Associated Genes</th>
                  <th>Saved Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workspace.records.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <Link to={`/medgen/${r.medgen_uid}`} style={{ fontWeight: 600, color: 'var(--text-primary)', textDecoration: 'none' }}>
                        {r.medgen_uid}
                      </Link>
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>{r.disease_title}</span>
                    </td>
                    <td>{r.concept_id || 'N/A'}</td>
                    <td>{r.semantic_type || 'N/A'}</td>
                    <td>{r.associated_genes_count} genes</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(r.saved_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <Link to={`/medgen/${r.medgen_uid}`} className="btn-secondary" style={{ textDecoration: 'none', fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}>
                          View →
                        </Link>
                        <button
                          onClick={() => removeRecord(r.medgen_uid)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No MedGen records saved to workspace yet. Open a record detail page and click <strong>"Save Record"</strong>.
          </div>
        )}
      </div>

      {/* 5. Saved Evidence Records */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">Saved Evidence Records ({savedEvidenceList.length})</div>
        </div>

        {savedEvidenceList.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Record ID</th>
                  <th>Gene Symbol</th>
                  <th>Disease / Condition</th>
                  <th>Interpretation / Significance</th>
                  <th>Saved Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {savedEvidenceList.map((ev, i) => (
                  <tr key={i}>
                    <td>
                      <span className="badge badge-blue">
                        {ev.source}
                      </span>
                    </td>
                    <td>
                      <strong style={{ fontSize: '0.85rem' }}>{ev.record_id}</strong>
                    </td>
                    <td>
                      <Link to={`/gene/${encodeURIComponent(ev.gene_symbol)}`} style={{ fontWeight: 700, color: 'var(--text-primary)', textDecoration: 'none' }}>
                        {ev.gene_symbol}
                      </Link>
                    </td>
                    <td>{ev.disease_name || 'N/A'}</td>
                    <td>
                      <span
                        style={{
                          fontWeight: 600,
                          color: (ev.interpretation || '').toLowerCase().includes('pathogenic') ? 'var(--danger)' : (ev.interpretation || '').toLowerCase().includes('benign') ? 'var(--success-text)' : 'var(--warning-text)',
                        }}
                      >
                        {ev.interpretation || 'N/A'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(ev.saved_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {ev.source_url && (
                          <a
                            href={ev.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-secondary"
                            style={{ textDecoration: 'none', fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}
                          >
                            Source ↗
                          </a>
                        )}
                        <button
                          onClick={() => removeEvidence(ev.source, ev.record_id)}
                          style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No evidence records saved to workspace yet. Visit the <Link to="/evidence" style={{ color: 'var(--primary)' }}>Evidence Platform</Link> and click <strong>"+ Save Evidence"</strong>.
          </div>
        )}
      </div>

      {/* 6. User Research Notes */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-title" style={{ marginBottom: '0.5rem' }}>User Research Notes ({workspace.notes.length})</div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Record custom research observations, hypotheses, or summaries during your exploration. Notes are saved locally in your browser workspace.
        </p>

        {/* Add Note Form */}
        <form onSubmit={handleAddNote} style={{ marginBottom: '1.5rem' }}>
          <div style={{ marginBottom: '0.75rem' }}>
            <textarea
              rows={3}
              placeholder="e.g. APOE appeared most frequently in analyzed Alzheimer's MedGen records. Compare with TREM2 in future run."
              value={newNoteText}
              onChange={(e) => setNewNoteText(e.target.value)}
              className="input-field"
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '0.9rem',
                resize: 'vertical',
              }}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ padding: '0.55rem 1.25rem', fontSize: '0.875rem' }}>
            + Add Research Note
          </button>
        </form>

        {/* Notes List */}
        {workspace.notes.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            {workspace.notes.map((note) => (
              <div
                key={note.id}
                style={{
                  padding: '1rem 1.25rem',
                  backgroundColor: 'var(--surface-soft)',
                  borderLeft: '4px solid var(--primary)',
                  border: '1px solid var(--border)',
                  borderLeftWidth: '4px',
                  borderRadius: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '1rem',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                    <span className="badge badge-blue">
                      User Research Note
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(note.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
                    {note.text}
                  </p>
                </div>
                <button
                  onClick={() => deleteNote(note.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--danger)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.9rem' }}>
            No research notes added yet. Use the box above to record observations.
          </div>
        )}
      </div>

      {/* Scientific Safeguards Callout */}
      <div className="disclaimer-callout">
        <h3>Scientific Safeguards & Provenance Distinction</h3>
        <p>
          The Research Workspace stores client-side references in your browser (<code>localStorage</code>).
          <strong> User Research Notes</strong> are observations created by you and are strictly separated from NCBI evidence.
          All disease–gene relationships originate from NCBI MedGen record-level data and represent reported associations, not proven biological causality or diagnostic predictions.
        </p>
      </div>
    </div>
  );
}

export default WorkspacePage;
