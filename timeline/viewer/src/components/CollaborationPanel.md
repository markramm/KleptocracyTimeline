# Collaboration Panel - UI Mockup

## Event Detail View - Collaboration Features

```jsx
// For each timeline event, display these collaboration options:

<div className="event-detail">
  <h2>{event.title}</h2>
  <p className="date">{event.date}</p>
  <p className="summary">{event.summary}</p>
  
  {/* Collaboration Actions */}
  <div className="collaboration-panel">
    
    {/* Report Issue Button */}
    <button 
      className="btn-report-issue"
      onClick={() => openGitHubIssue({
        title: `Issue with event: ${event.id}`,
        body: generateIssueTemplate(event),
        labels: ['event-correction', 'needs-verification']
      })}
    >
      🚩 Report Issue
    </button>
    
    {/* Suggest Additional Source */}
    <button 
      className="btn-suggest-source"
      onClick={() => openSourceModal(event.id)}
    >
      📎 Suggest Source
    </button>
    
    {/* Request Verification */}
    {event.status === 'pending' && (
      <button 
        className="btn-request-verification"
        onClick={() => addToVerificationQueue(event.id)}
      >
        ✓ Help Verify
      </button>
    )}
    
    {/* Share Event */}
    <div className="share-buttons">
      <button onClick={() => shareToTwitter(event)}>🐦 Tweet</button>
      <button onClick={() => copyPermalink(event)}>🔗 Copy Link</button>
      <button onClick={() => getCitation(event)}>📚 Cite</button>
    </div>
  </div>
  
  {/* Verification Status Indicator */}
  <div className="verification-status">
    <h4>Verification Status</h4>
    {event.sources.map(source => (
      <div key={source.url} className="source-status">
        <span className={source.verified ? 'verified' : 'unverified'}>
          {source.verified ? '✅' : '⏳'} {source.title}
        </span>
        {!source.archived && (
          <button onClick={() => requestArchive(source.url)}>
            📦 Archive
          </button>
        )}
      </div>
    ))}
  </div>
</div>
```

## Main Timeline View - Contribution Dashboard

```jsx
<div className="contribution-dashboard">
  
  {/* Quick Stats */}
  <div className="stats-bar">
    <span>📊 {verifiedCount}/303 events verified</span>
    <span>📎 {archivedCount}/1000+ sources archived</span>
    <span>👥 {contributorCount} contributors this week</span>
  </div>
  
  {/* Call to Action */}
  <div className="cta-panel">
    <h3>🤝 How You Can Help</h3>
    
    <div className="help-cards">
      {/* Verify Events */}
      <div className="help-card">
        <h4>Verify Events</h4>
        <p>{pendingEvents.length} events need verification</p>
        <button onClick={() => showPendingEvents()}>
          Start Verifying →
        </button>
      </div>
      
      {/* Archive Sources */}
      <div className="help-card">
        <h4>Archive Sources</h4>
        <p>{unarchivedSources.length} sources need archiving</p>
        <button onClick={() => showUnarchivedSources()}>
          Start Archiving →
        </button>
      </div>
      
      {/* Research Gaps */}
      <div className="help-card">
        <h4>Research Gaps</h4>
        <p>Help fill timeline gaps</p>
        <button onClick={() => showResearchPriorities()}>
          View Priorities →
        </button>
      </div>
    </div>
  </div>
  
  {/* Suggest New Event Button */}
  <button className="btn-suggest-event-large">
    ➕ Suggest New Event
  </button>
</div>
```

## Source Suggestion Modal

```jsx
<Modal isOpen={sourceModalOpen} onClose={closeModal}>
  <h2>Suggest Additional Source</h2>
  <p>Help verify this event by adding another source</p>
  
  <form onSubmit={submitSource}>
    <label>
      Source URL *
      <input 
        type="url" 
        required 
        placeholder="https://..."
        onChange={validateUrl}
      />
    </label>
    
    <label>
      What does this source verify? *
      <textarea 
        required
        placeholder="This article confirms the date and actors involved..."
      />
    </label>
    
    <label>
      Key Quote (optional)
      <textarea 
        placeholder="Paste the most relevant paragraph..."
      />
    </label>
    
    <div className="verification-checklist">
      <h4>Before submitting, please confirm:</h4>
      <label>
        <input type="checkbox" required />
        I have read the article
      </label>
      <label>
        <input type="checkbox" required />
        It discusses this specific event
      </label>
      <label>
        <input type="checkbox" required />
        The source is from a credible outlet
      </label>
    </div>
    
    <button type="submit">Submit Source</button>
  </form>
</Modal>
```

## Research Request Section

```jsx
<div className="research-requests">
  <h2>🔍 Research Needed</h2>
  
  {/* Priority Research Topics */}
  <div className="priority-topics">
    {researchTopics.map(topic => (
      <div className="research-topic" key={topic.id}>
        <h3>{topic.title}</h3>
        <p>{topic.description}</p>
        <div className="topic-meta">
          <span>🎯 Priority: {topic.priority}</span>
          <span>👥 {topic.researchers} researching</span>
          <span>📊 {topic.eventsFound} events found</span>
        </div>
        <button onClick={() => claimResearchTopic(topic.id)}>
          Contribute Research →
        </button>
      </div>
    ))}
  </div>
  
  {/* Voting System */}
  <div className="vote-priorities">
    <h3>Vote on Research Priorities</h3>
    {suggestedTopics.map(topic => (
      <div className="topic-vote" key={topic.id}>
        <span>{topic.title}</span>
        <button onClick={() => voteTopic(topic.id)}>
          👍 {topic.votes}
        </button>
      </div>
    ))}
  </div>
</div>
```

## Stable URL Examples

```javascript
// Permanent URLs for citations and sharing:

// Direct event link
https://kleptocracy-timeline.org/event/2025-01-17--trump-memecoin-launch

// Human readable alternative  
https://kleptocracy-timeline.org/event/2025-01-17/trump-launches-memecoin

// Citation formats
https://kleptocracy-timeline.org/cite/2025-01-17--trump-memecoin-launch
https://kleptocracy-timeline.org/cite/2025-01-17--trump-memecoin-launch.bib
https://kleptocracy-timeline.org/cite/2025-01-17--trump-memecoin-launch.ris

// Filtered timeline views
https://kleptocracy-timeline.org/timeline/2025-01
https://kleptocracy-timeline.org/timeline?tags=cryptocurrency&status=confirmed
https://kleptocracy-timeline.org/search?q=epstein&year=2025

// Embeddable widgets
https://kleptocracy-timeline.org/embed/2025-01-17--trump-memecoin-launch
https://kleptocracy-timeline.org/embed/timeline?tags=crypto&limit=10

// Version permalinks (for citing specific versions)
https://kleptocracy-timeline.org/event/2025-01-17--trump-memecoin-launch?v=abc123
```

## GitHub Integration

```javascript
// Automatic issue creation with pre-filled templates:

function createGitHubIssue(type, data) {
  const templates = {
    'event-correction': {
      title: `Correction needed: ${data.eventId}`,
      body: `
## Event Correction Request

**Event ID:** ${data.eventId}
**Current Title:** ${data.title}
**Date:** ${data.date}

### What needs correction?
- [ ] Date is incorrect
- [ ] Summary has errors
- [ ] Sources don't support claims
- [ ] Missing important context
- [ ] Other: ___

### Details:
${data.userDescription}

### Current Data:
\`\`\`yaml
${data.currentYaml}
\`\`\`

### Suggested Correction:
${data.suggestion}
      `,
      labels: ['event-correction', 'needs-review']
    },
    
    'new-event': {
      title: `New event suggestion: ${data.title}`,
      body: `
## New Event Suggestion

**Date:** ${data.date}
**Title:** ${data.title}
**Summary:** ${data.summary}

### Sources:
${data.sources.map(s => `- ${s.url}`).join('\n')}

### Verification:
- [ ] I have read all sources
- [ ] Sources verify the claims
- [ ] Date is accurate
- [ ] Event is significant

### Why this matters:
${data.significance}
      `,
      labels: ['new-event', 'needs-verification']
    }
  };
  
  const template = templates[type];
  const githubUrl = `https://github.com/user/kleptocracy-timeline/issues/new?title=${encodeURIComponent(template.title)}&body=${encodeURIComponent(template.body)}&labels=${template.labels.join(',')}`;
  
  window.open(githubUrl, '_blank');
}
```