import React, { useState } from 'react';
import { BarChart3, TrendingUp, Calendar, Tag, AlertCircle, Activity, Database, Search, FileText, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { useResearchMonitoring } from '../hooks/useResearchMonitoring';
import './StatsPanel.css';

const StatsPanel = ({ stats, events }) => {
  const [showResearchDetails, setShowResearchDetails] = useState(false);
  const { activities, summary, error, isPolling, clearActivities, refreshNow } = useResearchMonitoring();

  // Ensure stats is defined
  if (!stats) {
    return (
      <div className="stats-panel">
        <div className="stats-header">
          <h3>
            <BarChart3 size={20} />
            Analytics
          </h3>
        </div>
        <p>Loading statistics...</p>
      </div>
    );
  }

  // const getTopItems = (items, limit = 5) => {
  //   if (!items) return [];
  //   return Object.entries(items)
  //     .sort(([, a], [, b]) => b - a)
  //     .slice(0, limit);
  // };

  const getPatternInsights = () => {
    const insights = [];
    
    // Check monitoring status if available
    if (stats.monitoring_summary) {
      if (stats.monitoring_summary.active > 0) {
        insights.push({
          type: 'critical',
          text: `${stats.monitoring_summary.active} events actively being monitored`
        });
      }
      if (stats.monitoring_summary.total > 5) {
        insights.push({
          type: 'warning',
          text: `${stats.monitoring_summary.total} total events flagged for monitoring`
        });
      }
    }
    
    // Check recent activity
    if (stats.events_by_year && stats.events_by_year['2025'] > 50) {
      insights.push({
        type: 'info',
        text: `High activity in 2025: ${stats.events_by_year['2025']} events`
      });
    }
    
    return insights;
  };

  const insights = getPatternInsights();

  return (
    <div className="stats-panel">
      <div className="stats-header">
        <h3>
          <BarChart3 size={20} />
          Analytics
        </h3>
      </div>

      <div className="stats-sections">
        {/* Research Monitor Section */}
        <div className="stats-section research-monitor-section">
          <h4>
            <Activity size={16} />
            Research Monitor
            {isPolling && <span className="polling-indicator">●</span>}
          </h4>
          
          {/* Research Summary */}
          {summary && (
            <div className="research-summary">
              <div className="summary-grid">
                <div className="summary-item">
                  <Database size={14} />
                  <span className="summary-label">Total Events</span>
                  <span className="summary-value">{(summary.total_events || 0).toLocaleString()}</span>
                </div>
                <div className="summary-item">
                  <Search size={14} />
                  <span className="summary-label">Active Research</span>
                  <span className="summary-value">{summary.active_priorities || 0}</span>
                </div>
                <div className="summary-item">
                  <FileText size={14} />
                  <span className="summary-label">Staged Events</span>
                  <span className="summary-value">{summary.staged_events_count || 0}</span>
                </div>
              </div>
              
              {/* Commit Progress */}
              {summary.commit_progress && (
                <div className="commit-progress">
                  <div className="progress-header">
                    <span className="progress-label">Commit Progress</span>
                    <span className="progress-text">{summary.commit_progress}</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ 
                        width: `${((parseInt(summary.commit_progress.split('/')[0]) || 0) / (parseInt(summary.commit_progress.split('/')[1]) || 10)) * 100}%` 
                      }}
                    />
                  </div>
                </div>
              )}
              
              {/* Validation Status */}
              {summary.events_needing_validation > 0 && (
                <div className="validation-alert">
                  <Clock size={14} />
                  <span>{summary.events_needing_validation} events need validation</span>
                </div>
              )}
            </div>
          )}
          
          {error && (
            <div className="research-error">
              <AlertCircle size={14} />
              <span>Research monitor error: {error}</span>
            </div>
          )}
          
          {/* Activity Toggle */}
          <button
            onClick={() => setShowResearchDetails(!showResearchDetails)}
            className="activity-toggle"
          >
            <span>{showResearchDetails ? 'Hide Activity' : 'Show Recent Activity'}</span>
            {showResearchDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          
          {/* Activity Feed */}
          {showResearchDetails && (
            <div className="activity-feed">
              {activities.length > 0 ? (
                <div className="activity-list">
                  {activities.slice(-5).map((activity, index) => (
                    <div key={`${activity.time}-${index}`} className={`activity-item ${activity.type}`}>
                      <div className="activity-content">
                        <span className="activity-text">{activity.text}</span>
                        <span className="activity-time">{activity.time}</span>
                      </div>
                      <span className="activity-type-badge">{activity.type}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-activity">No recent research activity</div>
              )}
              
              {activities.length > 0 && (
                <div className="activity-controls">
                  <button onClick={refreshNow} className="refresh-btn">Refresh</button>
                  <button onClick={clearActivities} className="clear-btn">Clear</button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Overview */}
        <div className="stats-section">
          <h4>Overview</h4>
          <div className="stat-cards">
            <div className="stat-card">
              <span className="stat-value">{stats.total_events || 0}</span>
              <span className="stat-label">Total Events</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">
                {stats.events_by_year ? Object.keys(stats.events_by_year).length : 0}
              </span>
              <span className="stat-label">Years Covered</span>
            </div>
            {stats.date_range && (
            <div className="stat-card">
              <span className="stat-value">
                {stats.date_range.start?.substring(0, 4) || '?'} - {stats.date_range.end?.substring(0, 4) || '?'}
              </span>
              <span className="stat-label">Date Range</span>
            </div>
            )}
          </div>
        </div>

        {/* Events by Status */}
        {stats.events_by_status && (
        <div className="stats-section">
          <h4>Verification Status</h4>
          <div className="status-bars">
            {Object.entries(stats.events_by_status).map(([status, count]) => (
              <div key={status} className="status-bar">
                <div className="status-header">
                  <span className="status-name">{status.replace('_', ' ')}</span>
                  <span className="status-count">{count}</span>
                </div>
                <div className="bar-container">
                  <div 
                    className={`bar ${status}`}
                    style={{ 
                      width: `${(count / stats.total_events) * 100}%` 
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Monitoring Summary */}
        {stats.monitoring_summary && (
        <div className="stats-section">
          <h4>
            <Tag size={16} />
            Monitoring Status
          </h4>
          <div className="top-list">
            {Object.entries(stats.monitoring_summary).map(([status, count]) => (
              <div key={status} className="top-item">
                <span className="item-name">{status.replace(/_/g, ' ')}</span>
                <div className="item-bar">
                  <div 
                    className="bar-fill"
                    style={{ 
                      width: `${(count / Math.max(...Object.values(stats.monitoring_summary))) * 100}%`,
                      backgroundColor: status === 'active' ? '#ef4444' : '#6b7280'
                    }}
                  />
                  <span className="item-count">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Events by Year */}
        {stats.events_by_year && (
        <div className="stats-section">
          <h4>
            <Calendar size={16} />
            Events by Year
          </h4>
          <div className="year-chart">
            {Object.entries(stats.events_by_year)
              .sort(([a], [b]) => b.localeCompare(a))
              .slice(0, 10)
              .map(([year, count]) => (
                <div key={year} className="year-item">
                  <span className="year-label">{year}</span>
                  <div className="year-bar-container">
                    <div 
                      className="year-bar"
                      style={{ 
                        width: `${(count / Math.max(...Object.values(stats.events_by_year))) * 100}%`,
                        backgroundColor: year === '2025' ? '#ef4444' : '#3b82f6'
                      }}
                    />
                    <span className="year-count">{count}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
        )}

        {/* Insights */}
        {insights.length > 0 && (
          <div className="stats-section">
            <h4>
              <TrendingUp size={16} />
              Pattern Insights
            </h4>
            <div className="insights-list">
              {insights.map((insight, index) => (
                <div key={index} className={`insight ${insight.type}`}>
                  <AlertCircle size={16} />
                  <span>{insight.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Actors */}
        {stats.top_actors && stats.top_actors.length > 0 && (
        <div className="stats-section">
          <h4>
            <TrendingUp size={16} />
            Top Actors
          </h4>
          <div className="top-list">
            {stats.top_actors.slice(0, 5).map((actor, index) => (
              <div key={actor.name} className="top-item">
                <span className="item-name">{actor.name}</span>
                <div className="item-bar">
                  <div 
                    className="bar-fill"
                    style={{ 
                      width: `${(actor.event_count / stats.top_actors[0].event_count) * 100}%`,
                      backgroundColor: index === 0 ? '#ef4444' : '#3b82f6'
                    }}
                  />
                  <span className="item-count">{actor.event_count} events</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Importance Distribution */}
        {stats.importance_distribution && Object.keys(stats.importance_distribution).length > 0 && (
        <div className="stats-section">
          <h4>
            <AlertCircle size={16} />
            Importance Levels
          </h4>
          <div className="importance-chart">
            {Object.entries(stats.importance_distribution)
              .sort(([a], [b]) => Number(b) - Number(a))
              .slice(0, 8)
              .map(([level, count]) => (
                <div key={level} className="importance-item">
                  <span className="importance-label">Level {level}</span>
                  <div className="importance-bar-container">
                    <div 
                      className="importance-bar"
                      style={{ 
                        width: `${(count / Math.max(...Object.values(stats.importance_distribution))) * 100}%`,
                        backgroundColor: Number(level) >= 8 ? '#ef4444' : Number(level) >= 6 ? '#f59e0b' : '#3b82f6'
                      }}
                    />
                    <span className="importance-count">{count}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
        )}

        {/* Recent Trends */}
        {events && events.length > 0 && (
        <div className="stats-section">
          <h4>Recent Activity</h4>
          <div className="trend-info">
            <p>
              {events.filter(e => e.date?.startsWith('2025')).length} events in 2025
            </p>
            <p>
              {events.filter(e => e.date?.startsWith('2024')).length} events in 2024
            </p>
            {stats.events_by_year && (
            <p>
              Average: {Math.round(stats.total_events / Object.keys(stats.events_by_year).length)} events/year
            </p>
            )}
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

/* const getCategoryColor = (tag) => {
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
}; */

export default StatsPanel;