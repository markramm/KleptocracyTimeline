# Agent Guidelines - Viewer Application

## 🎯 Purpose
React-based interactive timeline viewer for exploring and understanding democratic capture patterns.

## 🏗️ Architecture

```
viewer/
├── src/
│   ├── components/       # React components
│   ├── utils/           # Helper functions
│   ├── hooks/           # Custom React hooks
│   ├── App.js           # Main application
│   └── config.js        # API endpoints
├── public/
│   └── api/            # Static JSON data
└── package.json        # Dependencies
```

## 🔧 Key Components

### Main Components
- **App.js** - Main application controller
- **LandingPage.js** - Entry point with project overview
- **EnhancedTimelineView.js** - Main timeline display
- **EventDetails.js** - Individual event modal
- **FilterPanel.js** - Event filtering controls
- **NetworkGraph.js** - D3.js network visualization
- **StatsPanel.js** - Statistics dashboard

### Utility Functions
- **githubUtils.js** - GitHub integration for contributions
- **shareUtils.js** - Deep linking and sharing
- **useUrlState.js** - URL parameter management

## 📊 Data Flow

1. **Static JSON** loaded from `/public/api/`
2. **State Management** via React hooks
3. **URL Sync** for deep linking
4. **Local Storage** for preferences

## 🚀 Development Tasks

### Running Locally
```bash
cd viewer
npm install
npm start
# Opens at http://localhost:3000
```

### Building for Production
```bash
# Standard build
npm run build

# GitHub Pages build
npm run build:gh-pages
```

### Testing Changes
```bash
# Component testing
npm test

# Visual testing
npm start
# Then manually verify in browser
```

## 🎨 Styling Guidelines

### CSS Structure
- Component-specific CSS files
- Dark theme with gradient backgrounds
- Responsive design (mobile-first)
- Consistent color scheme:
  - Primary: #3b82f6 (blue)
  - Success: #10b981 (green)
  - Warning: #fbbf24 (yellow)
  - Danger: #ef4444 (red)

### Component Patterns
```jsx
// Standard component structure
const ComponentName = ({ props }) => {
  // State hooks
  const [state, setState] = useState();
  
  // Effects
  useEffect(() => {}, []);
  
  // Handlers
  const handleAction = () => {};
  
  // Render
  return <div className="component-name">...</div>;
};
```

## 🔗 URL Parameters

### Supported Parameters
- `?event=EVENT_ID` - Open specific event
- `?lanes=Lane1,Lane2` - Filter by capture lanes
- `?tags=tag1,tag2` - Filter by tags
- `?actors=actor1,actor2` - Filter by actors
- `?dateRange=START:END` - Date filter
- `?search=query` - Search filter
- `?view=timeline|network` - View mode
- `?landing=true` - Show landing page

### Deep Link Examples
```
# Judicial capture events from 2025
?lanes=Judicial+Capture+%26+Corruption&dateRange=2025-01-01:2025-12-31

# Events involving specific actor
?actors=Trump&view=network

# Specific event
?event=2025-01-20--executive-order-spree
```

## 🐛 Common Issues & Solutions

### Build Warnings
```bash
# Unused variables - Safe to ignore for now
# React Hook dependencies - Review case by case
# These don't prevent building
```

### Performance Issues
1. **Too many events rendering**
   - Solution: Implement virtualization
   - Current: Pagination and filtering

2. **Network graph slow**
   - Solution: Limit initial nodes
   - Current: Progressive loading

3. **Large JSON files**
   - Solution: Already using static files
   - Future: Consider chunking

## ✅ Quality Checks

### Before Committing
1. **Builds without errors**: `npm run build`
2. **No console.logs**: Remove debug statements
3. **Mobile responsive**: Test at 375px width
4. **Links work**: Test GitHub integration
5. **State persists**: URL parameters maintain

### Component Checklist
- [ ] PropTypes or TypeScript types defined
- [ ] Error boundaries implemented
- [ ] Loading states handled
- [ ] Empty states designed
- [ ] Accessibility considered (ARIA labels)

## 📈 Performance Metrics

### Target Metrics
- Initial load: <3 seconds
- Time to interactive: <5 seconds
- Lighthouse score: >90
- Bundle size: <500KB gzipped

### Current Status
- Bundle size: ~182KB gzipped ✅
- Lighthouse: Not yet measured
- No backend needed ✅
- Static hosting compatible ✅

## 🔄 Update Workflows

### Adding New Features
1. Create component in `/src/components/`
2. Add styles in matching `.css` file
3. Import and integrate in App.js
4. Update URL state if needed
5. Test all view modes
6. Update this AGENT.md

### Updating Data Display
1. Modify component render logic
2. Update CSS for new elements
3. Ensure mobile responsive
4. Test with various data sizes
5. Verify filter integration

### Improving Performance
1. Profile with React DevTools
2. Identify render bottlenecks
3. Implement React.memo where needed
4. Lazy load heavy components
5. Optimize re-renders

## 🎯 User Experience Standards

### Navigation
- All features accessible within 2 clicks
- Clear visual feedback for actions
- Keyboard navigation support
- Back button works properly

### Information Display
- Progressive disclosure (don't overwhelm)
- Clear data hierarchy
- Consistent iconography
- Readable typography

### Interaction
- Immediate response to user actions
- Clear loading states
- Graceful error handling
- Helpful empty states

## 🚨 Critical Files

### Don't Break These
- `/public/api/*.json` - Data source
- `/src/config.js` - API endpoints
- `/src/App.js` - Main controller
- `/src/hooks/useUrlState.js` - URL management

### Safe to Modify
- Component styles (*.css)
- Component internal logic
- Utility functions
- Documentation files

## 🔧 Debugging Tools

### React DevTools
```javascript
// Inspect component state
// Check render performance
// Verify prop passing
```

### Browser Console
```javascript
// Check for errors
// Monitor network requests
// Debug state changes
```

### URL Debugging
```javascript
// Log URL parameters
console.log(window.location.search);
// Check state sync
console.log(urlState);
```

## 📋 Component Creation Template

```jsx
import React, { useState, useEffect } from 'react';
import './ComponentName.css';

const ComponentName = ({ requiredProp, optionalProp = defaultValue }) => {
  const [localState, setLocalState] = useState(initialValue);
  
  useEffect(() => {
    // Side effects here
  }, [dependencies]);
  
  const handleEvent = () => {
    // Event handler logic
  };
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data available</div>;
  
  return (
    <div className="component-name">
      {/* Component JSX */}
    </div>
  );
};

export default ComponentName;
```

## 🚀 Deployment

### GitHub Pages
```bash
# Build with correct public URL
npm run build:gh-pages

# Output in build/ directory
# GitHub Actions handles deployment
```

### Verification
1. Check https://markramm.github.io/KleptocracyTimeline/
2. Test deep links
3. Verify data loading
4. Check mobile view
5. Test share functionality

---

*"The interface is the message. Make the invisible visible, the complex comprehensible, the patterns undeniable."*