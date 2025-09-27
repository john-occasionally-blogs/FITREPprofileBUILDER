import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ProfileData } from '../types';
import { profileApi, scoringApi } from '../services/api';
import { LETTER_TO_NUMERIC } from '../utils/scoring';

// 14 trait names in order
const TRAIT_NAMES = [
  "Mission Accomplishment", "Proficiency", "Individual Character",
  "Effectiveness Under Stress", "Initiative", "Leadership", 
  "Developing Subordinates", "Setting the Example",
  "Ensuring Well-being of Subordinates", "Communication Skills",
  "Intellect and Wisdom", "Decision Making Ability", "Judgment",
  "Fulfillment of Evaluation Responsibilities"
];

// Helper function to get color for trait scores
const getTraitColor = (grade: string): string => {
  switch (grade) {
    case 'A': return '#28a745'; // Green
    case 'B': return '#17a2b8'; // Teal  
    case 'C': return '#ffc107'; // Yellow
    case 'D': return '#fd7e14'; // Orange
    case 'E': return '#dc3545'; // Red
    case 'F': return '#6f42c1'; // Purple
    case 'G': return '#343a40'; // Dark gray
    case 'H': return '#6c757d'; // Gray (Non-observed)
    default: return '#fd7e14'; // Default orange
  }
};

// Helper function to get RV color based on user's requirements
const getRVColor = (rv: number): string => {
  if (rv >= 93.3) return '#28a745'; // Green
  if (rv >= 86.6) return '#ffc107'; // Yellow
  if (rv >= 80) return '#dc3545';   // Red
  return '#6c757d'; // Gray for edge cases
};

