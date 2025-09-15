import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { ProfileSummary } from '../types';

const UpdateProfilePage: React.FC = () => {
  const { officerId } = useParams<{ officerId: string }>();
  const navigate = useNavigate();
  const [profileSummary, setProfileSummary] = useState<ProfileSummary | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);

  useEffect(() => {
    // Mock profile data - replace with API call
    const mockProfile: ProfileSummary = {
      officer_name: "SMITH, JOHN A",
      current_rank: "CAPT",
      total_reports: 15,
      latest_fra: 3.6,
      latest_rv: 95
    };
    
    setTimeout(() => {
      setProfileSummary(mockProfile);
    }, 500);
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
    multiple: true
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

    // Simulate file processing
    for (let i = 0; i < files.length; i++) {
      setCurrentFile(files[i].name);
      setProgress((i / files.length) * 100);
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    setProgress(100);
    
    // Simulate completion delay
    setTimeout(() => {
      setUploading(false);
      navigate(`/profile/${officerId}`);
    }, 2000);
  };

  const handleProceed = () => {
    if (!profileSummary) return;
    setShowConfirmation(true);
  };

  if (!profileSummary) {
    return (
      <div className="container">
        <div className="card">
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (showConfirmation) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>Confirm Profile Update</h2>
          <p style={{ marginBottom: '30px' }}>
            Is this the profile you would like to update?
          </p>
          
          <div className="card" style={{ backgroundColor: '#f8f9fa', marginBottom: '30px' }}>
            <h3>{profileSummary.officer_name}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginTop: '20px' }}>
              <div>
                <strong>Current Rank</strong>
                <p>{profileSummary.current_rank}</p>
              </div>
              <div>
                <strong>Total Reports</strong>
                <p>{profileSummary.total_reports}</p>
              </div>
              <div>
                <strong>Latest FRA</strong>
                <p>{profileSummary.latest_fra.toFixed(2)}</p>
              </div>
              <div>
                <strong>Latest RV</strong>
                <p>{profileSummary.latest_rv}</p>
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
          <p>Processing {files.length} additional FITREP files...</p>
          
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
            
            <p>
              {progress === 100 ? 
                '✅ Update complete! Redirecting to your updated profile...' : 
                `Processing: ${currentFile}`
              }
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2>Update Profile</h2>
            <p>Add additional FITREP files to: <strong>{profileSummary.officer_name}</strong></p>
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
        <h3>Current Profile Summary</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '20px', marginTop: '15px' }}>
          <div style={{ textAlign: 'center' }}>
            <strong>Current Rank</strong>
            <p style={{ fontSize: '1.5rem', color: '#003366', margin: '5px 0' }}>{profileSummary.current_rank}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <strong>Total Reports</strong>
            <p style={{ fontSize: '1.5rem', color: '#003366', margin: '5px 0' }}>{profileSummary.total_reports}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <strong>Latest FRA</strong>
            <p style={{ fontSize: '1.5rem', color: '#CC0000', margin: '5px 0' }}>{profileSummary.latest_fra.toFixed(2)}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <strong>Latest RV</strong>
            <p style={{ fontSize: '1.5rem', color: '#FFD700', margin: '5px 0' }}>{profileSummary.latest_rv}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Add Additional FITREP Files</h3>
        
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