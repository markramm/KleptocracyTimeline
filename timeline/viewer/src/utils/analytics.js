// Analytics utilities for privacy-respecting tracking
// Supports both Plausible and GoatCounter

/**
 * Track custom events with Plausible or GA4
 * Docs: https://plausible.io/docs/custom-event-goals
 * GA4 Docs: https://developers.google.com/analytics/devguides/collection/gtagjs/events
 */
export const trackEvent = (eventName, props = {}) => {
  // Track with Plausible if loaded
  if (window.plausible) {
    window.plausible(eventName, { props });
  }
  
  // Track with Google Analytics 4 if loaded
  if (window.gtag) {
    window.gtag('event', eventName, {
      custom_parameter: props
    });
  }
  
  // For development/debugging
  if (process.env.NODE_ENV === 'development') {
    console.log('Analytics Event:', eventName, props);
  }
};

/**
 * Track page views (for single-page app navigation)
 */
export const trackPageView = (path) => {
  // Plausible automatically tracks page views, but for SPA we might need manual tracking
  if (window.plausible) {
    window.plausible('pageview');
  }
  
  // GoatCounter tracking
  if (window.goatcounter && window.goatcounter.count) {
    window.goatcounter.count({
      path: path,
      title: document.title,
      referrer: document.referrer,
      event: false
    });
  }
};

/**
 * Common events to track
 */
export const AnalyticsEvents = {
  // Search and filtering
  SEARCH: 'Search',
  FILTER_TAG: 'Filter by Tag',
  FILTER_ACTOR: 'Filter by Actor',
  FILTER_CAPTURE_LANE: 'Filter by Capture Lane',
  FILTER_DATE_RANGE: 'Filter by Date Range',
  
  // Event interactions
  VIEW_EVENT_DETAILS: 'View Event Details',
  CLICK_SOURCE_LINK: 'Click Source Link',
  SHARE_EVENT: 'Share Event',
  BOOKMARK_EVENT: 'Bookmark Event',
  
  // Navigation
  CHANGE_VIEW_MODE: 'Change View Mode',
  TOGGLE_COMPACT_MODE: 'Toggle Compact Mode',
  USE_KEYBOARD_SHORTCUT: 'Use Keyboard Shortcut',
  
  // Contributing
  CLICK_CONTRIBUTE: 'Click Contribute',
  REPORT_BROKEN_LINK: 'Report Broken Link',
  VIEW_ON_GITHUB: 'View on GitHub',
  
  // Network graph
  VIEW_NETWORK_GRAPH: 'View Network Graph',
  
  // Timeline controls
  CHANGE_ZOOM: 'Change Zoom Level',
  TOGGLE_MINIMAP: 'Toggle Minimap',
  CHANGE_SORT: 'Change Sort Order'
};

/**
 * Track search queries (anonymized)
 */
export const trackSearch = (query) => {
  // Only track that a search happened, not the actual query for privacy
  trackEvent(AnalyticsEvents.SEARCH, {
    query_length: query.length,
    has_results: true // This would be determined by the search results
  });
};

/**
 * Track filter usage
 */
export const trackFilter = (filterType, value) => {
  const eventMap = {
    tag: AnalyticsEvents.FILTER_TAG,
    actor: AnalyticsEvents.FILTER_ACTOR,
    captureLane: AnalyticsEvents.FILTER_CAPTURE_LANE,
    dateRange: AnalyticsEvents.FILTER_DATE_RANGE
  };
  
  trackEvent(eventMap[filterType] || 'Filter', {
    filter_type: filterType,
    // Don't track actual values for privacy
    has_value: !!value
  });
};

/**
 * Track event interactions
 */
export const trackEventInteraction = (action, eventId, metadata = {}) => {
  trackEvent(action, {
    // Don't track specific event IDs for privacy
    // Just track patterns
    event_year: eventId?.substring(0, 4),
    ...metadata
  });
};

/**
 * Initialize analytics
 */
export const initAnalytics = () => {
  // Add Plausible callback support
  window.plausible = window.plausible || function() { 
    (window.plausible.q = window.plausible.q || []).push(arguments);
  };
  
  // Track initial page view
  trackPageView(window.location.pathname);
  
  // Log analytics status
  if (process.env.NODE_ENV === 'development') {
    console.log('Analytics initialized');
  }
};