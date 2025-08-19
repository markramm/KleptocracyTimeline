import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import EnhancedTimelineView from './components/EnhancedTimelineView';
import FilterPanel from './components/FilterPanel';
import EventDetails from './components/EventDetails';
import StatsPanel from './components/StatsPanel';
import SearchBar from './components/SearchBar';
import ViewToggle from './components/ViewToggle';
import NetworkGraph from './components/NetworkGraph';
import { API_ENDPOINTS, transformStaticData } from './config';
import { 
  Filter, 
  BarChart3,
  Loader2,
  AlertCircle 
} from 'lucide-react';
import './App.css';

function App() {
  // State management
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filter states
  const [selectedTags, setSelectedTags] = useState([]);
  const [selectedActors, setSelectedActors] = useState([]);
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('timeline'); // timeline, grid, list, graph
  
  // UI states
  const [showFilters, setShowFilters] = useState(true);
  const [showStats, setShowStats] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  
  // Timeline view controls
  const [timelineControls, setTimelineControls] = useState({
    compactMode: 'medium',
    sortBy: 'date',
    filterImportance: 0,
    showMinimap: true
  });
  
  // Metadata
  const [allTags, setAllTags] = useState([]);
  const [allActors, setAllActors] = useState([]);
  const [stats, setStats] = useState(null);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [eventsRes, tagsRes, actorsRes, statsRes] = await Promise.all([
        axios.get(API_ENDPOINTS.timeline),
        axios.get(API_ENDPOINTS.tags),
        axios.get(API_ENDPOINTS.actors),
        axios.get(API_ENDPOINTS.stats)
      ]);
      
      // Transform data if using static files
      const eventsData = transformStaticData(eventsRes.data, 'timeline');
      const tagsData = transformStaticData(tagsRes.data, 'tags');
      const actorsData = transformStaticData(actorsRes.data, 'actors');
      const statsData = transformStaticData(statsRes.data, 'stats');
      
      setEvents(eventsData.events || eventsData);
      setFilteredEvents(eventsData.events || eventsData);
      setAllTags(tagsData.tags || tagsData);
      setAllActors(actorsData.actors || actorsData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError('Failed to load timeline data. Please ensure the server is running or check your connection.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Apply filters
  useEffect(() => {
    let filtered = [...events];

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

    setFilteredEvents(filtered);
  }, [events, selectedTags, selectedActors, dateRange, searchQuery]);

  // Event handlers
  const handleEventClick = useCallback((event) => {
    setSelectedEvent(event);
  }, []);

  const handleTagClick = useCallback((tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  }, []);

  const handleActorClick = useCallback((actor) => {
    setSelectedActors(prev =>
      prev.includes(actor)
        ? prev.filter(a => a !== actor)
        : [...prev, actor]
    );
  }, []);
  
  const handleTimelineControlsChange = useCallback((newControls) => {
    setTimelineControls(newControls);
  }, []);

  const clearFilters = useCallback(() => {
    setSelectedTags([]);
    setSelectedActors([]);
    setDateRange({ start: null, end: null });
    setSearchQuery('');
    // Reset timeline controls to defaults
    setTimelineControls({
      compactMode: 'medium',
      sortBy: 'date',
      filterImportance: 0,
      showMinimap: true
    });
  }, []);

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

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Democracy Timeline</h1>
          <p className="subtitle">Tracking Patterns of Democratic Degradation</p>
        </div>
        
        <div className="header-controls">
          <SearchBar 
            value={searchQuery}
            onChange={setSearchQuery}
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
          </div>
          
          <ViewToggle 
            currentView={viewMode}
            onViewChange={setViewMode}
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
                selectedTags={selectedTags}
                selectedActors={selectedActors}
                dateRange={dateRange}
                onTagsChange={setSelectedTags}
                onActorsChange={setSelectedActors}
                onDateRangeChange={setDateRange}
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
                    // TODO: Implement navigation to date
                    console.log('Navigate to date:', date);
                  },
                  onDateRangeSelect: (range) => {
                    // TODO: Implement date range selection
                    console.log('Date range selected:', range);
                  }
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
              onEventClick={handleEventClick}
              onTagClick={handleTagClick}
              onActorClick={handleActorClick}
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
            onActorClick={handleActorClick}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;