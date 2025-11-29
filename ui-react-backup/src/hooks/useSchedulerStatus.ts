import { useEffect } from 'react';
import { useAppStore } from '../store';
import { SchedulerStatus } from '../store';

// Mock scheduler status generator
const generateMockSchedulerStatus = (): SchedulerStatus => {
  const isRunning = Math.random() > 0.3; // 70% chance of running
  const interval = [10, 30, 60, 300, 600][Math.floor(Math.random() * 5)];
  
  const nextRun = new Date();
  if (isRunning) {
    nextRun.setSeconds(nextRun.getSeconds() + interval);
  }

  return {
    isRunning,
    interval,
    nextRun: nextRun.toISOString(),
  };
};

export const useSchedulerStatus = () => {
  const { setSchedulerStatus, loading } = useAppStore();

  useEffect(() => {
    // Generate mock scheduler status for now - will be replaced with real API calls
    const updateSchedulerStatus = () => {
      if (!loading) {
        setSchedulerStatus(generateMockSchedulerStatus());
      }
    };

    // Initial data
    updateSchedulerStatus();

    // Update every 15 seconds
    const interval = setInterval(updateSchedulerStatus, 15000);

    return () => clearInterval(interval);
  }, [setSchedulerStatus, loading]);
};