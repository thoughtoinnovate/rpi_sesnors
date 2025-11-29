import { useEffect } from 'react';
import { useAppStore } from '../store';

// Mock data generator for PM2.5 and PM10
const generateMockPmData = (type: 'pm25' | 'pm10') => {
  const baseValue = type === 'pm25' ? 25 : 45;
  const variation = Math.random() * 20 - 10; // ±10 variation
  const value = Math.max(0, baseValue + variation);
  
  // Generate trend
  const trendValue = Math.random() * 10 - 5; // ±5% trend
  let trend: 'up' | 'down' | 'stable' = 'stable';
  if (trendValue > 2) trend = 'up';
  else if (trendValue < -2) trend = 'down';

  return {
    value: Math.round(value * 10) / 10,
    unit: 'μg/m³',
    trend,
    trendValue: Math.round(trendValue * 10) / 10,
    lastUpdated: new Date().toISOString(),
  };
};

export const usePmData = () => {
  const { setPm25Data, setPm10Data, loading } = useAppStore();

  useEffect(() => {
    // Generate mock data for now - will be replaced with real API calls
    const updatePmData = () => {
      if (!loading) {
        setPm25Data(generateMockPmData('pm25'));
        setPm10Data(generateMockPmData('pm10'));
      }
    };

    // Initial data
    updatePmData();

    // Update every 30 seconds
    const interval = setInterval(updatePmData, 30000);

    return () => clearInterval(interval);
  }, [setPm25Data, setPm10Data, loading]);
};