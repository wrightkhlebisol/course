import React, { useState } from 'react';
import { Search, Clock, AlertCircle, Info, Database, FileText, Upload } from 'lucide-react';
import FileBrowser from './FileBrowser';
import IndexedTerms from './IndexedTerms';

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [activeTab, setActiveTab] = useState('search'); // 'search' or 'browse'
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');

  const executeSearch = async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setMetadata(null);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}&limit=50`);
      const data = await response.json();
      
      setResults(data.results || []);
      setMetadata(data.metadata || null);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
      setMetadata({ error: 'Search failed' });
    } finally {
      setLoading(false);
    }
  };

  const getSuggestions = async (searchQuery) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/api/suggest?q=${encodeURIComponent(searchQuery)}&limit=5`);
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Suggestions error:', error);
      setSuggestions([]);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    getSuggestions(value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    executeSearch(query);
  };

  const selectSuggestion = (term) => {
    setQuery(term);
    setSuggestions([]);
    executeSearch(term);
  };

  const handleTermClick = (term) => {
    setQuery(term);
    setSuggestions([]);
    executeSearch(term);
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
  };

  const handleFileContent = (content) => {
    setFileContent(content);
  };

  const getLevelIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return <AlertCircle className="level-icon error" size={16} />;
      case 'warning':
        return <AlertCircle className="level-icon warning" size={16} />;
      case 'info':
        return <Info className="level-icon info" size={16} />;
      default:
        return <Database className="level-icon default" size={16} />;
    }
  };

  return (
    <div className="search-interface">
      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          <Search size={18} />
          <span>Search Logs</span>
        </button>
        <button
          className={`tab-button ${activeTab === 'browse' ? 'active' : ''}`}
          onClick={() => setActiveTab('browse')}
        >
          <FileText size={18} />
          <span>Browse Files</span>
        </button>
      </div>

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="tab-content">
          <div className="search-layout">
            <div className="search-main">
              <div className="search-form-container">
                <form onSubmit={handleSubmit} className="search-form">
                  <div className="search-input-container">
                    <Search className="search-icon" size={20} />
                    <input
                      type="text"
                      value={query}
                      onChange={handleInputChange}
                      placeholder="Search logs... (e.g., 'error authentication' or 'service:auth level:error')"
                      className="search-input"
                      autoComplete="off"
                    />
                    <button type="submit" className="search-button" disabled={loading}>
                      {loading ? 'Searching...' : 'Search'}
                    </button>
                  </div>
                  
                  {suggestions.length > 0 && (
                    <div className="suggestions">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          className="suggestion-item"
                          onClick={() => selectSuggestion(suggestion.term)}
                        >
                          {suggestion.term}
                          <span className="suggestion-frequency">({suggestion.frequency})</span>
                        </button>
                      ))}
                    </div>
                  )}
                </form>
              </div>

              {metadata && (
                <div className="search-metadata">
                  <div className="metadata-content">
                    {metadata.error ? (
                      <span className="error-message">❌ {metadata.error}</span>
                    ) : (
                      <span className="results-info">
                        Found {metadata.total_results} results in {metadata.search_time_ms}ms
                      </span>
                    )}
                  </div>
                </div>
              )}

              {loading && (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <span>Searching through logs...</span>
                </div>
              )}

              <div className="search-results">
                {results.map((result, index) => (
                  <div key={result.id || index} className="result-item">
                    <div className="result-header">
                      <span className="result-id">{result.id}</span>
                      <div className="result-meta">
                        {getLevelIcon(result.metadata?.level)}
                        <span className="result-service">{result.metadata?.service}</span>
                        <Clock className="time-icon" size={14} />
                        <span className="result-timestamp">{new Date(result.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="result-content">
                      <div 
                        className="result-message"
                        dangerouslySetInnerHTML={{__html: result.highlighted || result.content}}
                      />
                    </div>
                    {result.score && (
                      <div className="result-score">
                        Relevance: {result.score.toFixed(2)}
                      </div>
                    )}
                  </div>
                ))}
                
                {results.length === 0 && !loading && metadata && !metadata.error && (
                  <div className="no-results">
                    <Search size={48} className="no-results-icon" />
                    <h3>No logs found</h3>
                    <p>Try adjusting your search terms or using different keywords.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="search-sidebar">
              <IndexedTerms onTermClick={handleTermClick} />
            </div>
          </div>
        </div>
      )}

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div className="tab-content">
          <FileBrowser 
            onFileSelect={handleFileSelect}
            onFileContent={handleFileContent}
          />
        </div>
      )}
    </div>
  );
};

export default SearchInterface;
