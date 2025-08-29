import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import LandingPage from './components/LandingPage';
import EnhancedTimelineView from './components/EnhancedTimelineView';
import FilterPanel from './components/FilterPanel';
import EventDetails from './components/EventDetails';
import StatsPanel from './components/StatsPanel';
import SearchBar from './components/SearchBar';
import ViewToggle from './components/ViewToggle';
import NetworkGraph from './components/NetworkGraph';
import DownloadMenu from './components/DownloadMenu';
import { API_ENDPOINTS, transformStaticData } from './config';
import { useUrlState } from './hooks/useUrlState';
import { shareEvent, shareFilteredView } from './utils/shareUtils';
import { createNewEventIssue, openGitHub } from './utils/githubUtils';
import { initAnalytics, trackEvent, trackFilter, AnalyticsEvents } from './utils/analytics';
import { 
  Filter, 
  BarChart3,
  Loader2,
  AlertCircle,
  Share2,
  Plus
} from 'lucide-react';
import './App.css';

function App() {
  // URL state management
  const { urlState, updateUrl } = useUrlState();
  
  // State management
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLanding, setShowLanding] = useState(true);
  const [shareNotification, setShareNotification] = useState(null);
  
  // Filter states - initialize from URL or defaults
  const [selectedTags, setSelectedTags] = useState([]);
  const [selectedActors, setSelectedActors] = useState([]);
  const [selectedCaptureLanes, setSelectedCaptureLanes] = useState([]);
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('timeline');
  const [sortOrder, setSortOrder] = useState('chronological');
  const [minImportance, setMinImportance] = useState(0);
  
  // UI states - initialize from URL or defaults
  const [showFilters, setShowFilters] = useState(true);
  const [showStats, setShowStats] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  
  // Timeline view controls - initialize from URL or defaults
  const [timelineControls, setTimelineControls] = useState({
    compactMode: 'medium',
    sortBy: 'date',
    filterImportance: 0,
    showMinimap: true
  });
  
  // Metadata
  const [allTags, setAllTags] = useState([]);
  const [allActors, setAllActors] = useState([]);
  const [allCaptureLanes, setAllCaptureLanes] = useState([]);
  const [stats, setStats] = useState(null);

  // Initialize state from URL when urlState is available
  useEffect(() => {
    if (urlState) {
      setSelectedCaptureLanes(urlState.selectedCaptureLanes || []);
      setSelectedTags(urlState.selectedTags || []);
      setSelectedActors(urlState.selectedActors || []);
      setDateRange(urlState.dateRange || { start: null, end: null });
      setSearchQuery(urlState.searchQuery || '');
      setViewMode(urlState.viewMode || 'timeline');
      setSortOrder(urlState.sortOrder || 'chronological');
      setMinImportance(urlState.minImportance || 0);
      setTimelineControls(urlState.timelineControls || {
        compactMode: 'medium',
        sortBy: 'date',
        filterImportance: 0,
        showMinimap: true
      });
      setZoomLevel(urlState.zoomLevel || 1);
      setShowFilters(urlState.showFilters !== false);
      setShowStats(urlState.showStats || false);
      setShowLanding(urlState.showLanding || false);
      
      // Handle deep link to specific event
      if (urlState.selectedEventId && events.length > 0) {
        const event = events.find(e => e.id === urlState.selectedEventId);
        if (event) {
          setSelectedEvent(event);
          setShowLanding(false);
        }
      }
    }
  }, [urlState, events]);

  // Initialize analytics and load data
  useEffect(() => {
    initAnalytics();
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [eventsRes, tagsRes, actorsRes, captureLanesRes, statsRes] = await Promise.all([
        axios.get(API_ENDPOINTS.timeline),
        axios.get(API_ENDPOINTS.tags),
        axios.get(API_ENDPOINTS.actors),
        axios.get(API_ENDPOINTS.capture_lanes),
        axios.get(API_ENDPOINTS.stats)
      ]);
      
      // Transform data if using static files
      const eventsData = transformStaticData(eventsRes.data, 'timeline');
      const tagsData = transformStaticData(tagsRes.data, 'tags');
      const actorsData = transformStaticData(actorsRes.data, 'actors');
      const captureLanesData = transformStaticData(captureLanesRes.data, 'capture_lanes');
      const statsData = transformStaticData(statsRes.data, 'stats');
      
      setEvents(eventsData.events || eventsData);
      setFilteredEvents(eventsData.events || eventsData);
      setAllTags(tagsData.tags || tagsData);
      setAllActors(actorsData.actors || actorsData);
      setAllCaptureLanes(captureLanesData.capture_lanes || captureLanesData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError('Failed to load timeline data. Please ensure the server is running or check your connection.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...events];

    // Capture lanes filter (primary filter)
    if (selectedCaptureLanes.length > 0) {
      filtered = filtered.filter(event => 
        event.capture_lanes && selectedCaptureLanes.some(lane => event.capture_lanes.includes(lane))
      );
    }

    // Tag filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter(event => 
        event.tags && selectedTags.some(tag => event.tags.includes(tag))
      );
    }

    // Actor filter
    if (selectedActors.length > 0) {
      filtered = filtered.filter(event =>
        event.actors && selectedActors.some(actor => event.actors.includes(actor))
      );
    }

    // Date range filter
    if (dateRange.start) {
      filtered = filtered.filter(event => event.date >= dateRange.start);
    }
    if (dateRange.end) {
      filtered = filtered.filter(event => event.date <= dateRange.end);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(event =>
        event.title?.toLowerCase().includes(query) ||
        event.summary?.toLowerCase().includes(query) ||
        event.notes?.toLowerCase().includes(query) ||
        event.actors?.some(actor => actor.toLowerCase().includes(query)) ||
        event.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Importance filter
    if (minImportance > 0) {
      filtered = filtered.filter(event => 
        (event.importance || 0) >= minImportance
      );
    }

    // Apply sorting - create a new array to ensure React detects the change
    const sorted = [...filtered];
    switch (sortOrder) {
      case 'newest':
        sorted.sort((a, b) => {
          const dateA = a.date || '';
          const dateB = b.date || '';
          return dateB.localeCompare(dateA);
        });
        break;
      case 'importance':
        sorted.sort((a, b) => (b.importance || 0) - (a.importance || 0));
        break;
      case 'alphabetical':
        sorted.sort((a, b) => {
          const titleA = a.title || '';
          const titleB = b.title || '';
          return titleA.localeCompare(titleB);
        });
        break;
      case 'chronological':
      default:
        sorted.sort((a, b) => {
          const dateA = a.date || '';
          const dateB = b.date || '';
          return dateA.localeCompare(dateB);
        });
        break;
    }

    setFilteredEvents(sorted);
  }, [events, selectedCaptureLanes, selectedTags, selectedActors, dateRange, searchQuery, sortOrder, minImportance]);

  // Event handlers
  const handleEventClick = useCallback((event) => {
    setSelectedEvent(event);
    trackEvent(AnalyticsEvents.VIEW_EVENT_DETAILS, {
      event_year: event.date?.substring(0, 4),
      event_importance: event.importance
    });
  }, []);

  const handleTagClick = useCallback((tag) => {
    const newTags = selectedTags.includes(tag) 
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    
    setSelectedTags(newTags);
    trackFilter('tag', tag);
    
    // Update URL with new tags
    if (updateUrl) {
      updateUrl({
        selectedCaptureLanes,
        selectedTags: newTags,
        selectedActors,
        dateRange,
        searchQuery,
        viewMode,
        timelineControls,
        zoomLevel,
        showFilters,
        showStats
      });
    }
  }, [updateUrl, selectedTags, selectedActors, dateRange, searchQuery, viewMode, timelineControls, zoomLevel, showFilters, showStats, selectedCaptureLanes]);

  const handleActorClick = useCallback((actor) => {
    const newActors = selectedActors.includes(actor)
      ? selectedActors.filter(a => a !== actor)
      : [...selectedActors, actor];
    
    setSelectedActors(newActors);
    
    // Update URL with new actors
    if (updateUrl) {
      updateUrl({
        selectedCaptureLanes,
        selectedTags,
        selectedActors: newActors,
        dateRange,
        searchQuery,
        viewMode,
        timelineControls,
        zoomLevel,
        showFilters,
        showStats
      });
    }
  }, [updateUrl, selectedCaptureLanes, selectedTags, selectedActors, dateRange, searchQuery, viewMode, timelineControls, zoomLevel, showFilters, showStats]);

  const handleCaptureLaneClick = useCallback((lane) => {
    const newLanes = selectedCaptureLanes.includes(lane)
      ? selectedCaptureLanes.filter(l => l !== lane)
      : [...selectedCaptureLanes, lane];
    
    setSelectedCaptureLanes(newLanes);
    
    // Update URL with new capture lanes
    if (updateUrl) {
      updateUrl({
        selectedCaptureLanes: newLanes,
        selectedTags,
        selectedActors,
        dateRange,
        searchQuery,
        viewMode,
        timelineControls,
        zoomLevel,
        showFilters,
        showStats
      });
    }
  }, [updateUrl, selectedCaptureLanes, selectedTags, selectedActors, dateRange, searchQuery, viewMode, timelineControls, zoomLevel, showFilters, showStats]);
  
  const handleTimelineControlsChange = useCallback((newControls) => {
    setTimelineControls(newControls);
    // Update URL with new timeline controls
    if (updateUrl) {
      updateUrl({
        selectedCaptureLanes,
        selectedTags,
        selectedActors,
        dateRange,
        searchQuery,
        viewMode,
        timelineControls: newControls,
        zoomLevel,
        showFilters,
        showStats
      });
    }
  }, [updateUrl, selectedTags, selectedActors, dateRange, searchQuery, viewMode, zoomLevel, showFilters, showStats, selectedCaptureLanes]);

  const clearFilters = useCallback(() => {
    const defaultState = {
      selectedCaptureLanes: [],
      selectedTags: [],
      selectedActors: [],
      dateRange: { start: null, end: null },
      searchQuery: '',
      sortOrder: 'chronological',
      minImportance: 0,
      viewMode,
      timelineControls: {
        compactMode: 'medium',
        sortBy: 'date',
        filterImportance: 0,
        showMinimap: true
      },
      zoomLevel,
      showFilters,
      showStats
    };
    
    setSelectedCaptureLanes(defaultState.selectedCaptureLanes);
    setSelectedTags(defaultState.selectedTags);
    setSelectedActors(defaultState.selectedActors);
    setDateRange(defaultState.dateRange);
    setSearchQuery(defaultState.searchQuery);
    setSortOrder(defaultState.sortOrder);
    setMinImportance(defaultState.minImportance);
    setTimelineControls(defaultState.timelineControls);
    
    // Update URL to reflect cleared state
    if (updateUrl) {
      updateUrl(defaultState);
    }
  }, [updateUrl, viewMode, zoomLevel, showFilters, showStats]);

  // Compute timeline groups for better visualization
  const timelineGroups = useMemo(() => {
    const groups = {};
    filteredEvents.forEach(event => {
      const year = event.date?.substring(0, 4) || 'Unknown';
      if (!groups[year]) {
        groups[year] = [];
      }
      groups[year].push(event);
    });
    return groups;
  }, [filteredEvents]);

  // Handler for entering timeline from landing page
  const handleEnterTimeline = useCallback(() => {
    setShowLanding(false);
    if (updateUrl) {
      updateUrl({
        selectedCaptureLanes,
        selectedTags,
        selectedActors,
        dateRange,
        searchQuery,
        viewMode,
        timelineControls,
        zoomLevel,
        showFilters,
        showStats,
        showLanding: false
      });
    }
  }, [updateUrl, selectedCaptureLanes, selectedTags, selectedActors, dateRange, searchQuery, viewMode, timelineControls, zoomLevel, showFilters, showStats]);

  // Handler for sharing an event
  const handleShareEvent = useCallback(async (event) => {
    const result = await shareEvent(event, {
      selectedCaptureLanes,
      selectedTags,
      selectedActors,
      dateRange,
      searchQuery,
      viewMode
    });
    
    if (result.success) {
      setShareNotification({
        type: 'success',
        message: result.method === 'clipboard' 
          ? 'Link copied to clipboard!' 
          : 'Event shared successfully!'
      });
      setTimeout(() => setShareNotification(null), 3000);
    } else {
      setShareNotification({
        type: 'error',
        message: 'Failed to share event'
      });
      setTimeout(() => setShareNotification(null), 3000);
    }
  }, [selectedCaptureLanes, selectedTags, selectedActors, dateRange, searchQuery, viewMode]);

  // Handler for sharing filtered view
  const handleShareView = useCallback(async () => {
    const result = await shareFilteredView({
      selectedCaptureLanes,
      selectedTags,
      selectedActors,
      dateRange,
      searchQuery,
      viewMode
    });
    
    if (result.success) {
      setShareNotification({
        type: 'success',
        message: result.method === 'clipboard' 
          ? 'Link copied to clipboard!' 
          : 'View shared successfully!'
      });
      setTimeout(() => setShareNotification(null), 3000);
    } else {
      setShareNotification({
        type: 'error',
        message: 'Failed to share view'
      });
      setTimeout(() => setShareNotification(null), 3000);
    }
  }, [selectedCaptureLanes, selectedTags, selectedActors, dateRange, searchQuery, viewMode]);

  if (loading) {
    return (
      <div className="loading-container">
        <Loader2 className="spinner" size={48} />
        <p>Loading timeline data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <AlertCircle size={48} />
        <h2>Error Loading Timeline</h2>
        <p>{error}</p>
        <button onClick={loadData} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  // Show landing page if it's the initial visit or explicitly requested
  if (showLanding) {
    return <LandingPage onEnterTimeline={handleEnterTimeline} />;
  }

  return (
    <div className="app">
      {/* Share notification */}
      {shareNotification && (
        <div className={`share-notification ${shareNotification.type}`}>
          {shareNotification.message}
        </div>
      )}
      
      <header className="app-header">
        <div className="header-content">
          <h1 
            onClick={() => setShowLanding(true)}
            style={{ cursor: 'pointer' }}
            title="Return to landing page"
          >
            Democracy Timeline
          </h1>
          <p className="subtitle">Tracking Patterns of Democratic Degradation</p>
        </div>
        
        <div className="header-controls">
          <SearchBar 
            value={searchQuery}
            onChange={(newQuery) => {
              setSearchQuery(newQuery);
              if (updateUrl) {
                updateUrl({
                  selectedCaptureLanes,
                  selectedTags,
                  selectedActors,
                  dateRange,
                  searchQuery: newQuery,
                  viewMode,
                  timelineControls,
                  zoomLevel,
                  showFilters,
                  showStats
                });
              }
            }}
            placeholder="Search events, actors, tags..."
          />
          
          <div className="header-buttons">
            <button 
              className={`icon-button ${showFilters ? 'active' : ''}`}
              onClick={() => setShowFilters(!showFilters)}
              title="Toggle Filters"
            >
              <Filter size={20} />
            </button>
            
            <button 
              className={`icon-button ${showStats ? 'active' : ''}`}
              onClick={() => setShowStats(!showStats)}
              title="Toggle Statistics"
            >
              <BarChart3 size={20} />
            </button>
            
            <button 
              className="icon-button"
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                setShareNotification({ message: 'Link copied to clipboard!', type: 'success' });
                setTimeout(() => setShareNotification(null), 3000);
              }}
              title="Copy link to share this view"
            >
              <Share2 size={20} />
            </button>
            
            <DownloadMenu 
              onDownload={(format) => {
                trackEvent(AnalyticsEvents.EXPORT_DATA, { format });
                setShareNotification({ 
                  message: `Timeline exported as ${format.toUpperCase()}`, 
                  type: 'success' 
                });
                setTimeout(() => setShareNotification(null), 3000);
              }}
            />
          </div>
          
          <button 
            className="share-view-button"
            onClick={handleShareView}
            title="Share current view"
          >
            <Share2 size={18} />
            <span>Share View</span>
          </button>
          
          <button
            className="submit-event-button"
            onClick={() => openGitHub(createNewEventIssue())}
            title="Submit new event"
          >
            <Plus size={18} />
            <span>Submit Event</span>
          </button>
          
          <ViewToggle 
            currentView={viewMode}
            onViewChange={(newViewMode) => {
              setViewMode(newViewMode);
              if (updateUrl) {
                updateUrl({
                  selectedCaptureLanes,
                  selectedTags,
                  selectedActors,
                  dateRange,
                  searchQuery,
                  viewMode: newViewMode,
                  timelineControls,
                  zoomLevel,
                  showFilters,
                  showStats
                });
              }
            }}
          />
        </div>
      </header>

      <div className="app-body">
        <AnimatePresence>
          {showFilters && (
            <motion.aside 
              className="sidebar filter-sidebar"
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            >
              <FilterPanel
                allTags={allTags}
                allActors={allActors}
                allCaptureLanes={allCaptureLanes}
                selectedTags={selectedTags}
                selectedActors={selectedActors}
                selectedCaptureLanes={selectedCaptureLanes}
                dateRange={dateRange}
                events={events}
                sortOrder={sortOrder}
                onSortOrderChange={setSortOrder}
                minImportance={minImportance}
                onMinImportanceChange={setMinImportance}
                onTagsChange={(newTags) => {
                  setSelectedTags(newTags);
                  if (updateUrl) {
                    updateUrl({
                      selectedCaptureLanes,
                      selectedTags: newTags,
                      selectedActors,
                      dateRange,
                      searchQuery,
                      viewMode,
                      timelineControls,
                      zoomLevel,
                      showFilters,
                      showStats
                    });
                  }
                }}
                onCaptureLanesChange={(newLanes) => {
                  setSelectedCaptureLanes(newLanes);
                  if (updateUrl) {
                    updateUrl({
                      selectedCaptureLanes: newLanes,
                      selectedTags,
                      selectedActors,
                      dateRange,
                      searchQuery,
                      viewMode,
                      timelineControls,
                      zoomLevel,
                      showFilters,
                      showStats
                    });
                  }
                }}
                onActorsChange={(newActors) => {
                  setSelectedActors(newActors);
                  if (updateUrl) {
                    updateUrl({
                      selectedCaptureLanes,
                      selectedTags,
                      selectedActors: newActors,
                      dateRange,
                      searchQuery,
                      viewMode,
                      timelineControls,
                      zoomLevel,
                      showFilters,
                      showStats
                    });
                  }
                }}
                onDateRangeChange={(newDateRange) => {
                  setDateRange(newDateRange);
                  if (updateUrl) {
                    updateUrl({
                      selectedCaptureLanes,
                      selectedTags,
                      selectedActors,
                      dateRange: newDateRange,
                      searchQuery,
                      viewMode,
                      timelineControls,
                      zoomLevel,
                      showFilters,
                      showStats
                    });
                  }
                }}
                onClear={clearFilters}
                eventCount={filteredEvents.length}
                totalCount={events.length}
                viewMode={viewMode}
                timelineControls={timelineControls}
                onTimelineControlsChange={handleTimelineControlsChange}
                timelineData={viewMode === 'timeline' ? {
                  events: filteredEvents,
                  groups: timelineGroups,
                  onNavigate: (date) => {
                    // Navigate to specific date by setting it as center of view
                    if (date) {
                      const targetDate = new Date(date);
                      const beforeDate = new Date(targetDate);
                      const afterDate = new Date(targetDate);
                      beforeDate.setMonth(beforeDate.getMonth() - 3);
                      afterDate.setMonth(afterDate.getMonth() + 3);
                      
                      setDateRange({
                        start: beforeDate.toISOString().split('T')[0],
                        end: afterDate.toISOString().split('T')[0]
                      });
                    }
                  },
                  onDateRangeSelect: (range) => {
                    // Update date range from minimap selection
                    if (range && range.start && range.end) {
                      setDateRange({
                        start: range.start,
                        end: range.end
                      });
                    } else {
                      // Clear date range if null selection
                      setDateRange({ start: '', end: '' });
                    }
                  },
                  currentDateRange: dateRange
                } : null}
              />
            </motion.aside>
          )}
        </AnimatePresence>

        <main className="main-content">
          <div className="timeline-header">
            <h2>
              {filteredEvents.length} Events
              {filteredEvents.length !== events.length && 
                ` (filtered from ${events.length})`
              }
            </h2>
            
            <div className="zoom-controls">
              <button 
                onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.1))}
                className="zoom-button"
              >
                -
              </button>
              <span className="zoom-level">{Math.round(zoomLevel * 100)}%</span>
              <button 
                onClick={() => setZoomLevel(Math.min(2, zoomLevel + 0.1))}
                className="zoom-button"
              >
                +
              </button>
            </div>
          </div>

          {viewMode === 'graph' ? (
            <NetworkGraph 
              events={filteredEvents}
            />
          ) : (
            <EnhancedTimelineView
              events={filteredEvents}
              groups={timelineGroups}
              viewMode={viewMode}
              zoomLevel={zoomLevel}
              sortOrder={sortOrder}
              onEventClick={handleEventClick}
              onTagClick={handleTagClick}
              onActorClick={handleActorClick}
              onCaptureLaneClick={handleCaptureLaneClick}
              selectedTags={selectedTags}
              selectedActors={selectedActors}
              timelineControls={timelineControls}
              onTimelineControlsChange={setTimelineControls}
            />
          )}
        </main>

        <AnimatePresence>
          {showStats && stats && (
            <motion.aside 
              className="sidebar stats-sidebar"
              initial={{ x: 300 }}
              animate={{ x: 0 }}
              exit={{ x: 300 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            >
              <StatsPanel 
                stats={stats}
                events={filteredEvents}
              />
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {selectedEvent && (
          <EventDetails
            event={selectedEvent}
            onClose={() => setSelectedEvent(null)}
            onTagClick={handleTagClick}
            onShare={handleShareEvent}
            onActorClick={handleActorClick}
            onCaptureLaneClick={handleCaptureLaneClick}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;