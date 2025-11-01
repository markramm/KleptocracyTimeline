import { useState, useEffect, useCallback, useRef } from 'react';
import config from '../config';

export const useResearchMonitoring = (pollInterval = 15000) => {
  const [activities, setActivities] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const lastPollRef = useRef(new Date().toISOString());
  const isPollingRef = useRef(false);

  const pollForUpdates = useCallback(async () => {
    if (isPollingRef.current) return; // Prevent concurrent polls
    
    isPollingRef.current = true;
    setIsPolling(true);
    
    try {
      const response = await fetch(
        `${config.BASE_URL}/api/activity/recent?since=${lastPollRef.current}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch activity: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Append new activities
      if (data.activities && data.activities.length > 0) {
        setActivities(prev => {
          const newActivities = [...prev, ...data.activities];
          // Keep only last 50 activities to prevent memory issues
          return newActivities.slice(-50);
        });
        lastPollRef.current = data.timestamp;
      }
      
      setSummary(data.summary || null);
      setError(null);
      
    } catch (error) {
      console.error('Failed to poll research activity:', error);
      setError(error.message);
    } finally {
      isPollingRef.current = false;
      setIsPolling(false);
    }
  }, []);

  useEffect(() => {
    // Initial poll
    pollForUpdates();
    
    // Set up interval
    const interval = setInterval(pollForUpdates, pollInterval);
    
    return () => clearInterval(interval);
  }, [pollForUpdates, pollInterval]);

  const clearActivities = useCallback(() => {
    setActivities([]);
  }, []);

  const refreshNow = useCallback(() => {
    pollForUpdates();
  }, [pollForUpdates]);

  return { 
    activities, 
    summary, 
    error, 
    isPolling,
    clearActivities,
    refreshNow
  };
};