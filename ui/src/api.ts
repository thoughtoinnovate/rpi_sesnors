import axios, { AxiosInstance, CancelTokenSource } from 'axios';
import { SensorReading, AqiData, SchedulerStatus } from './store';

// Create axios instance with base configuration
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request cancellation tokens
let cancelTokens: { [key: string]: CancelTokenSource } = {};

// Helper to create cancel token
const createCancelToken = (key: string): CancelTokenSource => {
  if (cancelTokens[key]) {
    cancelTokens[key].cancel('Request cancelled');
  }
  cancelTokens[key] = axios.CancelToken.source();
  return cancelTokens[key];
};

// Helper to handle API errors
const handleApiError = (error: any): string => {
  if (axios.isCancel(error)) {
    return 'Request cancelled';
  }

  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.message || error.response.data?.error;

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
  } else if (error.request) {
    // Network error
    return 'Network error - unable to connect to server';
  } else {
    // Other error
    return error.message || 'Unknown error occurred';
  }
};

// API functions
export const apiClient = {
  // Get latest sensor reading for a location
  getLatestReading: async (location: string): Promise<SensorReading> => {
    const cancelToken = createCancelToken('latest-reading');
    try {
      const response = await api.get(`/api/latest/${location}`, {
        cancelToken: cancelToken.token,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get AQI sensor reading
  getAqiReading: async (): Promise<AqiData> => {
    const cancelToken = createCancelToken('aqi-reading');
    try {
      const response = await api.get('/sensor/aqi/sensor/reading', {
        cancelToken: cancelToken.token,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get scheduler status
  getSchedulerStatus: async (): Promise<SchedulerStatus> => {
    const cancelToken = createCancelToken('scheduler-status');
    try {
      const response = await api.get('/api/scheduler/status', {
        cancelToken: cancelToken.token,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get historical data
  getHistoricalData: async (location: string, hours: number = 24): Promise<SensorReading[]> => {
    const cancelToken = createCancelToken('historical-data');
    try {
      const response = await api.get(`/api/history/${location}`, {
        params: { hours },
        cancelToken: cancelToken.token,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Get statistics
  getStats: async (location: string, days: number = 7): Promise<any> => {
    const cancelToken = createCancelToken('stats');
    try {
      const response = await api.get(`/api/stats/${location}`, {
        params: { days },
        cancelToken: cancelToken.token,
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Control scheduler
  startScheduler: async (): Promise<void> => {
    const cancelToken = createCancelToken('start-scheduler');
    try {
      await api.post('/api/scheduler/start', {}, {
        cancelToken: cancelToken.token,
      });
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  stopScheduler: async (): Promise<void> => {
    const cancelToken = createCancelToken('stop-scheduler');
    try {
      await api.post('/api/scheduler/stop', {}, {
        cancelToken: cancelToken.token,
      });
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Sensor power management
  wakeSensor: async (): Promise<void> => {
    const cancelToken = createCancelToken('wake-sensor');
    try {
      await api.post('/api/sensor/wake', {}, {
        cancelToken: cancelToken.token,
      });
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  sleepSensor: async (): Promise<void> => {
    const cancelToken = createCancelToken('sleep-sensor');
    try {
      await api.post('/api/sensor/sleep', {}, {
        cancelToken: cancelToken.token,
      });
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  // Cancel all pending requests
  cancelAllRequests: (): void => {
    Object.values(cancelTokens).forEach(token => {
      token.cancel('All requests cancelled');
    });
    cancelTokens = {};
  },

  // Cancel specific request type
  cancelRequest: (key: string): void => {
    if (cancelTokens[key]) {
      cancelTokens[key].cancel('Request cancelled');
      delete cancelTokens[key];
    }
  },
};

export default apiClient;