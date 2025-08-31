import React, { useState } from 'react';

const LogSubmitter = ({ onSubmit }) => {
  const [logContent, setLogContent] = useState('');
  const [priority, setPriority] = useState('NORMAL');
  const [source, setSource] = useState('manual');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!logContent.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/logs/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: logContent,
          priority,
          source
        }),
      });

      const result = await response.json();
      setLastResult(result);
      
      if (result.status === 'accepted') {
        setLogContent('');
      }
      
      onSubmit(); // Refresh system status
    } catch (error) {
      console.error('Failed to submit log:', error);
      setLastResult({ status: 'error', reason: 'network_error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const generateSampleLogs = async (count = 10) => {
    setIsSubmitting(true);
    const priorities = ['CRITICAL', 'HIGH', 'NORMAL', 'LOW'];
    
    for (let i = 0; i < count; i++) {
      const randomPriority = priorities[Math.floor(Math.random() * priorities.length)];
      const sampleContent = `Sample log entry ${i + 1} - ${new Date().toISOString()}`;
      
      try {
        await fetch('http://localhost:8000/api/v1/logs/submit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: sampleContent,
            priority: randomPriority,
            source: 'batch_generator'
          }),
        });
        
        // Small delay between submissions
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        console.error('Failed to submit batch log:', error);
      }
    }
    
    setIsSubmitting(false);
    onSubmit(); // Refresh system status
  };

  return (
    <div className="log-submitter">
      <h3>📝 Log Message Submitter</h3>
      
      <form onSubmit={handleSubmit} className="submit-form">
        <div className="form-group">
          <label htmlFor="logContent">Log Content:</label>
          <textarea
            id="logContent"
            value={logContent}
            onChange={(e) => setLogContent(e.target.value)}
            placeholder="Enter your log message here..."
            rows={3}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="priority">Priority:</label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              disabled={isSubmitting}
            >
              <option value="LOW">🔵 Low (Debug/Trace)</option>
              <option value="NORMAL">🟢 Normal (Application)</option>
              <option value="HIGH">🟡 High (Business Critical)</option>
              <option value="CRITICAL">🔴 Critical (Errors/Security)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="source">Source:</label>
            <input
              id="source"
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="e.g., api, batch, manual"
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="button-group">
          <button type="submit" disabled={isSubmitting || !logContent.trim()}>
            {isSubmitting ? 'Submitting...' : 'Submit Log'}
          </button>
          
          <button 
            type="button" 
            onClick={() => generateSampleLogs(10)}
            disabled={isSubmitting}
            className="secondary-button"
          >
            Generate 10 Sample Logs
          </button>
        </div>
      </form>

      {lastResult && (
        <div className={`result-message ${lastResult.status}`}>
          <strong>Result:</strong> {lastResult.status}
          {lastResult.reason && <span> - {lastResult.reason}</span>}
          {lastResult.message_id && (
            <div className="message-id">Message ID: {lastResult.message_id}</div>
          )}
        </div>
      )}
    </div>
  );
};

export default LogSubmitter;
