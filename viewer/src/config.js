// Configuration for API endpoints
// Automatically detects if running locally or on GitHub Pages

const isDevelopment = process.env.NODE_ENV === 'development';
const isGitHubPages = window.location.hostname.includes('github.io') || 
                     window.location.pathname.includes('/kleptocracy-timeline');

// Base URL configuration
const getBaseUrl = () => {
  if (isDevelopment) {
    // Local development - use static JSON server
    return 'http://localhost:8081';
  } else {
    // Production - always use relative paths for static files
    // This works for GitHub Pages, local file://, and any static hosting
    return '';
  }
};

const BASE_URL = getBaseUrl();

// API endpoint configuration
// All files are served from /api/ folder relative to the app
export const API_ENDPOINTS = {
  timeline: '/api/timeline.json',
  tags: '/api/tags.json',
  actors: '/api/actors.json',
  capture_lanes: '/api/capture_lanes.json',
  stats: '/api/stats.json',
  monitoring: '/api/monitoring.json',
  
  // Raw data URL for GitHub
  rawData: `https://raw.githubusercontent.com/${process.env.REACT_APP_REPO || 'yourusername/kleptocracy-timeline'}/main/timeline_data`
};

// Helper to transform static JSON to match API format
export const transformStaticData = (data, endpoint) => {
  // Always return data as-is since our static files have the correct format
  return data;
  
  switch (endpoint) {
    case 'timeline':
      // Static timeline_index.json might have different structure
      if (Array.isArray(data)) {
        return { events: data };
      }
      return data;
    
    case 'tags':
      // Transform static tags array to API format
      if (Array.isArray(data)) {
        return { tags: data };
      }
      return data;
    
    case 'actors':
      // Transform static actors array to API format
      if (Array.isArray(data)) {
        return { actors: data };
      }
      return data;
    
    case 'stats':
      // Stats should already be in correct format
      return data;
    
    default:
      return data;
  }
};

const config = {
  BASE_URL,
  API_ENDPOINTS,
  transformStaticData,
  isDevelopment,
  isGitHubPages
};

export default config;