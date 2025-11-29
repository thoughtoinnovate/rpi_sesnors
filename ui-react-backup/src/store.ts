import { create } from 'zustand';

// Sensor data types
export interface SensorReading {
  pm25: number;
  pm10: number;
  aqi: number;
  temperature?: number;
  humidity?: number;
  timestamp: string;
  location: string;
}

export interface PmData {
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue?: number;
  lastUpdated: string;
}

export interface AqiData {
  aqi: number;
  level: string;
  color: string;
  healthMessage: string;
  timestamp: string;
}

export interface SchedulerStatus {
  isRunning: boolean;
  interval: number;
  nextRun: string;
}

export interface SensorStatus {
  connected: boolean;
  warmedUp: boolean;
  sleeping: boolean;
  lastReading: string;
}

export interface Location {
  id: string;
  name: string;
  latitude?: number;
  longitude?: number;
}

// Store state interface
interface AppState {
  // Current data
  currentReading: SensorReading | null;
  aqiData: AqiData | null;
  schedulerStatus: SchedulerStatus | null;
  sensorStatus: SensorStatus | null;
  pm25Data: PmData | null;
  pm10Data: PmData | null;

  // Locations
  locations: Location[];
  selectedLocation: string | null;

  // Settings
  refreshInterval: number;
  pollingEnabled: boolean;

  // UI state
  loading: boolean;
  error: string | null;

  // Actions
  setCurrentReading: (reading: SensorReading | null) => void;
  setAqiData: (data: AqiData | null) => void;
  setSchedulerStatus: (status: SchedulerStatus | null) => void;
  setSensorStatus: (status: SensorStatus | null) => void;
  setPm25Data: (data: PmData | null) => void;
  setPm10Data: (data: PmData | null) => void;
  setLocations: (locations: Location[]) => void;
  setSelectedLocation: (locationId: string | null) => void;
  setRefreshInterval: (interval: number) => void;
  setPollingEnabled: (enabled: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

// Initial state
const initialState = {
  currentReading: null,
  aqiData: null,
  schedulerStatus: null,
  sensorStatus: null,
  pm25Data: null,
  pm10Data: null,
  locations: [],
  selectedLocation: null,
  refreshInterval: 30, // seconds
  pollingEnabled: true,
  loading: false,
  error: null,
};

// Create the store
export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setCurrentReading: (reading) => set({ currentReading: reading }),
  setAqiData: (data) => set({ aqiData: data }),
  setSchedulerStatus: (status) => set({ schedulerStatus: status }),
  setSensorStatus: (status) => set({ sensorStatus: status }),
  setPm25Data: (data) => set({ pm25Data: data }),
  setPm10Data: (data) => set({ pm10Data: data }),
  setLocations: (locations) => set({ locations }),
  setSelectedLocation: (locationId) => set({ selectedLocation: locationId }),
  setRefreshInterval: (interval) => set({ refreshInterval: interval }),
  setPollingEnabled: (enabled) => set({ pollingEnabled: enabled }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}));