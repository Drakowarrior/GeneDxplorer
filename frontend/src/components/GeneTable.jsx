import React from 'react';
import { Link } from 'react-router-dom';

export function GeneTable({ genes = [] }) {
  if (!genes || genes.length === 0) {
    return (
      <div className="card">
        <p style={{ color: 'var(--text-muted)' }}>No direct associated genes found for this analysis.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Top Reported Associated Genes</div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Gene Symbol</th>
              <th>NCBI Gene ID</th>
              <th>Record Count</th>
              <th>Record Percentage</th>
            </tr>
          </thead>
          <tbody>
            {genes.map((g) => (
              <tr key={g.symbol || g.rank}>
                <td>{g.rank}</td>
                <td>
                  <Link to={`/gene/${encodeURIComponent(g.symbol)}`} className="clickable-link">
                    {g.symbol}
                  </Link>
                </td>
                <td>{g.ncbi_gene_id ? g.ncbi_gene_id : 'N/A'}</td>
                <td>{g.record_count}</td>
                <td>{typeof g.record_percentage === 'number' ? `${g.record_percentage.toFixed(2)}%` : g.record_percentage}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
