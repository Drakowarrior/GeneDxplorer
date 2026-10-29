import React from 'react';

export function ScientificInterpretationNotice({ customNotice }) {
  return (
    <div className="disclaimer-callout" style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
      <h3>Scientific Evidence Interpretation</h3>
      <p>
        {customNotice ||
          'These records represent database annotations and submitted variant interpretations retrieved from authoritative scientific evidence providers (NCBI MedGen, ClinVar). They are provided for research and exploration and should not be interpreted as an independent clinical diagnosis, proof of causality, or diagnostic prediction.'}
      </p>
    </div>
  );
}

export default ScientificInterpretationNotice;
