import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format, parseISO, differenceInDays, startOfMonth, endOfMonth } from 'date-fns';
import { 
  Calendar, MapPin, Users, Tag, ExternalLink, AlertCircle, 
  ChevronUp, ChevronDown, Clock, TrendingUp, Shield, AlertTriangle,
  Search, Filter, ArrowUp, Eye, EyeOff, Bookmark, Share2
} from 'lucide-react';
import { useInView } from 'react-intersection-observer';
import './EnhancedTimelineView.css';

const EnhancedTimelineView = ({
  events,
  groups,
  viewMode,
  zoomLevel,
  onEventClick,
  onTagClick,
  onActorClick,
  selectedTags,
  selectedActors
}) => {
  const timelineRef = useRef(null);
  const [visibleYears, setVisibleYears] = useState(new Set());
  const [expandedEvents, setExpandedEvents] = useState(new Set());
  const [bookmarkedEvents, setBookmarkedEvents] = useState(new Set());
  const [showMinimap, setShowMinimap] = useState(true);
  const [sortBy, setSortBy] = useState('date'); // date, importance
  const [filterImportance, setFilterImportance] = useState(0); // 0 = all
  const [compactMode, setCompactMode] = useState(false);
  const [stickyYear, setStickyYear] = useState(null);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.target.tagName === 'INPUT') return;
      
      switch(e.key) {
        case 'ArrowDown':
        case 'j':
          navigateToNextEvent();
          break;
        case 'ArrowUp':
        case 'k':
          navigateToPrevEvent();
          break;
        case 'Home':
          scrollToTop();
          break;
        case 'End':
          scrollToBottom();
          break;
        case 'm':
          setShowMinimap(prev => !prev);
          break;
        case 'c':
          setCompactMode(prev => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Sort and filter events
  const processedEvents = useMemo(() => {
    let processed = [...events];
    
    // Filter by importance
    if (filterImportance > 0) {
      processed = processed.filter(e => (e.importance || 5) >= filterImportance);
    }
    
    // Sort
    if (sortBy === 'importance') {
      processed.sort((a, b) => (b.importance || 5) - (a.importance || 5));
    } else {
      processed.sort((a, b) => new Date(b.date) - new Date(a.date));
    }
    
    return processed;
  }, [events, sortBy, filterImportance]);

  // Group events by year/month for timeline
  const timelineGroups = useMemo(() => {
    const groups = {};
    processedEvents.forEach(event => {
      const year = event.date?.substring(0, 4) || 'Unknown';
      const month = event.date?.substring(5, 7) || '01';
      const key = `${year}-${month}`;
      
      if (!groups[year]) {
        groups[year] = {};
      }
      if (!groups[year][month]) {
        groups[year][month] = [];
      }
      groups[year][month].push(event);
    });
    return groups;
  }, [processedEvents]);

  const navigateToNextEvent = () => {
    // Implementation for keyboard navigation
  };

  const navigateToPrevEvent = () => {
    // Implementation for keyboard navigation
  };

  const scrollToTop = () => {
    timelineRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const scrollToBottom = () => {
    timelineRef.current?.scrollTo({ 
      top: timelineRef.current.scrollHeight, 
      behavior: 'smooth' 
    });
  };

  const handleBookmark = (eventId) => {
    setBookmarkedEvents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(eventId)) {
        newSet.delete(eventId);
      } else {
        newSet.add(eventId);
      }
      return newSet;
    });
  };

  const shareEvent = (event) => {
    // Copy link to clipboard
    const url = `${window.location.origin}#event-${event.id}`;
    navigator.clipboard.writeText(url);
    // Show toast notification (would need to implement)
  };

  // Handle scroll for sticky headers
  useEffect(() => {
    const handleScroll = () => {
      if (!timelineRef.current) return;
      
      const scrollTop = timelineRef.current.scrollTop;
      const yearElements = timelineRef.current.querySelectorAll('.year-group');
      
      for (const yearEl of yearElements) {
        const rect = yearEl.getBoundingClientRect();
        const containerRect = timelineRef.current.getBoundingClientRect();
        
        if (rect.top <= containerRect.top + 60 && rect.bottom > containerRect.top + 60) {
          const year = yearEl.getAttribute('data-year');
          setStickyYear(year);
          break;
        }
      }
    };

    const container = timelineRef.current;
    container?.addEventListener('scroll', handleScroll);
    return () => container?.removeEventListener('scroll', handleScroll);
  }, []);

  // Render based on view mode
  if (viewMode === 'list') {
    return <EnhancedListView 
      events={processedEvents} 
      onEventClick={onEventClick}
      bookmarkedEvents={bookmarkedEvents}
      onBookmark={handleBookmark}
      compactMode={compactMode}
    />;
  }

  if (viewMode === 'grid') {
    return <EnhancedGridView 
      events={processedEvents} 
      onEventClick={onEventClick}
      bookmarkedEvents={bookmarkedEvents}
      onBookmark={handleBookmark}
    />;
  }

  // Default enhanced timeline view
  return (
    <div className="enhanced-timeline-container">
      {/* Toolbar */}
      <div className="timeline-toolbar">
        <div className="toolbar-left">
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="date">Sort by Date</option>
            <option value="importance">Sort by Importance</option>
          </select>
          
          <select 
            value={filterImportance} 
            onChange={(e) => setFilterImportance(Number(e.target.value))}
            className="filter-select"
          >
            <option value="0">All Events</option>
            <option value="6">Important (6+)</option>
            <option value="7">High Priority (7+)</option>
            <option value="8">Critical (8+)</option>
            <option value="9">Crisis Level (9+)</option>
          </select>
          
          <button 
            className={`toolbar-button ${compactMode ? 'active' : ''}`}
            onClick={() => setCompactMode(!compactMode)}
            title="Toggle Compact Mode (C)"
          >
            {compactMode ? <Eye size={18} /> : <EyeOff size={18} />}
            Compact
          </button>
          
          <button 
            className={`toolbar-button ${showMinimap ? 'active' : ''}`}
            onClick={() => setShowMinimap(!showMinimap)}
            title="Toggle Minimap (M)"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <rect x="7" y="7" width="10" height="10" />
            </svg>
            Minimap
          </button>
        </div>
        
        <div className="toolbar-right">
          <span className="event-counter">
            {processedEvents.length} events
            {filterImportance > 0 && ` (filtered from ${events.length})`}
          </span>
        </div>
      </div>

      {/* Sticky Year Header */}
      {stickyYear && (
        <div className="sticky-year-header">
          <h3>{stickyYear}</h3>
        </div>
      )}

      {/* Main Timeline */}
      <div className="timeline-layout">
        {/* Minimap */}
        {showMinimap && (
          <TimelineMinimap 
            events={processedEvents}
            groups={timelineGroups}
            onNavigate={(date) => {
              // Scroll to date
              const element = document.getElementById(`date-${date}`);
              element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }}
          />
        )}

        {/* Timeline Content */}
        <div className="timeline-scroll-container" ref={timelineRef}>
          <div 
            className="timeline-content"
            style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
          >
            {Object.entries(timelineGroups)
              .sort(([a], [b]) => b.localeCompare(a))
              .map(([year, months]) => (
                <EnhancedYearGroup
                  key={year}
                  year={year}
                  months={months}
                  onEventClick={onEventClick}
                  onTagClick={onTagClick}
                  onActorClick={onActorClick}
                  selectedTags={selectedTags}
                  selectedActors={selectedActors}
                  expandedEvents={expandedEvents}
                  setExpandedEvents={setExpandedEvents}
                  bookmarkedEvents={bookmarkedEvents}
                  onBookmark={handleBookmark}
                  onShare={shareEvent}
                  compactMode={compactMode}
                  onVisible={(visible) => {
                    setVisibleYears(prev => {
                      const newSet = new Set(prev);
                      if (visible) newSet.add(year);
                      else newSet.delete(year);
                      return newSet;
                    });
                  }}
                />
              ))}
          </div>
        </div>
      </div>

      {/* Floating Navigation */}
      <div className="floating-nav">
        <button onClick={scrollToTop} title="Go to top (Home)">
          <ChevronUp size={20} />
        </button>
        <button onClick={scrollToBottom} title="Go to bottom (End)">
          <ChevronDown size={20} />
        </button>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="keyboard-help">
        <span>↑/↓ or J/K: Navigate</span>
        <span>M: Minimap</span>
        <span>C: Compact</span>
      </div>
    </div>
  );
};

