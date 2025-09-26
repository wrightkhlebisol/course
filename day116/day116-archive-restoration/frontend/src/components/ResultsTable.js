import React from 'react';

const ResultsTable = ({ results }) => {
  if (!results || !results.records) {
    return null;
  }

  return (
    <div className="results-section">
      <h2>📊 Query Results</h2>
      
      <div className="results-summary">
        <div className="summary-item">
          <strong>Records Found:</strong> {results.total_count}
        </div>
        <div className="summary-item">
          <strong>Processing Time:</strong> {results.processing_time_ms}ms
        </div>
        <div className="summary-item">
          <strong>Cache Hit:</strong> {results.cache_hit ? '✅ Yes' : '❌ No'}
        </div>
        <div className="summary-item">
          <strong>Sources:</strong> {results.sources.length} archive(s)
        </div>
      </div>

      {results.records.length > 0 ? (
        <div className="results-table-container">
          <table className="results-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Service</th>
                <th>Message</th>
                <th>Request ID</th>
              </tr>
            </thead>
            <tbody>
              {results.records.map((record, index) => (
                <tr key={index}>
                  <td>{record.timestamp}</td>
                  <td>
                    <span className={`level-badge level-${record.level?.toLowerCase()}`}>
                      {record.level}
                    </span>
                  </td>
                  <td>{record.service}</td>
                  <td className="message-cell">{record.message}</td>
                  <td>{record.request_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="no-results">
          <p>No records found for the specified criteria.</p>
        </div>
      )}
    </div>
  );
};

export default ResultsTable;
