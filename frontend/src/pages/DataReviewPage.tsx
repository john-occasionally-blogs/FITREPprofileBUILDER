import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fitreportApi } from '../services/api';

interface FitReportData {
  id: number;
  officer_id: number;
  fitrep_id: string;
  last_name?: string;
  first_name?: string;
  rank_at_time: string;
  period_from: string;
  period_to: string;
  fra_score?: number;
  relative_value?: number;
  organization?: string;
  reporting_senior_name?: string;
}

const DataReviewPage: React.FC = () => {
  const [reports, setReports] = useState<FitReportData[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteLoading, setDeleteLoading] = useState<{[key: number]: boolean}>({});

  useEffect(() => {
    fetchAllReports();
  }, []);

  const fetchAllReports = async () => {
    try {
      setLoading(true);
      // Get ALL reports across all officers
      const data = await fitreportApi.getAllReports();
      setReports(data);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (reportId: number) => {
    if (!window.confirm('Are you sure you want to delete this FITREP? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleteLoading(prev => ({ ...prev, [reportId]: true }));
      await fitreportApi.deleteReport(reportId);
      
      // Remove from local state
      setReports(prev => prev.filter(report => report.id !== reportId));
      
      alert('FITREP deleted successfully');
    } catch (error) {
      console.error('Error deleting report:', error);
      alert('Error deleting FITREP');
    } finally {
      setDeleteLoading(prev => ({ ...prev, [reportId]: false }));
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('Are you sure you want to delete ALL FITREPs in the entire database? This action cannot be undone.')) {
      return;
    }

    if (!window.confirm('This will delete ALL FITREP data for ALL Reporting Seniors permanently. Are you absolutely sure?')) {
      return;
    }

    try {
      setLoading(true);
      await fitreportApi.deleteAllReports();

      // Clear local state
      setReports([]);

      alert('All FITREPs deleted successfully');
    } catch (error) {
      console.error('Error deleting all reports:', error);
      alert('Error deleting all FITREPs');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="card">
          <p>Loading FITREP data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2>Data Review & Management</h2>
            <p>Review all FITREPs in the database and delete problematic records</p>
          </div>
          <div>
            <Link to="/" className="btn btn-secondary" style={{ marginRight: '10px' }}>
              Back to Home
            </Link>
            {reports.length > 0 && (
              <button 
                onClick={handleDeleteAll}
                className="btn btn-primary"
                style={{ backgroundColor: '#dc3545' }}
              >
                🗑️ Delete All
              </button>
            )}
          </div>
        </div>
      </div>

      {reports.length === 0 ? (
        <div className="card" style={{ textAlign: 'center' }}>
          <h3>No FITREPs Found</h3>
          <p>There are currently no FITREP records in the database.</p>
          <Link to="/create-profile" className="btn btn-primary">
            Upload FITREPs
          </Link>
        </div>
      ) : (
        <div className="card">
          <h3>All FITREP Records ({reports.length})</h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>FITREP ID</th>
                  <th>Marine Name</th>
                  <th>Rank</th>
                  <th>Period</th>
                  <th>FRA Score</th>
                  <th>RV</th>
                  <th>Reporting Senior</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id}>
                    <td style={{ fontWeight: 'bold' }}>{report.fitrep_id}</td>
                    <td>
                      {report.organization?.replace('Marine: ', '') || 'Unknown'}
                    </td>
                    <td>
                      <span style={{
                        backgroundColor: '#003366',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '0.9rem',
                        fontWeight: 'bold'
                      }}>
                        {report.rank_at_time}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.9rem' }}>
                        {report.period_from} to<br/>{report.period_to}
                      </div>
                    </td>
                    <td>
                      {report.fra_score ?
                        <span style={{ fontWeight: 'bold', color: '#CC0000' }}>
                          {report.fra_score.toFixed(2)}
                        </span> :
                        <span style={{ color: '#666', fontStyle: 'italic' }}>N/A</span>
                      }
                    </td>
                    <td>
                      {report.relative_value ? (
                        <span style={{
                          backgroundColor: report.relative_value >= 90 ? '#28a745' :
                                         report.relative_value >= 85 ? '#ffc107' : '#dc3545',
                          color: report.relative_value >= 85 ? 'white' : 'black',
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
                    <td>{report.reporting_senior_name?.split(',')[0] || 'Unknown'}</td>
                    <td>
                      <button
                        onClick={() => handleDeleteReport(report.id)}
                        disabled={deleteLoading[report.id]}
                        style={{
                          backgroundColor: '#dc3545',
                          color: 'white',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.8rem'
                        }}
                      >
                        {deleteLoading[report.id] ? '⏳' : '🗑️'} Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card" style={{ backgroundColor: '#f8f9fa' }}>
        <h4>Data Management Tips</h4>
        <ul>
          <li><strong>Review Data Quality:</strong> Check for missing names, incorrect ranks, or invalid FRA scores</li>
          <li><strong>Delete Bad Records:</strong> Remove FITREPs that failed to extract properly</li>
          <li><strong>Bulk Cleanup:</strong> Use "Delete All" if you need to start fresh with new uploads</li>
          <li><strong>Re-upload:</strong> After deleting problematic records, re-upload the PDF files</li>
        </ul>
      </div>
    </div>
  );
};

export default DataReviewPage;