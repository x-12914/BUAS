// Smart environment detection for robust deployment
const getApiUrl = () => {
  // For production build, use hardcoded VPS IP to avoid DNS issues
  if (process.env.NODE_ENV === 'production') {
    return process.env.REACT_APP_VPS_URL || 'http://143.244.133.125:5000';
  }
  // For development, use environment variable or localhost fallback
  return process.env.REACT_APP_API_URL || 'http://localhost:5000';
};

const API_BASE_URL = getApiUrl();
const AUTH_USERNAME = process.env.REACT_APP_AUTH_USERNAME || 'admin';
const AUTH_PASSWORD = process.env.REACT_APP_AUTH_PASSWORD || 'supersecret';
const AUTH_HEADER = 'Basic ' + btoa(`${AUTH_USERNAME}:${AUTH_PASSWORD}`);

class ApiService {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.authHeader = AUTH_HEADER;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      mode: 'cors',
      credentials: 'omit',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.authHeader,
        'Accept': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      
      // Return fallback data for dashboard
      if (endpoint === '/api/dashboard-data') {
        return {
          active_sessions_count: 0,
          total_users: 0,
          connection_status: 'error',
          users: [],
          active_sessions: [],
          stats: {
            total_users: 0,
            active_sessions: 0,
            total_recordings: 0
          },
          error: error.message,
          last_updated: new Date().toISOString()
        };
      }
      
      throw error;
    }
  }

  async getDashboardData() {
    return this.request('/api/dashboard-data');
  }

  async getHealthCheck() {
    return this.request('/api/health');
  }

  async startListening(userId) {
    return this.request(`/api/start-listening/${userId}`, {
      method: 'POST'
    });
  }

  async stopListening(userId) {
    return this.request(`/api/stop-listening/${userId}`, {
      method: 'POST'
    });
  }

  async getLatestAudio(deviceId) {
    return this.request(`/api/audio/${deviceId}/latest`);
  }
}

export default new ApiService();
