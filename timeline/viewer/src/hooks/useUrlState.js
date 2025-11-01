import { useState, useEffect, useCallback } from 'react';

// Helper functions for URL state management
const encodeArrayParam = (arr) => arr.length > 0 ? arr.join(',') : '';
const decodeArrayParam = (param) => param ? param.split(',').filter(Boolean) : [];

const encodeDateRange = (dateRange) => {
  if (!dateRange.start && !dateRange.end) return '';
  return `${dateRange.start || ''}:${dateRange.end || ''}`;
};

const decodeDateRange = (param) => {
  if (!param) return { start: null, end: null };
  const [start, end] = param.split(':');
  return { 
    start: start || null, 
    end: end || null 
  };
};

const encodeTimelineControls = (controls) => {
  return `${controls.compactMode},${controls.sortBy},${controls.filterImportance},${controls.showMinimap}`;
};

const decodeTimelineControls = (param) => {
  if (!param) return {
    compactMode: 'medium',
    sortBy: 'date',
    filterImportance: 0,
    showMinimap: true
  };
  
  const [compactMode, sortBy, filterImportance, showMinimap] = param.split(',');
  return {
    compactMode: compactMode || 'medium',
    sortBy: sortBy || 'date',
    filterImportance: parseInt(filterImportance) || 0,
    showMinimap: showMinimap === 'true'
  };
};

export const useUrlState = () => {
  const [urlState, setUrlState] = useState(null);

  // Extract state from URL parameters
  const getStateFromUrl = useCallback(() => {
    const params = new URLSearchParams(window.location.search);
    
    return {
      selectedTags: decodeArrayParam(params.get('tags')),
      selectedActors: decodeArrayParam(params.get('actors')),
      selectedCaptureLanes: decodeArrayParam(params.get('lanes')),
      dateRange: decodeDateRange(params.get('dateRange')),
      searchQuery: params.get('search') || '',
      viewMode: params.get('view') || 'timeline',
      timelineControls: decodeTimelineControls(params.get('timeline')),
      zoomLevel: parseFloat(params.get('zoom')) || 1,
      showFilters: params.get('filters') !== 'false',
      showStats: params.get('stats') === 'true',
      selectedEventId: params.get('event') || null,
      showLanding: params.get('landing') === 'true' || (!params.toString() && !window.location.hash)
    };
  }, []);

  // Update URL with current state
  const updateUrl = useCallback((state) => {
    const params = new URLSearchParams();
    
    // Only add non-default values to keep URLs clean
    if (state.selectedTags?.length > 0) {
      params.set('tags', encodeArrayParam(state.selectedTags));
    }
    if (state.selectedActors?.length > 0) {
      params.set('actors', encodeArrayParam(state.selectedActors));
    }
    if (state.selectedCaptureLanes?.length > 0) {
      params.set('lanes', encodeArrayParam(state.selectedCaptureLanes));
    }
    if (state.dateRange?.start || state.dateRange?.end) {
      params.set('dateRange', encodeDateRange(state.dateRange));
    }
    if (state.searchQuery) {
      params.set('search', state.searchQuery);
    }
    if (state.viewMode && state.viewMode !== 'timeline') {
      params.set('view', state.viewMode);
    }
    if (state.timelineControls) {
      const defaultControls = 'medium,date,0,true';
      const currentControls = encodeTimelineControls(state.timelineControls);
      if (currentControls !== defaultControls) {
        params.set('timeline', currentControls);
      }
    }
    if (state.zoomLevel && state.zoomLevel !== 1) {
      params.set('zoom', state.zoomLevel.toString());
    }
    if (state.showFilters === false) {
      params.set('filters', 'false');
    }
    if (state.showStats === true) {
      params.set('stats', 'true');
    }
    if (state.selectedEventId) {
      params.set('event', state.selectedEventId);
    }
    if (state.showLanding === true) {
      params.set('landing', 'true');
    }

    const newUrl = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname;
    
    // Use replaceState to avoid creating browser history entries for every filter change
    window.history.replaceState(null, '', newUrl);
  }, []);

  // Initialize state from URL on mount
  useEffect(() => {
    setUrlState(getStateFromUrl());
  }, [getStateFromUrl]);

  // Listen for browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      setUrlState(getStateFromUrl());
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [getStateFromUrl]);

  return {
    urlState,
    updateUrl,
    getStateFromUrl
  };
};

export default useUrlState;