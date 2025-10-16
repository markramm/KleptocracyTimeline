// Configuration for API endpoints
// Automatically detects if running locally or on GitHub Pages
// Phase 2: Integrated with Research Monitor v2 API

const isDevelopment = process.env.NODE_ENV === 'development';
const isGitHubPages = window.location.hostname.includes('github.io') || 
                     window.location.pathname.includes('/kleptocracy-timeline');

// Base URL configuration
const getBaseUrl = () => {
  if (isDevelopment) {
    // Local development - use Research Monitor v2 API
    return 'http://localhost:5558';
  } else if (isGitHubPages) {
    // GitHub Pages - fall back to static files for deployment
    return '';
  } else {
    // Production deployment with Research Monitor v2 API
    return process.env.REACT_APP_API_URL || 'http://localhost:5558';
  }
};

const BASE_URL = getBaseUrl();

// Determine if we should use live API or static files
const USE_LIVE_API = isDevelopment || !isGitHubPages;

// API endpoint configuration
const getLiveApiPath = (endpoint) => `${BASE_URL}/api/${endpoint}`;
const getStaticApiPath = (filename) => {
  // For GitHub Pages, detect the base path from the current URL
  if (window.location.hostname === 'markramm.github.io') {
    return `/KleptocracyTimeline/api/${filename}`;
  }
  // For local development or other hosting
  return `/api/${filename}`;
};

export const API_ENDPOINTS = USE_LIVE_API ? {
  // Research Monitor v2 API endpoints
  timeline: getLiveApiPath('timeline/events'),
  events: {
    search: getLiveApiPath('events/search'),
    byId: (id) => getLiveApiPath(`events/${id}`),
    timeline: getLiveApiPath('timeline/events'),
    filter: getLiveApiPath('timeline/filter'),
    advancedSearch: getLiveApiPath('timeline/search')
  },
  metadata: {
    actors: getLiveApiPath('timeline/actors'),
    tags: getLiveApiPath('timeline/tags'), 
    sources: getLiveApiPath('timeline/sources'),
    dateRange: getLiveApiPath('timeline/date-range')
  },
  visualization: {
    actorNetwork: getLiveApiPath('viewer/actor-network'),
    tagCloud: getLiveApiPath('viewer/tag-cloud'),
    timelineData: getLiveApiPath('viewer/timeline-data')
  },
  stats: {
    overview: getLiveApiPath('viewer/stats/overview'),
    actors: getLiveApiPath('viewer/stats/actors'),
    tags: getLiveApiPath('viewer/stats/tags'),
    importance: getLiveApiPath('viewer/stats/importance'),
    patterns: getLiveApiPath('viewer/stats/patterns')
  },
  system: {
    health: getLiveApiPath('server/health'),
    stats: getLiveApiPath('stats'),
    docs: getLiveApiPath('docs')
  }
} : {
  // Legacy static file endpoints (fallback)
  timeline: getStaticApiPath('timeline.json'),
  tags: getStaticApiPath('tags.json'),
  actors: getStaticApiPath('actors.json'),
  capture_lanes: getStaticApiPath('capture_lanes.json'),
  stats: getStaticApiPath('stats.json'),
  monitoring: getStaticApiPath('monitoring.json')
};

// Raw data URL for GitHub (legacy)
export const RAW_DATA_URL = `https://raw.githubusercontent.com/${process.env.REACT_APP_REPO || 'yourusername/kleptocracy-timeline'}/main/timeline_data`;

// Helper to transform static JSON to match API format
export const transformStaticData = (data, endpoint) => {
  // Always return data as-is since our static files have the correct format
  return data;
  
  /* Unreachable code - keeping for reference
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
  */
};

const config = {
  BASE_URL,
  API_ENDPOINTS,
  USE_LIVE_API,
  transformStaticData,
  isDevelopment,
  isGitHubPages,
  RAW_DATA_URL
};

export { USE_LIVE_API };
export default config;