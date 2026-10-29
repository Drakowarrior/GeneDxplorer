import React, { createContext, useContext, useState, useEffect } from 'react';

const STORAGE_KEY = 'genedxplorer_workspace';
const WORKSPACE_VERSION = 1;

const DEFAULT_WORKSPACE = {
  version: WORKSPACE_VERSION,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  diseases: [],
  genes: [],
  comparisons: [],
  records: [],
  evidence: [],
  notes: [],
  graph_nodes: [],
  graph_edges: [],
  similarity_matrices: [],
};

const WorkspaceContext = createContext(null);

function loadSafeWorkspace() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_WORKSPACE;

    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || parsed.version !== WORKSPACE_VERSION) {
      console.warn('[Workspace] Corrupted or incompatible workspace data found. Resetting safely.');
      return { ...DEFAULT_WORKSPACE, updated_at: new Date().toISOString() };
    }

    return {
      version: WORKSPACE_VERSION,
      created_at: parsed.created_at || new Date().toISOString(),
      updated_at: parsed.updated_at || new Date().toISOString(),
      diseases: Array.isArray(parsed.diseases) ? parsed.diseases : [],
      genes: Array.isArray(parsed.genes) ? parsed.genes : [],
      comparisons: Array.isArray(parsed.comparisons) ? parsed.comparisons : [],
      records: Array.isArray(parsed.records) ? parsed.records : [],
      evidence: Array.isArray(parsed.evidence) ? parsed.evidence : [],
      notes: Array.isArray(parsed.notes) ? parsed.notes : [],
      graph_nodes: Array.isArray(parsed.graph_nodes) ? parsed.graph_nodes : [],
      graph_edges: Array.isArray(parsed.graph_edges) ? parsed.graph_edges : [],
      similarity_matrices: Array.isArray(parsed.similarity_matrices) ? parsed.similarity_matrices : [],
    };
  } catch (err) {
    console.error('[Workspace] Error loading workspace from localStorage:', err);
    return DEFAULT_WORKSPACE;
  }
}



