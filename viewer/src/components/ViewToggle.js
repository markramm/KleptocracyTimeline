import React from 'react';
import { LayoutGrid, List, GitBranch, Clock } from 'lucide-react';
import './ViewToggle.css';

const ViewToggle = ({ currentView, onViewChange }) => {
  const views = [
    { id: 'timeline', icon: Clock, label: 'Timeline' },
    { id: 'list', icon: List, label: 'List' },
    { id: 'grid', icon: LayoutGrid, label: 'Grid' },
    { id: 'graph', icon: GitBranch, label: 'Graph' }
  ];

  return (
    <div className="view-toggle">
      {views.map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          className={`view-button ${currentView === id ? 'active' : ''}`}
          onClick={() => onViewChange(id)}
          title={label}
        >
          <Icon size={18} />
          <span className="view-label">{label}</span>
        </button>
      ))}
    </div>
  );
};

export default ViewToggle;