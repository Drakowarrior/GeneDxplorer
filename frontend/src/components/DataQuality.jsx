import React from 'react';

export function DataQuality({ dataQuality, records }) {
  if (!dataQuality || !records) return null;

  return (
    <div className="card">
      <div className="card-title">Data Quality & Provenance</div>
      <div className="table-container">
        <table className="data-table">
          <tbody>
            <tr>
              <td><strong>Search Results Available:</strong></td>
              <td>{records.total_available} records in NCBI MedGen</td>
            </tr>
            <tr>
              <td><strong>Records Retrieved:</strong></td>
              <td>{records.retrieved} records</td>
            </tr>
            <tr>
              <td><strong>Records Analyzed:</strong></td>
              <td>{records.analyzed} records</td>
            </tr>
            <tr>
              <td><strong>Records with Direct Genes:</strong></td>
              <td>{dataQuality.records_with_genes} records</td>
            </tr>
            <tr>
              <td><strong>Records without Direct Genes:</strong></td>
              <td>{dataQuality.records_without_genes} records</td>
            </tr>
            <tr>
              <td><strong>Total Gene-Disease Relationships:</strong></td>
              <td>{dataQuality.total_relationships} associations</td>
            </tr>
            <tr>
              <td><strong>Unique Genes Identified:</strong></td>
              <td>{dataQuality.unique_genes} genes</td>
            </tr>
            <tr>
              <td><strong>Duplicate Gene Occurrences Removed:</strong></td>
              <td>{dataQuality.duplicate_genes_removed} (record-level deduplication)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
