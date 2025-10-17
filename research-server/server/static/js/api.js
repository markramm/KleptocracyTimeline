// API Client for Timeline Viewer
class TimelineAPI {
    constructor() {
        this.baseURL = '';  // Same origin
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    // Generic HTTP request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Cache management
    getCacheKey(endpoint, params = {}) {
        const key = endpoint + JSON.stringify(params);
        return key;
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    clearCache() {
        this.cache.clear();
    }

    // Timeline Events API
    async getEvents(params = {}) {
        const cacheKey = this.getCacheKey('/api/timeline/events', params);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/timeline/events${queryString ? '?' + queryString : ''}`;
        
        const data = await this.request(endpoint);
        this.setCache(cacheKey, data);
        return data;
    }

    async getEvent(eventId) {
        const cacheKey = this.getCacheKey(`/api/timeline/events/${eventId}`);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(`/api/timeline/events/${eventId}`);
        this.setCache(cacheKey, data);
        return data;
    }

    async getEventsByDate(date) {
        const cacheKey = this.getCacheKey(`/api/timeline/events/date/${date}`);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(`/api/timeline/events/date/${date}`);
        this.setCache(cacheKey, data);
        return data;
    }

    // Timeline Metadata API
    async getActors() {
        const cacheKey = this.getCacheKey('/api/timeline/actors');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/timeline/actors');
        this.setCache(cacheKey, data);
        return data;
    }

    async getTags() {
        const cacheKey = this.getCacheKey('/api/timeline/tags');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/timeline/tags');
        this.setCache(cacheKey, data);
        return data;
    }

    async getSources() {
        const cacheKey = this.getCacheKey('/api/timeline/sources');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/timeline/sources');
        this.setCache(cacheKey, data);
        return data;
    }

    async getDateRange() {
        const cacheKey = this.getCacheKey('/api/timeline/date-range');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/timeline/date-range');
        this.setCache(cacheKey, data);
        return data;
    }

    // Timeline Filtering and Search API
    async filterEvents(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        const endpoint = `/api/timeline/filter${queryString ? '?' + queryString : ''}`;
        
        // Don't cache filter results as they change frequently
        return await this.request(endpoint);
    }

    async searchEvents(query, filters = {}) {
        const searchData = {
            query,
            ...filters
        };

        return await this.request('/api/timeline/search', {
            method: 'POST',
            body: JSON.stringify(searchData)
        });
    }

    // Viewer-Specific Data API
    async getTimelineData(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/viewer/timeline-data${queryString ? '?' + queryString : ''}`;
        
        const cacheKey = this.getCacheKey(endpoint);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(endpoint);
        this.setCache(cacheKey, data);
        return data;
    }

    async getActorNetwork(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/viewer/actor-network${queryString ? '?' + queryString : ''}`;
        
        const cacheKey = this.getCacheKey(endpoint);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(endpoint);
        this.setCache(cacheKey, data);
        return data;
    }

    async getTagCloud(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/viewer/tag-cloud${queryString ? '?' + queryString : ''}`;
        
        const cacheKey = this.getCacheKey(endpoint);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(endpoint);
        this.setCache(cacheKey, data);
        return data;
    }

    // Statistics API
    async getOverviewStats() {
        const cacheKey = this.getCacheKey('/api/viewer/stats/overview');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/viewer/stats/overview');
        this.setCache(cacheKey, data);
        return data;
    }

    async getActorStats(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/viewer/stats/actors${queryString ? '?' + queryString : ''}`;
        
        const cacheKey = this.getCacheKey(endpoint);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(endpoint);
        this.setCache(cacheKey, data);
        return data;
    }

    async getTagStats(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/viewer/stats/tags${queryString ? '?' + queryString : ''}`;
        
        const cacheKey = this.getCacheKey(endpoint);
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request(endpoint);
        this.setCache(cacheKey, data);
        return data;
    }

    async getTimelineStats() {
        const cacheKey = this.getCacheKey('/api/viewer/stats/timeline');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/viewer/stats/timeline');
        this.setCache(cacheKey, data);
        return data;
    }

    async getImportanceStats() {
        const cacheKey = this.getCacheKey('/api/viewer/stats/importance');
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const data = await this.request('/api/viewer/stats/importance');
        this.setCache(cacheKey, data);
        return data;
    }

    // Utility methods
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }

    getImportanceColor(importance) {
        if (importance >= 9) return 'var(--critical-color)';
        if (importance >= 7) return 'var(--high-color)';
        if (importance >= 5) return 'var(--medium-color)';
        return 'var(--low-color)';
    }

    getImportanceLabel(importance) {
        if (importance >= 9) return 'Critical';
        if (importance >= 7) return 'High';
        if (importance >= 5) return 'Medium';
        return 'Low';
    }
}

// Create global API instance
window.timelineAPI = new TimelineAPI();