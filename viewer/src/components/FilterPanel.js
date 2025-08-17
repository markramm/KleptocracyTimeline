import React, { useState } from 'react';
import Select from 'react-select';
import { 
  Filter, 
  X, 
  Calendar, 
  Users, 
  Tag, 
  RotateCcw,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import './FilterPanel.css';

const FilterPanel = ({
  allTags,
  allActors,
  selectedTags,
  selectedActors,
  dateRange,
  onTagsChange,
  onActorsChange,
  onDateRangeChange,
  onClear,
  eventCount,
  totalCount
}) => {
  const [expandedSections, setExpandedSections] = useState({
    tags: true,
    actors: true,
    dates: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const tagOptions = allTags.map(tag => ({
    value: tag,
    label: tag.replace(/-/g, ' '),
    count: 0 // Would need to calculate from events
  }));

  const actorOptions = allActors.map(actor => ({
    value: actor,
    label: actor,
    count: 0 // Would need to calculate from events
  }));

  const customStyles = {
    control: (base) => ({
      ...base,
      backgroundColor: '#1f2937',
      borderColor: '#374151',
      minHeight: '38px'
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: '#1f2937',
      border: '1px solid #374151'
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? '#374151' : '#1f2937',
      color: '#e5e7eb',
      cursor: 'pointer'
    }),
    multiValue: (base) => ({
      ...base,
      backgroundColor: '#3b82f6',
      borderRadius: '4px'
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: 'white',
      fontSize: '12px'
    }),
    multiValueRemove: (base) => ({
      ...base,
      color: 'white',
      ':hover': {
        backgroundColor: '#2563eb',
        color: 'white'
      }
    })
  };

  const getCategoryColor = (tag) => {
    const colors = {
      'constitutional-crisis': '#ef4444',
      'foreign-influence': '#f59e0b',
      'crypto': '#8b5cf6',
      'money-laundering': '#10b981',
      'regulatory-capture': '#3b82f6',
      'immigration': '#ec4899',
      'intelligence': '#6b7280'
    };
    
    for (const [key, color] of Object.entries(colors)) {
      if (tag.includes(key)) return color;
    }
    return '#6b7280';
  };

  return (
    <div className="filter-panel">
      <div className="filter-header">
        <h3>
          <Filter size={20} />
          Filters
        </h3>
        {(selectedTags.length > 0 || selectedActors.length > 0 || 
          dateRange.start || dateRange.end) && (
          <button className="clear-filters-button" onClick={onClear}>
            <RotateCcw size={16} />
            Clear
          </button>
        )}
      </div>

      <div className="filter-stats">
        <div className="stat">
          <span className="stat-value">{eventCount}</span>
          <span className="stat-label">Filtered</span>
        </div>
        <div className="stat">
          <span className="stat-value">{totalCount}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat">
          <span className="stat-value">
            {Math.round((eventCount / totalCount) * 100)}%
          </span>
          <span className="stat-label">Shown</span>
        </div>
      </div>

      <div className="filter-sections">
        {/* Tags Section */}
        <div className="filter-section">
          <button 
            className="section-header"
            onClick={() => toggleSection('tags')}
          >
            <div className="header-title">
              <Tag size={16} />
              <span>Categories</span>
              {selectedTags.length > 0 && (
                <span className="badge">{selectedTags.length}</span>
              )}
            </div>
            {expandedSections.tags ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          {expandedSections.tags && (
            <div className="section-content">
              <Select
                isMulti
                options={tagOptions}
                value={tagOptions.filter(opt => selectedTags.includes(opt.value))}
                onChange={(selected) => onTagsChange(selected.map(s => s.value))}
                placeholder="Select categories..."
                styles={customStyles}
                className="filter-select"
                classNamePrefix="select"
              />
              
              {selectedTags.length > 0 && (
                <div className="selected-items">
                  {selectedTags.map(tag => (
                    <div 
                      key={tag}
                      className="selected-item"
                      style={{ backgroundColor: getCategoryColor(tag) }}
                    >
                      <span>{tag.replace(/-/g, ' ')}</span>
                      <button
                        onClick={() => onTagsChange(selectedTags.filter(t => t !== tag))}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Actors Section */}
        <div className="filter-section">
          <button 
            className="section-header"
            onClick={() => toggleSection('actors')}
          >
            <div className="header-title">
              <Users size={16} />
              <span>Actors</span>
              {selectedActors.length > 0 && (
                <span className="badge">{selectedActors.length}</span>
              )}
            </div>
            {expandedSections.actors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          {expandedSections.actors && (
            <div className="section-content">
              <Select
                isMulti
                options={actorOptions}
                value={actorOptions.filter(opt => selectedActors.includes(opt.value))}
                onChange={(selected) => onActorsChange(selected.map(s => s.value))}
                placeholder="Select actors..."
                styles={customStyles}
                className="filter-select"
                classNamePrefix="select"
              />
              
              {selectedActors.length > 0 && (
                <div className="selected-items">
                  {selectedActors.map(actor => (
                    <div key={actor} className="selected-item actor-item">
                      <span>{actor}</span>
                      <button
                        onClick={() => onActorsChange(selectedActors.filter(a => a !== actor))}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Date Range Section */}
        <div className="filter-section">
          <button 
            className="section-header"
            onClick={() => toggleSection('dates')}
          >
            <div className="header-title">
              <Calendar size={16} />
              <span>Date Range</span>
              {(dateRange.start || dateRange.end) && (
                <span className="badge">Active</span>
              )}
            </div>
            {expandedSections.dates ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          {expandedSections.dates && (
            <div className="section-content">
              <div className="date-inputs">
                <div className="date-input-group">
                  <label>From</label>
                  <input
                    type="date"
                    value={dateRange.start || ''}
                    onChange={(e) => onDateRangeChange({
                      ...dateRange,
                      start: e.target.value
                    })}
                    className="date-input"
                  />
                </div>
                <div className="date-input-group">
                  <label>To</label>
                  <input
                    type="date"
                    value={dateRange.end || ''}
                    onChange={(e) => onDateRangeChange({
                      ...dateRange,
                      end: e.target.value
                    })}
                    className="date-input"
                  />
                </div>
              </div>
              
              <div className="quick-ranges">
                <button
                  className="quick-range-button"
                  onClick={() => onDateRangeChange({
                    start: '2025-01-01',
                    end: '2025-12-31'
                  })}
                >
                  2025
                </button>
                <button
                  className="quick-range-button"
                  onClick={() => onDateRangeChange({
                    start: '2024-01-01',
                    end: '2024-12-31'
                  })}
                >
                  2024
                </button>
                <button
                  className="quick-range-button"
                  onClick={() => onDateRangeChange({
                    start: '2020-01-01',
                    end: '2025-12-31'
                  })}
                >
                  2020-2025
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="filter-footer">
        <p className="help-text">
          Click on tags or actors in events to quickly filter
        </p>
      </div>
    </div>
  );
};

export default FilterPanel;