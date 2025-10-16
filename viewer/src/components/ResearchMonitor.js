import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  ChevronRight, 
  ChevronLeft,
  Database,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  X
} from 'lucide-react';
import { useResearchMonitoring } from '../hooks/useResearchMonitoring';
import ActivityFeed from './ActivityFeed';
import ResearchSummary from './ResearchSummary';

const ResearchMonitor = ({ isCollapsed = false, onToggle }) => {
  const { activities, summary, error, isPolling, refreshNow } = useResearchMonitoring();
  const [showDetails, setShowDetails] = useState(false);

  // Format activity for display
  const formatActivity = (activity) => {
    const time = new Date(activity.timestamp).toLocaleTimeString();
    
    switch (activity.type) {
      case 'event_staged':
        return {
          icon: <Database className="w-4 h-4 text-blue-500" />,
          text: `Event staged: ${activity.data.event_id || 'New event'}`,
          time,
          type: 'event'
        };
      case 'priority_status_updated':
        return {
          icon: <CheckCircle className="w-4 h-4 text-green-500" />,
          text: `Priority ${activity.data.new_status}: ${activity.data.priority_id || 'Unknown'}`,
          time,
          type: 'priority'
        };
      case 'filesystem_sync':
        return {
          icon: <RefreshCw className="w-4 h-4 text-purple-500" />,
          text: `Synced ${activity.data.new_events || 0} new events`,
          time,
          type: 'sync'
        };
      default:
        return {
          icon: <Activity className="w-4 h-4 text-gray-500" />,
          text: `${activity.type}: ${JSON.stringify(activity.data)}`,
          time,
          type: 'other'
        };
    }
  };

  const recentActivities = activities.slice(-5).map(formatActivity);

  if (isCollapsed) {
    return (
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: 48 }}
        className="bg-gray-900 border-l border-gray-700 flex flex-col items-center py-4"
      >
        <button
          onClick={onToggle}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          title="Open Research Monitor"
        >
          <Activity className="w-5 h-5" />
        </button>
        
        {/* Activity indicator */}
        {activities.length > 0 && (
          <div className="mt-4 relative">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping"></div>
          </div>
        )}
        
        {error && (
          <AlertCircle className="w-4 h-4 text-red-500 mt-2" title={error} />
        )}
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ width: 0 }}
      animate={{ width: 320 }}
      exit={{ width: 0 }}
      className="bg-gray-900 border-l border-gray-700 flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <h3 className="text-white font-medium">Research Monitor</h3>
          {isPolling && (
            <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1 text-gray-400 hover:text-white hover:bg-gray-800 rounded transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-900/20 border-b border-gray-700">
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Connection Error</span>
          </div>
          <p className="text-gray-400 text-xs mt-1">{error}</p>
          <button
            onClick={refreshNow}
            className="text-blue-400 text-xs hover:underline mt-1"
          >
            Try again
          </button>
        </div>
      )}

      {/* Summary */}
      {summary && (
        <ResearchSummary 
          summary={summary} 
          onDetailsToggle={() => setShowDetails(!showDetails)}
          showDetails={showDetails}
        />
      )}

      {/* Activity Feed */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="p-3 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h4 className="text-gray-300 text-sm font-medium">Recent Activity</h4>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">
                {activities.length} events
              </span>
              <button
                onClick={refreshNow}
                className="text-gray-400 hover:text-white transition-colors"
                disabled={isPolling}
              >
                <RefreshCw className={`w-3 h-3 ${isPolling ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <ActivityFeed activities={recentActivities} />
        </div>
      </div>

      {/* Expanded details */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="border-t border-gray-700 overflow-hidden"
          >
            <div className="p-4 bg-gray-800/50">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white text-sm font-medium">Session Details</h4>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Poll Interval:</span>
                  <span className="text-gray-300">15s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Last Update:</span>
                  <span className="text-gray-300">
                    {new Date().toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Connection:</span>
                  <span className={`${error ? 'text-red-400' : 'text-green-400'}`}>
                    {error ? 'Error' : 'Active'}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ResearchMonitor;