const EnhancedYearGroup = ({ 
  year, 
  months,
  onEventClick, 
  onTagClick, 
  onActorClick,
  selectedTags,
  selectedActors,
  expandedEvents,
  setExpandedEvents,
  bookmarkedEvents,
  onBookmark,
  onShare,
  compactMode,
  onVisible 
}) => {
  const { ref, inView } = useInView({
    threshold: 0.1,
    rootMargin: '50px'
  });

  useEffect(() => {
    onVisible(inView);
  }, [inView, onVisible]);

  const totalEvents = Object.values(months).flat().length;
  const avgImportance = Object.values(months).flat()
    .reduce((sum, e) => sum + (e.importance || 5), 0) / totalEvents;

  return (
    <div ref={ref} className="year-group" data-year={year}>
      <div className="year-header">
        <h3>{year}</h3>
        <div className="year-meta">
          <span className="event-count">{totalEvents} events</span>
          <span className="avg-importance">
            Avg importance: {avgImportance.toFixed(1)}
          </span>
        </div>
      </div>
      
      {Object.entries(months)
        .sort(([a], [b]) => b.localeCompare(a))
        .map(([month, monthEvents]) => (
          <div key={`${year}-${month}`} className="month-group">
            <h4 className="month-header">
              {format(parseISO(`${year}-${month}-01`), 'MMMM')}
              <span className="month-count">({monthEvents.length})</span>
            </h4>
            
            <div className="month-timeline">
              <div className="timeline-line" />
              
              {monthEvents.map((event, index) => (
                <EnhancedTimelineEvent
                  key={event.id}
                  event={event}
                  index={index}
                  onClick={() => onEventClick(event)}
                  onTagClick={onTagClick}
                  onActorClick={onActorClick}
                  isHighlighted={
                    (selectedTags.length > 0 && event.tags?.some(t => selectedTags.includes(t))) ||
                    (selectedActors.length > 0 && event.actors?.some(a => selectedActors.includes(a)))
                  }
                  isExpanded={expandedEvents.has(event.id)}
                  onToggleExpand={() => {
                    setExpandedEvents(prev => {
                      const newSet = new Set(prev);
                      if (newSet.has(event.id)) {
                        newSet.delete(event.id);
                      } else {
                        newSet.add(event.id);
                      }
                      return newSet;
                    });
                  }}
                  isBookmarked={bookmarkedEvents.has(event.id)}
                  onBookmark={() => onBookmark(event.id)}
                  onShare={() => onShare(event)}
                  compactMode={compactMode}
                />
              ))}
            </div>
          </div>
        ))}
    </div>
  );
};

