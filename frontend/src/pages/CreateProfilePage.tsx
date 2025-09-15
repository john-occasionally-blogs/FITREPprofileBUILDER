import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { officerApi, fitreportApi } from '../services/api';
import { BatchProcessingResult } from '../types';

const CreateProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [processingComplete, setProcessingComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingResults, setProcessingResults] = useState<BatchProcessingResult | null>(null);
  const [uploadMode, setUploadMode] = useState<'auto' | 'manual'>('auto');
  const [officerData, setOfficerData] = useState({
    last_name: '',
    first_name: '',
    middle_initial: '',
    service_number: '',
    current_rank: 'CAPT'
  });

  const onDrop = (acceptedFiles: File[]) => {
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    setFiles(pdfFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      if (uploadMode === 'auto') {
        // Auto mode: Extract everything from PDFs
        setCurrentFile('🔍 Extracting officer info from PDF...');
        
        const startTime = Date.now();
        const updateProgress = () => {
          const elapsed = Date.now() - startTime;
          const expectedTime = files.length * 10000; // 10 seconds per file for auto
          const timeProgress = Math.min((elapsed / expectedTime) * 90, 90);
          setProgress(10 + timeProgress);
        };
        
        const progressInterval = setInterval(updateProgress, 1000);
        
        try {
          const results = await fitreportApi.multiRsUpload(files);
          clearInterval(progressInterval);
          
          setProcessingResults({
            total_files: files.length,
            successful: results.total_files_processed,
            failed: files.length - results.total_files_processed,
            results: files.map((file, i) => ({
              filename: file.name,
              status: 'success' as const,
              fitrep_id: `processed_${i}`,
              fra_score: undefined
            }))
          });
          setProgress(95);
          setCurrentFile(`✅ Created ${results.unique_rs_count} RS profiles!`);
          
          // Brief delay to show success
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          setProgress(100);
          setProcessingComplete(true);
          
          if (results.total_files_processed > 0) {
            // If only one RS profile created, go directly to it
            if (results.rs_profiles.length === 1) {
              setTimeout(() => {
                setUploading(false);
                navigate(`/profile/${results.rs_profiles[0].id}`);
              }, 2000);
            } else {
              // Multiple RS profiles created - show selection page
              setTimeout(() => {
                setUploading(false);
                navigate('/', { 
                  state: { 
                    message: `Successfully created ${results.unique_rs_count} RS profiles. Select one to view.`,
                    rsProfiles: results.rs_profiles 
                  }
                });
              }, 2000);
            }
          } else {
            throw new Error('No files were processed successfully');
          }
          
        } catch (procError) {
          clearInterval(progressInterval);
          throw procError;
        }
        
      } else {
        // Manual mode: Validate officer data first
        if (!officerData.last_name || !officerData.first_name || !officerData.service_number) {
          setError('Please fill in all required officer information');
          setUploading(false);
          return;
        }

        setCurrentFile('Creating officer profile...');

        // Step 1: Create officer
        const officer = await officerApi.createOfficer(officerData);
        
        setProgress(10);
        setCurrentFile('Officer profile created. Processing FITREP files...');
        
        // Step 2: Process files
        const startTime = Date.now();
        
        const updateProgress = () => {
          const elapsed = Date.now() - startTime;
          const expectedTime = files.length * 8000; // 8 seconds per file
          const timeProgress = Math.min((elapsed / expectedTime) * 80, 80);
          setProgress(10 + timeProgress);
        };
        
        const progressInterval = setInterval(updateProgress, 1000);
        
        try {
          const results = await fitreportApi.processFiles(files, officer.id);
          setProcessingResults(results);
          clearInterval(progressInterval);
          
          setProgress(95);
          setCurrentFile('Finalizing profile...');
          
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          setProgress(100);
          setProcessingComplete(true);
          
          if (results.successful > 0) {
            setTimeout(() => {
              setUploading(false);
              navigate(`/profile/${officer.id}`);
            }, 2000);
          } else {
            throw new Error('No files were processed successfully');
          }
          
        } catch (procError) {
          clearInterval(progressInterval);
          throw procError;
        }
      }
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during processing');
      setUploading(false);
      setProgress(0);
      setCurrentFile('');
    }
  };

  if (uploading) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>Creating Your Profile</h2>
          <p>Processing {files.length} FITREP files...</p>
          
          <div style={{ margin: '30px 0' }}>
            <div style={{ 
              width: '100%', 
              backgroundColor: '#f0f0f0', 
              borderRadius: '10px', 
              overflow: 'hidden',
              marginBottom: '20px'
            }}>
              <div style={{ 
                width: `${progress}%`, 
                backgroundColor: processingComplete ? '#28a745' : '#CC0000',
                height: '30px',
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold'
              }}>
                {Math.round(progress)}%
              </div>
            </div>
            
            <p>
              {processingComplete ? 
                '✅ Processing complete! Redirecting to your profile...' : 
                currentFile
              }
            </p>
            
            {error && (
              <div style={{ 
                backgroundColor: '#f8d7da', 
                color: '#721c24', 
                padding: '15px', 
                borderRadius: '5px', 
                marginTop: '20px',
                border: '1px solid #f5c6cb'
              }}>
                <strong>Error:</strong> {error}
                <button 
                  onClick={() => {setUploading(false); setError(null);}}
                  style={{ marginLeft: '10px', padding: '5px 10px' }}
                >
                  Try Again
                </button>
              </div>
            )}
            
            {processingResults && (
              <div style={{ fontSize: '0.9rem', marginTop: '20px', textAlign: 'left' }}>
                <h4>Processing Results:</h4>
                <p>✅ Successfully processed: {processingResults.successful} files</p>
                {processingResults.failed > 0 && (
                  <p>❌ Failed: {processingResults.failed} files</p>
                )}
                <details style={{ marginTop: '10px' }}>
                  <summary>View Details</summary>
                  {processingResults.results.map((result, i) => (
                    <div key={i} style={{ padding: '5px 0', fontSize: '0.8rem' }}>
                      {result.status === 'success' ? '✅' : '❌'} {result.filename}
                      {result.error && <span style={{ color: '#721c24' }}> - {result.error}</span>}
                    </div>
                  ))}
                </details>
              </div>
            )}
            
            <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '20px' }}>
              <p>📄 Extracting FITREP data from PDFs</p>
              <p>🧮 Calculating FRA scores</p>
              <p>📊 Computing relative values</p>
              <p>💾 Building your profile database</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>Create New FITREP Profile</h2>
          <button 
            onClick={() => navigate('/')} 
            className="btn btn-secondary"
          >
            Back to Home
          </button>
        </div>
        <p>Upload your FITREP PDF files to create your performance profile and analysis.</p>
      </div>

      <div className="card" style={{ backgroundColor: uploadMode === 'auto' ? '#e8f5e8' : '#f8f9fa' }}>
        <h3>🚀 Choose Upload Method</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
          <div 
            style={{ 
              padding: '20px', 
              border: uploadMode === 'auto' ? '3px solid #28a745' : '2px solid #ddd',
              borderRadius: '8px',
              cursor: 'pointer',
              backgroundColor: uploadMode === 'auto' ? '#fff' : '#f8f9fa',
              transition: 'all 0.3s ease'
            }}
            onClick={() => setUploadMode('auto')}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <input 
                type="radio" 
                checked={uploadMode === 'auto'} 
                onChange={() => setUploadMode('auto')}
                style={{ marginRight: '10px' }}
              />
              <h4 style={{ margin: 0, color: '#28a745' }}>🎯 Auto Upload (Recommended)</h4>
            </div>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>
              <strong>Zero manual entry!</strong> Just upload your PDFs and we'll extract all your information automatically from the reports.
            </p>
            <ul style={{ marginTop: '10px', paddingLeft: '20px', fontSize: '0.9rem', color: '#666' }}>
              <li>Extracts name, rank, and EDIPI from PDFs</li>
              <li>No typing required</li>
              <li>Fastest setup</li>
            </ul>
          </div>
          
          <div 
            style={{ 
              padding: '20px', 
              border: uploadMode === 'manual' ? '3px solid #CC0000' : '2px solid #ddd',
              borderRadius: '8px',
              cursor: 'pointer',
              backgroundColor: uploadMode === 'manual' ? '#fff' : '#f8f9fa',
              transition: 'all 0.3s ease'
            }}
            onClick={() => setUploadMode('manual')}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <input 
                type="radio" 
                checked={uploadMode === 'manual'} 
                onChange={() => setUploadMode('manual')}
                style={{ marginRight: '10px' }}
              />
              <h4 style={{ margin: 0, color: '#CC0000' }}>✏️ Manual Entry</h4>
            </div>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>
              Enter your officer information manually, then upload and process your FITREP files.
            </p>
            <ul style={{ marginTop: '10px', paddingLeft: '20px', fontSize: '0.9rem', color: '#666' }}>
              <li>Full control over profile details</li>
              <li>Good for unusual cases</li>
              <li>Requires manual typing</li>
            </ul>
          </div>
        </div>
      </div>

      {uploadMode === 'manual' && (
        <div className="card">
          <h3>Officer Information</h3>
          <p>Please provide basic officer information that will be used to create your profile.</p>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginTop: '20px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              Last Name *
            </label>
            <input
              type="text"
              value={officerData.last_name}
              onChange={(e) => setOfficerData({...officerData, last_name: e.target.value.toUpperCase()})}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
              placeholder="SMITH"
            />
          </div>
          
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              First Name *
            </label>
            <input
              type="text"
              value={officerData.first_name}
              onChange={(e) => setOfficerData({...officerData, first_name: e.target.value.toUpperCase()})}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
              placeholder="JOHN"
            />
          </div>
          
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              Middle Initial
            </label>
            <input
              type="text"
              maxLength={1}
              value={officerData.middle_initial}
              onChange={(e) => setOfficerData({...officerData, middle_initial: e.target.value.toUpperCase()})}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
              placeholder="A"
            />
          </div>
          
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              Service Number *
            </label>
            <input
              type="text"
              value={officerData.service_number}
              onChange={(e) => setOfficerData({...officerData, service_number: e.target.value})}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
              placeholder="123456789"
            />
          </div>
          
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              Current Rank
            </label>
            <select
              value={officerData.current_rank}
              onChange={(e) => setOfficerData({...officerData, current_rank: e.target.value})}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="SGT">SGT</option>
              <option value="SSGT">SSGT</option>
              <option value="GYSGT">GYSGT</option>
              <option value="MSGT">MSGT</option>
              <option value="MGYSGT">MGYSGT</option>
              <option value="1STSGT">1STSGT</option>
              <option value="SGTMAJ">SGTMAJ</option>
              <option value="2NDLT">2NDLT</option>
              <option value="1STLT">1STLT</option>
              <option value="CAPT">CAPT</option>
              <option value="MAJ">MAJ</option>
              <option value="LTCOL">LTCOL</option>
              <option value="COL">COL</option>
              <option value="WO">WO</option>
              <option value="CWO2">CWO2</option>
              <option value="CWO3">CWO3</option>
              <option value="CWO4">CWO4</option>
              <option value="CWO5">CWO5</option>
            </select>
          </div>
        </div>
        
        {error && (
          <div style={{ 
            backgroundColor: '#f8d7da', 
            color: '#721c24', 
            padding: '15px', 
            borderRadius: '5px', 
            marginTop: '15px',
            border: '1px solid #f5c6cb'
          }}>
            {error}
          </div>
        )}
        </div>
      )}

      <div className="card">
        <h3>Upload FITREP Files</h3>
        
        <div 
          {...getRootProps()} 
          style={{
            border: '3px dashed #ccc',
            borderRadius: '8px',
            padding: '40px',
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? '#f0f8ff' : '#fafafa',
            borderColor: isDragActive ? '#CC0000' : '#ccc',
            transition: 'all 0.3s ease'
          }}
        >
          <input {...getInputProps()} />
          
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>📁</div>
          
          {isDragActive ? (
            <p style={{ fontSize: '1.2rem', color: '#CC0000', fontWeight: 'bold' }}>
              Drop your FITREP PDF files here!
            </p>
          ) : (
            <div>
              <p style={{ fontSize: '1.2rem', marginBottom: '10px' }}>
                <strong>Drop your FITREP PDF files here</strong>
              </p>
              <p style={{ color: '#666' }}>
                or click to browse and select files
              </p>
              <p style={{ fontSize: '0.9rem', color: '#888', marginTop: '15px' }}>
                Only PDF files are accepted. You can upload multiple files at once.
              </p>
            </div>
          )}
        </div>

        {files.length > 0 && (
          <div style={{ marginTop: '30px' }}>
            <h4>Selected Files ({files.length}):</h4>
            <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px', padding: '10px' }}>
              {files.map((file, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  padding: '8px',
                  borderBottom: index < files.length - 1 ? '1px solid #eee' : 'none'
                }}>
                  <div>
                    <strong>{file.name}</strong>
                    <span style={{ color: '#666', marginLeft: '10px' }}>
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  <button 
                    onClick={() => removeFile(index)}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: '#CC0000', 
                      cursor: 'pointer',
                      fontSize: '1.2rem'
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <button 
                onClick={handleUpload}
                className="btn btn-primary"
                disabled={uploadMode === 'auto' ? files.length === 0 : (!officerData.last_name || !officerData.first_name || !officerData.service_number || files.length === 0)}
                style={{ 
                  fontSize: '1.1rem', 
                  padding: '15px 30px',
                  opacity: (uploadMode === 'auto' ? files.length === 0 : (!officerData.last_name || !officerData.first_name || !officerData.service_number || files.length === 0)) ? 0.5 : 1
                }}
              >
                {uploadMode === 'auto' ? '🚀 Auto Create Profile' : 'Create Profile'} ({files.length} files)
              </button>
              
              {uploadMode === 'auto' && files.length === 0 && (
                <p style={{ color: '#721c24', fontSize: '0.9rem', marginTop: '10px' }}>
                  Please upload at least one FITREP PDF file
                </p>
              )}
              
              {uploadMode === 'manual' && (!officerData.last_name || !officerData.first_name || !officerData.service_number) && (
                <p style={{ color: '#721c24', fontSize: '0.9rem', marginTop: '10px' }}>
                  Please fill in all required officer information above
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{ backgroundColor: '#f8f9fa' }}>
        <h4>What happens next?</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '15px' }}>
          <div>
            <strong>1. PDF Processing</strong>
            <p>We extract data from each FITREP including trait scores and administrative information.</p>
          </div>
          <div>
            <strong>2. Score Calculation</strong>
            <p>FRA scores are calculated and relative values are computed based on your reporting seniors.</p>
          </div>
          <div>
            <strong>3. Profile Creation</strong>
            <p>Your comprehensive profile is built, showing performance trends by rank and over time.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateProfilePage;