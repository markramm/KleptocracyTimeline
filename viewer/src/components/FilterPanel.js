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
  ChevronUp,
  Settings,
  ArrowUpDown,
  Star
} from 'lucide-react';
import TimelineMinimap from './TimelineMinimap';
import './FilterPanel.css';

const FilterPanel = ({
  allTags,
  allActors,
  allCaptureLanes,
  selectedTags,
  selectedActors,
  selectedCaptureLanes,
  dateRange,
  onTagsChange,
  onActorsChange,
  onCaptureLanesChange,
  onDateRangeChange,
  onClear,
  eventCount,
  totalCount,
  // Timeline view controls
  viewMode,
  timelineControls,
  onTimelineControlsChange,
  // Minimap data
  timelineData,
  // Events data for calculating counts
  events,
  // New props for sorting and importance
  sortOrder,
  onSortOrderChange,
  minImportance,
  onMinImportanceChange
}) => {
  const [expandedSections, setExpandedSections] = useState({
    sorting: true,
    importance: true,
    captureLanes: true,
    tags: false,
    actors: false,
    dates: true,
    timeline: viewMode === 'timeline'
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Calculate counts for each filter option
  const getTagCount = (tag) => {
    return events ? events.filter(event => 
      event.tags && event.tags.includes(tag)
    ).length : 0;
  };

  const getActorCount = (actor) => {
    return events ? events.filter(event => 
      event.actors && event.actors.includes(actor)
    ).length : 0;
  };

  const getCaptureLaneCount = (lane) => {
    return events ? events.filter(event => 
      event.capture_lanes && event.capture_lanes.includes(lane)
    ).length : 0;
  };

  // Create options with counts and sort by popularity (count desc)
  const tagOptions = allTags.map(tag => ({
    value: tag,
    label: tag.replace(/-/g, ' '),
    count: getTagCount(tag)
  })).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));

  const actorOptions = allActors.map(actor => ({
    value: actor,
    label: actor,
    count: getActorCount(actor)
  })).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));

  const captureLaneOptions = allCaptureLanes.map(lane => ({
    value: lane,
    label: lane,
    count: getCaptureLaneCount(lane)
  })).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));

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
      cursor: 'pointer',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
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

  // Custom option component to display counts
  const formatOptionLabel = ({ label, count }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
      <span>{label}</span>
      <span style={{ 
        backgroundColor: '#374151', 
        color: '#9ca3af', 
        fontSize: '12px', 
        padding: '2px 6px', 
        borderRadius: '10px',
        fontWeight: '500'
      }}>
        {count}
      </span>
    </div>
  );

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
    <div className="filter-panel">
      <div className="filter-header">
        <h3>
          <Filter size={20} />
          Filters
        </h3>
        {(selectedCaptureLanes.length > 0 || selectedTags.length > 0 || selectedActors.length > 0 || 
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
        {/* Sort Order Section */}
        <div className="filter-section">
          <button 
            className="section-header"
            onClick={() => toggleSection('sorting')}
          >
            <div className="header-title">
              <ArrowUpDown size={16} />
              <span>Sort Order</span>
              {sortOrder && sortOrder !== 'chronological' && (
                <span className="badge">Active</span>
              )}
            </div>
            {expandedSections.sorting ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          {expandedSections.sorting && (
            <div className="section-content">
              <div className="sort-options">
                <label className="radio-option">
                  <input
                    type="radio"
                    name="sortOrder"
                    value="chronological"
                    checked={sortOrder === 'chronological'}
                    onChange={(e) => onSortOrderChange(e.target.value)}
                  />
                  <span>Chronological (Oldest First)</span>
                </label>
                <label className="radio-option">
                  <input
                    type="radio"
                    name="sortOrder"
                    value="newest"
                    checked={sortOrder === 'newest'}
                    onChange={(e) => onSortOrderChange(e.target.value)}
                  />
                  <span>Newest First</span>
                </label>
                {viewMode !== 'timeline' && (
                  <>
                    <label className="radio-option">
                      <input
                        type="radio"
                        name="sortOrder"
                        value="importance"
                        checked={sortOrder === 'importance'}
                        onChange={(e) => onSortOrderChange(e.target.value)}
                      />
                      <span>By Importance</span>
                    </label>
                    <label className="radio-option">
                      <input
                        type="radio"
                        name="sortOrder"
                        value="alphabetical"
                        checked={sortOrder === 'alphabetical'}
                        onChange={(e) => onSortOrderChange(e.target.value)}
                      />
                      <span>Alphabetical</span>
                    </label>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Importance Filter Section */}
        <div className="filter-section">
          <button 
            className="section-header"
            onClick={() => toggleSection('importance')}
          >
            <div className="header-title">
              <Star size={16} />
              <span>Importance Level</span>
              {minImportance > 0 && (
                <span className="badge">{minImportance}+</span>
              )}
            </div>
            {expandedSections.importance ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          {expandedSections.importance && (
            <div className="section-content">
              <div className="importance-filter">
                <label>Show Events With Importance</label>
                <select
                  value={minImportance || 0}
                  onChange={(e) => onMinImportanceChange(Number(e.target.value))}
                  className="importance-select"
                >
                  <option value="0">All Events (1-10)</option>
                  <option value="5">5 or Higher (Noteworthy+)</option>
                  <option value="6">6 or Higher (Important+)</option>
                  <option value="7">7 or Higher (High Priority+)</option>
                  <option value="8">8 or Higher (Critical+)</option>
                  <option value="9">9 or Higher (Crisis+)</option>
                  <option value="10">10 Only (Maximum)</option>
                </select>
                <div className="importance-scale">
                  {[1,2,3,4,5,6,7,8,9,10].map(level => (
                    <div
                      key={level}
                      className={`importance-bar ${level >= minImportance ? 'active' : ''}`}
                      style={{
                        height: `${level * 10}%`,
                        backgroundColor: level >= minImportance ? 
                          (level >= 9 ? '#dc2626' : level >= 7 ? '#f59e0b' : level >= 5 ? '#3b82f6' : '#6b7280') :
                          '#374151'
                      }}
                      onClick={() => onMinImportanceChange(level)}
                      title={`Show events ${level}+`}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Capture Lanes Section */}
        <div className="filter-section">
          <button 
            className="section-header"
            onClick={() => toggleSection('captureLanes')}
          >
            <div className="header-title">
              <Filter size={16} />
              <span>Capture Lanes</span>
              {selectedCaptureLanes.length > 0 && (
                <span className="badge">{selectedCaptureLanes.length}</span>
              )}
            </div>
            {expandedSections.captureLanes ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          {expandedSections.captureLanes && (
            <div className="section-content">
              <Select
                isMulti
                options={captureLaneOptions}
                value={captureLaneOptions.filter(opt => selectedCaptureLanes.includes(opt.value))}
                onChange={(selected) => onCaptureLanesChange(selected.map(s => s.value))}
                placeholder="Select capture lanes..."
                styles={customStyles}
                className="filter-select"
                classNamePrefix="select"
                formatOptionLabel={formatOptionLabel}
              />
              
              {selectedCaptureLanes.length > 0 && (
                <div className="selected-items">
                  {selectedCaptureLanes.map(lane => (
                    <div 
                      key={lane}
                      className="selected-item capture-lane-item"
                      style={{ backgroundColor: getCaptureLaneColor(lane) }}
                    >
                      <span>{lane}</span>
                      <button
                        onClick={() => onCaptureLanesChange(selectedCaptureLanes.filter(l => l !== lane))}
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
                formatOptionLabel={formatOptionLabel}
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
                formatOptionLabel={formatOptionLabel}
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

        {/* Timeline View Controls */}
        {viewMode === 'timeline' && timelineControls && (
          <div className="filter-section">
            <button 
              className="section-header"
              onClick={() => toggleSection('timeline')}
            >
              <div className="header-title">
                <Settings size={16} />
                <span>Timeline View</span>
              </div>
              {expandedSections.timeline ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            
            {expandedSections.timeline && (
              <div className="section-content">
                <div className="control-group">
                  <label>Display Mode</label>
                  <select 
                    value={timelineControls.compactMode} 
                    onChange={(e) => onTimelineControlsChange({
                      ...timelineControls,
                      compactMode: e.target.value
                    })}
                    className="timeline-select"
                  >
                    <option value="none">Expand All</option>
                    <option value="low">Compact Low Importance</option>
                    <option value="medium">Compact Medium & Low</option>
                    <option value="all">Compact All</option>
                  </select>
                </div>
                
                <div className="control-group">
                  <label>Sort Events</label>
                  <select 
                    value={timelineControls.sortBy} 
                    onChange={(e) => onTimelineControlsChange({
                      ...timelineControls,
                      sortBy: e.target.value
                    })}
                    className="timeline-select"
                  >
                    <option value="date">By Date</option>
                    <option value="importance">By Importance</option>
                  </select>
                </div>
                
                <div className="control-group">
                  <label>Filter by Importance</label>
                  <select 
                    value={timelineControls.filterImportance} 
                    onChange={(e) => onTimelineControlsChange({
                      ...timelineControls,
                      filterImportance: Number(e.target.value)
                    })}
                    className="timeline-select"
                  >
                    <option value="0">All Events</option>
                    <option value="6">Important (6+)</option>
                    <option value="7">High Priority (7+)</option>
                    <option value="8">Critical (8+)</option>
                    <option value="9">Crisis (9+)</option>
                  </select>
                </div>
                
                <div className="control-group checkbox-group">
                  <label className="checkbox-label">
                    <input 
                      type="checkbox" 
                      checked={timelineControls.showMinimap}
                      onChange={(e) => onTimelineControlsChange({
                        ...timelineControls,
                        showMinimap: e.target.checked
                      })}
                    />
                    <span>Show Minimap</span>
                  </label>
                </div>
                
                {timelineControls.showMinimap && timelineData && (
                  <div className="minimap-container">
                    <TimelineMinimap 
                      events={timelineData.events}
                      groups={timelineData.groups}
                      onNavigate={timelineData.onNavigate}
                      onDateRangeSelect={timelineData.onDateRangeSelect}
                      currentDateRange={timelineData.currentDateRange}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="filter-footer">
        <p className="help-text">
          Click on tags or actors in events to quickly filter
        </p>
        {viewMode === 'timeline' && (
          <p className="help-text">
            Press M to toggle minimap, C to cycle display modes
          </p>
        )}
      </div>
    </div>
  );
};

export default FilterPanel;