// Configuration for API endpoints
// Automatically detects if running locally or on GitHub Pages

const isDevelopment = process.env.NODE_ENV === 'development';
const isGitHubPages = window.location.hostname.includes('github.io');

// Base URL configuration
const getBaseUrl = () => {
  if (isDevelopment) {
    // Local development - use static JSON server
    return 'http://localhost:8081';
  } else if (isGitHubPages) {
    // GitHub Pages - use static JSON files
    return `${window.location.origin}${process.env.PUBLIC_URL || ''}`;
  } else {
    // Other production deployments
    return process.env.REACT_APP_API_URL || window.location.origin;
  }
};

const BASE_URL = getBaseUrl();

// API endpoint configuration
export const API_ENDPOINTS = {
  timeline: isDevelopment
    ? `${BASE_URL}/timeline.json`
    : isGitHubPages 
    ? `${BASE_URL}/timeline_index.json`
    : `${BASE_URL}/api/timeline`,
  
  tags: isDevelopment
    ? `${BASE_URL}/tags.json`
    : isGitHubPages
    ? `${BASE_URL}/api/tags.json`
    : `${BASE_URL}/api/tags`,
  
  actors: isDevelopment
    ? `${BASE_URL}/actors.json`
    : isGitHubPages
    ? `${BASE_URL}/api/actors.json`
    : `${BASE_URL}/api/actors`,
  
  stats: isDevelopment
    ? `${BASE_URL}/stats.json`
    : isGitHubPages
    ? `${BASE_URL}/api/stats.json`
    : `${BASE_URL}/api/stats`,
  
  // Raw data URL for GitHub
  rawData: `https://raw.githubusercontent.com/${process.env.REACT_APP_REPO || 'yourusername/kleptocracy-timeline'}/main/timeline_data`
};

// Helper to transform static JSON to match API format
export const transformStaticData = (data, endpoint) => {
  if (!isGitHubPages) return data;
  
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

export default {
  BASE_URL,
  API_ENDPOINTS,
  transformStaticData,
  isDevelopment,
  isGitHubPages
};