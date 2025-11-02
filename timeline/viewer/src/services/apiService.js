/**
 * API Service Layer for Research Monitor v2 Integration
 * Provides clean abstraction between React components and API endpoints
 * Handles both live API and static file fallbacks
 */

import axios from 'axios';
import { API_ENDPOINTS, USE_LIVE_API, transformStaticData } from '../config';

// Create axios instance with default configuration
const apiClient = axios.create({
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    // Enhance error with context
    if (error.response) {
      // Server responded with error status
      error.context = {
        status: error.response.status,
        statusText: error.response.statusText,
        url: error.config?.url,
      };
    } else if (error.request) {
      // Network error
      error.context = {
        type: 'network',
        url: error.config?.url,
      };
    }
    
    return Promise.reject(error);
  }
);

/**
 * Timeline Events API
 */
export const timelineEventsAPI = {
  /**
   * Get paginated timeline events with optional filtering
   */
  async getEvents({
    page = 1,
    per_page = 50,
    start_date = null,
    end_date = null,
    importance_min = null,
    importance_max = null,
    tags = null,
    actors = null,
    search = null
  } = {}) {
    if (!USE_LIVE_API) {
      // Fallback to static data with cache busting
      const cacheBuster = `?v=${Date.now()}`;
      const response = await apiClient.get(API_ENDPOINTS.timeline + cacheBuster);
      return transformStaticData(response.data, 'timeline');
    }

    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (per_page) params.append('per_page', per_page);
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);
    if (importance_min) params.append('importance_min', importance_min);
    if (importance_max) params.append('importance_max', importance_max);
    if (tags) params.append('tags', tags);
    if (actors) params.append('actors', actors);
    if (search) params.append('search', search);

    const response = await apiClient.get(`${API_ENDPOINTS.events.timeline}?${params}`);
    return response.data;
  },

  /**
   * Get single event by ID
   */
  async getEventById(eventId) {
    if (!USE_LIVE_API) {
      throw new Error('Event by ID not supported in static mode');
    }

    const response = await apiClient.get(API_ENDPOINTS.events.byId(eventId));
    return response.data;
  },

  /**
   * Search events with full-text search
   */
  async searchEvents({
    q = '',
    limit = 50,
    offset = 0,
    start_date = null,
    end_date = null,
    min_importance = null,
    max_importance = null,
    tags = null,
    actors = null
  } = {}) {
    if (!USE_LIVE_API) {
      // Fallback: client-side search on static data
      const allEvents = await this.getEvents();
      return {
        events: allEvents.events?.filter(event => 
          event.title?.toLowerCase().includes(q.toLowerCase()) ||
          event.summary?.toLowerCase().includes(q.toLowerCase())
        ).slice(offset, offset + limit) || [],
        count: 0,
        total: 0,
        query: q
      };
    }

    const params = new URLSearchParams();
    if (q) params.append('q', q);
    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);
    if (min_importance) params.append('min_importance', min_importance);
    if (max_importance) params.append('max_importance', max_importance);
    if (tags) params.append('tags', tags);
    if (actors) params.append('actors', actors);

    const response = await apiClient.get(`${API_ENDPOINTS.events.search}?${params}`);
    return response.data;
  },

  /**
   * Advanced search with complex filters
   */
  async advancedSearch(searchRequest) {
    if (!USE_LIVE_API) {
      throw new Error('Advanced search not supported in static mode');
    }

    const response = await apiClient.post(API_ENDPOINTS.events.advancedSearch, searchRequest);
    return response.data;
  }
};

/**
 * Timeline Metadata API
 */
export const metadataAPI = {
  /**
   * Get all unique actors with event counts
   */
  async getActors({ min_events = null, limit = null } = {}) {
    if (!USE_LIVE_API) {
      const cacheBuster = `?v=${Date.now()}`;
      const response = await apiClient.get(API_ENDPOINTS.actors + cacheBuster);
      return transformStaticData(response.data, 'actors');
    }

    const params = new URLSearchParams();
    if (min_events) params.append('min_events', min_events);
    if (limit) params.append('limit', limit);

    const response = await apiClient.get(`${API_ENDPOINTS.metadata.actors}?${params}`);
    return response.data;
  },

  /**
   * Get all unique tags with usage counts
   */
  async getTags({ min_frequency = null, limit = null } = {}) {
    if (!USE_LIVE_API) {
      const cacheBuster = `?v=${Date.now()}`;
      const response = await apiClient.get(API_ENDPOINTS.tags + cacheBuster);
      return transformStaticData(response.data, 'tags');
    }

    const params = new URLSearchParams();
    if (min_frequency) params.append('min_frequency', min_frequency);
    if (limit) params.append('limit', limit);

    const response = await apiClient.get(`${API_ENDPOINTS.metadata.tags}?${params}`);
    return response.data;
  },

  /**
   * Get all unique source domains
   */
  async getSources({ limit = null } = {}) {
    if (!USE_LIVE_API) {
      return { sources: [] }; // Not available in static mode
    }

    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);

    const response = await apiClient.get(`${API_ENDPOINTS.metadata.sources}?${params}`);
    return response.data;
  },

  /**
   * Get timeline date range
   */
  async getDateRange() {
    if (!USE_LIVE_API) {
      return { date_range: { min_date: null, max_date: null }, total_events: 0 };
    }

    const response = await apiClient.get(API_ENDPOINTS.metadata.dateRange);
    return response.data;
  }
};

