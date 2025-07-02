import React, { useState, useEffect } from 'react';
import { Hash, TrendingUp, Search } from 'lucide-react';

const IndexedTerms = ({ onTermClick }) => {
  const [terms, setTerms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'high', 'medium', 'low'

  useEffect(() => {
    fetchIndexedTerms();
  }, []);

  const fetchIndexedTerms = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/stats');
      const data = await response.json();
      
      if (data.most_frequent_terms) {
        setTerms(data.most_frequent_terms);
      } else {
        setTerms([]);
      }
    } catch (error) {
      console.error('Error fetching indexed terms:', error);
      setError('Failed to load indexed terms');
    } finally {
      setLoading(false);
    }
  };

  const handleTermClick = (term) => {
    if (onTermClick) {
      onTermClick(term);
    }
  };

  const getFrequencyLevel = (frequency) => {
    if (frequency >= 10) return 'high';
    if (frequency >= 5) return 'medium';
    return 'low';
  };

  const filteredTerms = terms.filter(([term, frequency]) => {
    if (filter === 'all') return true;
    return getFrequencyLevel(frequency) === filter;
  });

  const getFrequencyColor = (frequency) => {
    const level = getFrequencyLevel(frequency);
    switch (level) {
      case 'high':
        return 'frequency-high';
      case 'medium':
        return 'frequency-medium';
      case 'low':
        return 'frequency-low';
      default:
        return 'frequency-low';
    }
  };

  if (loading) {
    return (
      <div className="indexed-terms">
        <div className="terms-header">
          <Hash size={18} />
          <span>Indexed Terms</span>
        </div>
        <div className="terms-loading">
          <div className="loading-spinner small"></div>
          <span>Loading terms...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="indexed-terms">
        <div className="terms-header">
          <Hash size={18} />
          <span>Indexed Terms</span>
        </div>
        <div className="terms-error">
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="indexed-terms">
      <div className="terms-header">
        <Hash size={18} />
        <span>Indexed Terms</span>
        <span className="terms-count">({terms.length})</span>
      </div>

      <div className="terms-filters">
        <button
          className={`filter-button ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All
        </button>
        <button
          className={`filter-button ${filter === 'high' ? 'active' : ''}`}
          onClick={() => setFilter('high')}
        >
          High
        </button>
        <button
          className={`filter-button ${filter === 'medium' ? 'active' : ''}`}
          onClick={() => setFilter('medium')}
        >
          Medium
        </button>
        <button
          className={`filter-button ${filter === 'low' ? 'active' : ''}`}
          onClick={() => setFilter('low')}
        >
          Low
        </button>
      </div>

      {filteredTerms.length > 0 ? (
        <div className="terms-grid">
          {filteredTerms.map(([term, frequency], index) => (
            <button
              key={index}
              className="term-chip"
              onClick={() => handleTermClick(term)}
              title={`Click to search for "${term}" (${frequency} occurrences)`}
            >
              <Search size={14} />
              <span className="term-text">{term}</span>
              <span className={`term-frequency ${getFrequencyColor(frequency)}`}>
                {frequency}
              </span>
            </button>
          ))}
        </div>
      ) : (
        <div className="no-terms">
          <TrendingUp size={24} />
          <span>No terms found</span>
          <small>Upload some log files to see indexed terms</small>
        </div>
      )}

      <div className="terms-footer">
        <small>
          Click any term to search for it in the logs
        </small>
      </div>
    </div>
  );
};

export default IndexedTerms; 