import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList
} from 'recharts';

export function GeneChart({ genes = [], diseaseName = '' }) {
  if (!genes || genes.length === 0) return null;

  // Prepare top 10 genes in reverse order so highest rank is at top of horizontal chart
  const data = genes
    .slice(0, 10)
    .map(g => ({
      name: g.symbol,
      count: g.record_count,
      pct: g.record_percentage
    }))
    .reverse();

  return (
    <div className="card">
      <div className="card-title">Top Reported Associated Genes</div>
      <div style={{ width: '100%', height: 350, marginTop: '1rem' }}>
        <ResponsiveContainer>
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border-subtle)" />
            <XAxis type="number" allowDecimals={false} label={{ value: 'Number of MedGen Records', position: 'insideBottom', offset: -5 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 13, fontWeight: 600, fill: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }} width={80} />
            <Tooltip
              formatter={(value, name, props) => [`${value} records (${props.payload.pct}%)`, 'Record Count']}
            />
            <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]} barSize={24}>
              <LabelList dataKey="count" position="right" style={{ fontSize: 12, fontWeight: 600, fill: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="disclaimer-box">
        <div className="disclaimer-title">Scientific Interpretation Note</div>
        <p>
          Record count indicates how many analyzed NCBI MedGen records reported the gene as directly associated with the condition.
          This frequency does not establish biological causality, disease severity, clinical risk, or medical importance.
        </p>
      </div>
    </div>
  );
}