const EnhancedTimelineEvent = ({ 
  event, 
  index, 
  onClick, 
  onTagClick, 
  onActorClick,
  isHighlighted,
  isExpanded,
  onToggleExpand,
  isBookmarked,
  onBookmark,
  onShare,
  compactMode
}) => {
  const side = index % 2 === 0 ? 'left' : 'right';
  const importance = event.importance || 5;
  
  const getStatusColor = (status) => {
    switch(status) {
      case 'confirmed': return '#10b981';
      case 'pending_verification': return '#f59e0b';
      case 'disputed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getImportanceColor = (importance) => {
    if (importance >= 9) return '#dc2626'; // Red for crisis
    if (importance >= 8) return '#ea580c'; // Orange for critical
    if (importance >= 7) return '#f59e0b'; // Amber for high
    if (importance >= 6) return '#3b82f6'; // Blue for notable
    return '#6b7280'; // Gray for standard
  };

  const getImportanceIcon = (importance) => {
    if (importance >= 9) return <AlertTriangle size={16} />;
    if (importance >= 7) return <TrendingUp size={16} />;
    if (importance >= 5) return <Shield size={16} />;
    return <Clock size={16} />;
  };

  const getPatternIcon = (tags) => {
    if (tags?.includes('constitutional-crisis')) return '⚖️';
    if (tags?.includes('foreign-influence')) return '🌍';
    if (tags?.includes('crypto')) return '₿';
    if (tags?.includes('money-laundering')) return '💰';
    if (tags?.includes('regulatory-capture')) return '🏛️';
    if (tags?.includes('immigration')) return '🛂';
    if (tags?.includes('intelligence')) return '🕵️';
    return '📌';
  };

  if (compactMode && !isHighlighted && importance < 7) {
    // Compact mode for less important events
    return (
      <div 
        className={`timeline-event compact ${side}`}
        id={`event-${event.id}`}
        onClick={onClick}
      >
        <div className="event-connector" />
        <div 
          className="event-dot"
          style={{ 
            backgroundColor: getImportanceColor(importance),
            width: `${8 + importance}px`,
            height: `${8 + importance}px`
          }}
        />
        <div className="compact-event-card">
          <span className="compact-date">
            {format(parseISO(event.date), 'MMM d')}
          </span>
          <span className="compact-title">{event.title}</span>
          <span className="importance-badge" style={{ color: getImportanceColor(importance) }}>
            {importance}
          </span>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className={`timeline-event ${side} ${isHighlighted ? 'highlighted' : ''} importance-${importance}`}
      id={`event-${event.id}`}
      initial={{ opacity: 0, x: side === 'left' ? -50 : 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
      layout
    >
      <div className="event-connector" />
      <div 
        className="event-dot"
        style={{ 
          backgroundColor: getImportanceColor(importance),
          width: `${12 + importance * 2}px`,
          height: `${12 + importance * 2}px`,
          boxShadow: importance >= 8 ? `0 0 20px ${getImportanceColor(importance)}` : 'none'
        }}
      />
      
      <div 
        className="event-card"
        style={{ 
          borderLeft: `4px solid ${getImportanceColor(importance)}`,
          borderColor: isHighlighted ? '#3b82f6' : getImportanceColor(importance)
        }}
      >
        <div className="event-header">
          <div className="event-header-left">
            <span className="event-icon">{getPatternIcon(event.tags)}</span>
            <div className="event-date">
              <Calendar size={14} />
              {format(parseISO(event.date), 'MMM d, yyyy')}
            </div>
            <div className="importance-indicator" title={`Importance: ${importance}/10`}>
              {getImportanceIcon(importance)}
              <span className="importance-value">{importance}</span>
            </div>
          </div>
          
          <div className="event-actions">
            <button 
              className={`action-button ${isBookmarked ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                onBookmark();
              }}
              title="Bookmark"
            >
              <Bookmark size={14} />
            </button>
            <button 
              className="action-button"
              onClick={(e) => {
                e.stopPropagation();
                onShare();
              }}
              title="Share"
            >
              <Share2 size={14} />
            </button>
          </div>
        </div>
        
        <h4 className="event-title" onClick={onClick}>
          {event.title}
        </h4>
        
        <p className="event-summary">
          {isExpanded ? event.summary : `${event.summary?.substring(0, 150)}...`}
        </p>
        
        {isExpanded && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="event-details"
            >
              {event.location && (
                <div className="event-location">
                  <MapPin size={14} />
                  {event.location}
                </div>
              )}
              
              {event.actors && event.actors.length > 0 && (
                <div className="event-actors">
                  <Users size={14} />
                  <div className="actor-list">
                    {event.actors.map(actor => (
                      <span 
                        key={actor}
                        className="actor-chip"
                        onClick={(e) => {
                          e.stopPropagation();
                          onActorClick(actor);
                        }}
                      >
                        {actor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {event.sources && event.sources.length > 0 && (
                <div className="event-sources">
                  <ExternalLink size={14} />
                  <span>{event.sources.length} sources</span>
                </div>
              )}
              
              {event.monitoring_status && (
                <div className="monitoring-status">
                  <AlertCircle size={14} />
                  <span>Monitoring: {event.monitoring_status}</span>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        )}
        
        {event.tags && event.tags.length > 0 && (
          <div className="event-tags">
            {event.tags.slice(0, isExpanded ? undefined : 3).map(tag => (
              <span 
                key={tag}
                className="tag-chip"
                onClick={(e) => {
                  e.stopPropagation();
                  onTagClick(tag);
                }}
              >
                #{tag}
              </span>
            ))}
            {!isExpanded && event.tags.length > 3 && (
              <span className="more-tags">+{event.tags.length - 3}</span>
            )}
          </div>
        )}
        
        <button 
          className="expand-button"
          onClick={(e) => {
            e.stopPropagation();
            onToggleExpand();
          }}
        >
          {isExpanded ? 'Show less' : 'Show more'}
        </button>
      </div>
    </motion.div>
  );
};

const TimelineMinimap = ({ events, groups, onNavigate }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw timeline visualization
    const years = Object.keys(groups).sort();
    const yearHeight = height / years.length;
    
    years.forEach((year, index) => {
      const y = index * yearHeight;
      const yearEvents = Object.values(groups[year]).flat();
      const maxImportance = Math.max(...yearEvents.map(e => e.importance || 5));
      
      // Draw year background
      ctx.fillStyle = index % 2 === 0 ? '#f8fafc' : '#ffffff';
      ctx.fillRect(0, y, width, yearHeight);
      
      // Draw importance bars
      const monthWidth = width / 12;
      Object.entries(groups[year]).forEach(([month, monthEvents]) => {
        const monthIndex = parseInt(month) - 1;
        const x = monthIndex * monthWidth;
        const avgImportance = monthEvents.reduce((sum, e) => sum + (e.importance || 5), 0) / monthEvents.length;
        const barHeight = (avgImportance / 10) * yearHeight * 0.8;
        
        // Color based on average importance
        if (avgImportance >= 8) ctx.fillStyle = '#dc2626';
        else if (avgImportance >= 7) ctx.fillStyle = '#f59e0b';
        else if (avgImportance >= 6) ctx.fillStyle = '#3b82f6';
        else ctx.fillStyle = '#94a3b8';
        
        ctx.fillRect(x + 2, y + yearHeight - barHeight - 2, monthWidth - 4, barHeight);
      });
      
      // Draw year label
      ctx.fillStyle = '#1f2937';
      ctx.font = '10px sans-serif';
      ctx.fillText(year, 4, y + yearHeight / 2);
    });
  }, [events, groups]);
  
  const handleClick = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yearIndex = Math.floor(y / (canvas.height / Object.keys(groups).length));
    const years = Object.keys(groups).sort();
    const year = years[yearIndex];
    
    if (year) {
      onNavigate(`${year}-01-01`);
    }
  };
  
  return (
    <div className="timeline-minimap">
      <h4>Timeline Overview</h4>
      <canvas 
        ref={canvasRef}
        width={200}
        height={400}
        onClick={handleClick}
        style={{ cursor: 'pointer' }}
      />
      <div className="minimap-legend">
        <div><span style={{ background: '#dc2626' }}></span> Critical (8+)</div>
        <div><span style={{ background: '#f59e0b' }}></span> High (7+)</div>
        <div><span style={{ background: '#3b82f6' }}></span> Notable (6+)</div>
        <div><span style={{ background: '#94a3b8' }}></span> Standard</div>
      </div>
    </div>
  );
};

const EnhancedListView = ({ events, onEventClick, bookmarkedEvents, onBookmark, compactMode }) => {
  return (
    <div className="enhanced-list-view">
      {events.map(event => (
        <motion.div
          key={event.id}
          className={`list-item ${compactMode ? 'compact' : ''}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.02 }}
        >
          <div className="list-item-importance" style={{ 
            background: `linear-gradient(90deg, ${getImportanceColor(event.importance || 5)} 0%, transparent 100%)` 
          }}>
            {event.importance || 5}
          </div>
          
          <div className="list-item-date">
            {format(parseISO(event.date), 'MMM d, yyyy')}
          </div>
          
          <div className="list-item-content" onClick={() => onEventClick(event)}>
            <h4>{event.title}</h4>
            {!compactMode && (
              <p>{event.summary?.substring(0, 200)}...</p>
            )}
            <div className="list-item-meta">
              {event.tags?.slice(0, 3).map(tag => (
                <span key={tag} className="tag-chip">#{tag}</span>
              ))}
              {event.actors?.length > 0 && (
                <span className="actor-count">
                  <Users size={12} /> {event.actors.length}
                </span>
              )}
            </div>
          </div>
          
          <button 
            className={`bookmark-button ${bookmarkedEvents.has(event.id) ? 'active' : ''}`}
            onClick={() => onBookmark(event.id)}
          >
            <Bookmark size={16} />
          </button>
        </motion.div>
      ))}
    </div>
  );
};

