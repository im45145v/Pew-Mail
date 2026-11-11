import React, { useState, useEffect } from 'react';
import './TestingLab.css';

interface StagingSnapshot {
  id: string;
  emailName: string;
  versionNumber: number;
  authorName: string;
  createdAt: string;
  stagingStatus: 'VALIDATION_PENDING' | 'VALIDATION_IN_PROGRESS' | 'VALIDATION_COMPLETED' | 'APPROVED' | 'DISCARDED';
  validationScore?: number;
}

const TestingLab: React.FC = () => {
  const [stagingHistory, setStagingHistory] = useState<StagingSnapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<StagingSnapshot | null>(null);
  const [validationResults, setValidationResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Mock data for demonstration
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockStagingHistory: StagingSnapshot[] = [
        {
          id: '1',
          emailName: 'Welcome Email',
          versionNumber: 3,
          authorName: 'John Doe',
          createdAt: '2023-06-15T10:30:00Z',
          stagingStatus: 'VALIDATION_COMPLETED',
          validationScore: 92
        },
        {
          id: '2',
          emailName: 'Newsletter Template',
          versionNumber: 1,
          authorName: 'Jane Smith',
          createdAt: '2023-06-14T14:45:00Z',
          stagingStatus: 'APPROVED',
          validationScore: 98
        },
        {
          id: '3',
          emailName: 'Promotional Offer',
          versionNumber: 2,
          authorName: 'Mike Johnson',
          createdAt: '2023-06-13T09:15:00Z',
          stagingStatus: 'VALIDATION_PENDING'
        }
      ];
      
      setStagingHistory(mockStagingHistory);
      setSelectedSnapshot(mockStagingHistory[0]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const handleSnapshotSelect = (snapshot: StagingSnapshot) => {
    setSelectedSnapshot(snapshot);
    
    // Simulate loading validation results
    if (snapshot.stagingStatus !== 'VALIDATION_PENDING') {
      // Mock validation results
      const mockResults = [
        {
          id: '1',
          category: 'HTML',
          severity: 'ERROR',
          status: 'FAIL',
          description: 'Missing DOCTYPE declaration',
          location: 'Line 1'
        },
        {
          id: '2',
          category: 'Accessibility',
          severity: 'WARNING',
          status: 'PASS',
          description: 'Image has alt text',
          location: 'Line 15'
        },
        {
          id: '3',
          category: 'Links',
          severity: 'ERROR',
          status: 'FAIL',
          description: 'Broken link detected',
          location: 'Line 22'
        }
      ];
      setValidationResults(mockResults);
    } else {
      setValidationResults([]);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'VALIDATION_COMPLETED':
        return 'status-badge status-completed';
      case 'APPROVED':
        return 'status-badge status-approved';
      case 'VALIDATION_PENDING':
        return 'status-badge status-pending';
      case 'VALIDATION_IN_PROGRESS':
        return 'status-badge status-in-progress';
      case 'DISCARDED':
        return 'status-badge status-discarded';
      default:
        return 'status-badge';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'VALIDATION_COMPLETED':
        return 'Validation Completed';
      case 'APPROVED':
        return 'Approved';
      case 'VALIDATION_PENDING':
        return 'Validation Pending';
      case 'VALIDATION_IN_PROGRESS':
        return 'Validation In Progress';
      case 'DISCARDED':
        return 'Discarded';
      default:
        return status;
    }
  };

  if (isLoading) {
    return <div className="testing-lab-container">Loading...</div>;
  }

  return (
    <div className="testing-lab-container">
      <h1>Email Testing Lab</h1>
      
      <div className="testing-lab-layout">
        {/* Left sidebar - Staging History */}
        <div className="staging-history-panel">
          <h2>Staging History</h2>
          <div className="staging-history-list">
            {stagingHistory.map((snapshot) => (
              <div 
                key={snapshot.id}
                className={`staging-item ${selectedSnapshot?.id === snapshot.id ? 'selected' : ''}`}
                onClick={() => handleSnapshotSelect(snapshot)}
              >
                <div className="staging-header">
                  <h3>{snapshot.emailName} v{snapshot.versionNumber}</h3>
                  <span className={getStatusBadgeClass(snapshot.stagingStatus)}>
                    {getStatusText(snapshot.stagingStatus)}
                  </span>
                </div>
                <div className="staging-details">
                  <p>By {snapshot.authorName}</p>
                  <p>{new Date(snapshot.createdAt).toLocaleDateString()}</p>
                  {snapshot.validationScore !== undefined && (
                    <p>Score: {snapshot.validationScore}/100</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main content area */}
        <div className="testing-main-content">
          {selectedSnapshot ? (
            <>
              <div className="snapshot-header">
                <h2>{selectedSnapshot.emailName} v{selectedSnapshot.versionNumber}</h2>
                <div className="snapshot-actions">
                  <button className="btn btn-primary">Send Test Email</button>
                  <button className="btn btn-secondary">Approve</button>
                  <button className="btn btn-danger">Discard</button>
                </div>
              </div>

              {/* Preview Panel */}
              <div className="preview-section">
                <h3>Preview</h3>
                <div className="preview-tabs">
                  <button className="tab-button active">Desktop</button>
                  <button className="tab-button">Mobile</button>
                  <button className="tab-button">Tablet</button>
                </div>
                <div className="preview-frame">
                  <iframe 
                    srcDoc="<html><body><h1>Welcome to Our Service</h1><p>This is a test email preview.</p></body></html>"
                    title="email-preview"
                  />
                </div>
              </div>

              {/* Validation Results */}
              <div className="validation-results">
                <h3>Validation Results</h3>
                {selectedSnapshot.stagingStatus === 'VALIDATION_PENDING' ? (
                  <p>Validation pending. Click "Run Validation" to start.</p>
                ) : (
                  <div className="validation-results-list">
                    {validationResults.map((result) => (
                      <div key={result.id} className={`validation-item severity-${result.severity.toLowerCase()}`}>
                        <div className="validation-header">
                          <span className="validation-category">{result.category}</span>
                          <span className={`validation-status ${result.status.toLowerCase()}`}>
                            {result.status}
                          </span>
                          <span className={`validation-severity severity-${result.severity.toLowerCase()}`}>
                            {result.severity}
                          </span>
                        </div>
                        <div className="validation-description">
                          <p>{result.description}</p>
                          <p className="validation-location">{result.location}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Approval Panel */}
              <div className="approval-panel">
                <h3>Approval</h3>
                <div className="approval-comments">
                  <div className="comment-input">
                    <textarea placeholder="Add a comment..." />
                    <button className="btn btn-primary">Add Comment</button>
                  </div>
                  <div className="comments-list">
                    <div className="comment">
                      <p><strong>John Doe</strong> - 2 hours ago</p>
                      <p>This looks good, but please check the broken link before approving.</p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="no-selection">
              <p>Select a staging snapshot to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestingLab;