import React, { useState, useEffect } from 'react';
import StatusBar from './StatusBar';
import UserList from './UserList';
import AudioPlayer from './AudioPlayer';
import ConnectionStatus from './ConnectionStatus';
import ApiService from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  // State Management
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [selectedUser, setSelectedUser] = useState(null);
  const [currentAudio, setCurrentAudio] = useState(null);

  // Polling function
  const fetchDashboardData = async () => {
    try {
      // First check if server is healthy
      try {
        await ApiService.getHealthCheck();
      } catch (healthError) {
        console.warn('Health check failed, but attempting dashboard data fetch...');
      }
      
      const data = await ApiService.getDashboardData();
      setDashboardData(data);
      setConnectionStatus(data.connection_status || 'connected');
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err.message);
      setConnectionStatus('error');
    } finally {
      setLoading(false);
    }
  };

  // Real-time Polling with 2-second intervals
  useEffect(() => {
    let pollInterval;
    
    if (isPolling) {
      // Initial fetch
      fetchDashboardData();
      
      // Set up polling
      pollInterval = setInterval(fetchDashboardData, 2000);
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [isPolling]);

  // Handle user actions
  const handleStartListening = async (userId) => {
    try {
      await ApiService.startListening(userId);
      // Refresh data to get updated status
      await fetchDashboardData();
    } catch (err) {
      console.error('Failed to start listening:', err);
    }
  };

  const handleStopListening = async (userId) => {
    try {
      await ApiService.stopListening(userId);
      // Refresh data to get updated status
      await fetchDashboardData();
    } catch (err) {
      console.error('Failed to stop listening:', err);
    }
  };

  const handlePlayAudio = async (user) => {
    try {
      if (user.latest_audio) {
        // Use API service base URL for consistency
        const apiBaseUrl = process.env.NODE_ENV === 'production' 
          ? 'http://143.244.133.125:5000' 
          : 'http://localhost:5000';
        setCurrentAudio({
          url: `${apiBaseUrl}${user.latest_audio}`,
          user: user.user_id,
          filename: user.latest_audio.split('/').pop()
        });
      }
    } catch (err) {
      console.error('Failed to play audio:', err);
    }
  };

  const handleCloseAudio = () => {
    setCurrentAudio(null);
  };

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  if (loading && !dashboardData) {
    return (
      <div className="dashboard dark-theme">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading BUAS Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard dark-theme">
      {/* Dashboard Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🦇 BUAS Dashboard</h1>
          <div className="dashboard-controls">
            <button 
              className={`polling-toggle ${isPolling ? 'active' : ''}`}
              onClick={togglePolling}
            >
              {isPolling ? '⏸️' : '▶️'} 
              {isPolling ? 'Pause Updates' : 'Resume Updates'}
            </button>
            <div className="polling-indicator">
              <span className={`indicator-dot ${isPolling ? 'active' : ''}`}></span>
              <span>Live Updates</span>
            </div>
          </div>
        </div>
      </header>

      {/* Status Bar */}
      <StatusBar 
        data={dashboardData}
        connectionStatus={connectionStatus}
        lastUpdated={lastUpdated}
        error={error}
      />

      {/* Main Content */}
      <main className="dashboard-content">
        <div className="dashboard-main">
          {/* Connection Status */}
          <ConnectionStatus 
            status={connectionStatus}
            lastUpdated={lastUpdated}
            isPolling={isPolling}
          />

          {/* User List */}
          <UserList 
            users={dashboardData?.users || []}
            loading={loading}
            onPlayAudio={handlePlayAudio}
            onStartListening={handleStartListening}
            onStopListening={handleStopListening}
            selectedUser={selectedUser}
            onUserSelect={setSelectedUser}
          />
        </div>
      </main>

      {/* Audio Player Overlay */}
      {currentAudio && (
        <AudioPlayer 
          audio={currentAudio}
          onClose={handleCloseAudio}
        />
      )}

      {/* Footer */}
      <footer className="dashboard-footer">
        <div className="footer-content">
          <p>BUAS Dashboard v1.0.0 | Last Updated: {lastUpdated?.toLocaleTimeString()}</p>
          <p>Connected Users: {dashboardData?.total_users || 0} | Active Sessions: {dashboardData?.active_sessions_count || 0}</p>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