const EnhancedGridView = ({ events, onEventClick, bookmarkedEvents, onBookmark }) => {
  return (
    <div className="enhanced-grid-view">
      {events.map(event => (
        <motion.div
          key={event.id}
          className="grid-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          style={{ 
            borderTop: `4px solid ${getImportanceColor(event.importance || 5)}` 
          }}
        >
          <div className="grid-card-header">
            <span className="grid-date">
              {format(parseISO(event.date), 'MMM yyyy')}
            </span>
            <div className="grid-badges">
              <span className="importance-badge">
                {event.importance || 5}
              </span>
              <span className={`status-badge ${event.status}`}>
                {event.status}
              </span>
            </div>
          </div>
          
          <h4 className="grid-title" onClick={() => onEventClick(event)}>
            {event.title}
          </h4>
          
          <p className="grid-summary">
            {event.summary?.substring(0, 100)}...
          </p>
          
          {event.actors && (
            <div className="grid-actors">
              {event.actors.slice(0, 3).map(actor => (
                <span key={actor} className="actor-chip small">{actor}</span>
              ))}
              {event.actors.length > 3 && (
                <span className="more-actors">+{event.actors.length - 3}</span>
              )}
            </div>
          )}
          
          <div className="grid-actions">
            <button 
              className={`bookmark-button ${bookmarkedEvents.has(event.id) ? 'active' : ''}`}
              onClick={() => onBookmark(event.id)}
            >
              <Bookmark size={14} />
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

// Helper functions
const getImportanceColor = (importance) => {
  if (importance >= 9) return '#dc2626';
  if (importance >= 8) return '#ea580c';
  if (importance >= 7) return '#f59e0b';
  if (importance >= 6) return '#3b82f6';
  return '#6b7280';
};

export default EnhancedTimelineView;