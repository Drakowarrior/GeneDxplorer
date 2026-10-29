import React from 'react';

export function ErrorState({ error, onRetry }) {
  const message = error?.message || 'An unexpected error occurred while communicating with the research service.';
  const status = error?.status;

  let title = 'Error Loading Data';
  if (status === 404) {
    title = 'No Matching Records Found';
  } else if (status === 502) {
    title = 'NCBI MedGen Unavailable';
  } else if (status === 400) {
    title = 'Invalid Request';
  } else if (!status) {
    title = 'Unable to Connect to Research API';
  }

  return (
    <div className="error-box">
      <div className="error-title">{title}</div>
      <div className="error-desc">{message}</div>
      {onRetry && (
        <button type="button" className="btn-primary" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
}
