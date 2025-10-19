import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { officerApi, fitreportApi } from '../services/api';

interface RSSummary {
  rs_name: string;
  rs_edipi: string;
  total_reports: number;
}

const UpdateProfilePage: React.FC = () => {
  const { officerId } = useParams<{ officerId: string }>();
  const navigate = useNavigate();
  const [rsSummary, setRsSummary] = useState<RSSummary | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [uploadMode, setUploadMode] = useState<'individual' | 'summary'>('individual');
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [estimatedTotal, setEstimatedTotal] = useState<number>(0);

  useEffect(() => {
    const fetchOfficerData = async () => {
      try {
        const officers = await officerApi.getOfficers();
        const officer = officers.find((o: any) => o.id === parseInt(officerId || '0'));

        if (officer) {
          setRsSummary({
            rs_name: `${officer.last_name}, ${officer.first_name}`,
            rs_edipi: officer.service_number,
            total_reports: officer.total_reports || 0
          });
        }
      } catch (error) {
        console.error('Error fetching officer data:', error);
        setError('Failed to load officer profile');
      }
    };

    fetchOfficerData();
  }, [officerId]);

  const onDrop = (acceptedFiles: File[]) => {
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    setFiles(pdfFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: uploadMode !== 'summary' // Summary mode accepts only 1 file
  });

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleConfirmProfile = () => {
    setShowConfirmation(false);
    handleUpload();
  };

  const handleRejectProfile = () => {
    setShowConfirmation(false);
    navigate('/');
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      if (uploadMode === 'summary') {
        // RS Summary mode
        if (files.length !== 1) {
          setError('Please upload exactly one RS summary list PDF');
          setUploading(false);
          return;
        }

        setCurrentFile('📋 Importing RS summary list...');
        const startTime = Date.now();
        const estimatedTime = 15000;
        setEstimatedTotal(estimatedTime);

        const updateProgress = () => {
          const elapsed = Date.now() - startTime;
          const remaining = Math.max(0, estimatedTime - elapsed);
          setTimeRemaining(remaining);
          const processingProgress = Math.min((elapsed / estimatedTime) * 90, 90);
          setProgress(processingProgress);
        };

        updateProgress();
        const progressInterval = setInterval(updateProgress, 500);

        try {
          await fitreportApi.importRsList(files[0]);
          clearInterval(progressInterval);
          setProgress(100);
          setCurrentFile('✅ RS summary imported successfully!');
          setTimeout(() => {
            setUploading(false);
            navigate(`/profile/${officerId}`);
          }, 1500);
        } catch (err) {
          clearInterval(progressInterval);
          throw err;
        }
      } else {
        // Individual FITREP mode
        setCurrentFile('🔍 Processing individual FITREPs...');
        const startTime = Date.now();
        const estimatedTimePerFile = 9000;
        const totalEstimatedTime = files.length * estimatedTimePerFile;
        setEstimatedTotal(totalEstimatedTime);

        const updateProgress = () => {
          const elapsed = Date.now() - startTime;
          const remaining = Math.max(0, totalEstimatedTime - elapsed);
          setTimeRemaining(remaining);
          const processingProgress = Math.min((elapsed / totalEstimatedTime) * 90, 90);
          setProgress(processingProgress);
        };

        updateProgress();
        const progressInterval = setInterval(updateProgress, 500);

        try {
          await fitreportApi.multiRsUpload(files);
          clearInterval(progressInterval);
          setProgress(100);
          setCurrentFile('✅ FITREPs processed successfully!');
          setTimeout(() => {
            setUploading(false);
            navigate(`/profile/${officerId}`);
          }, 1500);
        } catch (err) {
          clearInterval(progressInterval);
          throw err;
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during upload');
      setUploading(false);
      setProgress(0);
      setCurrentFile('');
      setTimeRemaining(0);
    }
  };

  const formatTime = (milliseconds: number): string => {
    const totalSeconds = Math.ceil(milliseconds / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const handleProceed = () => {
    if (!rsSummary) return;
    setShowConfirmation(true);
  };

  if (!rsSummary && !error) {
    return (
      <div className="container">
        <div className="card">
          <p>Loading RS profile...</p>
        </div>
      </div>
    );
  }

  if (error && !rsSummary) {
    return (
      <div className="container">
        <div className="card">
          <h2>Error Loading Profile</h2>
          <p style={{ color: '#721c24' }}>{error}</p>
          <button onClick={() => navigate('/')} className="btn btn-secondary">
            Return Home
          </button>
        </div>
      </div>
    );
  }

  if (showConfirmation && rsSummary) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>Confirm Profile Update</h2>
          <p style={{ marginBottom: '30px' }}>
            Is this the profile you would like to update?
          </p>

          <div className="card" style={{ backgroundColor: '#f8f9fa', marginBottom: '30px' }}>
            <h3>{rsSummary.rs_name}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
              <div>
                <strong>RS EDIPI</strong>
                <p>{rsSummary.rs_edipi}</p>
              </div>
              <div>
                <strong>Total Reports</strong>
                <p>{rsSummary.total_reports}</p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
            <button
              onClick={handleConfirmProfile}
              className="btn btn-primary"
              style={{ fontSize: '1.1rem', padding: '15px 30px' }}
            >
              Yes, Update This Profile
            </button>
            <button
              onClick={handleRejectProfile}
              className="btn btn-secondary"
              style={{ fontSize: '1.1rem', padding: '15px 30px' }}
            >
              No, Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (uploading) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>Updating Profile</h2>
          <p>Processing {files.length} additional file{files.length > 1 ? 's' : ''}...</p>

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
                backgroundColor: progress === 100 ? '#28a745' : '#CC0000',
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

            {timeRemaining > 0 && (
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '10px' }}>
                Time remaining: {formatTime(timeRemaining)}
              </p>
            )}

            <p style={{ fontSize: '1.1rem' }}>
              {currentFile}
            </p>

            {error && (
              <div style={{
                backgroundColor: '#f8d7da',
                color: '#721c24',
                padding: '15px',
                borderRadius: '5px',
                marginTop: '20px'
              }}>
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!rsSummary) return null;

  return (
    <div className="container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2>Update Profile</h2>
            <p>Add additional FITREP files to: <strong>{rsSummary.rs_name}</strong></p>
          </div>
          <button
            onClick={() => navigate(`/profile/${officerId}`)}
            className="btn btn-secondary"
          >
            Back to Profile
          </button>
        </div>
      </div>

      <div className="card" style={{ backgroundColor: '#f8f9fa' }}>
        <h3>Current RS Profile</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '15px' }}>
          <div style={{ textAlign: 'center' }}>
            <strong>RS Name</strong>
            <p style={{ fontSize: '1.3rem', color: '#003366', margin: '5px 0' }}>{rsSummary.rs_name}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <strong>RS EDIPI</strong>
            <p style={{ fontSize: '1.3rem', color: '#003366', margin: '5px 0' }}>{rsSummary.rs_edipi}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <strong>Total Reports</strong>
            <p style={{ fontSize: '1.3rem', color: '#CC0000', margin: '5px 0' }}>{rsSummary.total_reports}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>🚀 Choose Upload Method</h3>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px', marginBottom: '30px' }}>
          <div
            style={{
              padding: '20px',
              border: uploadMode === 'individual' ? '3px solid #28a745' : '2px solid #ddd',
              borderRadius: '8px',
              cursor: 'pointer',
              backgroundColor: uploadMode === 'individual' ? '#e8f5e8' : '#f8f9fa',
              transition: 'all 0.3s ease'
            }}
            onClick={() => setUploadMode('individual')}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <input
                type="radio"
                checked={uploadMode === 'individual'}
                onChange={() => setUploadMode('individual')}
                style={{ marginRight: '10px' }}
              />
              <h4 style={{ margin: 0, color: '#28a745' }}>📄 Individual FITREPs</h4>
            </div>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>
              Upload individual FITREP PDFs with full trait scores.
            </p>
          </div>

          <div
            style={{
              padding: '20px',
              border: uploadMode === 'summary' ? '3px solid #0066cc' : '2px solid #ddd',
              borderRadius: '8px',
              cursor: 'pointer',
              backgroundColor: uploadMode === 'summary' ? '#e6f2ff' : '#f8f9fa',
              transition: 'all 0.3s ease'
            }}
            onClick={() => setUploadMode('summary')}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <input
                type="radio"
                checked={uploadMode === 'summary'}
                onChange={() => setUploadMode('summary')}
                style={{ marginRight: '10px' }}
              />
              <h4 style={{ margin: 0, color: '#0066cc' }}>📋 RS Summary List</h4>
            </div>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>
              Upload RS summary PDF (synthetic traits, placeholder IDs).
            </p>
          </div>
        </div>

        <h3>Upload Additional FITREP Files</h3>
        
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
          
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>📄</div>
          
          {isDragActive ? (
            <p style={{ fontSize: '1.2rem', color: '#CC0000', fontWeight: 'bold' }}>
              Drop your additional FITREP PDF files here!
            </p>
          ) : (
            <div>
              <p style={{ fontSize: '1.2rem', marginBottom: '10px' }}>
                <strong>Drop additional FITREP PDF files here</strong>
              </p>
              <p style={{ color: '#666' }}>
                or click to browse and select files
              </p>
              <p style={{ fontSize: '0.9rem', color: '#888', marginTop: '15px' }}>
                These files will be added to your existing profile
              </p>
            </div>
          )}
        </div>

        {files.length > 0 && (
          <div style={{ marginTop: '30px' }}>
            <h4>Files to Add ({files.length}):</h4>
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
                onClick={handleProceed}
                className="btn btn-primary"
                style={{ fontSize: '1.1rem', padding: '15px 30px' }}
              >
                Update Profile ({files.length} new files)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UpdateProfilePage;