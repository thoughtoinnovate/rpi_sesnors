import { useEffect } from 'react';
import { useAppStore } from '../store';
import { SensorStatus } from '../store';

// Mock sensor status generator
const generateMockSensorStatus = (): SensorStatus => {
  const connected = Math.random() > 0.1; // 90% chance of being connected
  const warmedUp = connected && Math.random() > 0.2; // 80% chance if connected
  const sleeping = connected && Math.random() > 0.7; // 30% chance if connected

  return {
    connected,
    warmedUp,
    sleeping,
    lastReading: new Date(Date.now() - Math.random() * 60000).toISOString(), // Random time in last minute
  };
};

export const useSensorStatus = () => {
  const { setSensorStatus, loading } = useAppStore();

  useEffect(() => {
    // Generate mock sensor status for now - will be replaced with real API calls
    const updateSensorStatus = () => {
      if (!loading) {
        setSensorStatus(generateMockSensorStatus());
      }
    };

    // Initial data
    updateSensorStatus();

    // Update every 10 seconds
    const interval = setInterval(updateSensorStatus, 10000);

    return () => clearInterval(interval);
  }, [setSensorStatus, loading]);
};