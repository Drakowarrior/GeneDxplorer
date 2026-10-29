import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';

export default function GraphInspector({
  selectedNode,
  selectedEdge,
  onClose,
  onExploreNode
}) {
  const navigate = useNavigate();
  const {
    isGraphNodeSaved,
    saveGraphNode,
    removeGraphNode,
    isGraphEdgeSaved,
    saveGraphEdge,
    removeGraphEdge
  } = useWorkspace();

  if (!selectedNode && !selectedEdge) {
    return (
      <div className="graph-inspector-panel" style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.5rem',
        color: 'var(--text-muted)',
        fontSize: '0.9rem',
        height: '100%',
        minHeight: '380px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center'
      }}>
        <div style={{ color: 'var(--accent-sage)', marginBottom: '0.75rem' }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </div>
        <h3 style={{ color: 'var(--text-primary)', margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: 600 }}>Graph Inspector</h3>
        <p style={{ margin: 0, maxWidth: '240px', lineHeight: 1.4, color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
          Select any disease, gene, or record node (or graph edge) to inspect details.
        </p>
      </div>
    );
  }

  // --- INSPECT EDGE ---
  if (selectedEdge) {
    const isSaved = isGraphEdgeSaved(selectedEdge.edge_id);
    return (
      <div className="graph-inspector-panel" style={{
        background: 'var(--surface)',
        border: '1px solid var(--border-strong)',
        borderRadius: '12px',
        padding: '1.5rem',
        color: 'var(--text-primary)',
        height: '100%',
        overflowY: 'auto',
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <span className="badge badge-blue">
            Edge Evidence Provenance
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem', fontWeight: 'bold' }}>×</button>
        </div>

        <h3 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '1.1rem' }}>
          {selectedEdge.relationship === 'direct_associated_gene' ? 'Direct Associated Gene Relationship' : 'Record Inclusion Edge'}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
          <div style={{ background: 'var(--surface-soft)', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>SOURCE NODE</span>
            <strong style={{ color: 'var(--text-primary)' }}>{selectedEdge.source_node}</strong>
          </div>

          <div style={{ background: 'var(--surface-soft)', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>TARGET NODE</span>
            <strong style={{ color: 'var(--text-primary)' }}>{selectedEdge.target_node}</strong>
          </div>

          <div>
            <span style={{ color: 'var(--text-muted)' }}>Relationship: </span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{selectedEdge.relationship}</span>
          </div>

          <div>
            <span style={{ color: 'var(--text-muted)' }}>Source Database: </span>
            <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{selectedEdge.source}</span>
          </div>

          <div>
            <span style={{ color: 'var(--text-muted)' }}>MedGen Record UID: </span>
            <span style={{ color: 'var(--accent)', fontFamily: 'monospace', fontWeight: 600 }}>{selectedEdge.medgen_uid || 'N/A'}</span>
          </div>

          <div>
            <span style={{ color: 'var(--text-muted)' }}>Evidence Rule: </span>
            <span style={{ color: 'var(--accent-hover)', fontWeight: 600 }}>{selectedEdge.evidence_type}</span>
          </div>

          <div>
            <span style={{ color: 'var(--text-muted)' }}>Retrieved At: </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{selectedEdge.retrieved_at ? new Date(selectedEdge.retrieved_at).toLocaleString() : 'N/A'}</span>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {selectedEdge.medgen_uid && selectedEdge.medgen_uid !== 'N/A' && (
            <button
              onClick={() => navigate(`/medgen/${selectedEdge.medgen_uid}`)}
              className="btn-primary"
              style={{ width: '100%', fontSize: '0.85rem' }}
            >
              Open MedGen Record ({selectedEdge.medgen_uid})
            </button>
          )}

          <button
            onClick={() => isSaved ? removeGraphEdge(selectedEdge.edge_id) : saveGraphEdge(selectedEdge)}
            className={isSaved ? "btn-danger" : "btn-secondary"}
            style={{ width: '100%', fontSize: '0.85rem' }}
          >
            {isSaved ? 'Remove Edge from Workspace' : 'Save Edge to Workspace'}
          </button>
        </div>
      </div>
    );
  }

  // --- INSPECT NODE ---
  const node = selectedNode;
  const isSaved = isGraphNodeSaved(node.node_id);

  return (
    <div className="graph-inspector-panel" style={{
      background: 'var(--surface)',
      border: '1px solid var(--border-strong)',
      borderRadius: '12px',
      padding: '1.5rem',
      color: 'var(--text-primary)',
      height: '100%',
      overflowY: 'auto',
      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <span className={node.node_type === 'disease' ? 'badge badge-purple' : node.node_type === 'gene' ? 'badge badge-blue' : 'badge badge-warning'}>
          {node.node_type === 'disease' ? 'Disease Concept' : node.node_type === 'gene' ? 'Gene Entity' : 'MedGen Record'}
        </span>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem', fontWeight: 'bold' }}>×</button>
      </div>

      <h3 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '1.25rem', lineHeight: 1.3 }}>
        {node.title || node.symbol || node.node_id}
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
        {/* Node Specific Details */}
        {node.node_type === 'disease' && (
          <>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>MedGen UID: </span>
              <strong style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>{node.medgen_uid || 'N/A'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Concept ID (CUI): </span>
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{node.concept_id || 'N/A'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Semantic Type: </span>
              <span style={{ color: 'var(--text-primary)' }}>{node.semantic_type || 'Disease or Syndrome'}</span>
            </div>
            {node.definition && (
              <div style={{ background: 'var(--surface-soft)', padding: '0.75rem', borderRadius: '6px', marginTop: '0.25rem', border: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem', marginBottom: '0.25rem' }}>DEFINITION / SUMMARY</span>
                <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: 1.4, fontSize: '0.8rem' }}>{node.definition}</p>
              </div>
            )}
          </>
        )}

        {node.node_type === 'gene' && (
          <>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Gene Symbol: </span>
              <strong style={{ color: 'var(--text-primary)', fontSize: '1.05rem' }}>{node.symbol}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>NCBI Gene ID: </span>
              <strong style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>{node.ncbi_gene_id || 'N/A'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Chromosome: </span>
              <span style={{ color: 'var(--text-primary)' }}>{node.chromosome || 'N/A'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Cytogenetic Location: </span>
              <span style={{ color: 'var(--text-primary)' }}>{node.location || 'N/A'}</span>
            </div>
          </>
        )}

        {node.node_type === 'medgen_record' && (
          <>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>MedGen Record UID: </span>
              <strong style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>{node.medgen_uid}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Concept ID: </span>
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{node.concept_id || 'N/A'}</strong>
            </div>
            {node.definition && (
              <div style={{ background: 'var(--surface-soft)', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem', marginBottom: '0.25rem' }}>SUMMARY</span>
                <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.8rem', lineHeight: 1.4 }}>{node.definition}</p>
              </div>
            )}
          </>
        )}

        <div>
          <span style={{ color: 'var(--text-muted)' }}>Source Database: </span>
          <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{node.source || 'NCBI MedGen'}</span>
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <button
          onClick={() => onExploreNode(node)}
          className="btn-primary"
          style={{ width: '100%', fontSize: '0.85rem' }}
        >
          Explore Node Network
        </button>

        {node.node_type === 'disease' && (
          <button
            onClick={() => navigate(`/disease/${encodeURIComponent(node.title)}`)}
            className="btn-secondary"
            style={{ width: '100%', fontSize: '0.85rem' }}
          >
            View Full Disease Page
          </button>
        )}

        {node.node_type === 'gene' && (
          <button
            onClick={() => navigate(`/gene/${encodeURIComponent(node.symbol)}`)}
            className="btn-secondary"
            style={{ width: '100%', fontSize: '0.85rem' }}
          >
            View Full Gene Page
          </button>
        )}

        {node.node_type === 'medgen_record' && node.medgen_uid && (
          <button
            onClick={() => navigate(`/medgen/${node.medgen_uid}`)}
            className="btn-secondary"
            style={{ width: '100%', fontSize: '0.85rem' }}
          >
            Open MedGen Record Page ({node.medgen_uid})
          </button>
        )}

        <button
          onClick={() => isSaved ? removeGraphNode(node.node_id) : saveGraphNode(node)}
          className={isSaved ? "btn-danger" : "btn-secondary"}
          style={{ width: '100%', fontSize: '0.85rem', marginTop: '0.25rem' }}
        >
          {isSaved ? 'Remove Node from Workspace' : 'Save Node to Research Workspace'}
        </button>
      </div>
    </div>
  );
}
