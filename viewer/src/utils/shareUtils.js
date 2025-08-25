// Utility functions for sharing timeline views and events

export const generateShareUrl = (params) => {
  const url = new URL(window.location.origin + window.location.pathname);
  
  // Add event ID if sharing a specific event
  if (params.eventId) {
    url.searchParams.set('event', params.eventId);
  }
  
  // Add current filters if sharing a filtered view
  if (params.filters) {
    const { 
      selectedCaptureLanes, 
      selectedTags, 
      selectedActors, 
      dateRange, 
      searchQuery,
      viewMode 
    } = params.filters;
    
    if (selectedCaptureLanes?.length > 0) {
      url.searchParams.set('lanes', selectedCaptureLanes.join(','));
    }
    if (selectedTags?.length > 0) {
      url.searchParams.set('tags', selectedTags.join(','));
    }
    if (selectedActors?.length > 0) {
      url.searchParams.set('actors', selectedActors.join(','));
    }
    if (dateRange?.start || dateRange?.end) {
      url.searchParams.set('dateRange', `${dateRange.start || ''}:${dateRange.end || ''}`);
    }
    if (searchQuery) {
      url.searchParams.set('search', searchQuery);
    }
    if (viewMode && viewMode !== 'timeline') {
      url.searchParams.set('view', viewMode);
    }
  }
  
  return url.toString();
};

export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch (err) {
      document.body.removeChild(textArea);
      return false;
    }
  }
};

export const shareEvent = async (event, filters = null) => {
  const url = generateShareUrl({ 
    eventId: event.id, 
    filters 
  });
  
  const shareData = {
    title: `Kleptocracy Timeline: ${event.title}`,
    text: event.summary || `${event.title} - ${event.date}`,
    url: url
  };
  
  // Try native share API first (mobile)
  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return { success: true, method: 'native' };
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Error sharing:', err);
      }
    }
  }
  
  // Fallback to clipboard
  const copied = await copyToClipboard(url);
  return { 
    success: copied, 
    method: 'clipboard',
    url: url 
  };
};

export const shareFilteredView = async (filters) => {
  const url = generateShareUrl({ filters });
  
  const shareData = {
    title: 'Kleptocracy Timeline - Filtered View',
    text: 'Explore this filtered view of the Kleptocracy Timeline',
    url: url
  };
  
  // Try native share API first
  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return { success: true, method: 'native' };
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Error sharing:', err);
      }
    }
  }
  
  // Fallback to clipboard
  const copied = await copyToClipboard(url);
  return { 
    success: copied, 
    method: 'clipboard',
    url: url 
  };
};