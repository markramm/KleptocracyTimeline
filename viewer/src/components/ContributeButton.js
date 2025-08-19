import React, { useState } from 'react';
import { Github, Plus, Edit, AlertCircle, ExternalLink } from 'lucide-react';
import './ContributeButton.css';

const ContributeButton = ({ eventId = null, eventTitle = null }) => {
  const [showModal, setShowModal] = useState(false);
  
  const repoUrl = 'https://github.com/yourusername/kleptocracy-timeline'; // Update with actual repo
  const contributingUrl = `${repoUrl}/blob/main/CONTRIBUTING.md`;
  
  const generateIssueUrl = (type) => {
    const baseUrl = `${repoUrl}/issues/new`;
    let title, body;
    
    switch (type) {
      case 'new-event':
        title = 'New Event: [Brief Description]';
        body = `## Event Proposal

**Date:** YYYY-MM-DD
**Title:** [Event title]
**Summary:** [1-2 sentence summary]

## Sources
1. [Source 1 URL]
2. [Source 2 URL]
3. [Source 3 URL]

## Why This Matters
[Explain the significance of this event]

## Tags
[Suggested tags]

## Actors
[Key people/organizations involved]`;
        break;
        
      case 'correction':
        title = eventTitle ? `Correction: ${eventTitle}` : 'Correction: [Event Title]';
        body = `## Correction Request

**Event ID:** ${eventId || '[Event ID]'}
**Event Title:** ${eventTitle || '[Event Title]'}

## What needs correction?
[Describe the issue]

## Correct information
[Provide the correct information]

## Sources
[Provide sources for the correction]`;
        break;
        
      case 'source':
        title = eventTitle ? `Additional Source: ${eventTitle}` : 'Additional Source: [Event Title]';
        body = `## Additional Source

**Event ID:** ${eventId || '[Event ID]'}
**Event Title:** ${eventTitle || '[Event Title]'}

## New Source
**URL:** [Source URL]
**Title:** [Article/Document Title]
**Date:** [Publication Date]

## Why this source is valuable
[Explain what this source adds]`;
        break;
        
      default:
        title = 'Timeline Contribution';
        body = 'Please describe your contribution...';
    }
    
    const params = new URLSearchParams({
      title,
      body,
      labels: 'contribution'
    });
    
    return `${baseUrl}?${params.toString()}`;
  };
  
  return (
    <>
      <button 
        className="contribute-button"
        onClick={() => setShowModal(true)}
        title="Contribute to timeline"
      >
        <Github size={16} />
        <span>Contribute</span>
      </button>
      
      {showModal && (
        <div className="contribute-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="contribute-modal" onClick={(e) => e.stopPropagation()}>
            <button 
              className="modal-close"
              onClick={() => setShowModal(false)}
              aria-label="Close"
            >
              ×
            </button>
            
            <h2>Contribute to the Timeline</h2>
            
            <div className="contribute-options">
              <a 
                href={generateIssueUrl('new-event')}
                target="_blank"
                rel="noopener noreferrer"
                className="contribute-option"
              >
                <Plus size={20} />
                <div>
                  <h3>Propose New Event</h3>
                  <p>Submit a new event with sources</p>
                </div>
                <ExternalLink size={16} />
              </a>
              
              {eventId && (
                <a 
                  href={generateIssueUrl('correction')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="contribute-option"
                >
                  <Edit size={20} />
                  <div>
                    <h3>Submit Correction</h3>
                    <p>Report an error in this event</p>
                  </div>
                  <ExternalLink size={16} />
                </a>
              )}
              
              {eventId && (
                <a 
                  href={generateIssueUrl('source')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="contribute-option"
                >
                  <AlertCircle size={20} />
                  <div>
                    <h3>Add Source</h3>
                    <p>Provide additional documentation</p>
                  </div>
                  <ExternalLink size={16} />
                </a>
              )}
            </div>
            
            <div className="contribute-guidelines">
              <h3>Contribution Guidelines</h3>
              <ul>
                <li>All events must have at least 3 credible sources</li>
                <li>Events must be factual and verifiable</li>
                <li>No speculation or future predictions</li>
                <li>Maintain neutral, factual tone</li>
              </ul>
              <a 
                href={contributingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="guidelines-link"
              >
                Read full guidelines <ExternalLink size={14} />
              </a>
            </div>
            
            <div className="contribute-direct">
              <p>Experienced contributor?</p>
              <a 
                href={`${repoUrl}/fork`}
                target="_blank"
                rel="noopener noreferrer"
                className="fork-link"
              >
                <Github size={16} />
                Fork repository and submit PR
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ContributeButton;