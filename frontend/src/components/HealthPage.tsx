import React, { useEffect } from 'react';
import { useHealthService } from '../hooks/useHealthService';

const HealthPage: React.FC = () => {
  const { healthData, loading, error, fetchHealth } = useHealthService();

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'ok':
        return 'status-ok';
      case 'error':
        return 'status-error';
      default:
        return 'status-warning';
    }
  };

  const getCerbosStatusClass = (ok: boolean) => {
    return ok ? 'status-ok' : 'status-error';
  };

  return (
    <div className="page">
      <h1 className="page-title">System Health</h1>
      <p className="page-description">
        Monitor the health status of all system components including the API, database, and external services.
      </p>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button 
          onClick={fetchHealth} 
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Health'}
        </button>
      </div>

      {loading && <div className="spinner"></div>}

      {error && (
        <div className="card" style={{ border: '1px solid #dc3545', backgroundColor: '#f8d7da' }}>
          <h3 className="card-title" style={{ color: '#dc3545' }}>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {healthData && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          <div className="card">
            <h3 className="card-title">Overall Status</h3>
            <p>
              <strong>Status:</strong> 
              <span className={getStatusClass(healthData.status)}> {healthData.status}</span>
            </p>
            <p><strong>Environment:</strong> {healthData.env}</p>
            <p><strong>Debug Mode:</strong> {healthData.debug ? 'Enabled' : 'Disabled'}</p>
          </div>

          <div className="card">
            <h3 className="card-title">Cerbos Authorization Service</h3>
            <p>
              <strong>Status:</strong> 
              <span className={getCerbosStatusClass(healthData.cerbos.ok)}>
                {healthData.cerbos.ok ? ' Connected' : ' Disconnected'}
              </span>
            </p>
            <p><strong>Host:</strong> {healthData.cerbos.host}</p>
            {healthData.cerbos.error && (
              <p><strong>Error:</strong> <span className="status-error">{healthData.cerbos.error}</span></p>
            )}
          </div>

          <div className="card">
            <h3 className="card-title">System Information</h3>
            <p><strong>API Version:</strong> v1.0.0</p>
            <p><strong>Frontend Version:</strong> v1.0.0</p>
            <p><strong>Last Updated:</strong> {new Date().toLocaleString()}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthPage;
