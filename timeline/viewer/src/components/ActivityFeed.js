import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const ActivityFeed = ({ activities }) => {
  if (!activities || activities.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        No recent activity
      </div>
    );
  }

  return (
    <div className="p-2">
      <AnimatePresence>
        {activities.map((activity, index) => (
          <motion.div
            key={`${activity.time}-${index}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            className={`
              p-3 mb-2 rounded-lg border transition-all hover:shadow-sm
              ${getActivityStyles(activity.type)}
            `}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                {activity.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 leading-relaxed">
                  {activity.text}
                </p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-500">
                    {activity.time}
                  </span>
                  <span className={`
                    text-xs px-2 py-0.5 rounded-full
                    ${getTypeStyles(activity.type)}
                  `}>
                    {activity.type}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

function getActivityStyles(type) {
  switch (type) {
    case 'event':
      return 'bg-blue-900/20 border-blue-700/30 hover:bg-blue-900/30';
    case 'priority':
      return 'bg-green-900/20 border-green-700/30 hover:bg-green-900/30';
    case 'sync':
      return 'bg-purple-900/20 border-purple-700/30 hover:bg-purple-900/30';
    default:
      return 'bg-gray-800/50 border-gray-700/50 hover:bg-gray-800/70';
  }
}

function getTypeStyles(type) {
  switch (type) {
    case 'event':
      return 'bg-blue-700/30 text-blue-300';
    case 'priority':
      return 'bg-green-700/30 text-green-300';
    case 'sync':
      return 'bg-purple-700/30 text-purple-300';
    default:
      return 'bg-gray-700/30 text-gray-400';
  }
}

export default ActivityFeed;