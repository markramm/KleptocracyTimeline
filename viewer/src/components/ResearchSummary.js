import React from 'react';
import { motion } from 'framer-motion';
import { 
  Database, 
  Search, 
  FileText, 
  CheckCircle,
  Clock,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

const ResearchSummary = ({ summary, onDetailsToggle, showDetails }) => {
  if (!summary) {
    return (
      <div className="p-4 border-b border-gray-700">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  const {
    total_events = 0,
    active_priorities = 0,
    staged_events_count = 0,
    commit_progress = '0/10',
    events_needing_validation = 0
  } = summary;

  const commitProgress = commit_progress.split('/');
  const commitCurrent = parseInt(commitProgress[0]) || 0;
  const commitTotal = parseInt(commitProgress[1]) || 10;
  const commitPercentage = (commitCurrent / commitTotal) * 100;

  return (
    <div className="border-b border-gray-700">
      {/* Main Summary */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Database className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-gray-400">Total Events</span>
            </div>
            <div className="text-lg font-semibold text-white">
              {total_events.toLocaleString()}
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Search className="w-4 h-4 text-green-400" />
              <span className="text-xs text-gray-400">Active Research</span>
            </div>
            <div className="text-lg font-semibold text-white">
              {active_priorities}
            </div>
          </div>
        </div>

        {/* Commit Progress */}
        <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-400">Commit Progress</span>
            </div>
            <span className="text-xs text-gray-300">{commit_progress}</span>
          </div>
          
          <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
            <motion.div
              className="bg-purple-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${commitPercentage}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          
          <div className="text-xs text-gray-400">
            {commitCurrent} staged events ready for commit
          </div>
        </div>

        {/* Validation Status */}
        {events_needing_validation > 0 && (
          <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-yellow-400">Needs Validation</span>
            </div>
            <div className="text-sm text-yellow-300">
              {events_needing_validation} events awaiting validation
            </div>
          </div>
        )}
      </div>

      {/* Toggle Details */}
      <button
        onClick={onDetailsToggle}
        className="w-full flex items-center justify-center gap-2 p-2 text-xs text-gray-400 hover:text-gray-300 hover:bg-gray-800/50 transition-colors border-t border-gray-700"
      >
        <span>{showDetails ? 'Hide Details' : 'Show Details'}</span>
        {showDetails ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>
    </div>
  );
};

export default ResearchSummary;