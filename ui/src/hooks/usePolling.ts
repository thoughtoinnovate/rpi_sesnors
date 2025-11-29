import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store';
import apiClient from '../api';

interface UsePollingOptions {
  enabled?: boolean;
  interval?: number;
  maxRetries?: number;
  backoffMultiplier?: number;
}

export const usePolling = (options: UsePollingOptions = {}) => {
  const {
    enabled = true,
    interval = 30000, // 30 seconds default
    maxRetries = 5,
    backoffMultiplier = 2,
  } = options;

  const store = useAppStore();
  const intervalRef = useRef<number | null>(null);
  const retryCountRef = useRef(0);
  const isPollingRef = useRef(false);

  // Calculate backoff delay
  const getBackoffDelay = useCallback((retryCount: number): number => {
    return Math.min(interval * Math.pow(backoffMultiplier, retryCount), 300000); // Max 5 minutes
  }, [interval, backoffMultiplier]);

  // Fetch data function
  const fetchData = useCallback(async () => {
    if (isPollingRef.current) return; // Prevent concurrent requests

    isPollingRef.current = true;
    store.setLoading(true);
    store.setError(null);

    try {
      // Fetch AQI data
      const aqiData = await apiClient.getAqiReading();
      store.setAqiData(aqiData);

      // Reset retry count on success
      retryCountRef.current = 0;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      store.setError(errorMessage);

      // Increment retry count
      retryCountRef.current += 1;

      if (retryCountRef.current >= maxRetries) {
        console.error('Max retries reached, stopping polling');
        store.setPollingEnabled(false);
        return;
      }

      // Schedule retry with backoff
      const backoffDelay = getBackoffDelay(retryCountRef.current);
      console.warn(`Polling failed, retrying in ${backoffDelay / 1000}s:`, errorMessage);

      setTimeout(() => {
        if (enabled && store.pollingEnabled) {
          fetchData();
        }
      }, backoffDelay);

      return; // Don't continue to normal polling
    } finally {
      isPollingRef.current = false;
      store.setLoading(false);
    }

    // Schedule next poll if successful
    if (enabled && store.pollingEnabled) {
      intervalRef.current = setTimeout(fetchData, interval);
    }
  }, [enabled, interval, maxRetries, getBackoffDelay, store]);

  // Start polling
  const startPolling = useCallback(() => {
    if (!enabled || !store.pollingEnabled) return;

    // Clear any existing interval
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
    }

    // Reset retry count
    retryCountRef.current = 0;

    // Start polling
    fetchData();
  }, [enabled, fetchData, store.pollingEnabled]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
    isPollingRef.current = false;
    apiClient.cancelAllRequests();
  }, []);

  // Effect to handle polling lifecycle
  useEffect(() => {
    if (enabled && store.pollingEnabled) {
      startPolling();
    } else {
      stopPolling();
    }

    // Cleanup on unmount
    return () => {
      stopPolling();
    };
  }, [enabled, store.pollingEnabled, startPolling, stopPolling]);

  // Effect to restart polling when interval changes
  useEffect(() => {
    if (enabled && store.pollingEnabled) {
      stopPolling();
      startPolling();
    }
  }, [interval, enabled, store.pollingEnabled, startPolling, stopPolling]);

  return {
    startPolling,
    stopPolling,
    isPolling: isPollingRef.current,
    retryCount: retryCountRef.current,
  };
};