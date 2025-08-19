import React from 'react';
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
  XCircle
} from 'lucide-react';
import ContributeButton from './ContributeButton';
import './EventDetails.css';

const EventDetails = ({ event, onClose, onTagClick, onActorClick }) => {
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
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="modal-footer">
            <div className="event-id">
              ID: {event.id}
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