const ProfileViewPage: React.FC = () => {
  const { officerId } = useParams<{ officerId: string }>();
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [selectedRank, setSelectedRank] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [expandedView, setExpandedView] = useState(false);
  const [sortBy, setSortBy] = useState<'date' | 'rv'>('date');
  const [showWhatIfModal, setShowWhatIfModal] = useState(false);
  const [hypotheticalReports, setHypotheticalReports] = useState<Array<{id: string; marineName: string; traitScores: {[key: string]: string}}>>([]);
  const [whatIfResults, setWhatIfResults] = useState<any>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        setLoading(true);
        const data = await profileApi.getProfile(parseInt(officerId || '1'));
        setProfileData(data);
        // Set initial selected rank to the officer's current rank or first available rank
        const availableRanks = Object.keys(data.rank_breakdown);
        setSelectedRank(availableRanks.includes(data.officer_info.rank) ? 
          data.officer_info.rank : 
          availableRanks[0] || ''
        );
      } catch (error) {
        console.error('Error fetching profile data:', error);
        // Keep loading false to show error state
      } finally {
        setLoading(false);
      }
    };

    if (officerId) {
      fetchProfileData();
    }
  }, [officerId]);

  if (loading) {
    return (
      <div className="container">
        <div className="card">
          <p>Loading profile data...</p>
        </div>
      </div>
    );
  }

  if (!profileData) {
    return (
      <div className="container">
        <div className="card">
          <h2>Profile Not Found</h2>
          <p>The requested profile could not be loaded.</p>
          <Link to="/" className="btn btn-primary">Return Home</Link>
        </div>
      </div>
    );
  }

  const selectedRankData = profileData.rank_breakdown[selectedRank];

  return (
    <div className="container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2>{profileData.officer_info.name.split(',')[0]}</h2>
            <p>Total Reports: {profileData.officer_info.total_reports}</p>
          </div>
          <div>
            <Link to="/update-profile/1" className="btn btn-secondary" style={{ marginRight: '10px' }}>
              Add Reports
            </Link>
            <Link to="/" className="btn btn-primary">Home</Link>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Select Rank to Analyze</h3>
        <div style={{ marginBottom: '20px' }}>
          <select 
            value={selectedRank} 
            onChange={(e) => setSelectedRank(e.target.value)}
            style={{ padding: '8px 12px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ddd' }}
          >
            {Object.keys(profileData.rank_breakdown).map(rank => (
              <option key={rank} value={rank}>{rank}</option>
            ))}
          </select>
        </div>

        {selectedRankData && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
              <div style={{ 
                textAlign: 'center', 
                backgroundColor: '#ffffff', 
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                padding: '24px',
                marginBottom: '20px'
              }}>
                <h4 style={{ color: '#000000 !important', margin: '0 0 10px 0', fontWeight: 'bold' }}>Total Reports</h4>
                <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#000000 !important', margin: '10px 0' }}>
                  {selectedRankData.total_reports}
                </p>
              </div>
              <div style={{ 
                textAlign: 'center', 
                backgroundColor: '#ffffff', 
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                padding: '24px',
                marginBottom: '20px'
              }}>
                <h4 style={{ color: '#000000', margin: '0 0 10px 0' }}>Average FRA</h4>
                <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#CC0000', margin: '10px 0' }}>
                  {selectedRankData.average_fra.toFixed(2)}
                </p>
              </div>
              <div style={{ 
                textAlign: 'center', 
                backgroundColor: '#ffffff', 
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                padding: '24px',
                marginBottom: '20px'
              }}>
                <h4 style={{ color: '#000000 !important', margin: '0 0 10px 0', fontWeight: 'bold' }}>Range</h4>
                <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#000000 !important', margin: '10px 0' }}>
                  {selectedRankData.lowest_fra.toFixed(2)} - {selectedRankData.highest_fra.toFixed(2)}
                </p>
              </div>
            </div>

            <div style={{ marginBottom: '30px', textAlign: 'center' }}>
              <button 
                onClick={() => setExpandedView(!expandedView)}
                className="btn btn-secondary"
                style={{ marginRight: '10px' }}
              >
                {expandedView ? '📊 Summary View' : '🔍 Expanded Trait View'}
              </button>
              <span style={{ color: '#666', fontSize: '0.9rem' }}>
                {expandedView ? 'Switch to condensed view' : 'Show all 14 trait scores for comparison'}
              </span>
            </div>

{expandedView ? (
            (() => {
              // Collect all reports for the selected rank and filter them properly
              const allRankReports = profileData.marines.flatMap((marine, marineIndex) => 
                marine.fitreports
                  .filter(report => report.rank_at_time === selectedRank)
                  .map((report, reportIndex) => {
                    // Check if we have updated RV values from what-if scenario
                    let updatedRV = report.relative_value;
                    if (whatIfResults && whatIfResults.updated_existing_reports) {
                      console.log(`DEBUG: Looking for RV update for report ${report.fitrep_id}`);
                      console.log('DEBUG: Available updates:', whatIfResults.updated_existing_reports);
                      
                      const rvUpdate = whatIfResults.updated_existing_reports.find((update: any) => 
                        update.fitrep_id === report.fitrep_id
                      );
                      if (rvUpdate) {
                        console.log(`DEBUG: Found RV update for ${report.fitrep_id}: ${report.relative_value} -> ${rvUpdate.updated_rv}`);
                        updatedRV = rvUpdate.updated_rv;
                      } else {
                        console.log(`DEBUG: No RV update found for ${report.fitrep_id}`);
                      }
                    }

                    return {
                      ...report,
                      marineName: report.organization?.replace('Marine: ', '') || 'Unknown Marine',
                      relative_value: updatedRV,
                      isHypothetical: false
                    };
                  })
              );

              // Add hypothetical reports with calculated FRA and predicted RV
              const hypotheticalReportsWithCalculations = hypotheticalReports.map((hypReport, hypIndex) => {
                // Calculate FRA for this hypothetical report
                const fraSum = TRAIT_NAMES.reduce((sum, trait) => {
                  const score = hypReport.traitScores[trait];
                  if (score === 'H') return sum; // Skip non-observed
                  return sum + (LETTER_TO_NUMERIC[score] || 0);
                }, 0);
                
                const observedTraits = TRAIT_NAMES.filter(trait => hypReport.traitScores[trait] !== 'H').length;
                const fra = observedTraits > 0 ? fraSum / observedTraits : 0;

                // For now, show a predicted RV based on what-if results if available
                let predictedRV = null;
                if (whatIfResults && whatIfResults.new_reports && whatIfResults.new_reports[hypIndex]) {
                  predictedRV = whatIfResults.new_reports[hypIndex]?.predicted_rv || null;
                }

                return {
                  fitrep_id: hypReport.id,
                  marineName: hypReport.marineName,
                  period_to: new Date().toISOString().split('T')[0], // Today's date as placeholder
                  fra_score: parseFloat(fra.toFixed(2)),
                  relative_value: predictedRV,
                  trait_scores: TRAIT_NAMES.map(trait => ({
                    trait_name: trait,
                    score_letter: hypReport.traitScores[trait]
                  })),
                  isHypothetical: true
                };
              });

              // Combine real and hypothetical reports
              const allReports = [...allRankReports, ...hypotheticalReportsWithCalculations];

              // Sort all reports based on sortBy preference
              const sortedReports = [...allReports].sort((a, b) => {
                if (sortBy === 'date') {
                  return new Date(a.period_to || '').getTime() - new Date(b.period_to || '').getTime();
                } else {
                  return (b.relative_value || 0) - (a.relative_value || 0);
                }
              });

              return (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h3>Spreadsheet View - All {selectedRank} Reports</h3>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      <label style={{ fontSize: '14px' }}>
                        Sort by: 
                        <select 
                          value={sortBy} 
                          onChange={(e) => setSortBy(e.target.value as 'date' | 'rv')}
                          style={{ marginLeft: '5px', padding: '4px 8px' }}
                        >
                          <option value="date">End Date</option>
                          <option value="rv">Relative Value</option>
                        </select>
                      </label>
                      <button 
                        onClick={() => setShowWhatIfModal(true)}
                        className="btn btn-success"
                        style={{ fontSize: '14px', marginRight: '10px' }}
                      >
                        + Add Potential Reports
                      </button>
                      {hypotheticalReports.length > 0 && (
                        <button 
                          onClick={() => {
                            setHypotheticalReports([]);
                            setWhatIfResults(null);
                          }}
                          className="btn btn-warning"
                          style={{ fontSize: '14px' }}
                        >
                          Clear What-If
                        </button>
                      )}
                    </div>
                  </div>

                  {whatIfResults && (
                    <div style={{ 
                      backgroundColor: '#e7f3ff', 
                      border: '1px solid #b8daff', 
                      borderRadius: '8px', 
                      padding: '15px', 
                      marginBottom: '20px' 
                    }}>
                      <h4 style={{ margin: '0 0 10px 0', color: '#0056b3' }}>What-If Impact Analysis</h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
                        <div>
                          <strong>Current Average FRA:</strong> {
                            typeof whatIfResults.current?.average_fra === 'number' && whatIfResults.current.average_fra > 0 
                              ? whatIfResults.current.average_fra.toFixed(2) 
                              : selectedRankData?.average_fra?.toFixed(2) || 'N/A'
                          }
                        </div>
                        <div>
                          <strong>Predicted Average FRA:</strong> 
                          <span style={{ 
                            color: whatIfResults.predicted?.fra_change > 0 ? '#28a745' : '#dc3545',
                            marginLeft: '5px'
                          }}>
                            {typeof whatIfResults.predicted?.average_fra === 'number' ? whatIfResults.predicted.average_fra.toFixed(2) : 'N/A'}
                            {whatIfResults.predicted?.fra_change !== undefined && typeof whatIfResults.predicted.fra_change === 'number' && (
                              <span style={{ fontSize: '12px' }}>
                                ({whatIfResults.predicted.fra_change > 0 ? '+' : ''}{whatIfResults.predicted.fra_change.toFixed(2)})
                              </span>
                            )}
                          </span>
                        </div>
                        <div>
                          <strong>Total Reports:</strong> {whatIfResults.current?.total_reports || 0} → {whatIfResults.predicted?.total_reports || 0}
                        </div>
                      </div>
                    </div>
                  )}

                  <div style={{ overflowX: 'auto' }}>
                    <table className="table" style={{ margin: 0, minWidth: '1400px', fontSize: '13px' }}>
                      <thead>
                        <tr style={{ backgroundColor: '#f8f9fa', color: '#000000' }}>
                          <th style={{ minWidth: '120px' }}>Marine Name</th>
                          <th style={{ minWidth: '90px' }}>End Date</th>
                          <th style={{ minWidth: '60px' }}>FRA</th>
                          <th style={{ minWidth: '50px' }}>RV</th>
                          {TRAIT_NAMES.map(trait => (
                            <th key={trait} style={{ 
                              minWidth: '45px', 
                              fontSize: '11px', 
                              textAlign: 'center',
                              padding: '8px 4px',
                              writingMode: 'vertical-rl',
                              textOrientation: 'mixed',
                              maxWidth: '45px'
                            }}>
                              {trait.split(' ').map(word => word.slice(0, 3)).join(' ')}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sortedReports.map((report, index) => {
                          // Check if this is an EN (End of Active Service) report
                          const isENReport = (report as any).occasion_type && (report as any).occasion_type.toUpperCase() === 'EN';
                          
                          return (
                          <tr key={`${report.fitrep_id}-${index}`} style={{ 
                            backgroundColor: index % 2 === 0 ? 'white' : '#f9f9f9',
                            opacity: report.isHypothetical ? 0.8 : (isENReport ? 0.7 : 1),
                            borderLeft: report.isHypothetical ? '4px solid #ffc107' : (isENReport ? '4px solid #6c757d' : 'none'),
                            fontStyle: isENReport ? 'italic' : 'normal'
                          }}>
                            <td style={{ fontWeight: 'bold', fontSize: '12px' }}>
                              {report.marineName}
                              {report.isHypothetical && <span style={{ color: '#ffc107', marginLeft: '5px' }}>*</span>}
                              {isENReport && <span style={{ color: '#6c757d', marginLeft: '5px', fontSize: '10px' }}>(EN)</span>}
                            </td>
                            <td style={{ fontSize: '11px' }}>
                              {report.period_to ? new Date(report.period_to).toLocaleDateString() : 'N/A'}
                            </td>
                            <td>
                              <span style={{ fontWeight: 'bold', color: '#CC0000' }}>
                                {typeof report.fra_score === 'number' ? report.fra_score.toFixed(2) : 'N/A'}
                              </span>
                            </td>
                            <td>
                              {report.relative_value ? (
                                <span style={{
                                  backgroundColor: getRVColor(report.relative_value),
                                  color: 'white',
                                  padding: '2px 6px',
                                  borderRadius: '3px',
                                  fontWeight: 'bold',
                                  fontSize: '11px'
                                }}>
                                  {report.relative_value}
                                </span>
                              ) : 'N/A'}
                            </td>
                            {TRAIT_NAMES.map(traitName => {
                              const trait = report.trait_scores?.find(t => t.trait_name === traitName);
                              const score = trait?.score_letter || 'H';
                              return (
                                <td key={traitName} style={{ textAlign: 'center', padding: '4px' }}>
                                  <span style={{
                                    backgroundColor: getTraitColor(score),
                                    color: score === 'H' ? '#666' : 'white',
                                    padding: '3px 5px',
                                    borderRadius: '3px',
                                    fontWeight: 'bold',
                                    fontSize: '11px',
                                    border: score === 'H' ? '1px solid #ccc' : 'none',
                                    display: 'inline-block',
                                    minWidth: '20px'
                                  }}>
                                    {score}
                                  </span>
                                </td>
                              );
                            })}
                          </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666', marginTop: '15px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
                    <div>
                      <strong>Trait Legend:</strong> A=Adverse, B=Excellent, C=Above Avg, D=Average, E=Below Avg, F=Unsat, G=Unacceptable, H=Not Observed
                    </div>
                    <div>
                      <strong>RV Colors:</strong> <span style={{backgroundColor: '#28a745', color: 'white', padding: '2px 4px', borderRadius: '2px'}}>≥93.3</span> <span style={{backgroundColor: '#ffc107', color: 'black', padding: '2px 4px', borderRadius: '2px'}}>86.6-93.2</span> <span style={{backgroundColor: '#dc3545', color: 'white', padding: '2px 4px', borderRadius: '2px'}}>80-86.5</span>
                      <br />
                      <strong>Indicators:</strong> * = Hypothetical | (EN) = End of Active Service (excluded from RS statistics)
                    </div>
                  </div>
                </div>
              );
            })()
          ) : (
              <div>
                <h3>Individual Reports for {selectedRank}</h3>
                <table className="table">
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa', color: '#000000' }}>
                  <th style={{ color: '#000000 !important' }}>Marine</th>
                  <th style={{ color: '#000000 !important' }}>End Date</th>
                  <th style={{ color: '#000000 !important' }}>FRA Score</th>
                  <th style={{ color: '#000000 !important' }}>Relative Value</th>
                  <th style={{ color: '#000000 !important' }}>Reporting Senior</th>
                </tr>
              </thead>
              <tbody>
                {selectedRankData.reports.map((report) => (
                  <tr key={report.fitrep_id}>
                    <td>{report.organization?.replace('Marine: ', '') || 'Unknown'}</td>
                    <td>{report.period?.split(' to ')[1] || report.period || 'Unknown'}</td>
                    <td style={{ fontWeight: 'bold' }}>{typeof report.fra_score === 'number' ? report.fra_score.toFixed(2) : 'N/A'}</td>
                    <td>
                      {report.relative_value ? (
                        <span style={{ 
                          backgroundColor: getRVColor(report.relative_value),
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontWeight: 'bold'
                        }}>
                          {report.relative_value}
                        </span>
                      ) : (
                        <span style={{ color: '#666', fontStyle: 'italic' }}>N/A</span>
                      )}
                    </td>
                    <td>{report.reporting_senior?.split(',')[0] || 'Unknown'}</td>
                  </tr>
                ))}
              </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      {/* What-If Modal */}
      {showWhatIfModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '30px',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflowY: 'auto',
            width: '90%'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>Add Hypothetical {selectedRank} Reports</h3>
              <button 
                onClick={() => setShowWhatIfModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer' }}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <button 
                onClick={() => {
                  const newId = `hyp-${Date.now()}`;
                  const defaultScores = TRAIT_NAMES.reduce((acc, trait) => {
                    acc[trait] = 'D';
                    return acc;
                  }, {} as {[key: string]: string});
                  
                  setHypotheticalReports([...hypotheticalReports, {
                    id: newId,
                    marineName: `Marine ${hypotheticalReports.length + 1}`,
                    traitScores: defaultScores
                  }]);
                }}
                className="btn btn-success"
              >
                + Add Another Report
              </button>
            </div>

            {hypotheticalReports.map((report, reportIndex) => (
              <div key={report.id} style={{ 
                border: '1px solid #ddd', 
                borderRadius: '8px', 
                padding: '20px', 
                marginBottom: '20px',
                backgroundColor: '#f8f9fa'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                  <input
                    type="text"
                    value={report.marineName}
                    onChange={(e) => {
                      const updated = [...hypotheticalReports];
                      updated[reportIndex].marineName = e.target.value;
                      setHypotheticalReports(updated);
                    }}
                    style={{ 
                      fontWeight: 'bold', 
                      fontSize: '16px',
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                    placeholder="Marine Name"
                  />
                  <button
                    onClick={() => {
                      setHypotheticalReports(hypotheticalReports.filter(r => r.id !== report.id));
                    }}
                    style={{ 
                      backgroundColor: '#dc3545', 
                      color: 'white', 
                      border: 'none', 
                      padding: '5px 10px', 
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Remove
                  </button>
                </div>

                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                  gap: '15px' 
                }}>
                  {TRAIT_NAMES.map(trait => (
                    <div key={trait} style={{ display: 'flex', flexDirection: 'column' }}>
                      <label style={{ fontSize: '12px', marginBottom: '5px', fontWeight: '500' }}>
                        {trait}
                      </label>
                      <select
                        value={report.traitScores[trait] || 'D'}
                        onChange={(e) => {
                          const updated = [...hypotheticalReports];
                          updated[reportIndex].traitScores[trait] = e.target.value;
                          setHypotheticalReports(updated);
                        }}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '4px',
                          border: '1px solid #ddd',
                          fontSize: '14px'
                        }}
                      >
                        <option value="A">A - Adverse</option>
                        <option value="B">B</option>
                        <option value="C">C</option>
                        <option value="D">D</option>
                        <option value="E">E</option>
                        <option value="F">F</option>
                        <option value="G">G</option>
                        <option value="H">H - Not Observed</option>
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
              <button 
                onClick={() => {
                  setHypotheticalReports([]);
                  setShowWhatIfModal(false);
                }}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={async () => {
                  if (hypotheticalReports.length === 0) {
                    setShowWhatIfModal(false);
                    return;
                  }

                  setIsCalculating(true);
                  try {
                    // Get the RS name from profileData and format it to match database format
                    // Database stores as "LAST, FIRST" but profile returns "LAST, FIRST MIDDLE"
                    let rsName = profileData?.officer_info.name || '';
                    if (rsName) {
                      // Convert "LAST, FIRST MIDDLE" to "LAST, FIRST" 
                      const parts = rsName.split(', ');
                      if (parts.length >= 2) {
                        const lastName = parts[0];
                        const firstAndMiddle = parts[1].split(' ');
                        const firstName = firstAndMiddle[0];
                        rsName = `${lastName}, ${firstName}`;
                      }
                    }
                    
                    // Convert hypothetical reports to the format expected by the API
                    const proposedReports = hypotheticalReports.map(report => report.traitScores);
                    
                    // Call the predict impact API
                    const impactResult = await scoringApi.predictImpact({
                      officer_id: parseInt(officerId || '1'),
                      rank: selectedRank,
                      reporting_senior: rsName,
                      proposed_reports: proposedReports
                    });
                    
                    console.log('DEBUG: What-if results received:', impactResult);
                    console.log('DEBUG: Updated existing reports:', impactResult.updated_existing_reports);
                    setWhatIfResults(impactResult);
                    setShowWhatIfModal(false);
                  } catch (error) {
                    console.error('Error calculating what-if scenario:', error);
                    alert('Error calculating what-if scenario. Please try again.');
                  } finally {
                    setIsCalculating(false);
                  }
                }}
                className="btn btn-primary"
                disabled={isCalculating || hypotheticalReports.length === 0}
              >
                {isCalculating ? 'Calculating...' : 'Apply What-If Scenario'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileViewPage;