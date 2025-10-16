# Web UI Validation Workflow Design

## Overview

Design for integrating the new validation logging system into the existing timeline viewer web application. This adds manual validation capabilities with PR/patch generation for collaborative timeline curation.

## Core Components

### 1. ValidationPanel Component

**Location**: `viewer/src/components/ValidationPanel.js`

A collapsible panel that provides validation controls for timeline events:

```jsx
// ValidationPanel.js
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, AlertCircle, FileText, GitPullRequest } from 'lucide-react';

const ValidationPanel = ({ event, onValidationSubmit, onCreatePatch }) => {
  const [validationData, setValidationData] = useState({
    status: 'validated',
    confidence: 0.8,
    notes: '',
    issuesFound: [],
    sourcesVerified: [],
    timeSpent: 0
  });

  const [validationHistory, setValidationHistory] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Validation status options
  const statusOptions = [
    { value: 'validated', label: 'Validated', icon: CheckCircle, color: 'text-green-600' },
    { value: 'flagged', label: 'Needs Review', icon: AlertCircle, color: 'text-yellow-600' },
    { value: 'needs_work', label: 'Needs Work', icon: Clock, color: 'text-orange-600' },
    { value: 'rejected', label: 'Rejected', icon: AlertCircle, color: 'text-red-600' }
  ];

  return (
    <div className="validation-panel">
      {/* Validation Form */}
      <ValidationForm 
        data={validationData}
        onChange={setValidationData}
        onSubmit={onValidationSubmit}
        isSubmitting={isSubmitting}
      />
      
      {/* Validation History */}
      <ValidationHistory logs={validationHistory} />
      
      {/* Patch Generation */}
      <PatchGenerator 
        event={event}
        validationData={validationData}
        onCreatePatch={onCreatePatch}
      />
    </div>
  );
};
```

### 2. ValidationForm Sub-component

```jsx
const ValidationForm = ({ data, onChange, onSubmit, isSubmitting }) => (
  <form onSubmit={onSubmit} className="space-y-4">
    {/* Status Selection */}
    <div className="grid grid-cols-2 gap-2">
      {statusOptions.map(status => (
        <ValidationStatusButton key={status.value} {...status} />
      ))}
    </div>
    
    {/* Confidence Slider */}
    <ConfidenceSlider value={data.confidence} onChange={onChange} />
    
    {/* Notes Textarea */}
    <ValidationNotesField value={data.notes} onChange={onChange} />
    
    {/* Source Verification Checklist */}
    <SourceVerificationList event={event} data={data} onChange={onChange} />
    
    {/* Submit Button */}
    <ValidationSubmitButton isSubmitting={isSubmitting} />
  </form>
);
```

### 3. ValidationHistory Sub-component

```jsx
const ValidationHistory = ({ logs }) => (
  <div className="validation-history">
    <h4>Validation History ({logs.length})</h4>
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {logs.map(log => (
        <ValidationLogEntry key={log.id} log={log} />
      ))}
    </div>
  </div>
);

const ValidationLogEntry = ({ log }) => (
  <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
    <StatusIcon status={log.status} />
    <div className="flex-1">
      <div className="flex items-center justify-between">
        <span className="font-medium">{log.validator_type}</span>
        <time className="text-sm text-gray-500">
          {new Date(log.validation_date).toLocaleDateString()}
        </time>
      </div>
      <p className="text-sm text-gray-700 mt-1">{log.notes}</p>
      {log.confidence && (
        <div className="text-xs text-gray-500">
          Confidence: {Math.round(log.confidence * 100)}%
        </div>
      )}
    </div>
  </div>
);
```

### 4. PatchGenerator Sub-component

```jsx
const PatchGenerator = ({ event, validationData, onCreatePatch }) => {
  const [patchType, setPatchType] = useState('enhancement');
  const [patchDescription, setPatchDescription] = useState('');
  
  const patchTypes = [
    { value: 'enhancement', label: 'Enhancement', description: 'Improve sources, summary, or metadata' },
    { value: 'correction', label: 'Correction', description: 'Fix factual errors or inconsistencies' },
    { value: 'validation', label: 'Validation', description: 'Add validation log only' }
  ];

  const generatePatchPreview = () => {
    // Generate preview of changes that would be made
    return {
      files_changed: ['timeline_data/events/' + event.id + '.json'],
      additions: validationData.notes ? 1 : 0,
      deletions: 0,
      patch_size: 'small'
    };
  };

  return (
    <div className="patch-generator border-t pt-4">
      <h4>Generate Patch/PR</h4>
      
      {/* Patch Type Selection */}
      <PatchTypeSelector 
        types={patchTypes}
        selected={patchType}
        onChange={setPatchType}
      />
      
      {/* Patch Description */}
      <textarea
        value={patchDescription}
        onChange={(e) => setPatchDescription(e.target.value)}
        placeholder="Describe the changes being made..."
        className="w-full p-3 border rounded"
        rows={3}
      />
      
      {/* Patch Preview */}
      <PatchPreview preview={generatePatchPreview()} />
      
      {/* Generate Button */}
      <button
        onClick={() => onCreatePatch({
          type: patchType,
          description: patchDescription,
          validationData,
          event
        })}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        <GitPullRequest className="inline w-4 h-4 mr-2" />
        Create Patch/PR
      </button>
    </div>
  );
};
```

### 5. ValidationRunsManager Component

**Location**: `viewer/src/components/ValidationRunsManager.js`

A dedicated interface for creating and managing validation runs:

```jsx
const ValidationRunsManager = ({ onClose }) => {
  const [runs, setRuns] = useState([]);
  const [createRunForm, setCreateRunForm] = useState({
    run_type: 'random_sample',
    target_count: 50,
    min_importance: 6
  });

  const runTypes = [
    { value: 'random_sample', label: 'Random Sample', description: 'Random selection for health assessment' },
    { value: 'importance_focused', label: 'High Importance', description: 'Focus on critical events' },
    { value: 'date_range', label: 'Date Range', description: 'Events from specific period' },
    { value: 'pattern_detection', label: 'Pattern Detection', description: 'Find potential issues' }
  ];

  return (
    <div className="validation-runs-manager">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Create New Run */}
        <CreateRunForm 
          form={createRunForm}
          onChange={setCreateRunForm}
          runTypes={runTypes}
          onSubmit={createValidationRun}
        />
        
        {/* Active Runs List */}
        <ActiveRunsList 
          runs={runs.filter(r => r.status === 'active')}
          onSelectRun={setSelectedRun}
        />
      </div>
      
      {/* Run Progress */}
      {selectedRun && (
        <ValidationRunProgress 
          run={selectedRun}
          onValidateNext={validateNextEvent}
        />
      )}
    </div>
  );
};
```

### 6. API Service Extensions

**Location**: `viewer/src/services/validationService.js`

```javascript
// validationService.js
import { apiClient } from './apiService';

export const validationAPI = {
  // Validation Runs
  async getValidationRuns(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await apiClient.get(`/api/validation-runs?${params}`);
    return response.data;
  },

  async createValidationRun(runData) {
    const response = await apiClient.post('/api/validation-runs', runData, {
      headers: { 'X-API-Key': 'test-key' }
    });
    return response.data;
  },

  async getNextValidationEvent(runId, validatorId) {
    const params = validatorId ? `?validator_id=${validatorId}` : '';
    const response = await apiClient.get(`/api/validation-runs/${runId}/next${params}`);
    return response.data;
  },

  // Validation Logs
  async createValidationLog(logData) {
    const response = await apiClient.post('/api/validation-logs', logData, {
      headers: { 'X-API-Key': 'test-key' }
    });
    return response.data;
  },

  async getValidationLogs(eventId) {
    const response = await apiClient.get(`/api/validation-logs?event_id=${eventId}`);
    return response.data;
  },

  // Patch Generation
  async generatePatch(patchData) {
    // This would integrate with GitHub API or generate patch files
    const response = await apiClient.post('/api/validation/generate-patch', patchData, {
      headers: { 'X-API-Key': 'test-key' }
    });
    return response.data;
  }
};
```

### 7. Integration Points

#### App.js Integration

```jsx
// App.js additions
import ValidationPanel from './components/ValidationPanel';
import ValidationRunsManager from './components/ValidationRunsManager';
import { validationAPI } from './services/validationService';

function App() {
  // Add validation state
  const [showValidationPanel, setShowValidationPanel] = useState(false);
  const [showValidationRuns, setShowValidationRuns] = useState(false);
  const [validationMode, setValidationMode] = useState(false);

  // Add validation handlers
  const handleValidationSubmit = async (eventId, validationData) => {
    try {
      await validationAPI.createValidationLog({
        event_id: eventId,
        validator_type: 'human',
        validator_id: 'web-user',
        ...validationData
      });
      
      // Refresh validation history
      refreshValidationHistory(eventId);
      
      // Show success notification
      showNotification('Validation submitted successfully', 'success');
    } catch (error) {
      showNotification('Failed to submit validation', 'error');
    }
  };

  // Add to JSX
  return (
    <div className="App">
      {/* Existing content */}
      
      {/* Validation Toggle Button */}
      <ValidationToggleButton 
        active={validationMode}
        onClick={() => setValidationMode(!validationMode)}
      />
      
      {/* Validation Panel */}
      <AnimatePresence>
        {showValidationPanel && selectedEvent && (
          <ValidationPanel 
            event={selectedEvent}
            onValidationSubmit={handleValidationSubmit}
            onCreatePatch={handleCreatePatch}
          />
        )}
      </AnimatePresence>
      
      {/* Validation Runs Manager */}
      <AnimatePresence>
        {showValidationRuns && (
          <ValidationRunsManager onClose={() => setShowValidationRuns(false)} />
        )}
      </AnimatePresence>
    </div>
  );
}
```

#### EventDetails.js Integration

```jsx
// EventDetails.js additions
const EventDetails = ({ event, onClose, validationMode = false }) => {
  const [validationHistory, setValidationHistory] = useState([]);
  
  useEffect(() => {
    if (event && validationMode) {
      loadValidationHistory(event.id);
    }
  }, [event, validationMode]);

  return (
    <div className="event-details">
      {/* Existing event details */}
      
      {validationMode && (
        <>
          {/* Validation Status Badge */}
          <ValidationStatusBadge history={validationHistory} />
          
          {/* Quick Validation Actions */}
          <QuickValidationActions 
            event={event}
            onValidate={onQuickValidate}
          />
        </>
      )}
    </div>
  );
};
```

## Implementation Plan

### Phase 1: Core Components (Week 1)
1. Create ValidationPanel component with basic form
2. Add ValidationForm and ValidationHistory sub-components  
3. Implement validationService API integration
4. Basic validation log submission

### Phase 2: Advanced Features (Week 2)
1. Add PatchGenerator component
2. Implement ValidationRunsManager
3. Add validation mode toggle to main app
4. Integrate with EventDetails component

### Phase 3: PR/Patch Generation (Week 3)
1. Design patch generation API endpoint
2. Implement GitHub integration for PR creation
3. Add patch preview functionality
4. Test end-to-end validation workflow

### Phase 4: Polish & Testing (Week 4)
1. Add comprehensive error handling
2. Implement user authentication for validators
3. Add validation analytics and reporting
4. Performance optimization and testing

## Technical Considerations

### Authentication
- Use validator_id from user session
- Integrate with existing auth system
- Track validation contributions

### Performance
- Lazy load validation history
- Cache validation run data
- Optimize for mobile validation workflow

### Accessibility
- Keyboard navigation for validation forms
- Screen reader support for validation status
- High contrast validation indicators

### Data Integrity
- Validate form inputs client-side
- Handle network failures gracefully
- Provide offline validation capability

This design provides a comprehensive validation workflow that integrates seamlessly with the existing timeline viewer while adding powerful collaborative curation capabilities.