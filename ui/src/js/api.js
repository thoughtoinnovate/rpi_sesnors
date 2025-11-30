// API Client using Fetch API
class ApiClient {
  constructor() {
    // Use relative URLs since UI and API are on same port
    this.baseURL = window.location.origin;
    this.timeout = 10000; // 10 seconds
    this.abortControllers = {};
  }

  // Helper to create abort controller for request cancellation
  createAbortController(key) {
    if (this.abortControllers[key]) {
      this.abortControllers[key].abort();
    }
    this.abortControllers[key] = new AbortController();
    return this.abortControllers[key];
  }

  // Helper to handle API errors
  handleApiError(error) {
    if (error.name === 'AbortError') {
      return 'Request cancelled';
    }

    if (error.response) {
      // For fetch, we need to check the response status
      const status = error.status;
      const message = error.message || 'Unknown error';

      switch (status) {
        case 400:
          return message || 'Bad request';
        case 401:
          return 'Unauthorized access';
        case 403:
          return 'Access forbidden';
        case 404:
          return 'Resource not found';
        case 500:
          return 'Internal server error';
        default:
          return message || `Server error: ${status}`;
      }
    } else if (error.message === 'Failed to fetch') {
      return 'Network error - unable to connect to server';
    } else {
      return error.message || 'Unknown error occurred';
    }
  }

  // Generic fetch wrapper
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const controller = this.createAbortController(endpoint);
    
    const config = {
      timeout: this.timeout,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        error.status = response.status;
        error.response = response;
        
        try {
          const errorData = await response.json();
          error.message = errorData.message || errorData.error || error.message;
        } catch {
          // If JSON parsing fails, use default error message
        }
        
        throw error;
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return response;
      }
    } catch (error) {
      throw new Error(this.handleApiError(error));
    } finally {
      delete this.abortControllers[endpoint];
    }
  }

  // GET request
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  }

  // POST request
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // PUT request
  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Cancel all pending requests
  cancelAllRequests() {
    Object.values(this.abortControllers).forEach(controller => {
      controller.abort();
    });
    this.abortControllers = {};
  }

  // Cancel specific request
  cancelRequest(endpoint) {
    if (this.abortControllers[endpoint]) {
      this.abortControllers[endpoint].abort();
      delete this.abortControllers[endpoint];
    }
  }

  // API Methods
  async getLatestReading(location) {
    return this.get(`/api/latest/${location}`);
  }

  async getAqiReading() {
    return this.get('/sensor/aqi/sensor/reading');
  }

  async getSchedulerStatus() {
    return this.get('/api/scheduler/status');
  }

  async getHistoricalData(location, hours = 24) {
    return this.get(`/api/history/${location}`, { hours });
  }

  async getStats(location, days = 7) {
    return this.get(`/api/stats/${location}`, { days });
  }

  async startScheduler(location, interval) {
    return this.post('/api/scheduler/start', { location, interval });
  }

  async stopScheduler() {
    return this.post('/api/scheduler/stop');
  }

  async wakeSensor() {
    return this.post('/api/sensor/wake');
  }

  async sleepSensor() {
    return this.post('/api/sensor/sleep');
  }

  async getLocations() {
    return this.get('/api/locations');
  }

  async addLocation(locationData) {
    return this.post('/api/locations', locationData);
  }

  async deleteLocation(locationId) {
    return this.delete(`/api/locations/${locationId}`);
  }

  async getHealth() {
    return this.get('/api/health');
  }
}

// Create singleton instance
const apiClient = new ApiClient();

// Export for use in other modules
window.apiClient = apiClient;