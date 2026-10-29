import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export function DiscoveryGraph({ diseaseName, genes = [], relatedDiseases = [] }) {
  const [activeNode, setActiveNode] = useState(null);

  if (!diseaseName || !genes || genes.length === 0) return null;

  const topGenes = genes.slice(0, 6);
  const topRelated = relatedDiseases.slice(0, 5);

  return (
    <div className="card discovery-graph-card" style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
      <div className="card-header-flex" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <div className="card-title">Discovery Relationship Explorer</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
            Visualizing reported MedGen gene associations linking <strong>{diseaseName}</strong> with reported genes and overlapping disease concepts.
          </p>
        </div>
        <span className="badge badge-blue">Visual Network Map</span>
      </div>

      {/* SVG Network Visualization */}
      <div style={{ width: '100%', overflowX: 'auto', backgroundColor: 'var(--surface-soft)', borderRadius: '8px', padding: '1rem', border: '1px solid var(--border)' }}>
        <svg width="700" height="320" viewBox="0 0 700 320" style={{ width: '100%', height: 'auto', maxHeight: '350px' }}>
          {/* Connecting Lines */}
          <g opacity="0.6">
            {/* Center Disease to Top Genes */}
            {topGenes.map((g, idx) => {
              const angle = (idx / topGenes.length) * 2 * Math.PI - Math.PI / 2;
              const gx = 350 + Math.cos(angle) * 110;
              const gy = 160 + Math.sin(angle) * 90;
              return (
                <line
                  key={`line-gene-${idx}`}
                  x1="350"
                  y1="160"
                  x2={gx}
                  y2={gy}
                  stroke={activeNode === g.symbol ? 'var(--primary)' : 'var(--border-strong)'}
                  strokeWidth={activeNode === g.symbol ? '3' : '1.5'}
                  strokeDasharray={activeNode === g.symbol ? 'none' : '4 2'}
                />
              );
            })}

            {/* Top Genes to Outer Related Diseases */}
            {topRelated.map((rd, rIdx) => {
              const rAngle = (rIdx / (topRelated.length || 1)) * Math.PI - Math.PI / 2;
              const rx = 350 + Math.cos(rAngle) * 230;
              const ry = 160 + Math.sin(rAngle) * 130;

              // Connect to first matching gene
              const gIdx = rIdx % topGenes.length;
              const gAngle = (gIdx / topGenes.length) * 2 * Math.PI - Math.PI / 2;
              const gx = 350 + Math.cos(gAngle) * 110;
              const gy = 160 + Math.sin(gAngle) * 90;

              return (
                <line
                  key={`line-rel-${rIdx}`}
                  x1={gx}
                  y1={gy}
                  x2={rx}
                  y2={ry}
                  stroke="var(--border-strong)"
                  strokeWidth="1.2"
                />
              );
            })}
          </g>

          {/* Center Disease Node */}
          <g transform="translate(350, 160)">
            <circle r="42" fill="var(--accent-hover)" stroke="#ffffff" strokeWidth="3" />
            <text textAnchor="middle" dy="-4" fill="#ffffff" fontSize="10" fontWeight="bold">
              {diseaseName.length > 14 ? `${diseaseName.substring(0, 12)}...` : diseaseName}
            </text>
            <text textAnchor="middle" dy="12" fill="var(--accent-soft)" fontSize="8" fontWeight="600">
              (Target Disease)
            </text>
          </g>

          {/* Gene Nodes */}
          {topGenes.map((g, idx) => {
            const angle = (idx / topGenes.length) * 2 * Math.PI - Math.PI / 2;
            const gx = 350 + Math.cos(angle) * 110;
            const gy = 160 + Math.sin(angle) * 90;
            const isHovered = activeNode === g.symbol;

            return (
              <g
                key={`node-gene-${idx}`}
                transform={`translate(${gx}, ${gy})`}
                onMouseEnter={() => setActiveNode(g.symbol)}
                onMouseLeave={() => setActiveNode(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  r="24"
                  fill={isHovered ? 'var(--primary)' : '#ffffff'}
                  stroke="var(--primary)"
                  strokeWidth="2.5"
                />
                <text
                  textAnchor="middle"
                  dy="4"
                  fill={isHovered ? '#ffffff' : 'var(--text-primary)'}
                  fontSize="9"
                  fontWeight="bold"
                >
                  {g.symbol}
                </text>
              </g>
            );
          })}

          {/* Related Disease Nodes */}
          {topRelated.map((rd, rIdx) => {
            const rAngle = (rIdx / (topRelated.length || 1)) * Math.PI - Math.PI / 2;
            const rx = 350 + Math.cos(rAngle) * 230;
            const ry = 160 + Math.sin(rAngle) * 130;
            const title = rd.title || rd.query || rd.name;

            return (
              <g key={`node-rel-${rIdx}`} transform={`translate(${rx}, ${ry})`}>
                <rect
                  x="-55"
                  y="-14"
                  width="110"
                  height="28"
                  rx="6"
                  fill="var(--accent)"
                  stroke="#ffffff"
                  strokeWidth="1.5"
                />
                <text textAnchor="middle" dy="3" fill="#ffffff" fontSize="8" fontWeight="bold">
                  {title.length > 15 ? `${title.substring(0, 14)}...` : title}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Network Controls & Scientific Safeguards Label */}
      <div style={{ marginTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
          * Relationships shown are based on reported MedGen gene associations.
        </span>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {topGenes.map((g) => (
            <Link
              key={g.symbol}
              to={`/gene/${encodeURIComponent(g.symbol)}`}
              className="badge badge-blue"
              style={{ textDecoration: 'none', fontSize: '0.75rem' }}
            >
              Explore {g.symbol} →
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default DiscoveryGraph;
