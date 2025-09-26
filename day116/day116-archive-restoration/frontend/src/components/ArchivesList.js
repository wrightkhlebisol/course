import React, { useState, useEffect } from 'react';

const ArchivesList = () => {
  const [archives, setArchives] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArchives();
  }, []);

  const fetchArchives = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/archives');
      const data = await response.json();
      setArchives(data.archives || []);
    } catch (error) {
      console.error('Failed to fetch archives:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">⏳ Loading archives...</div>;
  }

  if (archives.length === 0) {
    return (
      <div className="empty-state">
        <h2>📦 No Archives Found</h2>
        <p>Create some sample archives to get started.</p>
      </div>
    );
  }

  return (
    <div className="archives-list">
      <h2>🗄️ Available Archives</h2>
      
      <div className="archives-summary">
        <p>Total Archives: <strong>{archives.length}</strong></p>
      </div>

      <div className="archives-table-container">
        <table className="archives-table">
          <thead>
            <tr>
              <th>File Path</th>
              <th>Time Range</th>
              <th>Compression</th>
              <th>Records</th>
              <th>Size (MB)</th>
            </tr>
          </thead>
          <tbody>
            {archives.map((archive, index) => (
              <tr key={index}>
                <td className="file-path">{archive.file_path.split('/').pop()}</td>
                <td>
                  <div className="time-range">
                    <div>{new Date(archive.start_time).toLocaleString()}</div>
                    <div className="to-separator">to</div>
                    <div>{new Date(archive.end_time).toLocaleString()}</div>
                  </div>
                </td>
                <td>
                  <span className={`compression-badge compression-${archive.compression}`}>
                    {archive.compression.toUpperCase()}
                  </span>
                </td>
                <td>{archive.record_count.toLocaleString()}</td>
                <td>{archive.size_mb.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ArchivesList;
