import React from 'react';
import { BarChart3, TrendingUp, Calendar, Tag, Users, AlertCircle } from 'lucide-react';
import './StatsPanel.css';

const StatsPanel = ({ stats, events }) => {
  const getTopItems = (items, limit = 5) => {
    return Object.entries(items)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit);
  };

  const getPatternInsights = () => {
    const insights = [];
    const tagCounts = stats.tag_counts;
    
    if (tagCounts['constitutional-crisis'] > 10) {
      insights.push({
        type: 'critical',
        text: `${tagCounts['constitutional-crisis']} constitutional crisis events detected`
      });
    }
    
    if (tagCounts['foreign-influence'] > 15) {
      insights.push({
        type: 'warning',
        text: `High foreign influence activity: ${tagCounts['foreign-influence']} events`
      });
    }
    
    if (tagCounts['crypto'] > 20) {
      insights.push({
        type: 'info',
        text: `Significant crypto-related activity: ${tagCounts['crypto']} events`
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
        {/* Overview */}
        <div className="stats-section">
          <h4>Overview</h4>
          <div className="stat-cards">
            <div className="stat-card">
              <span className="stat-value">{stats.total_events}</span>
              <span className="stat-label">Total Events</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">
                {Object.keys(stats.events_by_year).length}
              </span>
              <span className="stat-label">Years Covered</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">
                {stats.date_range.start.substring(0, 4)} - {stats.date_range.end.substring(0, 4)}
              </span>
              <span className="stat-label">Date Range</span>
            </div>
          </div>
        </div>

        {/* Events by Status */}
        <div className="stats-section">
          <h4>Verification Status</h4>
          <div className="status-bars">
            {Object.entries(stats.status_counts).map(([status, count]) => (
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

        {/* Top Categories */}
        <div className="stats-section">
          <h4>
            <Tag size={16} />
            Top Categories
          </h4>
          <div className="top-list">
            {getTopItems(stats.tag_counts).map(([tag, count]) => (
              <div key={tag} className="top-item">
                <span className="item-name">{tag.replace(/-/g, ' ')}</span>
                <div className="item-bar">
                  <div 
                    className="bar-fill"
                    style={{ 
                      width: `${(count / stats.total_events) * 100}%`,
                      backgroundColor: getCategoryColor(tag)
                    }}
                  />
                  <span className="item-count">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Events by Year */}
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

        {/* Recent Trends */}
        <div className="stats-section">
          <h4>Recent Activity</h4>
          <div className="trend-info">
            <p>
              {events.filter(e => e.date?.startsWith('2025')).length} events in 2025
            </p>
            <p>
              {events.filter(e => e.date?.startsWith('2024')).length} events in 2024
            </p>
            <p>
              Average: {Math.round(stats.total_events / Object.keys(stats.events_by_year).length)} events/year
            </p>
          </div>
        </div>
      </div>
    </div>
  );
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

export default StatsPanel;