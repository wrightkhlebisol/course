import React, { useState } from 'react';

const QueryForm = ({ onQuery, loading }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [filters, setFilters] = useState('');
  const [pageSize, setPageSize] = useState(100);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!startDate || !endDate) {
      alert('Please select both start and end dates');
      return;
    }

    const queryData = {
      start_time: new Date(startDate).toISOString(),
      end_time: new Date(endDate).toISOString(),
      filters: filters ? JSON.parse(filters) : {},
      page_size: pageSize,
      include_archived: true
    };

    onQuery(queryData);
  };

  const createSampleArchives = async () => {
    try {
      const response = await fetch('/api/demo/create-sample-archives', {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('Sample archives created successfully!');
      } else {
        alert('Failed to create sample archives');
      }
    } catch (error) {
      alert('Error creating sample archives: ' + error.message);
    }
  };

  return (
    <div className="query-form">
      <h2>📋 Query Configuration</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Start Date:</label>
            <input
              type="datetime-local"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>End Date:</label>
            <input
              type="datetime-local"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label>Filters (JSON):</label>
          <textarea
            value={filters}
            onChange={(e) => setFilters(e.target.value)}
            placeholder='{"level": "ERROR", "service": "api"}'
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>Page Size:</label>
          <input
            type="number"
            value={pageSize}
            onChange={(e) => setPageSize(parseInt(e.target.value))}
            min={1}
            max={1000}
          />
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading}>
            {loading ? '⏳ Querying...' : '🔍 Execute Query'}
          </button>
          
          <button type="button" onClick={createSampleArchives}>
            📦 Create Sample Data
          </button>
        </div>
      </form>
    </div>
  );
};

export default QueryForm;
