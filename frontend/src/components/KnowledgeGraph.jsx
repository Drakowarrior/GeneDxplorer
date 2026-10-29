import React, { useState, useEffect, useRef } from 'react';

export default function KnowledgeGraph({
  nodes = [],
  edges = [],
  selectedNode,
  selectedEdge,
  onSelectNode,
  onSelectEdge,
  filterType = 'all',
  searchQuery = ''
}) {
  const containerRef = useRef(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [nodePositions, setNodePositions] = useState({});
  const [draggedNode, setDraggedNode] = useState(null);

  const width = 800;
  const height = 600;
  const centerX = width / 2;
  const centerY = height / 2;

  // Filter nodes according to type and search query
  const filteredNodes = nodes.filter((n) => {
    if (filterType !== 'all' && n.node_type !== filterType) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const titleMatch = (n.title || n.symbol || '').toLowerCase().includes(q);
      const uidMatch = (n.medgen_uid || n.concept_id || '').toLowerCase().includes(q);
      return titleMatch || uidMatch;
    }
    return true;
  });

  const filteredNodeIds = new Set(filteredNodes.map((n) => n.node_id));

  // Filter edges to only include visible nodes
  const filteredEdges = edges.filter(
    (e) => filteredNodeIds.has(e.source_node) && filteredNodeIds.has(e.target_node)
  );

  // Compute initial node positions in rings if not dragged
  useEffect(() => {
    if (!nodes.length) return;

    const newPositions = { ...nodePositions };
    const diseaseNodes = nodes.filter((n) => n.node_type === 'disease');
    const geneNodes = nodes.filter((n) => n.node_type === 'gene');
    const recordNodes = nodes.filter((n) => n.node_type === 'medgen_record');

    // Disease nodes near center
    diseaseNodes.forEach((n, idx) => {
      if (!newPositions[n.node_id]) {
        const radius = diseaseNodes.length === 1 ? 0 : 70;
        const angle = (idx / (diseaseNodes.length || 1)) * 2 * Math.PI;
        newPositions[n.node_id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        };
      }
    });

    // Gene nodes in inner ring
    const geneRadius = 180;
    geneNodes.forEach((n, idx) => {
      if (!newPositions[n.node_id]) {
        const angle = (idx / (geneNodes.length || 1)) * 2 * Math.PI - Math.PI / 4;
        newPositions[n.node_id] = {
          x: centerX + geneRadius * Math.cos(angle),
          y: centerY + geneRadius * Math.sin(angle)
        };
      }
    });

    // Record nodes in outer ring
    const recordRadius = 270;
    recordNodes.forEach((n, idx) => {
      if (!newPositions[n.node_id]) {
        const angle = (idx / (recordNodes.length || 1)) * 2 * Math.PI + Math.PI / 6;
        newPositions[n.node_id] = {
          x: centerX + recordRadius * Math.cos(angle),
          y: centerY + recordRadius * Math.sin(angle)
        };
      }
    });

    setNodePositions(newPositions);
  }, [nodes]);

  // Pan handlers
  const handleMouseDown = (e) => {
    if (draggedNode) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
  };

  const handleMouseMove = (e) => {
    if (draggedNode) {
      // Dragging a specific node
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - transform.x) / transform.scale;
      const mouseY = (e.clientY - rect.top - transform.y) / transform.scale;

      setNodePositions((prev) => ({
        ...prev,
        [draggedNode]: { x: mouseX, y: mouseY }
      }));
      return;
    }

    if (isDragging) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      }));
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDraggedNode(null);
  };

  // Zoom handlers
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setTransform((prev) => ({
      ...prev,
      scale: Math.max(0.4, Math.min(3.0, prev.scale * zoomFactor))
    }));
  };

  const zoomIn = () => setTransform((prev) => ({ ...prev, scale: Math.min(3.0, prev.scale * 1.25) }));
  const zoomOut = () => setTransform((prev) => ({ ...prev, scale: Math.max(0.4, prev.scale * 0.8) }));
  const resetTransform = () => setTransform({ x: 0, y: 0, scale: 1 });

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      style={{
        width: '100%',
        height: '600px',
        background: 'var(--page-background)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        position: 'relative',
        overflow: 'hidden',
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none'
      }}
    >
      {/* Zoom Controls */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        background: 'var(--surface)',
        padding: '6px',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <button onClick={zoomIn} style={controlButtonStyle} title="Zoom In">+</button>
        <button onClick={zoomOut} style={controlButtonStyle} title="Zoom Out">−</button>
        <button onClick={resetTransform} style={{ ...controlButtonStyle, fontSize: '0.7rem' }} title="Reset View">Fit</button>
      </div>

      {/* SVG Canvas */}
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: '100%' }}
      >
        <defs>
          <marker
            id="arrow-direct"
            viewBox="0 0 10 10"
            refX="22"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--primary)" />
          </marker>

          <marker
            id="arrow-record"
            viewBox="0 0 10 10"
            refX="22"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--text-muted)" />
          </marker>
        </defs>

        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}>
          {/* Render Edges */}
          {filteredEdges.map((edge) => {
            const sourcePos = nodePositions[edge.source_node] || { x: centerX, y: centerY };
            const targetPos = nodePositions[edge.target_node] || { x: centerX, y: centerY };
            const isSelected = selectedEdge?.edge_id === edge.edge_id;
            const isDirect = edge.relationship === 'direct_associated_gene';

            return (
              <g key={edge.edge_id} onClick={(e) => { e.stopPropagation(); onSelectEdge(edge); }}>
                <line
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke={isSelected ? 'var(--text-primary)' : (isDirect ? 'var(--primary)' : 'var(--border-strong)')}
                  strokeWidth={isSelected ? 3 : (isDirect ? 1.75 : 1.25)}
                  strokeDasharray={isDirect ? 'none' : '4 4'}
                  markerEnd={isDirect ? 'url(#arrow-direct)' : 'url(#arrow-record)'}
                  style={{ cursor: 'pointer', transition: 'stroke 0.2s ease' }}
                />
              </g>
            );
          })}

          {/* Render Nodes */}
          {filteredNodes.map((node) => {
            const pos = nodePositions[node.node_id] || { x: centerX, y: centerY };
            const isSelected = selectedNode?.node_id === node.node_id;

            let fillColor = '#40576f'; // Disease deep slate
            let strokeColor = '#ccd5e2';
            let radius = 18;

            if (node.node_type === 'gene') {
              fillColor = '#526b85'; // Gene primary slate
              strokeColor = '#dfe5ee';
              radius = 14;
            } else if (node.node_type === 'medgen_record') {
              fillColor = '#7c899c'; // Record muted slate
              strokeColor = '#f0f4f9';
              radius = 12;
            }

            const label = node.symbol || node.title || node.node_id;
            const truncatedLabel = label.length > 18 ? label.substring(0, 16) + '...' : label;

            return (
              <g
                key={node.node_id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={(e) => { e.stopPropagation(); onSelectNode(node); }}
                onMouseDown={(e) => { e.stopPropagation(); setDraggedNode(node.node_id); }}
                style={{ cursor: 'pointer' }}
              >
                {/* Selected Node Glow Halo */}
                {isSelected && (
                  <circle
                    r={radius + 8}
                    fill="none"
                    stroke="var(--focus-ring)"
                    strokeWidth="3"
                    opacity="0.8"
                  />
                )}

                {/* Main Node Circle */}
                <circle
                  r={radius}
                  fill={fillColor}
                  stroke={isSelected ? 'var(--text-primary)' : strokeColor}
                  strokeWidth={isSelected ? 3 : 2}
                  style={{ filter: 'drop-shadow(0px 2px 4px rgba(0,0,0,0.15))' }}
                />

                {/* Node Label */}
                <text
                  y={radius + 14}
                  textAnchor="middle"
                  fill="var(--text-primary)"
                  fontSize={node.node_type === 'disease' ? '12px' : '10px'}
                  fontWeight={node.node_type === 'disease' ? 'bold' : '600'}
                  fontFamily="var(--font-heading)"
                  style={{ pointerEvents: 'none' }}
                >
                  {truncatedLabel}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

const controlButtonStyle = {
  background: 'var(--surface)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
  width: '26px',
  height: '26px',
  fontSize: '0.9rem',
  fontWeight: 'bold',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
};
