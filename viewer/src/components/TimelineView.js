import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { format, parseISO, differenceInDays } from 'date-fns';
import { Calendar, MapPin, Users, Tag, ExternalLink, AlertCircle } from 'lucide-react';
import { useInView } from 'react-intersection-observer';
import './TimelineView.css';

const TimelineView = ({
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

  // Render based on view mode
  if (viewMode === 'list') {
    return <ListView events={events} onEventClick={onEventClick} />;
  }

  if (viewMode === 'grid') {
    return <GridView events={events} onEventClick={onEventClick} />;
  }

  if (viewMode === 'graph') {
    return <GraphView events={events} groups={groups} />;
  }

  // Default timeline view
  return (
    <div className="timeline-container" ref={timelineRef}>
      <div 
        className="timeline-content"
        style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
      >
        {Object.entries(groups)
          .sort(([a], [b]) => b.localeCompare(a))
          .map(([year, yearEvents]) => (
            <YearGroup
              key={year}
              year={year}
              events={yearEvents}
              onEventClick={onEventClick}
              onTagClick={onTagClick}
              onActorClick={onActorClick}
              selectedTags={selectedTags}
              selectedActors={selectedActors}
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

      {/* Floating year indicator */}
      <div className="year-indicator">
        {Array.from(visibleYears).sort().join(', ')}
      </div>
    </div>
  );
};

const YearGroup = ({ 
  year, 
  events, 
  onEventClick, 
  onTagClick, 
  onActorClick,
  selectedTags,
  selectedActors,
  onVisible 
}) => {
  const { ref, inView } = useInView({
    threshold: 0.1,
    rootMargin: '50px'
  });

  useEffect(() => {
    onVisible(inView);
  }, [inView, onVisible]);

  return (
    <div ref={ref} className="year-group">
      <div className="year-header">
        <h3>{year}</h3>
        <span className="event-count">{events.length} events</span>
      </div>
      
      <div className="year-timeline">
        <div className="timeline-line" />
        
        {events.map((event, index) => (
          <TimelineEvent
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
          />
        ))}
      </div>
    </div>
  );
};

const TimelineEvent = ({ 
  event, 
  index, 
  onClick, 
  onTagClick, 
  onActorClick,
  isHighlighted 
}) => {
  const [expanded, setExpanded] = useState(false);
  const side = index % 2 === 0 ? 'left' : 'right';
  
  const getStatusColor = (status) => {
    switch(status) {
      case 'confirmed': return '#10b981';
      case 'pending_verification': return '#f59e0b';
      case 'disputed': return '#ef4444';
      default: return '#6b7280';
    }
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

  return (
    <motion.div
      className={`timeline-event ${side} ${isHighlighted ? 'highlighted' : ''}`}
      initial={{ opacity: 0, x: side === 'left' ? -50 : 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
      layout
    >
      <div className="event-connector" />
      <div 
        className="event-dot"
        style={{ backgroundColor: getStatusColor(event.status) }}
      />
      
      <div className="event-card" onClick={onClick}>
        <div className="event-header">
          <span className="event-icon">{getPatternIcon(event.tags)}</span>
          <div className="event-date">
            <Calendar size={14} />
            {format(parseISO(event.date), 'MMM d, yyyy')}
          </div>
        </div>
        
        <h4 className="event-title">{event.title}</h4>
        
        <p className="event-summary">
          {expanded ? event.summary : `${event.summary?.substring(0, 150)}...`}
        </p>
        
        {expanded && (
          <>
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
          </>
        )}
        
        {event.tags && event.tags.length > 0 && (
          <div className="event-tags">
            {event.tags.map(tag => (
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
          </div>
        )}
        
        <button 
          className="expand-button"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      </div>
    </motion.div>
  );
};

const ListView = ({ events, onEventClick }) => {
  return (
    <div className="list-view">
      {events.map(event => (
        <motion.div
          key={event.id}
          className="list-item"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.02 }}
          onClick={() => onEventClick(event)}
        >
          <div className="list-item-date">
            {format(parseISO(event.date), 'MMM d, yyyy')}
          </div>
          <div className="list-item-content">
            <h4>{event.title}</h4>
            <p>{event.summary?.substring(0, 200)}...</p>
            <div className="list-item-meta">
              {event.tags?.map(tag => (
                <span key={tag} className="tag-chip">#{tag}</span>
              ))}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

const GridView = ({ events, onEventClick }) => {
  return (
    <div className="grid-view">
      {events.map(event => (
        <motion.div
          key={event.id}
          className="grid-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          onClick={() => onEventClick(event)}
        >
          <div className="grid-card-header">
            <span className="grid-date">
              {format(parseISO(event.date), 'MMM yyyy')}
            </span>
            <span className={`status-badge ${event.status}`}>
              {event.status}
            </span>
          </div>
          <h4 className="grid-title">{event.title}</h4>
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
        </motion.div>
      ))}
    </div>
  );
};

const GraphView = ({ events, groups }) => {
  // This would integrate with a charting library like Chart.js
  // For now, showing a simple year-by-year breakdown
  return (
    <div className="graph-view">
      <h3>Events by Year</h3>
      <div className="year-bars">
        {Object.entries(groups).map(([year, yearEvents]) => (
          <div key={year} className="year-bar">
            <div 
              className="bar"
              style={{ 
                height: `${Math.min(200, yearEvents.length * 10)}px`,
                backgroundColor: year === '2025' ? '#ef4444' : '#3b82f6'
              }}
            >
              <span className="bar-value">{yearEvents.length}</span>
            </div>
            <span className="bar-label">{year}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineView;