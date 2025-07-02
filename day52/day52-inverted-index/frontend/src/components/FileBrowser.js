import React, { useState, useRef } from 'react';
import { Upload, FileText, X, Eye, Download, Search, CheckCircle } from 'lucide-react';

const FileBrowser = ({ onFileSelect, onFileContent }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.log') && !file.name.endsWith('.txt')) {
      setError('Please select a .log or .txt file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setError('');
    setUploadStatus(null);
    setIsLoading(true);

    // Read file content
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      setFileContent(content);
      setIsLoading(false);
      
      // Notify parent component
      if (onFileSelect) onFileSelect(file);
      if (onFileContent) onFileContent(content);
    };

    reader.onerror = () => {
      setError('Failed to read file');
      setIsLoading(false);
    };

    reader.readAsText(file);
  };

  const uploadAndIndex = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStatus(null);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus({
          type: 'success',
          message: result.message,
          details: result.file_info
        });
      } else {
        setError(result.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setFileContent('');
    setError('');
    setUploadStatus(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const downloadFile = () => {
    if (!selectedFile) return;
    
    const blob = new Blob([fileContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = selectedFile.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="file-browser">
      <div className="file-browser-header">
        <h3>Log File Browser</h3>
        <p>Select a log file to view its contents and optionally index it for searching</p>
      </div>

      <div className="file-upload-section">
        <input
          ref={fileInputRef}
          type="file"
          accept=".log,.txt"
          onChange={handleFileSelect}
          className="file-input"
          id="file-input"
        />
        <label htmlFor="file-input" className="file-upload-button">
          <Upload size={20} />
          <span>Choose Log File</span>
        </label>
        
        {error && (
          <div className="file-error">
            <X size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {isLoading && (
        <div className="file-loading">
          <div className="loading-spinner"></div>
          <span>Loading file...</span>
        </div>
      )}

      {selectedFile && (
        <div className="file-info">
          <div className="file-details">
            <FileText size={20} />
            <div className="file-meta">
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">{formatFileSize(selectedFile.size)}</span>
            </div>
            <div className="file-actions">
              <button 
                onClick={uploadAndIndex} 
                className="action-button upload-button" 
                title="Upload and Index"
                disabled={isUploading}
              >
                {isUploading ? (
                  <div className="loading-spinner small"></div>
                ) : (
                  <Search size={16} />
                )}
              </button>
              <button onClick={downloadFile} className="action-button" title="Download">
                <Download size={16} />
              </button>
              <button onClick={clearFile} className="action-button" title="Clear">
                <X size={16} />
              </button>
            </div>
          </div>

          {uploadStatus && (
            <div className={`upload-status ${uploadStatus.type}`}>
              <CheckCircle size={16} />
              <div className="upload-message">
                <span className="status-text">{uploadStatus.message}</span>
                {uploadStatus.details && (
                  <div className="upload-details">
                    <span>Lines processed: {uploadStatus.details.lines_processed}</span>
                    <span>Lines indexed: {uploadStatus.details.lines_indexed}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {fileContent && (
        <div className="file-content">
          <div className="content-header">
            <Eye size={16} />
            <span>File Contents</span>
            <span className="line-count">
              {fileContent.split('\n').length} lines
            </span>
          </div>
          <div className="content-viewer">
            <pre className="log-content">{fileContent}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileBrowser; 