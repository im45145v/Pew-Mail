import React, { useState, useRef } from 'react';
import { ContactImport, CSVColumnMapping } from './types';
import { ContactService } from './services';

interface ImportPageProps {
  organizationId: string;
}

const ImportPage: React.FC<ImportPageProps> = ({ organizationId }) => {
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<any[][]>([]);
  const [columnHeaders, setColumnHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'upload' | 'mapping' | 'preview' | 'importing' | 'complete'>('upload');
  const [error, setError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<ContactImport | null>(null);
  const [hasHeaders, setHasHeaders] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const requiredFields = ['email'];
  const optionalFields = [
    'first_name', 'last_name', 'organization', 'job_title', 
    'phone_number', 'notes', 'consent_status', 'tags'
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setFile(selectedFile);
    parseCSV(selectedFile);
  };

  const parseCSV = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const lines = content.split('\n').filter(line => line.trim() !== '');
      
      if (lines.length === 0) {
        setError('The CSV file is empty');
        return;
      }

      const parsedData = lines.map(line => {
        // Simple CSV parser (doesn't handle quoted fields with commas)
        return line.split(',').map(field => field.trim());
      });

      if (parsedData.length === 0) {
        setError('Unable to parse the CSV file');
        return;
      }

      setColumnHeaders(hasHeaders ? parsedData[0] : 
        Array.from({ length: parsedData[0].length }, (_, i) => `Column ${i + 1}`));
      
      const dataToPreview = hasHeaders ? parsedData.slice(1, 6) : parsedData.slice(0, 5);
      setPreviewData(dataToPreview);
      setStep('mapping');
      setError(null);
    };
    
    reader.onerror = () => {
      setError('Error reading the file');
    };
    
    reader.readAsText(file);
  };

  const handleMappingChange = (csvColumn: string, contactField: string) => {
    setMapping(prev => ({
      ...prev,
      [csvColumn]: contactField
    }));
  };

  const handleImport = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setStep('importing');

    try {
      // Validate that required fields are mapped
      const mappedRequiredFields = requiredFields.filter(field => 
        Object.values(mapping).includes(field)
      );

      if (mappedRequiredFields.length !== requiredFields.length) {
        throw new Error('Please map all required fields (email)');
      }

      const formData = new FormData();
      formData.append('file', file);
      
      // Add mapping to form data as JSON
      formData.append('mapping', JSON.stringify(mapping));
      formData.append('has_headers', hasHeaders.toString());

      const service = new ContactService();
      const result = await service.importContactsCSV(organizationId, formData);
      
      setImportResult(result);
      setStep('complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import contacts');
      setStep('preview');
    } finally {
      setLoading(false);
    }
  };

  const resetImport = () => {
    setFile(null);
    setPreviewData([]);
    setColumnHeaders([]);
    setMapping({});
    setStep('upload');
    setError(null);
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const unmappedColumns = columnHeaders.filter(header => !mapping[header]);

  return (
    <div className="import-page">
      <div className="import-header">
        <h1>Import Contacts</h1>
        <p>Upload a CSV file to add contacts to your organization</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {step === 'upload' && (
        <div className="upload-step">
          <div className="upload-box">
            <div className="upload-icon">📁</div>
            <h2>Upload CSV File</h2>
            <p>Choose a CSV file containing your contacts</p>
            
            <div className="file-input-container">
              <input
                type="file"
                ref={fileInputRef}
                accept=".csv"
                onChange={handleFileChange}
                className="file-input"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="btn btn-primary">
                Select CSV File
              </label>
            </div>
            
            <div className="options">
              <label>
                <input
                  type="checkbox"
                  checked={hasHeaders}
                  onChange={(e) => setHasHeaders(e.target.checked)}
                />
                First row contains column headers
              </label>
            </div>
          </div>
          
          <div className="import-instructions">
            <h3>CSV Format Requirements</h3>
            <ul>
              <li>File must be in CSV format</li>
              <li>Must contain at least an email column</li>
              <li>Recommended columns: first_name, last_name, organization</li>
              <li>UTF-8 encoding preferred</li>
              <li>Maximum file size: 10MB</li>
            </ul>
          </div>
        </div>
      )}

      {step === 'mapping' && columnHeaders.length > 0 && (
        <div className="mapping-step">
          <h2>Map Columns</h2>
          <p>Match your CSV columns to contact fields</p>
          
          <div className="mapping-table">
            <div className="mapping-row header">
              <div className="csv-column">CSV Column</div>
              <div className="arrow">→</div>
              <div className="contact-field">Contact Field</div>
            </div>
            
            {columnHeaders.map((header, index) => (
              <div key={index} className="mapping-row">
                <div className="csv-column">
                  <strong>{header}</strong>
                  {previewData.length > 0 && (
                    <div className="sample-data">
                      {previewData.slice(0, 3).map((row, rowIndex) => (
                        <div key={rowIndex} className="sample-value">
                          {row[index] || <em>Empty</em>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="arrow">→</div>
                <div className="contact-field">
                  <select
                    value={mapping[header] || ''}
                    onChange={(e) => handleMappingChange(header, e.target.value)}
                  >
                    <option value="">Select a field</option>
                    <optgroup label="Required">
                      {requiredFields.map(field => (
                        <option key={field} value={field}>
                          {field.replace('_', ' ')}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Optional">
                      {optionalFields.map(field => (
                        <option key={field} value={field}>
                          {field.replace('_', ' ')}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>
              </div>
            ))}
          </div>
          
          {unmappedColumns.length > 0 && (
            <div className="warning-message">
              Unmapped columns: {unmappedColumns.join(', ')}
            </div>
          )}
          
          <div className="step-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => setStep('upload')}
            >
              Back
            </button>
            <button 
              className="btn btn-primary"
              onClick={() => setStep('preview')}
              disabled={unmappedColumns.length === columnHeaders.length}
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <div className="preview-step">
          <h2>Preview Import</h2>
          
          <div className="import-summary">
            <div className="summary-item">
              <span className="label">File:</span>
              <span className="value">{file?.name}</span>
            </div>
            <div className="summary-item">
              <span className="label">Columns:</span>
              <span className="value">{columnHeaders.length}</span>
            </div>
            <div className="summary-item">
              <span className="label">Mapped Fields:</span>
              <span className="value">{Object.keys(mapping).length}</span>
            </div>
          </div>
          
          <div className="mapping-preview">
            <h3>Column Mapping</h3>
            <ul>
              {Object.entries(mapping).map(([csvColumn, contactField]) => (
                <li key={csvColumn}>
                  <strong>{csvColumn}</strong> → {contactField.replace('_', ' ')}
                </li>
              ))}
            </ul>
          </div>
          
          {previewData.length > 0 && (
            <div className="data-preview">
              <h3>Data Preview</h3>
              <div className="preview-table">
                <table>
                  <thead>
                    <tr>
                      {columnHeaders.map((header, index) => (
                        <th key={index}>{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex}>{cell || <em>Empty</em>}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          <div className="step-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => setStep('mapping')}
            >
              Back
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleImport}
              disabled={loading}
            >
              {loading ? 'Importing...' : 'Start Import'}
            </button>
          </div>
        </div>
      )}

      {step === 'importing' && (
        <div className="importing-step">
          <div className="spinner"></div>
          <h2>Importing Contacts</h2>
          <p>Your contacts are being imported. This may take a few moments...</p>
        </div>
      )}

      {step === 'complete' && importResult && (
        <div className="complete-step">
          <div className="success-icon">✓</div>
          <h2>Import Complete!</h2>
          
          <div className="import-results">
            <div className="result-item success">
              <span className="label">Successfully Imported:</span>
              <span className="value">{importResult.processed_count}</span>
            </div>
            <div className="result-item warning">
              <span className="label">Duplicates Skipped:</span>
              <span className="value">{importResult.duplicate_count}</span>
            </div>
            <div className="result-item error">
              <span className="label">Errors:</span>
              <span className="value">{importResult.error_count}</span>
            </div>
          </div>
          
          {importResult.error_count > 0 && (
            <div className="error-details">
              <h3>Import Errors</h3>
              <p>Some rows could not be imported. Please check your CSV file and try again.</p>
            </div>
          )}
          
          <div className="step-actions">
            <button 
              className="btn btn-secondary"
              onClick={resetImport}
            >
              Import Another File
            </button>
            <button 
              className="btn btn-primary"
              onClick={() => window.location.hash = '#/contacts'}
            >
              View Contacts
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportPage;