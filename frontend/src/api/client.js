const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function fetchJSON(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  let data;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    const errorMessage =
      data?.detail?.error ||
      data?.error ||
      `Request failed with status ${response.status}`;
    const error = new Error(errorMessage);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const api = {
  getHealth: () => fetchJSON('/api/health'),

  getReady: () => fetchJSON('/api/ready'),

  getDiseaseAnalysis: (diseaseName) =>
    fetchJSON(`/api/disease/${encodeURIComponent(diseaseName)}`),

  getDiseaseEvidence: (diseaseName) =>
    fetchJSON(`/api/disease/${encodeURIComponent(diseaseName)}/evidence`),

  getDiseaseInfo: (diseaseName) =>
    fetchJSON(`/api/disease/${encodeURIComponent(diseaseName)}/info`),

  getDiseaseGenes: (diseaseName) =>
    fetchJSON(`/api/disease/${encodeURIComponent(diseaseName)}/genes`),

  getDiseaseRecords: (diseaseName) =>
    fetchJSON(`/api/disease/${encodeURIComponent(diseaseName)}/records`),

  getGeneDiseases: (geneSymbol) =>
    fetchJSON(`/api/gene/${encodeURIComponent(geneSymbol)}`),

  getGeneSummary: (geneSymbol) =>
    fetchJSON(`/api/gene/${encodeURIComponent(geneSymbol)}/summary`),

  getGeneEvidence: (geneSymbol) =>
    fetchJSON(`/api/gene/${encodeURIComponent(geneSymbol)}/evidence`),

  getMedGenRecord: (medgenUid) =>
    fetchJSON(`/api/medgen/${encodeURIComponent(medgenUid)}`),

  compareDiseases: (diseaseA, diseaseB) =>
    fetchJSON('/api/disease/compare', {
      method: 'POST',
      body: JSON.stringify({
        disease_a: diseaseA,
        disease_b: diseaseB,
      }),
    }),

  discoverDiseases: (query, limit = 25) =>
    fetchJSON(`/api/discover/diseases?q=${encodeURIComponent(query)}&limit=${limit}`),

  discoverGenes: (query, limit = 25) =>
    fetchJSON(`/api/discover/genes?q=${encodeURIComponent(query)}&limit=${limit}`),

  getEvidenceHealth: () => fetchJSON('/api/evidence/health'),

  getUnifiedGeneEvidence: (geneSymbol) =>
    fetchJSON(`/api/evidence/gene/${encodeURIComponent(geneSymbol)}`),

  getDiseaseKnowledgeGraph: (diseaseName, maxGenes = 15, includeRecords = true) =>
    fetchJSON(`/api/graph/disease/${encodeURIComponent(diseaseName)}?max_genes=${maxGenes}&include_records=${includeRecords}`),

  getGeneKnowledgeGraph: (geneSymbol, maxDiseases = 15, includeRecords = true) =>
    fetchJSON(`/api/graph/gene/${encodeURIComponent(geneSymbol)}?max_diseases=${maxDiseases}&include_records=${includeRecords}`),

  exploreGraphNode: (nodeType, nodeId, limit = 10) =>
    fetchJSON(`/api/graph/explore/${encodeURIComponent(nodeType)}/${encodeURIComponent(nodeId)}?limit=${limit}`),

  getMultiDiseaseSimilarity: (diseases, maxRecords = 100) =>
    fetchJSON('/api/similarity/matrix', {
      method: 'POST',
      body: JSON.stringify({
        diseases: diseases,
        max_records: maxRecords,
      }),
    }),

  generateDiseaseReport: (diseaseName, maxRecords = null) =>
    fetchJSON('/api/reports/disease', {
      method: 'POST',
      body: JSON.stringify({ disease_name: diseaseName, max_records: maxRecords }),
    }),

  generateGeneReport: (geneSymbol) =>
    fetchJSON('/api/reports/gene', {
      method: 'POST',
      body: JSON.stringify({ gene_symbol: geneSymbol }),
    }),

  generateComparisonReport: (diseaseA, diseaseB) =>
    fetchJSON('/api/reports/comparison', {
      method: 'POST',
      body: JSON.stringify({ disease_a: diseaseA, disease_b: diseaseB }),
    }),

  generateSimilarityReport: (diseases) =>
    fetchJSON('/api/reports/similarity', {
      method: 'POST',
      body: JSON.stringify({ diseases: diseases }),
    }),

  generateGraphReport: (query, nodeType = 'disease') =>
    fetchJSON('/api/reports/graph', {
      method: 'POST',
      body: JSON.stringify({ query: query, node_type: nodeType }),
    }),

  generateWorkspaceReport: (workspaceData) =>
    fetchJSON('/api/reports/workspace', {
      method: 'POST',
      body: JSON.stringify({ workspace: workspaceData }),
    }),

  getReport: (reportId) =>
    fetchJSON(`/api/reports/${encodeURIComponent(reportId)}`),

  createSnapshot: (reportData, workspace = null) =>
    fetchJSON('/api/reproducibility/snapshot', {
      method: 'POST',
      body: JSON.stringify({ report_data: reportData, workspace: workspace }),
    }),

  createSnapshotFromReport: (reportId) =>
    fetchJSON(`/api/reproducibility/report/${encodeURIComponent(reportId)}`, {
      method: 'POST',
    }),

  getSnapshot: (snapshotId) =>
    fetchJSON(`/api/reproducibility/snapshot/${encodeURIComponent(snapshotId)}`),

  getSnapshotManifest: (snapshotId) =>
    fetchJSON(`/api/reproducibility/snapshot/${encodeURIComponent(snapshotId)}/manifest`),

  getSnapshotCitations: (snapshotId) =>
    fetchJSON(`/api/reproducibility/snapshot/${encodeURIComponent(snapshotId)}/citations`),
};




