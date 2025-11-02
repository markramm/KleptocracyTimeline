import React, { useRef, useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format, parseISO } from 'date-fns';
import {
  Calendar, MapPin, Users, ExternalLink, AlertCircle,
  ChevronUp, ChevronDown, Clock, TrendingUp, Shield, AlertTriangle,
  Bookmark, Share2
} from 'lucide-react';
import { useInView } from 'react-intersection-observer';
import './EnhancedTimelineView.css';

// Helper function to safely format dates
const safeFormat = (dateString, formatStr) => {
  // Handle null/undefined/empty dates
  if (!dateString || dateString === 'undefined' || dateString === 'Unknown-01-01') {
    return 'Unknown';
  }

  try {
    const parsed = parseISO(dateString);
    // Check if date is valid
    if (isNaN(parsed.getTime())) {
      return dateString || 'Unknown';
    }
    return format(parsed, formatStr);
  } catch (error) {
    return dateString || 'Unknown';
  }
};

const EnhancedTimelineView = ({
  events,
  groups,
  viewMode,
  zoomLevel,
  sortOrder,
  onEventClick,
  onTagClick,
  onActorClick,
  selectedTags,
  selectedActors,
  timelineControls,
  onTimelineControlsChange
}) => {
  const timelineRef = useRef(null);
  const [, setVisibleYears] = useState(new Set());
  const [expandedEvents, setExpandedEvents] = useState(new Set());
  const [bookmarkedEvents, setBookmarkedEvents] = useState(new Set());
  const [stickyYear, setStickyYear] = useState(null);
  
  // Use controls from props
  const { compactMode, showMinimap } = timelineControls || {
    compactMode: 'medium',
    showMinimap: true
  };

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
          if (onTimelineControlsChange) {
            onTimelineControlsChange({
              ...timelineControls,
              showMinimap: !showMinimap
            });
          }
          break;
        case 'c':
          // Cycle through compact modes
          if (onTimelineControlsChange) {
            let nextMode = 'none';
            if (compactMode === 'none') nextMode = 'low';
            if (compactMode === 'low') nextMode = 'medium';
            if (compactMode === 'medium') nextMode = 'all';
            
            onTimelineControlsChange({
              ...timelineControls,
              compactMode: nextMode
            });
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showMinimap, compactMode, timelineControls, onTimelineControlsChange]);

  // Use events as-is since they're already filtered and sorted by App.js
  const processedEvents = events;

  // Group events by year/month for timeline
  const timelineGroups = useMemo(() => {
    const groups = {};
    processedEvents.forEach(event => {
      const year = event.date?.substring(0, 4) || 'Unknown';
      const month = event.date?.substring(5, 7) || '01';
      // const key = `${year}-${month}`;
      
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
      
      // const scrollTop = timelineRef.current.scrollTop;
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

      {/* Sticky Year Header */}
      {stickyYear && (
        <div className="sticky-year-header">
          <h3>{stickyYear}</h3>
        </div>
      )}

      {/* Main Timeline Content */}
      <div className="timeline-scroll-container" ref={timelineRef}>
        <div 
          className="timeline-content"
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
        >
          {Object.entries(timelineGroups)
            .sort(([a], [b]) => {
              // Sort years based on sortOrder
              if (sortOrder === 'newest') {
                return b.localeCompare(a); // Newest first (2025, 2024, 2023...)
              } else {
                return a.localeCompare(b); // Chronological (1970, 1971, 1972...)
              }
            })
            .map(([year, months]) => (
              <EnhancedYearGroup
                key={year}
                year={year}
                months={months}
                sortOrder={sortOrder}
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
        <span>M: Toggle Minimap</span>
        <span>C: Cycle Display</span>
      </div>
    </div>
  );
};

const EnhancedYearGroup = ({ 
  year, 
  months,
  sortOrder,
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
        .sort(([a], [b]) => {
          // Sort months based on sortOrder
          if (sortOrder === 'newest') {
            return b.localeCompare(a); // December to January
          } else {
            return a.localeCompare(b); // January to December
          }
        })
        .map(([month, monthEvents]) => (
          <div key={`${year}-${month}`} className="month-group">
            <h4 className="month-header">
              {safeFormat(`${year}-${month}-01`, 'MMMM')}
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
  
  // const getStatusColor = (status) => {
  //   switch(status) {
  //     case 'confirmed': return '#10b981';
  //     case 'pending_verification': return '#f59e0b';
  //     case 'disputed': return '#ef4444';
  //     default: return '#6b7280';
  //   }
  // };

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

  // Determine if this event should be compact based on mode
  const shouldBeCompact = !isExpanded && compactMode !== 'none' && (
    (compactMode === 'all') ||
    (compactMode === 'medium' && importance <= 7) ||
    (compactMode === 'low' && importance <= 5)
  );
  
  if (shouldBeCompact) { // Show compact based on mode and importance
    // Compact mode for less important events
    return (
      <div 
        className={`timeline-event compact ${side} ${isHighlighted ? 'highlighted' : ''}`}
        id={`event-${event.id}`}
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
        <div className="compact-event-card" style={{ 
          borderLeft: `3px solid ${getImportanceColor(importance)}`,
          background: importance >= 7 ? 'rgba(30, 41, 59, 0.7)' : 'rgba(30, 41, 59, 0.5)'
        }}
        onClick={(e) => {
          e.stopPropagation();
          // If already expanded, open full details; otherwise expand
          if (isExpanded) {
            onClick();
          } else {
            onToggleExpand();
          }
        }}>
          <span className="compact-date">
            {safeFormat(event.date, 'MMM d')}
          </span>
          <span className="compact-title" style={{
            fontWeight: importance >= 7 ? '600' : '400',
            cursor: 'pointer'
          }}>{event.title}</span>
          {event.tags && event.tags.length > 0 && (
            <span className="compact-tags">
              {event.tags.slice(0, 2).map(tag => (
                <span key={tag} className="tag-micro">#{tag}</span>
              ))}
            </span>
          )}
          <span className="importance-badge" style={{ 
            color: getImportanceColor(importance),
            fontWeight: '600'
          }}>
            {importance}
          </span>
          {isExpanded && (
            <button 
              className="view-details-btn"
              onClick={(e) => {
                e.stopPropagation();
                onClick();
              }}
              title="View full details"
            >
              View Details
            </button>
          )}
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
              {safeFormat(event.date, 'MMM d, yyyy')}
            </div>
            <div className="importance-indicator" title={`Importance: ${importance}/10`}>
              {getImportanceIcon(importance)}
              <span className="importance-value">{importance}</span>
            </div>
            {event.tags && event.tags.length > 0 && (
              <div className="event-tags-inline">
                {event.tags.slice(0, 2).map(tag => (
                  <span 
                    key={tag}
                    className="tag-chip-inline"
                    onClick={(e) => {
                      e.stopPropagation();
                      onTagClick(tag);
                    }}
                  >
                    #{tag}
                  </span>
                ))}
                {event.tags.length > 2 && (
                  <span className="more-tags-inline">+{event.tags.length - 2}</span>
                )}
              </div>
            )}
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
          {isExpanded ? event.summary : `${event.summary?.substring(0, 300)}...`}
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
                  <span>{event.sources.length} source{event.sources.length > 1 ? 's' : ''}:</span>
                  <div className="source-links-inline">
                    {event.sources.slice(0, 2).map((source, idx) => (
                      source.url && (
                        <a
                          key={idx}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-link-inline"
                          onClick={(e) => e.stopPropagation()}
                          title={`${source.outlet || 'Source'}: ${source.title}`}
                        >
                          <ExternalLink size={12} />
                          {source.outlet || 'Link'}
                        </a>
                      )
                    ))}
                    {event.sources.length > 2 && (
                      <span className="more-sources">+{event.sources.length - 2} more</span>
                    )}
                  </div>
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

/* const TimelineMinimap = ({ events, groups, onNavigate, onDateRangeSelect }) => {
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [dragEnd, setDragEnd] = useState(null);
  const [selectedRange, setSelectedRange] = useState(null);
  
  const years = useMemo(() => Object.keys(groups).sort(), [groups]);
  
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || years.length === 0) {
      return;
    }
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Simple background
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);
    
    // Draw timeline visualization
    const yearHeight = height / years.length;
    
    years.forEach((year, index) => {
      const y = index * yearHeight;
      // const yearEvents = Object.values(groups[year]).flat();
      
      // Draw year background
      ctx.fillStyle = index % 2 === 0 ? 'rgba(248, 250, 252, 0.1)' : 'rgba(255, 255, 255, 0.05)';
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
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px sans-serif';
      ctx.fillText(year, 4, y + yearHeight / 2);
    });
    
    // Draw selection overlay if dragging or selected
    if (selectedRange || (isDragging && dragStart !== null && dragEnd !== null)) {
      const start = selectedRange ? selectedRange.start : Math.min(dragStart, dragEnd);
      const end = selectedRange ? selectedRange.end : Math.max(dragStart, dragEnd);
      
      ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
      ctx.fillRect(0, start, width, end - start);
      
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.strokeRect(0, start, width, end - start);
    }
  }, [groups, years, isDragging, dragStart, dragEnd, selectedRange]);
  
  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);
  
  const getDateFromY = (y) => {
    const yearIndex = Math.floor(y / (canvasRef.current.height / years.length));
    const yearProgress = (y % (canvasRef.current.height / years.length)) / (canvasRef.current.height / years.length);
    const year = years[Math.min(yearIndex, years.length - 1)];
    const month = Math.floor(yearProgress * 12) + 1;
    return `${year}-${String(month).padStart(2, '0')}-01`;
  };
  
  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const y = e.clientY - rect.top;
    
    setIsDragging(true);
    setDragStart(y);
    setDragEnd(y);
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const y = e.clientY - rect.top;
    
    setDragEnd(y);
  };
  
  const handleMouseUp = (e) => {
    if (!isDragging) return;
    
    const startDate = getDateFromY(Math.min(dragStart, dragEnd));
    const endDate = getDateFromY(Math.max(dragStart, dragEnd));
    
    if (Math.abs(dragEnd - dragStart) > 5) {
      // Range selection
      setSelectedRange({ start: Math.min(dragStart, dragEnd), end: Math.max(dragStart, dragEnd) });
      onDateRangeSelect({ start: startDate, end: endDate });
    } else {
      // Single click navigation
      setSelectedRange(null);
      onNavigate(startDate);
      onDateRangeSelect({ start: null, end: null });
    }
    
    setIsDragging(false);
    setDragStart(null);
    setDragEnd(null);
  };
  
  const handleClearSelection = () => {
    setSelectedRange(null);
    onDateRangeSelect({ start: null, end: null });
  };
  
  return (
    <div className="timeline-minimap">
      <div className="minimap-header">
        <h4>Timeline Navigation</h4>
        {selectedRange && (
          <button className="clear-selection-btn" onClick={handleClearSelection}>
            Clear Range
          </button>
        )}
      </div>
      <canvas 
        ref={canvasRef}
        width={200}
        height={400}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      />
      <div className="minimap-instructions">
        Click to jump • Drag to filter range
      </div>
      <div className="minimap-legend">
        <div><span style={{ background: '#dc2626' }}></span> Critical</div>
        <div><span style={{ background: '#f59e0b' }}></span> High</div>
        <div><span style={{ background: '#3b82f6' }}></span> Notable</div>
      </div>
    </div>
  );
}; */

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
            {safeFormat(event.date, 'MMM d, yyyy')}
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
              {safeFormat(event.date, 'MMM yyyy')}
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