// GitHub integration utilities for timeline events

const GITHUB_REPO = 'https://github.com/markramm/KleptocracyTimeline';
// const GITHUB_RAW = 'https://raw.githubusercontent.com/markramm/KleptocracyTimeline/main';

/**
 * Generate GitHub edit URL for an event YAML file
 */
export const getEventEditUrl = (eventId) => {
  return `${GITHUB_REPO}/edit/main/timeline_data/events/${eventId}.yaml`;
};

/**
 * Generate GitHub view URL for an event YAML file
 */
export const getEventViewUrl = (eventId) => {
  return `${GITHUB_REPO}/blob/main/timeline_data/events/${eventId}.yaml`;
};

/**
 * Generate GitHub history URL for an event
 */
export const getEventHistoryUrl = (eventId) => {
  return `${GITHUB_REPO}/commits/main/timeline_data/events/${eventId}.yaml`;
};

/**
 * Generate new issue URL with pre-filled template for broken link
 */
export const createBrokenLinkIssue = (eventId, brokenUrl, errorType = '404 Not Found') => {
  const params = new URLSearchParams({
    template: 'broken-link.yml',
    title: `[Broken Link] ${eventId}`,
    labels: 'broken-link,sources'
  });
  
  // Pre-fill the form fields
  const body = `
Event ID: ${eventId}
Broken URL: ${brokenUrl}
Error Type: ${errorType}
  `.trim();
  
  params.append('body', body);
  
  return `${GITHUB_REPO}/issues/new?${params.toString()}`;
};

/**
 * Generate new issue URL for event correction
 */
export const createCorrectionIssue = (eventId, correctionType = 'Other') => {
  const params = new URLSearchParams({
    template: 'event-correction.yml',
    title: `[Correction] ${eventId}`,
    labels: 'correction,needs-review'
  });
  
  return `${GITHUB_REPO}/issues/new?${params.toString()}`;
};

/**
 * Generate new issue URL for submitting a new event
 */
export const createNewEventIssue = (date = '', title = '') => {
  const params = new URLSearchParams({
    template: 'new-event.yml',
    title: `[New Event] ${title}`,
    labels: 'new-event,needs-validation'
  });
  
  if (date) {
    const body = `Date: ${date}`;
    params.append('body', body);
  }
  
  return `${GITHUB_REPO}/issues/new?${params.toString()}`;
};

/**
 * Generate URL to view all issues for a specific event
 */
export const getEventIssuesUrl = (eventId) => {
  const params = new URLSearchParams({
    q: `is:issue "${eventId}"`
  });
  
  return `${GITHUB_REPO}/issues?${params.toString()}`;
};

/**
 * Generate URL for creating a PR with event changes
 */
export const createEventPR = (eventId) => {
  return `${GITHUB_REPO}/compare/main...main?quick_pull=1&title=Update+event+${eventId}`;
};

/**
 * Check if a URL is likely broken (basic client-side check)
 * Returns a promise that resolves to an error type or null
 */
export const checkLinkStatus = async (url) => {
  try {
    // Try to fetch with no-cors mode (limited but won't trigger CORS errors)
    await fetch(url, {
      method: 'HEAD',
      mode: 'no-cors'
    });
    
    // In no-cors mode, we can't read the status, but if it doesn't throw, 
    // the server at least exists
    return null;
  } catch (error) {
    // Network error likely means the site doesn't exist
    return 'Site No Longer Exists';
  }
};

/**
 * Try to find an archived version of a URL
 */
export const getArchiveUrl = (url, date = '') => {
  // If we have a date, try to get archive from around that time
  const dateParam = date ? date.replace(/-/g, '') : '2';
  return `https://web.archive.org/web/${dateParam}/${url}`;
};

/**
 * Generate a shareable GitHub link for contributing
 */
export const getContributeUrl = () => {
  return `${GITHUB_REPO}#contributing`;
};

/**
 * Generate link to validation guide
 */
export const getValidationGuideUrl = () => {
  return `${GITHUB_REPO}#validation`;
};

/**
 * Helper to open GitHub URLs in new tab
 */
export const openGitHub = (url) => {
  window.open(url, '_blank', 'noopener,noreferrer');
};

/**
 * Format event ID from date and title for consistency
 */
export const formatEventId = (date, title) => {
  const dateStr = date.replace(/\//g, '-');
  const titleStr = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 50);
  
  return `${dateStr}--${titleStr}`;
};