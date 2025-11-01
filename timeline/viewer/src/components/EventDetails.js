import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { format, parseISO } from 'date-fns';
import { 
  X, 
  Calendar, 
  MapPin, 
  Users, 
  Tag, 
  ExternalLink, 
  FileText,
  CheckCircle,
  AlertCircle,
  XCircle,
  Share2,
  Github,
  Edit3,
  AlertTriangle
} from 'lucide-react';
import ContributeButton from './ContributeButton';
import { 
  getEventEditUrl, 
  getEventViewUrl, 
  createBrokenLinkIssue,
  createCorrectionIssue,
  getArchiveUrl,
  openGitHub
} from '../utils/githubUtils';
import './EventDetails.css';

const EventDetails = ({ event, onClose, onTagClick, onActorClick, onCaptureLaneClick, onShare }) => {
  const [brokenLinks, setBrokenLinks] = useState({});
  const getStatusIcon = (status) => {
    switch(status) {
      case 'confirmed': 
        return <CheckCircle className="status-icon confirmed" size={20} />;
      case 'pending_verification': 
        return <AlertCircle className="status-icon pending" size={20} />;
      case 'disputed': 
        return <XCircle className="status-icon disputed" size={20} />;
      default: 
        return null;
    }
  };

  const formatSourceDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy');
    } catch {
      return dateStr;
    }
  };

  const getCaptureLaneColor = (lane) => {
    const colors = {
      // Critical (Red)
      'Executive Power & Emergency Authority': '#dc2626',
      'Judicial Capture & Corruption': '#b91c1c',
      'Election System Attack': '#991b1b',
      'Law Enforcement Weaponization': '#7f1d1d',
      
      // High (Orange)  
      'Financial Corruption & Kleptocracy': '#ea580c',
      'Foreign Influence Operations': '#c2410c',
      'Constitutional & Democratic Breakdown': '#9a3412',
      
      // Medium (Yellow)
      'Federal Workforce Capture': '#ca8a04',
      'Information & Media Control': '#a16207',
      'Corporate Capture & Regulatory Breakdown': '#854d0e',
      
      // Monitoring (Blue)
      'Immigration & Border Militarization': '#1d4ed8',
      'International Democracy Impact': '#1e40af',
      
      // Specialized (Purple)
      'Epstein Network & Kompromat': '#7c3aed'
    };
    
    return colors[lane] || '#6b7280';
  };

  return (
    <motion.div 
      className="event-details-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div 
        className="event-details-modal"
        initial={{ scale: 0.9, y: 50 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 50 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>{event.title}</h2>
            <div className="status-badge">
              {getStatusIcon(event.status)}
              <span>{event.status?.replace('_', ' ')}</span>
            </div>
          </div>
          <div className="modal-actions">
            <ContributeButton 
              eventId={event.id} 
              eventTitle={event.title}
            />
            {onShare && (
              <button 
                className="share-button" 
                onClick={() => onShare(event)}
                title="Share this event"
              >
                <Share2 size={20} />
              </button>
            )}
            <button className="close-button" onClick={onClose}>
              <X size={24} />
            </button>
          </div>
        </div>

        <div className="modal-body">
          <div className="event-meta">
            <div className="meta-item">
              <Calendar size={16} />
              <span>{format(parseISO(event.date), 'MMMM d, yyyy')}</span>
            </div>
            
            {event.location && (
              <div className="meta-item">
                <MapPin size={16} />
                <span>{event.location}</span>
              </div>
            )}
            
            {event._file && (
              <div className="meta-item">
                <FileText size={16} />
                <span className="file-name">{event._file}</span>
              </div>
            )}
          </div>

          <div className="detail-section">
            <h3>Summary</h3>
            <p className="summary-text">{event.summary}</p>
          </div>

          {event.notes && (
            <div className="detail-section">
              <h3>Additional Notes</h3>
              <p className="notes-text">{event.notes}</p>
            </div>
          )}

          {event.actors && event.actors.length > 0 && (
            <div className="detail-section">
              <h3>
                <Users size={18} />
                Key Actors
              </h3>
              <div className="actors-grid">
                {event.actors.map(actor => (
                  <button
                    key={actor}
                    className="actor-button"
                    onClick={() => {
                      onActorClick(actor);
                      onClose();
                    }}
                  >
                    {actor}
                  </button>
                ))}
              </div>
            </div>
          )}

          {event.capture_lanes && event.capture_lanes.length > 0 && (
            <div className="detail-section">
              <h3>
                <FileText size={18} />
                Capture Lanes
              </h3>
              <div className="capture-lanes-grid">
                {event.capture_lanes.map(lane => (
                  <button
                    key={lane}
                    className="capture-lane-button"
                    onClick={() => {
                      onCaptureLaneClick(lane);
                      onClose();
                    }}
                    style={{ backgroundColor: getCaptureLaneColor(lane) }}
                  >
                    {lane}
                  </button>
                ))}
              </div>
            </div>
          )}

          {event.tags && event.tags.length > 0 && (
            <div className="detail-section">
              <h3>
                <Tag size={18} />
                Categories
              </h3>
              <div className="tags-grid">
                {event.tags.map(tag => (
                  <button
                    key={tag}
                    className="tag-button"
                    onClick={() => {
                      onTagClick(tag);
                      onClose();
                    }}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {event.sources && event.sources.length > 0 && (
            <div className="detail-section">
              <h3>
                <ExternalLink size={18} />
                Sources
              </h3>
              <div className="sources-list">
                {event.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-header">
                      <h4>{source.title}</h4>
                      {source.date && (
                        <span className="source-date">
                          {formatSourceDate(source.date)}
                        </span>
                      )}
                    </div>
                    {source.outlet && (
                      <span className="source-outlet">{source.outlet}</span>
                    )}
                    {source.url && (
                      <div className="source-links">
                        <a 
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-link"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink size={14} />
                          View Source
                        </a>
                        {brokenLinks[source.url] && (
                          <a
                            href={getArchiveUrl(source.url, source.date)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="archive-link"
                            onClick={(e) => e.stopPropagation()}
                          >
                            Try Archive
                          </a>
                        )}
                        <button
                          className="report-broken-link"
                          onClick={() => {
                            setBrokenLinks({...brokenLinks, [source.url]: true});
                            openGitHub(createBrokenLinkIssue(event.id, source.url));
                          }}
                          title="Report broken link"
                        >
                          <AlertTriangle size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="modal-footer">
            <div className="footer-left">
              <div className="event-id">
                ID: {event.id}
              </div>
            </div>
            <div className="github-links">
              <button
                className="github-link"
                onClick={() => openGitHub(getEventViewUrl(event.id))}
                title="View event source on GitHub"
              >
                <Github size={16} />
                View Source
              </button>
              <button
                className="github-link"
                onClick={() => openGitHub(getEventEditUrl(event.id))}
                title="Edit event on GitHub"
              >
                <Edit3 size={16} />
                Edit Event
              </button>
              <button
                className="github-link"
                onClick={() => openGitHub(createCorrectionIssue(event.id))}
                title="Suggest correction"
              >
                <AlertCircle size={16} />
                Report Issue
              </button>
            </div>
            <button className="action-button" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default EventDetails;