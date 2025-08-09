import React, { useState, useMemo } from 'react';
import './UserList.css';

const UserList = ({ 
  users = [], 
  loading = false, 
  onPlayAudio, 
  onStartListening, 
  onStopListening,
  selectedUser, 
  onUserSelect 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Filter and search users
  const filteredUsers = useMemo(() => {
    let filtered = users;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(user => 
        user.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (user.device_name && user.device_name.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(user => user.status === statusFilter);
    }

    return filtered;
  }, [users, searchTerm, statusFilter]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'listening':
        return <span className="status-badge status-listening">🎧 Listening</span>;
      case 'idle':
        return <span className="status-badge status-idle">😴 Idle</span>;
      case 'offline':
        return <span className="status-badge status-offline">📵 Offline</span>;
      default:
        return <span className="status-badge status-idle">❓ Unknown</span>;
    }
  };

  const formatLastSeen = (timestamp) => {
    if (!timestamp) return 'Never';
    
    const now = new Date();
    const lastSeen = new Date(timestamp);
    const diffMs = now - lastSeen;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const handleUserAction = (user, action) => {
    switch (action) {
      case 'play':
        onPlayAudio && onPlayAudio(user);
        break;
      case 'start':
        onStartListening && onStartListening(user.user_id);
        break;
      case 'stop':
        onStopListening && onStopListening(user.user_id);
        break;
      default:
        break;
    }
  };

  if (loading && users.length === 0) {
    return (
      <div className="user-list-container">
        <div className="user-list-header">
          <h2>🦇 Connected Devices</h2>
        </div>
        <div className="loading-users">
          <div className="spinner"></div>
          <p>Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-list-container">
      <div className="user-list-header">
        <h2>🦇 Connected Devices ({filteredUsers.length})</h2>
        
        <div className="user-list-controls">
          {/* Search Input */}
          <div className="search-container">
            <input
              type="text"
              placeholder="Search devices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="status-filter"
          >
            <option value="all">All Status</option>
            <option value="listening">Listening</option>
            <option value="idle">Idle</option>
            <option value="offline">Offline</option>
          </select>
        </div>
      </div>

      {/* User Cards */}
      <div className="user-list">
        {filteredUsers.length === 0 ? (
          <div className="no-users">
            <p>
              {searchTerm || statusFilter !== 'all' 
                ? '🔍 No devices match your search criteria'
                : '📱 No devices connected yet'
              }
            </p>
            {searchTerm && (
              <button 
                className="btn btn-secondary"
                onClick={() => setSearchTerm('')}
              >
                Clear Search
              </button>
            )}
          </div>
        ) : (
          filteredUsers.map(user => (
            <div 
              key={user.user_id}
              className={`user-card ${selectedUser === user.user_id ? 'selected' : ''}`}
              onClick={() => onUserSelect && onUserSelect(user.user_id)}
            >
              <div className="user-header">
                <div className="user-info">
                  <h3 className="user-id">📱 {user.user_id}</h3>
                  <p className="user-location">
                    📍 {user.location?.lat?.toFixed(4)}, {user.location?.lng?.toFixed(4)}
                  </p>
                </div>
                {getStatusBadge(user.status)}
              </div>

              <div className="user-details">
                <div className="user-stats">
                  <div className="stat-item">
                    <span className="stat-label">Recordings:</span>
                    <span className="stat-value">{user.uploads?.length || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Last Seen:</span>
                    <span className="stat-value">{formatLastSeen(user.last_seen)}</span>
                  </div>
                </div>

                <div className="user-actions">
                  {user.latest_audio && (
                    <button
                      className="btn btn-primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUserAction(user, 'play');
                      }}
                      title="Play latest recording"
                    >
                      🎵 Play Audio
                    </button>
                  )}

                  {user.status === 'listening' ? (
                    <button
                      className="btn btn-danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUserAction(user, 'stop');
                      }}
                      title="Stop listening"
                    >
                      ⏹️ Stop
                    </button>
                  ) : (
                    <button
                      className="btn btn-success"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUserAction(user, 'start');
                      }}
                      title="Start listening"
                    >
                      ▶️ Listen
                    </button>
                  )}
                </div>
              </div>

              {/* Recent Uploads */}
              {user.uploads && user.uploads.length > 0 && (
                <div className="user-uploads">
                  <h4>Recent Uploads:</h4>
                  <div className="upload-list">
                    {user.uploads.slice(0, 3).map((upload, index) => (
                      <div key={index} className="upload-item">
                        <span className="upload-filename">🎵 {upload.filename}</span>
                        <span className="upload-time">
                          {new Date(upload.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                    {user.uploads.length > 3 && (
                      <p className="more-uploads">
                        +{user.uploads.length - 3} more recordings...
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default UserList;