/**
 * Visualization Data API
 */
export const visualizationAPI = {
  /**
   * Get actor network graph data
   */
  async getActorNetwork({
    min_connections = 2,
    max_actors = 50,
    date_from = null,
    date_to = null
  } = {}) {
    if (!USE_LIVE_API) {
      return { network: { nodes: [], edges: [] }, metadata: {} };
    }

    const params = new URLSearchParams();
    if (min_connections) params.append('min_connections', min_connections);
    if (max_actors) params.append('max_actors', max_actors);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);

    const response = await apiClient.get(`${API_ENDPOINTS.visualization.actorNetwork}?${params}`);
    return response.data;
  },

  /**
   * Get tag cloud data
   */
  async getTagCloud({
    min_frequency = 2,
    max_tags = 50,
    date_from = null,
    date_to = null
  } = {}) {
    if (!USE_LIVE_API) {
      return { tag_cloud: [], metadata: {} };
    }

    const params = new URLSearchParams();
    if (min_frequency) params.append('min_frequency', min_frequency);
    if (max_tags) params.append('max_tags', max_tags);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);

    const response = await apiClient.get(`${API_ENDPOINTS.visualization.tagCloud}?${params}`);
    return response.data;
  },

  /**
   * Get timeline visualization data
   */
  async getTimelineData({
    granularity = 'year',
    date_from = null,
    date_to = null
  } = {}) {
    if (!USE_LIVE_API) {
      return { timeline: [], metadata: {} };
    }

    const params = new URLSearchParams();
    if (granularity) params.append('granularity', granularity);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);

    const response = await apiClient.get(`${API_ENDPOINTS.visualization.timelineData}?${params}`);
    return response.data;
  }
};

/**
 * Statistics API
 */
export const statisticsAPI = {
  /**
   * Get overview statistics
   */
  async getOverview() {
    if (!USE_LIVE_API) {
      const cacheBuster = `?v=${Date.now()}`;
      const response = await apiClient.get(API_ENDPOINTS.stats + cacheBuster);
      return transformStaticData(response.data, 'stats');
    }

    const response = await apiClient.get(API_ENDPOINTS.stats.overview);
    return response.data;
  },

  /**
   * Get actor statistics
   */
  async getActorStats({
    limit = 20,
    date_from = null,
    date_to = null
  } = {}) {
    if (!USE_LIVE_API) {
      return { actor_stats: [], metadata: {} };
    }

    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);

    const response = await apiClient.get(`${API_ENDPOINTS.stats.actors}?${params}`);
    return response.data;
  },

  /**
   * Get tag statistics
   */
  async getTagStats({
    limit = 20,
    date_from = null,
    date_to = null
  } = {}) {
    if (!USE_LIVE_API) {
      return { tag_stats: [], metadata: {} };
    }

    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);

    const response = await apiClient.get(`${API_ENDPOINTS.stats.tags}?${params}`);
    return response.data;
  },

  /**
   * Get importance distribution
   */
  async getImportanceStats() {
    if (!USE_LIVE_API) {
      return { distribution: {}, by_year: {} };
    }

    const response = await apiClient.get(API_ENDPOINTS.stats.importance);
    return response.data;
  },

  /**
   * Get timeline patterns
   */
  async getPatterns() {
    if (!USE_LIVE_API) {
      return { yearly_trends: {}, patterns: [] };
    }

    const response = await apiClient.get(API_ENDPOINTS.stats.patterns);
    return response.data;
  }
};

/**
 * System API
 */
export const systemAPI = {
  /**
   * Check API health
   */
  async getHealth() {
    if (!USE_LIVE_API) {
      return { status: 'static', mode: 'static-files' };
    }

    const response = await apiClient.get(API_ENDPOINTS.system.health);
    return response.data;
  },

  /**
   * Get system statistics
   */
  async getSystemStats() {
    if (!USE_LIVE_API) {
      return { mode: 'static' };
    }

    const response = await apiClient.get(API_ENDPOINTS.system.stats);
    return response.data;
  }
};

/**
 * Combined API service
 */
const apiService = {
  events: timelineEventsAPI,
  metadata: metadataAPI,
  visualization: visualizationAPI,
  stats: statisticsAPI,
  system: systemAPI,
  
  // Configuration helpers
  isLiveMode: () => USE_LIVE_API,
  getApiEndpoints: () => API_ENDPOINTS,
  
  // Health check
  async checkConnection() {
    try {
      const health = await this.system.getHealth();
      return { connected: true, health };
    } catch (error) {
      return { connected: false, error: error.message };
    }
  }
};

export default apiService;