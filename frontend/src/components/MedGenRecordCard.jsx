import React from 'react';
import { Link } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';

export default function MedGenRecordCard({ record, showFull = false }) {
  const { isRecordSaved, saveRecord } = useWorkspace();
  if (!record) return null;

  const uid = record.medgen_uid || record.uid;
  const title = record.disease_title || record.title || 'Untitled MedGen Record';
  const conceptId = record.concept_id;
  const semanticType = record.semantic_type;
  const definition = record.definition;
  const genes = record.genes || record.associated_genes || [];
  const source = record.source || 'NCBI MedGen';
  const retrievedAt = record.retrieved_at ? new Date(record.retrieved_at).toLocaleString() : null;
  const isSaved = isRecordSaved(uid);

  return (
    <div className="medgen-record-card">
      <div className="record-card-header">
        <div className="record-title-area">
          <span className="record-badge">MedGen ID: {uid}</span>
          <h4 className="record-title">{title}</h4>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            onClick={() =>
              saveRecord({
                medgen_uid: uid,
                disease_title: title,
                concept_id: conceptId,
                semantic_type: semanticType,
                source,
                associated_genes: genes,
              })
            }
            className={isSaved ? 'btn-secondary' : 'btn-primary'}
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
          >
            {isSaved ? 'Saved' : 'Save'}
          </button>
          <Link to={`/medgen/${uid}`} className="record-link-btn" title="View Full Record Details">
            View Detail →
          </Link>
        </div>
      </div>


      {(conceptId || semanticType) && (
        <div className="record-meta-pills">
          {conceptId && (
            <span className="meta-pill concept-pill">
              <strong>Concept ID:</strong> {conceptId}
            </span>
          )}
          {semanticType && (
            <span className="meta-pill semantic-pill">
              <strong>Semantic Type:</strong> {semanticType}
            </span>
          )}
        </div>
      )}

      {definition && (
        <p className="record-definition">
          {definition}
        </p>
      )}

      {genes.length > 0 ? (
        <div className="record-genes-section">
          <h5 className="genes-section-title">Direct Associated Genes ({genes.length})</h5>
          <div className="gene-tags-grid">
            {genes.map((g, idx) => (
              <div key={idx} className="gene-evidence-tag">
                <Link to={`/gene/${g.symbol}`} className="gene-symbol-link">
                  {g.symbol}
                </Link>
                {(g.ncbi_gene_id || g.gene_id) && (
                  <span className="gene-id-sub">NCBI: {g.ncbi_gene_id || g.gene_id}</span>
                )}
                {(g.chromosome || g.location) && (
                  <span className="gene-loc-sub">
                    {g.chromosome ? `Chr ${g.chromosome}` : ''} {g.location ? `(${g.location})` : ''}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="no-genes-notice">
          <em>No direct associated genes annotated for this record.</em>
        </div>
      )}

      <div className="record-footer">
        <span className="source-tag">Source: <strong>{source}</strong></span>
        {retrievedAt && <span className="retrieved-tag">Retrieved: {retrievedAt}</span>}
      </div>
    </div>
  );
}
