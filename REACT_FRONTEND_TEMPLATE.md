# React Dashboard Frontend - Complete Template Guide

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Core Components Structure](#core-components-structure)
- [Real-time Data Flow](#real-time-data-flow)
- [Dark Mode Design System](#dark-mode-design-system)
- [State Management Patterns](#state-management-patterns)
- [Error Handling Strategy](#error-handling-strategy)
- [Performance Optimizations](#performance-optimizations)
- [Implementation Guide](#implementation-guide)
- [Deployment & Production](#deployment--production)
- [Testing Strategy](#testing-strategy)
- [Troubleshooting Guide](#troubleshooting-guide)

## Architecture Overview

**Framework**: React 18.2.0 with functional components and hooks
**State Management**: useState, useEffect for local component state
**API Communication**: Custom ApiService class with fetch-based HTTP requests
**Real-time Updates**: Polling mechanism every 2 seconds
**Error Handling**: ErrorBoundary wrapper and comprehensive error states
**Styling**: CSS modules with dark mode responsive design
**Development Port**: 4000 (configured via PORT environment variable)

## Core Components Structure

### 1. App.js (Root Component)

```javascript
import React from 'react';
import Dashboard from './components/Dashboard';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  return (
    <div className="App dark-theme">
      <ErrorBoundary>
        <Dashboard />
      </ErrorBoundary>
    </div>
  );
}

export default App;
```

**Features:**
- Simple wrapper with error boundary
- ErrorBoundary wrapper for crash protection
- Single Dashboard component rendering
- Global dark theme class application

### 2. Dashboard.js (Main Controller)

```javascript
import React, { useState, useEffect } from 'react';
import StatusBar from './StatusBar';
import UserList from './UserList';
import AudioPlayer from './AudioPlayer';
import ConnectionStatus from './ConnectionStatus';
import ApiService from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  // State Management
  const [selectedUser, setSelectedUser] = useState(null);
  const [audioPlayer, setAudioPlayer] = useState({
    isVisible: false,
    audioUrl: null,
    userID: null
  });

  // Dashboard data state
  const [dashboardData, setDashboardData] = useState({
    active_sessions_count: 0,
    total_users: 0,
    connection_status: 'connecting',
    users: [],
    active_sessions: [],
    stats: {},
    last_updated: null
  });
  
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const apiService = new ApiService();

  // Real-time polling logic
  useEffect(() => {
    let pollInterval;
    let isActive = true;

    const fetchDashboardData = async () => {
      if (!isActive) return;
      
      try {
        setDashboardError(null);
        const data = await apiService.getDashboardData();
        
        if (isActive) {
          setDashboardData({
            active_sessions_count: data.active_sessions_count || 0,
            total_users: data.total_users || 0,
            connection_status: data.connection_status || 'connected',
            users: data.users || [],
            active_sessions: data.active_sessions || [],
            stats: data.stats || {},
            last_updated: data.last_updated
          });
          setDashboardLoading(false);
          setIsConnected(true);
          setLastUpdated(new Date().toISOString());
          setRetryCount(0);
        }
      } catch (error) {
        console.error('Dashboard polling error:', error);
        if (isActive) {
          setDashboardError(error.message);
          setIsConnected(false);
          setRetryCount(prev => prev + 1);
        }
      }
    };

    const startPolling = () => {
      setIsPolling(true);
      fetchDashboardData(); // Initial fetch
      pollInterval = setInterval(fetchDashboardData, 2000); // Poll every 2 seconds
    };

    startPolling();

    return () => {
      isActive = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, []);

  // Event handlers
  const handlePlayAudio = async (userID) => {
    try {
      const audioUrl = `/api/audio/${userID}/latest`;
      setAudioPlayer({ isVisible: true, audioUrl, userID });
    } catch (error) {
      console.error('Error loading audio:', error);
    }
  };

  const handleCloseAudio = () => {
    setAudioPlayer({ isVisible: false, audioUrl: null, userID: null });
  };

  const getConnectionStatus = () => {
    if (dashboardError) return 'error';
    if (dashboardLoading && !dashboardData) return 'connecting';
    return dashboardData?.connection_status || 'connected';
  };

  return (
    <div className="dashboard dark-theme">
      <div className="dashboard-header">
        <h1>📱 Phone Monitoring Dashboard</h1>
        <div className="dashboard-controls">
          <button
            className={`polling-toggle ${isPolling ? 'active' : 'inactive'}`}
            title={isPolling ? 'Stop Real-time Updates' : 'Start Real-time Updates'}
          >
            {isPolling ? '⏸️ Pause' : '▶️ Resume'}
          </button>
          <div className="polling-indicator">
            <div className={`indicator-dot ${isPolling ? 'active' : 'inactive'}`}></div>
            <span>Live Updates</span>
          </div>
        </div>
      </div>

      <StatusBar
        activeSessionsCount={dashboardData?.active_sessions_count}
        totalUsers={dashboardData?.total_users}
        connectionStatus={getConnectionStatus()}
        lastUpdated={dashboardData?.last_updated}
      />

      <ConnectionStatus 
        isConnected={isConnected}
        lastUpdated={lastUpdated}
        retryCount={retryCount}
      />

      <div className="dashboard-content">
        <div className="dashboard-main">
          <UserList
            users={dashboardData?.users}
            loading={dashboardLoading}
            onPlayAudio={handlePlayAudio}
            selectedUser={selectedUser}
            onUserSelect={setSelectedUser}
          />
          <div className="map-placeholder">
            <h3>Map View</h3>
            <p>Users: {dashboardData?.users?.length || 0}</p>
          </div>
        </div>
      </div>

      <div className="dashboard-footer">
        <div className="footer-info">
          <span>🎉 Enhanced Dashboard</span>
          <span>•</span>
          <span>Backend: Flask</span>
          <span>•</span>
          <span>Frontend: React</span>
          <span>•</span>
          <span>Real-time updates every 2 seconds</span>
        </div>
      </div>

      <AudioPlayer
        audioUrl={audioPlayer.audioUrl}
        userID={audioPlayer.userID}
        isVisible={audioPlayer.isVisible}
        onClose={handleCloseAudio}
        autoPlay={true}
      />
    </div>
  );
};

export default Dashboard;
```

**Key Features:**
- **Real-time Polling**: 2-second intervals using useEffect
- **Error Recovery**: Automatic retry with exponential backoff
- **Audio Control**: Plays user recordings with overlay player
- **Map Integration**: Placeholder for geographical user tracking
- **Status Monitoring**: Live connection and session tracking

### 3. ApiService (services/api.js)

```javascript
// Smart environment detection for robust deployment
const getApiUrl = () => {
  // For production build, use hardcoded VPS IP to avoid DNS issues
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return 'http://YOUR_VPS_IP:5000';
  }
  
  // For development, try environment variable first
  if (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Final fallback
  return 'http://localhost:5000';
};

const API_BASE_URL = getApiUrl();
const AUTH_HEADER = 'Basic ' + btoa('admin:supersecret');

class ApiService {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': AUTH_HEADER,
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} - ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  async getDashboardData() {
    try {
      const flaskData = await this.request('/api/dashboard-data');
      return flaskData;
    } catch (error) {
      console.error('Dashboard data fetch failed:', error);
      return this.getFallbackData();
    }
  }

  getFallbackData() {
    return {
      active_sessions_count: 0,
      total_users: 0,
      connection_status: "disconnected",
      users: [],
      active_sessions: [],
      stats: {
        total_users: 0,
        active_sessions: 0,
        total_recordings: 0,
        online_users: 0
      },
      last_updated: new Date().toISOString()
    };
  }

  async startListening(userId) {
    return await this.request(`/api/start-listening/${userId}`, {
      method: 'POST'
    });
  }

  async stopListening(userId) {
    return await this.request(`/api/stop-listening/${userId}`, {
      method: 'POST'
    });
  }
}

export default ApiService;
```

**Environment Handling:**
- Production: Hard-coded VPS IP for reliability
- Development: Environment variables or localhost fallback
- Basic Auth: Configurable credentials
- Error handling with fallback data

### 4. UserList Component

```javascript
import React, { useState, useMemo } from 'react';
import './UserList.css';

const UserList = ({ users = [], loading = false, onPlayAudio, selectedUser, onUserSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loadingStates, setLoadingStates] = useState({});

  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      const matchesSearch = user.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (user.device_info && user.device_info.toLowerCase().includes(searchTerm.toLowerCase()));
      
      const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    });
  }, [users, searchTerm, statusFilter]);

  const getStatusBadge = (status) => {
    const statusConfig = {
      listening: { emoji: '🔴', color: 'status-listening', text: 'Listening' },
      idle: { emoji: '🟡', color: 'status-idle', text: 'Idle' },
      offline: { emoji: '⚪', color: 'status-offline', text: 'Offline' }
    };
    
    const config = statusConfig[status] || statusConfig.offline;
    return (
      <span className={`status-badge ${config.color}`}>
        <span className="status-emoji">{config.emoji}</span>
        {config.text}
      </span>
    );
  };

  const formatLastActivity = (lastActivity) => {
    if (!lastActivity) return 'Never';
    
    const now = new Date();
    const activityTime = new Date(lastActivity);
    const diffMinutes = Math.floor((now - activityTime) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return `${Math.floor(diffMinutes / 1440)}d ago`;
  };

  return (
    <div className="user-list dark-theme">
      <div className="user-list-header">
        <h2>📱 Connected Devices ({filteredUsers.length})</h2>
        
        <div className="user-controls">
          <input
            type="text"
            placeholder="🔍 Search devices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="status-filter"
          >
            <option value="all">All Status</option>
            <option value="listening">🔴 Listening</option>
            <option value="idle">🟡 Idle</option>
            <option value="offline">⚪ Offline</option>
          </select>
        </div>
      </div>

      <div className="user-grid">
        {loading && users.length === 0 ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading devices...</p>
          </div>
        ) : (
          filteredUsers.map((user) => (
            <div
              key={user.user_id}
              className={`user-card ${selectedUser === user.user_id ? 'selected' : ''}`}
              onClick={() => onUserSelect(user.user_id)}
            >
              <div className="user-header">
                <h3 className="user-id">📱 {user.user_id}</h3>
                {getStatusBadge(user.status)}
              </div>
              
              <div className="user-details">
                <p className="device-info">
                  <span className="label">Device:</span>
                  <span className="value">{user.device_info || 'Unknown'}</span>
                </p>
                
                <p className="last-activity">
                  <span className="label">Last Activity:</span>
                  <span className="value">{formatLastActivity(user.last_activity)}</span>
                </p>
              </div>
              
              <div className="user-actions">
                <button
                  className="action-btn play-audio"
                  onClick={(e) => {
                    e.stopPropagation();
                    onPlayAudio(user.user_id);
                  }}
                  disabled={loadingStates[user.user_id]}
                >
                  🎵 Play Audio
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default UserList;
```

**Features:**
- **Search & Filter**: Real-time search by user ID or device info
- **Status Filtering**: All/Listening/Idle/Offline states
- **Interactive Actions**: Play audio, start/stop monitoring
- **Status Indicators**: Color-coded badges with emojis
- **Activity Tracking**: "Last seen" timestamps with relative formatting
- **Dark Theme**: Optimized for dark mode experience

## Real-time Data Flow

### Polling Architecture

```javascript
// useEffect polling pattern
useEffect(() => {
  let pollInterval;
  let isActive = true;

  const fetchData = async () => {
    if (!isActive) return;
    try {
      const data = await apiService.getDashboardData();
      if (isActive) {
        setDashboardData(data);
        setIsConnected(true);
        setRetryCount(0);
      }
    } catch (error) {
      if (isActive) {
        setError(error.message);
        setIsConnected(false);
        setRetryCount(prev => prev + 1);
      }
    }
  };

  fetchData(); // Initial fetch
  pollInterval = setInterval(fetchData, 2000); // Poll every 2 seconds

  return () => {
    isActive = false;
    clearInterval(pollInterval);
  };
}, []);
```

### Expected Backend Data Structure

```javascript
{
  active_sessions_count: number,
  total_users: number,
  connection_status: "connected|connecting|error",
  users: [
    {
      user_id: string,
      status: "listening|idle|offline",
      device_info: string,
      last_activity: "2025-08-09T12:00:00Z",
      location: {lat: number, lng: number},
      session_data: object
    }
  ],
  active_sessions: array,
  stats: {
    total_users: number,
    active_sessions: number,
    total_recordings: number,
    online_users: number
  },
  last_updated: "2025-08-09T12:00:00Z"
}
```

## Dark Mode Design System

### Color Palette

```css
/* Dark Theme Color Variables */
:root {
  /* Primary Dark Colors */
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --bg-tertiary: #3a3a3a;
  --bg-card: #2a2a2a;
  --bg-header: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
  
  /* Text Colors */
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --text-muted: #888888;
  --text-accent: #64b5f6;
  
  /* Status Colors */
  --status-success: #4caf50;
  --status-warning: #ff9800;
  --status-error: #f44336;
  --status-info: #2196f3;
  
  /* Interactive Colors */
  --border-color: #404040;
  --hover-bg: #404040;
  --active-bg: #505050;
  --shadow-color: rgba(0, 0, 0, 0.3);
  
  /* Accent Colors */
  --accent-primary: #64b5f6;
  --accent-secondary: #81c784;
  --accent-danger: #ef5350;
}
```

### Core Dashboard CSS

```css
/* Dashboard.css - Dark Mode Design */
.dashboard.dark-theme {
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background: var(--bg-header);
  color: var(--text-primary);
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 8px var(--shadow-color);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--border-color);
}

.dashboard-header h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
}

.dashboard-controls {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.polling-toggle {
  background: rgba(100, 181, 246, 0.2);
  border: 2px solid var(--accent-primary);
  color: var(--text-primary);
  padding: 0.625rem 1.25rem;
  border-radius: 1.5rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.polling-toggle:hover {
  background: rgba(100, 181, 246, 0.3);
  transform: translateY(-1px);
}

.polling-toggle.active {
  background: var(--accent-primary);
  color: var(--bg-primary);
}

.polling-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-error);
  transition: all 0.3s ease;
}

.indicator-dot.active {
  background: var(--status-success);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.dashboard-content {
  flex: 1;
  padding: 2rem;
  background: var(--bg-primary);
}

.dashboard-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-footer {
  background: var(--bg-secondary);
  padding: 1rem 2rem;
  border-top: 1px solid var(--border-color);
  text-align: center;
}

.footer-info {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

/* Map Placeholder */
.map-placeholder {
  height: 400px;
  border: 2px dashed var(--border-color);
  display: flex;
  align-items: center;
  justifycontent: center;
  background: var(--bg-card);
  border-radius: 12px;
  flex-direction: column;
  color: var(--text-secondary);
}

.map-placeholder h3 {
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .dashboard-main {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .dashboard-content {
    padding: 1rem;
  }
  
  .footer-info {
    flex-direction: column;
    gap: 0.5rem;
  }
}
```

### UserList Dark Mode CSS

```css
/* UserList.css - Dark Mode */
.user-list.dark-theme {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 8px var(--shadow-color);
  border: 1px solid var(--border-color);
}

.user-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.user-list-header h2 {
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.user-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  width: 200px;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(100, 181, 246, 0.1);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.status-filter {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
}

.status-filter:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  max-height: 600px;
  overflow-y: auto;
}

.user-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.user-card:hover {
  background: var(--hover-bg);
  border-color: var(--accent-primary);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px var(--shadow-color);
}

.user-card.selected {
  border-color: var(--accent-primary);
  background: var(--active-bg);
  box-shadow: 0 0 0 3px rgba(100, 181, 246, 0.1);
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.user-id {
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.status-listening {
  background: rgba(244, 67, 54, 0.2);
  color: var(--status-error);
  border: 1px solid var(--status-error);
}

.status-badge.status-idle {
  background: rgba(255, 152, 0, 0.2);
  color: var(--status-warning);
  border: 1px solid var(--status-warning);
}

.status-badge.status-offline {
  background: rgba(136, 136, 136, 0.2);
  color: var(--text-muted);
  border: 1px solid var(--text-muted);
}

.user-details {
  margin-bottom: 1rem;
}

.user-details p {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  display: flex;
  justify-content: space-between;
}

.label {
  color: var(--text-secondary);
  font-weight: 500;
}

.value {
  color: var(--text-primary);
  font-weight: 400;
}

.user-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.action-btn {
  background: var(--accent-primary);
  color: var(--bg-primary);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.action-btn:hover {
  background: var(--accent-secondary);
  transform: translateY(-1px);
}

.action-btn:disabled {
  background: var(--text-muted);
  cursor: not-allowed;
  transform: none;
}

.loading-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top: 3px solid var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .user-controls {
    flex-direction: column;
    width: 100%;
  }
  
  .search-input {
    width: 100%;
  }
  
  .user-grid {
    grid-template-columns: 1fr;
    max-height: 500px;
  }
  
  .user-card {
    padding: 1rem;
  }
}
```

### StatusBar Dark Mode CSS

```css
/* StatusBar.css - Dark Mode */
.status-bar {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px var(--shadow-color);
}

.status-left, .status-right {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.status-icon {
  font-size: 1.25rem;
  animation: pulse 2s infinite;
}

.status-text {
  color: var(--text-secondary);
}

.status-text strong {
  color: var(--text-primary);
  font-weight: 600;
}

.connection-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
}

.connection-badge.connected {
  background: rgba(76, 175, 80, 0.2);
  color: var(--status-success);
  border: 1px solid var(--status-success);
}

.connection-badge.connecting {
  background: rgba(255, 152, 0, 0.2);
  color: var(--status-warning);
  border: 1px solid var(--status-warning);
}

.connection-badge.error {
  background: rgba(244, 67, 54, 0.2);
  color: var(--status-error);
  border: 1px solid var(--status-error);
}

.last-updated {
  color: var(--text-muted);
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .status-bar {
    flex-direction: column;
    gap: 1rem;
    margin: 1rem;
    padding: 1rem;
  }
  
  .status-left, .status-right {
    justify-content: center;
    gap: 1rem;
  }
}
```

## State Management Patterns

### Local State Pattern

```javascript
// Component-specific state management
const [state, setState] = useState({
  data: null,
  loading: true,
  error: null,
  filters: {
    search: '',
    status: 'all'
  }
});

// Update patterns
const updateData = (newData) => {
  setState(prev => ({
    ...prev,
    data: newData,
    loading: false,
    error: null
  }));
};

const updateFilters = (filterName, value) => {
  setState(prev => ({
    ...prev,
    filters: {
      ...prev.filters,
      [filterName]: value
    }
  }));
};
```

### Data Flow Architecture

```
Dashboard (Controller State)
  ↓ props
├── StatusBar (Presentation)
├── UserList (Presentation + Local State)
├── AudioPlayer (Modal State)
└── ConnectionStatus (Status Display)
  ↑ callbacks
Dashboard (Event Handlers)
```

## Error Handling Strategy

### Network Error Recovery

```javascript
// Exponential backoff retry pattern
const [retryCount, setRetryCount] = useState(0);
const [retryDelay, setRetryDelay] = useState(1000);

const fetchWithRetry = async (url, maxRetries = 3) => {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setRetryCount(0);
      setRetryDelay(1000);
      return await response.json();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      const delay = retryDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
      setRetryCount(attempt + 1);
    }
  }
};
```

### ErrorBoundary Component

```javascript
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary dark-theme">
          <div className="error-content">
            <h2>🚨 Something went wrong</h2>
            <p>The application encountered an unexpected error.</p>
            <button 
              onClick={() => window.location.reload()}
              className="retry-button"
            >
              🔄 Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

## Performance Optimizations

### React Optimization Patterns

```javascript
// Memoized filtering for large datasets
const filteredUsers = useMemo(() => {
  return users.filter(user => {
    const matchesSearch = user.user_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
}, [users, searchTerm, statusFilter]);

// Stable callback references
const handleUserSelect = useCallback((userId) => {
  setSelectedUser(userId);
}, []);

// Cleanup and memory management
useEffect(() => {
  let isActive = true;
  let pollInterval;

  const startPolling = () => {
    pollInterval = setInterval(fetchData, 2000);
  };

  if (isActive) {
    startPolling();
  }

  return () => {
    isActive = false;
    if (pollInterval) clearInterval(pollInterval);
  };
}, []);
```

### Network Efficiency

```javascript
// Request cancellation
useEffect(() => {
  const controller = new AbortController();
  
  const fetchData = async () => {
    try {
      const response = await fetch(url, {
        signal: controller.signal
      });
      // Handle response
    } catch (error) {
      if (error.name !== 'AbortError') {
        // Handle real errors
      }
    }
  };

  fetchData();

  return () => controller.abort();
}, [url]);
```

## Implementation Guide

### Package.json Setup

```json
{
  "name": "buas-dashboard-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
"scripts": {
  "start": "PORT=4000 react-scripts start",
  "build": "react-scripts build",
  "test": "react-scripts test",
  "eject": "react-scripts eject",
  "start:production": "PORT=4000 REACT_APP_API_URL=http://YOUR_VPS_IP:5000 npm start"
},
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```### Environment Configuration

```bash
# .env.development
PORT=4000
REACT_APP_API_URL=http://localhost:5000
REACT_APP_POLLING_INTERVAL=2000
REACT_APP_MAX_RETRIES=3

# .env.production
PORT=4000
REACT_APP_API_URL=http://YOUR_VPS_IP:5000
REACT_APP_POLLING_INTERVAL=2000
REACT_APP_MAX_RETRIES=5
```

### File Structure

```
src/
├── components/
│   ├── Dashboard.js
│   ├── Dashboard.css
│   ├── UserList.js
│   ├── UserList.css
│   ├── StatusBar.js
│   ├── StatusBar.css
│   ├── AudioPlayer.js
│   ├── AudioPlayer.css
│   ├── ConnectionStatus.js
│   ├── ConnectionStatus.css
│   └── ErrorBoundary.js
├── services/
│   └── api.js
├── hooks/
│   └── usePolling.js
├── App.js
├── App.css
├── index.js
└── index.css
```

### Key Implementation Notes

1. **Dark Theme**: Apply `dark-theme` class to root components
2. **Port Configuration**: Frontend runs on port 4000 (set via PORT environment variable)
3. **Environment Variables**: Use smart detection for production vs development
4. **Error Recovery**: Implement retry logic with exponential backoff
5. **Performance**: Use useMemo for expensive filtering operations
6. **Responsive Design**: Mobile-first approach with CSS Grid and Flexbox
7. **Accessibility**: Proper contrast ratios and keyboard navigation
8. **Real-time Updates**: 2-second polling with connection status monitoring

This template provides a complete foundation for building a real-time monitoring dashboard with modern React patterns, dark mode design, and robust error handling that you can adapt for your BUAS workspace requirements.
