import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import KnowledgeGraph from '../components/KnowledgeGraph';
import GraphLegend from '../components/GraphLegend';
import GraphInspector from '../components/GraphInspector';

export default function KnowledgeGraphPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialDisease = searchParams.get('disease') || "Alzheimer's disease";
  const initialGene = searchParams.get('gene') || '';

  const [queryInput, setQueryInput] = useState(initialGene ? initialGene : initialDisease);
  const [queryType, setQueryType] = useState(initialGene ? 'gene' : 'disease');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [graphData, setGraphData] = useState({ nodes: [], edges: [], summary: {} });
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const loadGraph = async (query, type) => {
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setSelectedEdge(null);

    try {
      let data;
      if (type === 'gene') {
        data = await api.getGeneKnowledgeGraph(query);
      } else {
        data = await api.getDiseaseKnowledgeGraph(query);
      }
      setGraphData(data);
    } catch (err) {
      console.error('Error fetching knowledge graph:', err);
      setError(err.message || 'Failed to load knowledge graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialGene) {
      setQueryInput(initialGene);
      setQueryType('gene');
      loadGraph(initialGene, 'gene');
    } else if (initialDisease) {
      setQueryInput(initialDisease);
      setQueryType('disease');
      loadGraph(initialDisease, 'disease');
    }
  }, [searchParams]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!queryInput.trim()) return;
    setSearchParams(queryType === 'gene' ? { gene: queryInput.trim() } : { disease: queryInput.trim() });
    loadGraph(queryInput.trim(), queryType);
  };

  const handleExploreNode = async (node) => {
    if (!node) return;
    setLoading(true);
    try {
      const expansion = await api.exploreGraphNode(node.node_type, node.node_id);

      setGraphData((prev) => {
        const existingNodeIds = new Set(prev.nodes.map((n) => n.node_id));
        const existingEdgeIds = new Set(prev.edges.map((e) => e.edge_id));

        const newNodes = [...prev.nodes];
        expansion.nodes.forEach((n) => {
          if (!existingNodeIds.has(n.node_id)) {
            newNodes.push(n);
            existingNodeIds.add(n.node_id);
          }
        });

        const newEdges = [...prev.edges];
        expansion.edges.forEach((e) => {
          if (!existingEdgeIds.has(e.edge_id)) {
            newEdges.push(e);
            existingEdgeIds.add(e.edge_id);
          }
        });

        return {
          ...prev,
          nodes: newNodes,
          edges: newEdges,
        };
      });
    } catch (err) {
      console.error('Error expanding node:', err);
      setError(`Failed to expand node '${node.title || node.symbol}': ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!graphData.query) return;
    try {
      const res = await api.generateReport(graphData.query, 'disease');
      if (res && res.report_id) {
        window.location.href = `/report/${res.report_id}`;
      }
    } catch (err) {
      alert(`Report generation failed: ${err.message}`);
    }
  };

  const exportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(graphData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `knowledge_graph_${graphData.query || 'export'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const exportCSV = () => {
    const nodeRows = [['Node_ID', 'Node_Type', 'Label', 'NCBI_Gene_ID', 'MedGen_UID']];
    (graphData.nodes || []).forEach((n) => {
      nodeRows.push([n.node_id, n.node_type, n.title || n.symbol || '', n.ncbi_gene_id || '', n.medgen_uid || '']);
    });

    const edgeRows = [['Edge_ID', 'Source', 'Target', 'Relationship', 'Weight']];
    (graphData.edges || []).forEach((e) => {
      edgeRows.push([e.edge_id, e.source_node, e.target_node, e.relationship, e.weight]);
    });

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'NODES\n' +
      nodeRows.map((e) => e.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n') +
      '\n\nEDGES\n' +
      edgeRows.map((e) => e.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');

    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', csvContent);
    downloadAnchor.setAttribute('download', `knowledge_graph_${graphData.query || 'export'}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const nodeCounts = {
    all: graphData.nodes?.length || 0,
    disease: graphData.nodes?.filter((n) => n.node_type === 'disease').length || 0,
    gene: graphData.nodes?.filter((n) => n.node_type === 'gene').length || 0,
    medgen_record: graphData.nodes?.filter((n) => n.node_type === 'medgen_record').length || 0,
  };

  return (
    <div className="container" style={{ maxWidth: '1280px' }}>
      {/* Header Banner */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title">Knowledge Graph</h1>
          <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.95rem' }}>
            Explore relationships between diseases, genes and supporting records.
          </p>
        </div>

        {/* Search Query Toolbar Form */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            value={queryType}
            onChange={(e) => setQueryType(e.target.value)}
            className="select-field"
            style={{ width: 'auto', padding: '0.55rem 0.85rem' }}
          >
            <option value="disease">Disease Search</option>
            <option value="gene">Gene Search</option>
          </select>

          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder={queryType === 'gene' ? 'e.g. APOE, CFTR' : "e.g. Alzheimer's disease"}
            className="search-input"
            style={{ width: '220px', padding: '0.55rem 0.85rem' }}
          />

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ padding: '0.55rem 1.15rem' }}
          >
            {loading ? 'Building Graph...' : 'Explore Graph'}
          </button>
        </form>
      </div>

      {error && (
        <div style={{ background: 'var(--danger-light)', border: '1px solid var(--danger-border)', color: 'var(--danger)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {/* Legend & Controls */}
      <GraphLegend
        filterType={filterType}
        setFilterType={setFilterType}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        nodeCounts={nodeCounts}
        onResetView={() => { setFilterType('all'); setSearchQuery(''); setSelectedNode(null); setSelectedEdge(null); }}
      />

      {/* Main Knowledge Graph Display & Inspector Split */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem', alignItems: 'start' }}>
        <div>
          <KnowledgeGraph
            nodes={graphData.nodes || []}
            edges={graphData.edges || []}
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onSelectNode={(node) => { setSelectedNode(node); setSelectedEdge(null); }}
            onSelectEdge={(edge) => { setSelectedEdge(edge); setSelectedNode(null); }}
            filterType={filterType}
            searchQuery={searchQuery}
          />

          {/* Export Toolbar & Graph Summary */}
          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', background: '#ffffff', padding: '0.85rem 1.25rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Query: <strong style={{ color: 'var(--text-primary)' }}>{graphData.query}</strong> &nbsp;•&nbsp;
              Nodes: <strong style={{ color: 'var(--text-primary)' }}>{graphData.nodes?.length || 0}</strong> &nbsp;•&nbsp;
              Edges: <strong style={{ color: 'var(--text-primary)' }}>{graphData.edges?.length || 0}</strong>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={handleGenerateReport} className="btn-primary" style={{ padding: '0.45rem 0.95rem', fontSize: '0.85rem' }}>
                Generate report
              </button>
              <button onClick={exportJSON} className="btn-secondary" style={{ padding: '0.45rem 0.95rem', fontSize: '0.85rem' }}>
                Export Graph JSON
              </button>
              <button onClick={exportCSV} className="btn-secondary" style={{ padding: '0.45rem 0.95rem', fontSize: '0.85rem' }}>
                Export CSV
              </button>
            </div>
          </div>
        </div>

        {/* Right Inspector Panel */}
        <div style={{ height: '600px' }}>
          <GraphInspector
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onClose={() => { setSelectedNode(null); setSelectedEdge(null); }}
            onExploreNode={handleExploreNode}
          />
        </div>
      </div>

      {/* Scientific Disclaimer Card */}
      <div className="disclaimer-callout" style={{ marginTop: '2rem' }}>
        <h3>How to Interpret the Knowledge Graph</h3>
        <p>
          A line between a disease and a gene means that the gene was directly reported in the structured <code>&lt;AssociatedGenes&gt;</code> section of an analyzed NCBI MedGen record. A connection between two diseases through a shared gene means that the same reported gene appeared in the analyzed MedGen record sets for both diseases. This is a data-exploration relationship, not a clinical conclusion or proof of etiology.
        </p>
      </div>
    </div>
  );
}
