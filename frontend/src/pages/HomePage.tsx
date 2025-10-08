import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { officerApi } from '../services/api';

const HomePage: React.FC = () => {
  const location = useLocation();
  const [autoProfileId, setAutoProfileId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rsProfiles, setRsProfiles] = useState<Array<{id: number, name: string, rank: string, fitrep_count: number}> | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showRegularMenu, setShowRegularMenu] = useState(false);

  const checkForExistingProfiles = async () => {
    try {
      const officers = await officerApi.getOfficers();
      if (officers.length === 1) {
        setAutoProfileId(officers[0].id);
      } else if (officers.length > 1) {
        // Multiple RS profiles exist, show them for selection
        const rsProfiles = officers.map(officer => ({
          id: officer.id,
          name: officer.last_name,
          rank: officer.current_rank,
          fitrep_count: officer.total_reports || 0
        }));
        setRsProfiles(rsProfiles);
      }
    } catch (error) {
      console.log('No existing profiles found');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Check if we came from multi-RS upload with profile data
    if (location.state && (location.state as any).rsProfiles) {
      setRsProfiles((location.state as any).rsProfiles);
      setSuccessMessage((location.state as any).message);
      setIsLoading(false);
      return;
    }

    checkForExistingProfiles();
  }, [location.state]);
  return (
    <div className="container">
      <div className="home-screen">
        <div className="card" style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h2>Welcome to the FITREP Assistance Tool</h2>
          <p>
            This tool helps Marine Corps officers manage their FITREP profiles and 
            predict the impact of new reports before finalizing them.
          </p>
        </div>

        {successMessage && (
          <div className="card" style={{ backgroundColor: '#d4edda', borderColor: '#c3e6cb', marginBottom: '20px' }}>
            <h3 style={{ color: '#155724', marginBottom: '15px' }}>✅ Success!</h3>
            <p style={{ color: '#155724', marginBottom: '0' }}>{successMessage}</p>
          </div>
        )}

        {showRegularMenu && rsProfiles && (
          <div className="home-buttons" style={{ marginBottom: '40px' }}>
            <Link to="/create-profile" className="home-button btn-primary">
              <div className="home-button-icon">📁</div>
              <div>
                <div>Create New Profile</div>
                <small>Upload FITREPs to create new reporting senior profile</small>
              </div>
            </Link>
          </div>
        )}

        {rsProfiles && (
          <div className="card" style={{ marginBottom: '40px' }}>
            <h3>Select a Reporting Senior Profile to View</h3>
            <p>Multiple Reporting Senior profiles were created from your uploaded FITREPs. Choose one to analyze:</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
              {rsProfiles.map((profile) => (
                <Link
                  key={profile.id}
                  to={`/profile/${profile.id}`}
                  className="home-button btn-primary"
                  style={{ textDecoration: 'none', backgroundColor: '#CC0000' }}
                >
                  <div className="home-button-icon">👤</div>
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{profile.name}</div>
                    <small>{profile.fitrep_count} FITREPs</small>
                  </div>
                </Link>
              ))}
            </div>

            {!showRegularMenu && (
              <div style={{ textAlign: 'center', marginTop: '20px' }}>
                <button
                  onClick={() => {
                    setShowRegularMenu(true);
                    setSuccessMessage(null);
                  }}
                  className="btn btn-secondary"
                  style={{ padding: '10px 20px' }}
                >
                  Continue with Regular Menu
                </button>
              </div>
            )}
          </div>
        )}
        
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p>Checking for existing profiles...</p>
          </div>
        ) : rsProfiles ? null : (
          <div className="home-buttons">
            <Link to="/create-profile" className="home-button btn-primary">
              <div className="home-button-icon">📁</div>
              <div>
                <div>Create New Profile</div>
                <small>Upload FITREPs to create initial profile</small>
              </div>
            </Link>

            {autoProfileId && (
              <>
                <Link to={`/profile/${autoProfileId}`} className="home-button btn-secondary">
                  <div className="home-button-icon">📊</div>
                  <div>
                    <div>View My Profile</div>
                    <small>Continue with existing profile analysis</small>
                  </div>
                </Link>

                <Link to={`/update-profile/${autoProfileId}`} className="home-button marine-gold" style={{ color: '#000' }}>
                  <div className="home-button-icon">📝</div>
                  <div>
                    <div>Update Profile</div>
                    <small>Add additional reports to existing profile</small>
                  </div>
                </Link>
              </>
            )}

            {!autoProfileId && (
              <div className="home-button" style={{ opacity: 0.6, cursor: 'not-allowed', backgroundColor: '#e9ecef' }}>
                <div className="home-button-icon">📊</div>
                <div>
                  <div>No Profile Found</div>
                  <small>Create a profile first to view or update</small>
                </div>
              </div>
            )}
          </div>
        )}
        
        <div className="card" style={{ marginTop: '40px', backgroundColor: '#f8f9fa' }}>
          <h3>How It Works</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
            <div>
              <strong>1. Upload FITREPs</strong>
              <p>Drag and drop your PDF FITREP files</p>
            </div>
            <div>
              <strong>2. View Analysis</strong>
              <p>See your FRA and RV scores by rank</p>
            </div>
            <div>
              <strong>3. Predict Impact</strong>
              <p>Test how new reports affect your profile</p>
            </div>
          </div>
        </div>
        
        {/* Data Review Button - Bottom Right */}
        <div style={{ 
          position: 'fixed', 
          bottom: '30px', 
          right: '30px',
          zIndex: 1000
        }}>
          <Link 
            to="/data-review" 
            className="btn"
            style={{
              backgroundColor: '#6c757d',
              color: 'white',
              borderRadius: '50px',
              padding: '15px 20px',
              fontSize: '16px',
              fontWeight: 'bold',
              textDecoration: 'none',
              boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            🗂️ Data Review
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;