export function WorkspaceProvider({ children }) {
  const [workspace, setWorkspace] = useState(loadSafeWorkspace);
  const [toastMessage, setToastMessage] = useState(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
    } catch (err) {
      console.error('[Workspace] Error persisting workspace to localStorage:', err);
    }
  }, [workspace]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3000);
  };

  const updateWorkspace = (updater) => {
    setWorkspace((prev) => {
      const next = updater(prev);
      return {
        ...next,
        updated_at: new Date().toISOString(),
      };
    });
  };

  // --- DISEASE ACTIONS ---
  const isDiseaseSaved = (query) => {
    if (!query) return false;
    const clean = query.trim().toLowerCase();
    return workspace.diseases.some((d) => d.query.trim().toLowerCase() === clean);
  };

  const saveDisease = (diseaseObj) => {
    if (!diseaseObj || !diseaseObj.query) return;
    const clean = diseaseObj.query.trim().toLowerCase();

    if (isDiseaseSaved(clean)) {
      showToast('Already saved in Research Workspace');
      return;
    }

    const newItem = {
      query: diseaseObj.query,
      source: diseaseObj.source || 'NCBI MedGen',
      retrieved_at: diseaseObj.retrieved_at || new Date().toISOString(),
      saved_at: new Date().toISOString(),
      records_available: diseaseObj.records?.total_available || 0,
      records_analyzed: diseaseObj.records?.analyzed || 0,
      records_with_genes: diseaseObj.data_quality?.records_with_genes || 0,
      unique_genes: diseaseObj.data_quality?.unique_genes || 0,
      top_genes: (diseaseObj.genes || []).slice(0, 5).map((g) => ({
        symbol: g.symbol,
        count: g.record_count,
        pct: g.record_percentage,
      })),
    };

    updateWorkspace((prev) => ({
      ...prev,
      diseases: [newItem, ...prev.diseases],
    }));
    showToast('Added to Research Workspace');
  };

  const removeDisease = (query) => {
    const clean = query.trim().toLowerCase();
    updateWorkspace((prev) => ({
      ...prev,
      diseases: prev.diseases.filter((d) => d.query.trim().toLowerCase() !== clean),
    }));
    showToast('Removed from Workspace');
  };

  // --- GENE ACTIONS ---
  const isGeneSaved = (symbol) => {
    if (!symbol) return false;
    const clean = symbol.trim().toUpperCase();
    return workspace.genes.some((g) => g.symbol.trim().toUpperCase() === clean);
  };

  const saveGene = (geneObj) => {
    if (!geneObj || !geneObj.symbol) return;
    const clean = geneObj.symbol.trim().toUpperCase();

    if (isGeneSaved(clean)) {
      showToast('Already saved in Research Workspace');
      return;
    }

    const newItem = {
      symbol: clean,
      ncbi_gene_id: geneObj.ncbi_gene_id || 'N/A',
      candidate_records: geneObj.candidate_records || geneObj.records_examined || 0,
      verified_diseases_count: geneObj.verified_diseases_count || geneObj.matching_disease_count || 0,
      saved_at: new Date().toISOString(),
    };

    updateWorkspace((prev) => ({
      ...prev,
      genes: [newItem, ...prev.genes],
    }));
    showToast('Added to Research Workspace');
  };

  const removeGene = (symbol) => {
    const clean = symbol.trim().toUpperCase();
    updateWorkspace((prev) => ({
      ...prev,
      genes: prev.genes.filter((g) => g.symbol.trim().toUpperCase() !== clean),
    }));
    showToast('Removed from Workspace');
  };

  // --- MEDGEN RECORD ACTIONS ---
  const isRecordSaved = (medgenUid) => {
    if (!medgenUid) return false;
    const clean = String(medgenUid).trim();
    return workspace.records.some((r) => String(r.medgen_uid).trim() === clean);
  };

  const saveRecord = (recordObj) => {
    if (!recordObj || !recordObj.medgen_uid) return;
    const cleanUid = String(recordObj.medgen_uid).trim();

    if (isRecordSaved(cleanUid)) {
      showToast('Already saved in Research Workspace');
      return;
    }

    const newItem = {
      medgen_uid: cleanUid,
      disease_title: recordObj.disease_title || recordObj.title || 'Untitled Record',
      concept_id: recordObj.concept_id || null,
      semantic_type: recordObj.semantic_type || null,
      source: recordObj.source || 'NCBI MedGen',
      retrieved_at: recordObj.retrieved_at || new Date().toISOString(),
      saved_at: new Date().toISOString(),
      associated_genes_count: (recordObj.associated_genes || recordObj.genes || []).length,
    };

    updateWorkspace((prev) => ({
      ...prev,
      records: [newItem, ...prev.records],
    }));
    showToast('Added to Research Workspace');
  };

  const removeRecord = (medgenUid) => {
    const cleanUid = String(medgenUid).trim();
    updateWorkspace((prev) => ({
      ...prev,
      records: prev.records.filter((r) => String(r.medgen_uid).trim() !== cleanUid),
    }));
    showToast('Removed from Workspace');
  };

  // --- COMPARISON ACTIONS ---
  const getComparisonKey = (disA, disB) => {
    const a = disA.trim().toLowerCase();
    const b = disB.trim().toLowerCase();
    return [a, b].sort().join('__vs__');
  };

  const isComparisonSaved = (disA, disB) => {
    if (!disA || !disB) return false;
    const key = getComparisonKey(disA, disB);
    return workspace.comparisons.some(
      (c) => getComparisonKey(c.disease_a, c.disease_b) === key
    );
  };

  const saveComparison = (compObj) => {
    if (!compObj || !compObj.disease_a || !compObj.disease_b) return;
    const disA = typeof compObj.disease_a === 'object' ? compObj.disease_a.query : compObj.disease_a;
    const disB = typeof compObj.disease_b === 'object' ? compObj.disease_b.query : compObj.disease_b;

    if (isComparisonSaved(disA, disB)) {
      showToast('Already saved in Research Workspace');
      return;
    }

    const newItem = {
      disease_a: disA,
      disease_b: disB,
      records_analyzed_a: compObj.disease_a?.records_analyzed ?? compObj.records_analyzed_a ?? 0,
      records_analyzed_b: compObj.disease_b?.records_analyzed ?? compObj.records_analyzed_b ?? 0,
      unique_genes_a: compObj.disease_a?.unique_genes ?? compObj.unique_genes_a_count ?? (compObj.unique_to_a || []).length,
      unique_genes_b: compObj.disease_b?.unique_genes ?? compObj.unique_to_b_count ?? (compObj.unique_to_b || []).length,
      shared_genes_count: compObj.similarity?.shared_count ?? compObj.shared_genes_count ?? (compObj.shared_genes || []).length,
      jaccard_percentage: compObj.similarity?.jaccard_percentage ?? compObj.jaccard_percentage ?? 0,
      overlap_coefficient: compObj.similarity?.overlap_coefficient ?? 0,
      saved_at: new Date().toISOString(),
    };

    updateWorkspace((prev) => ({
      ...prev,
      comparisons: [newItem, ...prev.comparisons],
    }));
    showToast('Added to Research Workspace');
  };

  const removeComparison = (disA, disB) => {
    const key = getComparisonKey(disA, disB);
    updateWorkspace((prev) => ({
      ...prev,
      comparisons: prev.comparisons.filter(
        (c) => getComparisonKey(c.disease_a, c.disease_b) !== key
      ),
    }));
    showToast('Removed from Workspace');
  };

  // --- SAVED EVIDENCE ACTIONS ---
  const isEvidenceSaved = (source, recordId) => {
    if (!source || !recordId) return false;
    const cleanSource = String(source).trim().toLowerCase();
    const cleanId = String(recordId).trim().toLowerCase();
    return (workspace.evidence || []).some(
      (e) => String(e.source).trim().toLowerCase() === cleanSource && String(e.record_id).trim().toLowerCase() === cleanId
    );
  };

  const saveEvidence = (evidenceObj) => {
    if (!evidenceObj || !evidenceObj.source || !evidenceObj.record_id) return;

    if (isEvidenceSaved(evidenceObj.source, evidenceObj.record_id)) {
      showToast('Already saved in Research Workspace');
      return;
    }

    const newItem = {
      source: evidenceObj.source,
      source_type: evidenceObj.source_type || 'Official Database Evidence',
      record_id: evidenceObj.record_id,
      entity_type: evidenceObj.entity_type || 'gene',
      gene_symbol: evidenceObj.gene_symbol || 'N/A',
      ncbi_gene_id: evidenceObj.ncbi_gene_id || 'N/A',
      disease_name: evidenceObj.disease_name || 'N/A',
      interpretation: evidenceObj.interpretation || 'N/A',
      review_status: evidenceObj.review_status || 'N/A',
      retrieved_at: evidenceObj.retrieved_at || new Date().toISOString(),
      saved_at: new Date().toISOString(),
      source_url: evidenceObj.source_url || null,
    };

    updateWorkspace((prev) => ({
      ...prev,
      evidence: [newItem, ...(prev.evidence || [])],
    }));
    showToast('Added Evidence to Research Workspace');
  };

  const removeEvidence = (source, recordId) => {
    const cleanSource = String(source).trim().toLowerCase();
    const cleanId = String(recordId).trim().toLowerCase();
    updateWorkspace((prev) => ({
      ...prev,
      evidence: (prev.evidence || []).filter(
        (e) => !(String(e.source).trim().toLowerCase() === cleanSource && String(e.record_id).trim().toLowerCase() === cleanId)
      ),
    }));
    showToast('Removed Evidence from Workspace');
  };

  // --- RESEARCH NOTES ---
  const addNote = (noteText) => {
    if (!noteText || !noteText.trim()) return;

    const newNote = {
      id: `note_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      text: noteText.trim(),
      type: 'User Research Note',
      created_at: new Date().toISOString(),
    };

    updateWorkspace((prev) => ({
      ...prev,
      notes: [newNote, ...prev.notes],
    }));
    showToast('Research Note Added');
  };

  const deleteNote = (noteId) => {
    updateWorkspace((prev) => ({
      ...prev,
      notes: prev.notes.filter((n) => n.id !== noteId),
    }));
    showToast('Note Removed');
  };

  // --- CLEAR WORKSPACE ---
  const clearWorkspace = () => {
    setWorkspace({
      ...DEFAULT_WORKSPACE,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    showToast('Workspace Cleared');
  };

  // --- EXPORT JSON ---
  const exportWorkspaceJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(workspace, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `genedxplorer_research_workspace.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  // --- GRAPH NODE ACTIONS ---
  const isGraphNodeSaved = (nodeId) => {
    if (!nodeId) return false;
    return workspace.graph_nodes.some((n) => n.node_id === nodeId);
  };

  const saveGraphNode = (nodeObj) => {
    if (!nodeObj || !nodeObj.node_id) return;
    if (isGraphNodeSaved(nodeObj.node_id)) {
      showToast('Already saved in Research Workspace');
      return;
    }
    const newItem = {
      ...nodeObj,
      saved_at: new Date().toISOString(),
    };
    updateWorkspace((prev) => ({
      ...prev,
      graph_nodes: [newItem, ...prev.graph_nodes],
    }));
    showToast(`Saved Node '${nodeObj.title || nodeObj.symbol || nodeObj.node_id}' to Workspace`);
  };

  const removeGraphNode = (nodeId) => {
    updateWorkspace((prev) => ({
      ...prev,
      graph_nodes: prev.graph_nodes.filter((n) => n.node_id !== nodeId),
    }));
    showToast('Removed node from Workspace');
  };

  // --- GRAPH EDGE ACTIONS ---
  const isGraphEdgeSaved = (edgeId) => {
    if (!edgeId) return false;
    return workspace.graph_edges.some((e) => e.edge_id === edgeId);
  };

  const saveGraphEdge = (edgeObj) => {
    if (!edgeObj || !edgeObj.edge_id) return;
    if (isGraphEdgeSaved(edgeObj.edge_id)) {
      showToast('Already saved in Research Workspace');
      return;
    }
    const newItem = {
      ...edgeObj,
      saved_at: new Date().toISOString(),
    };
    updateWorkspace((prev) => ({
      ...prev,
      graph_edges: [newItem, ...prev.graph_edges],
    }));
    showToast(`Saved Edge '${edgeObj.edge_id}' to Workspace`);
  };

  const removeGraphEdge = (edgeId) => {
    updateWorkspace((prev) => ({
      ...prev,
      graph_edges: prev.graph_edges.filter((e) => e.edge_id !== edgeId),
    }));
    showToast('Removed edge from Workspace');
  };

  // --- SIMILARITY MATRIX ACTIONS ---
  const isSimilaritySaved = (title) => {
    if (!title) return false;
    return workspace.similarity_matrices.some((s) => s.title === title);
  };

  const saveSimilarity = (simObj) => {
    if (!simObj || !simObj.title) return;
    if (isSimilaritySaved(simObj.title)) {
      showToast('Already saved in Research Workspace');
      return;
    }
    const newItem = {
      ...simObj,
      saved_at: new Date().toISOString(),
    };
    updateWorkspace((prev) => ({
      ...prev,
      similarity_matrices: [newItem, ...prev.similarity_matrices],
    }));
    showToast(`Saved Similarity Matrix '${simObj.title}' to Workspace`);
  };

  const removeSimilarity = (title) => {
    updateWorkspace((prev) => ({
      ...prev,
      similarity_matrices: prev.similarity_matrices.filter((s) => s.title !== title),
    }));
    showToast('Removed similarity matrix from Workspace');
  };

  // --- EXPORT CSV UPDATE ---
  const exportWorkspaceCSV = () => {
    const rows = [
      ['Type', 'Name', 'Identifier', 'Source', 'Saved_At']
    ];

    workspace.diseases.forEach((d) => {
      rows.push(['Saved Disease', d.query, `Available: ${d.records_available}, Analyzed: ${d.records_analyzed}`, d.source, d.saved_at]);
    });

    workspace.genes.forEach((g) => {
      rows.push(['Saved Gene', g.symbol, `NCBI Gene ID: ${g.ncbi_gene_id}`, 'NCBI MedGen', g.saved_at]);
    });

    workspace.comparisons.forEach((c) => {
      rows.push(['Saved Comparison', `${c.disease_a} vs ${c.disease_b}`, `Jaccard: ${c.jaccard_percentage}%, Overlap Coeff: ${c.overlap_coefficient}%`, 'NCBI MedGen', c.saved_at]);
    });

    workspace.records.forEach((r) => {
      rows.push(['Saved MedGen Record', r.disease_title, `MedGen UID: ${r.medgen_uid}`, r.source, r.saved_at]);
    });

    (workspace.evidence || []).forEach((e) => {
      rows.push(['Saved Evidence Record', `${e.gene_symbol} - ${e.disease_name}`, `Record ID: ${e.record_id}, Interp: ${e.interpretation}`, e.source, e.saved_at]);
    });

    (workspace.graph_nodes || []).forEach((gn) => {
      rows.push(['Saved Graph Node', gn.title || gn.symbol || gn.node_id, `Type: ${gn.node_type}`, gn.source || 'NCBI MedGen', gn.saved_at]);
    });

    (workspace.graph_edges || []).forEach((ge) => {
      rows.push(['Saved Graph Edge', ge.edge_id, `Rel: ${ge.relationship}, Ev: ${ge.evidence_type}`, ge.source || 'NCBI MedGen', ge.saved_at]);
    });

    (workspace.similarity_matrices || []).forEach((sm) => {
      rows.push(['Saved Similarity Matrix', sm.title, `Diseases: ${sm.disease_count}`, sm.source || 'NCBI MedGen', sm.saved_at]);
    });

    workspace.notes.forEach((n) => {
      rows.push(['User Research Note', n.text.replace(/\n/g, ' '), n.id, 'User Input', n.created_at]);
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map((e) => e.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', csvContent);
    downloadAnchor.setAttribute('download', `genedxplorer_research_workspace.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspace,
        toastMessage,
        isDiseaseSaved,
        saveDisease,
        removeDisease,
        isGeneSaved,
        saveGene,
        removeGene,
        isRecordSaved,
        saveRecord,
        removeRecord,
        isComparisonSaved,
        saveComparison,
        removeComparison,
        isEvidenceSaved,
        saveEvidence,
        removeEvidence,
        isGraphNodeSaved,
        saveGraphNode,
        removeGraphNode,
        isGraphEdgeSaved,
        saveGraphEdge,
        removeGraphEdge,
        isSimilaritySaved,
        saveSimilarity,
        removeSimilarity,
        addNote,
        deleteNote,
        clearWorkspace,
        exportWorkspaceJSON,
        exportWorkspaceCSV,
      }}
    >
      {children}
      {toastMessage && <div className="workspace-toast">{toastMessage}</div>}
    </WorkspaceContext.Provider>
  );
}



export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return ctx;
}
