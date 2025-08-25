let events = [];
let sourceStatuses = {};

async function loadEvents() {
    const response = await fetch('/api/events');
    events = await response.json();
    renderEvents();
    updateStats();
}

function renderEvents() {
    const container = document.getElementById('events-container');
    const statusFilter = document.getElementById('status-filter').value;
    const importanceFilter = document.getElementById('importance-filter').value;
    
    let filteredEvents = events;
    
    // Apply status filter
    if (statusFilter === 'validated') {
        filteredEvents = filteredEvents.filter(e => e.validated);
    } else if (statusFilter === 'unvalidated') {
        filteredEvents = filteredEvents.filter(e => !e.validated);
    }
    
    // Apply importance filter
    if (importanceFilter) {
        if (importanceFilter === '7') {
            filteredEvents = filteredEvents.filter(e => e.importance <= 7);
        } else {
            filteredEvents = filteredEvents.filter(e => e.importance == importanceFilter);
        }
    }
    
    container.innerHTML = filteredEvents.map(event => `
        <div class="event-card ${event.validated ? 'validated' : ''}" data-event-id="${event.id}">
            <div class="event-header">
                <div>
                    <div class="event-title">
                        ${event.validated ? '<span class="validation-badge">✓ Validated</span>' : ''}
                        ${event.title}
                    </div>
                    <div class="event-date">${event.date}</div>
                    ${event.validated && event.validated_date ? `<div class="validated-info">Validated on ${new Date(event.validated_date).toLocaleDateString()}</div>` : ''}</div>
                <span class="importance importance-${event.importance}">
                    Importance: ${event.importance}
                </span>
            </div>
            <div class="summary">${event.summary}</div>
            
            <div class="sources-section">
                <h4>Sources (${event.sources ? event.sources.length : 0})</h4>
                <div class="verification-hint">
                    <strong>🔍 Verify:</strong> Check that each source confirms the key facts: <em>${event.title}</em>
                </div>
                <div id="sources-${event.id}">
                    ${renderSources(event)}
                </div>
            </div>
            
            <button class="validate-btn ${event.validated ? 'validated' : ''}" onclick="validateEvent('${event.id}', ${!event.validated})">
                ${event.validated ? '✗ Remove Validation' : '✓ Mark as Validated'}
            </button>
        </div>
    `).join('');
}

function renderSources(event) {
    if (!event.sources || event.sources.length === 0) {
        return '<p style="color: #666;">No sources found</p>';
    }
    
    return event.sources.map((source, idx) => {
        const sourceId = `${event.id}_source${idx + 1}`;
        const status = sourceStatuses[sourceId] || {};
        
        let statusClass = '';
        if (status.accessible) statusClass = 'status-good';
        else if (status.archived) statusClass = 'status-archived';
        else if (status.error) statusClass = 'status-error';
        
        return `
            <div class="source-item ${statusClass}" id="source-${sourceId}">
                <div class="source-header">
                    <div class="source-title">${source.title || 'Untitled'}</div>
                    <div class="source-status">
                        ${status.accessible ? '<span class="status-indicator good">✓ Live</span>' : ''}
                        ${status.scraped ? `<a href="/api/scraped/${sourceId}.html" target="_blank" rel="noopener noreferrer" class="status-indicator cached">📁 Cached</a>` : ''}
                        ${status.archived ? `<a href="${status.archive_url || '#'}" target="_blank" rel="noopener noreferrer" class="status-indicator archived">🗄️ Archived</a>` : ''}
                        ${status.error ? '<span class="status-indicator error">⚠️ Error</span>' : ''}
                        ${!status.checked ? '<span class="status-indicator">? Unchecked</span>' : ''}
                    </div>
                </div>
                <div class="source-url">
                    <a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.url}</a>
                </div>
                <div class="source-outlet">Source: ${source.outlet || 'Unknown'} | ${source.date || ''}</div>
                <div class="source-actions">
                    <a href="${source.url}" target="_blank" rel="noopener noreferrer" class="btn btn-view">
                        🔗 View Live
                    </a>
                    ${status.archive_url ? `<a href="${status.archive_url}" target="_blank" rel="noopener noreferrer" class="btn btn-view-archive">
                        📚 View Archive
                    </a>` : ''}
                    <button class="btn btn-check" onclick="checkSource('${sourceId}', '${source.url}')">
                        🔍 Check Status
                    </button>
                    <button class="btn btn-scrape" onclick="scrapeSource('${sourceId}', '${source.url}')"
                        ${status.scraped ? 'disabled' : ''}>
                        💾 Scrape
                    </button>
                    <button class="btn btn-archive" onclick="archiveSource('${sourceId}', '${source.url}')"
                        ${status.archived ? 'disabled' : ''}>
                        🗄️ Archive
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

async function checkSource(sourceId, url) {
    const sourceEl = document.getElementById(`source-${sourceId}`);
    sourceEl.querySelector('.source-status').innerHTML = '<div class="loading"></div> Checking...';
    
    try {
        const response = await fetch('/api/check_source', {
            method: 'POST',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"source_id": sourceId, "url": url})
        });
        const data = await response.json();
        
        sourceStatuses[sourceId] = data;
        sourceStatuses[sourceId].checked = true;
        
        // Re-render this event's sources
        const eventId = sourceId.split('_source')[0];
        const event = events.find(e => e.id === eventId);
        if (event) {
            document.getElementById(`sources-${eventId}`).innerHTML = renderSources(event);
        }
        
        updateStats();
    } catch (error) {
        console.error('Error checking source:', error);
        sourceEl.querySelector('.source-status').innerHTML = 
            '<span class="status-indicator error">Error checking</span>';
    }
}

async function scrapeSource(sourceId, url) {
    const sourceEl = document.getElementById(`source-${sourceId}`);
    sourceEl.querySelector('.source-status').innerHTML = '<div class="loading"></div> Scraping...';
    
    try {
        const response = await fetch('/api/scrape_source', {
            method: 'POST',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"source_id": sourceId, "url": url})
        });
        const data = await response.json();
        
        if (data.success) {
            sourceStatuses[sourceId].scraped = true;
            // Re-render
            const eventId = sourceId.split('_source')[0];
            const event = events.find(e => e.id === eventId);
            if (event) {
                document.getElementById(`sources-${eventId}`).innerHTML = renderSources(event);
            }
            updateStats();
        } else {
            alert('Failed to scrape: ' + data.error);
        }
    } catch (error) {
        console.error('Error scraping source:', error);
        alert('Error scraping source');
    }
}

async function archiveSource(sourceId, url) {
    const sourceEl = document.getElementById(`source-${sourceId}`);
    sourceEl.querySelector('.source-status').innerHTML = '<div class="loading"></div> Archiving...';
    
    try {
        const response = await fetch('/api/archive_source', {
            method: 'POST',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"source_id": sourceId, "url": url})
        });
        const data = await response.json();
        
        if (data.success) {
            sourceStatuses[sourceId].archived = true;
            sourceStatuses[sourceId].archive_url = data.archive_url;
            // Re-render
            const eventId = sourceId.split('_source')[0];
            const event = events.find(e => e.id === eventId);
            if (event) {
                document.getElementById(`sources-${eventId}`).innerHTML = renderSources(event);
            }
            updateStats();
        } else {
            alert('Failed to archive: ' + data.error);
        }
    } catch (error) {
        console.error('Error archiving source:', error);
        alert('Error archiving source');
    }
}

async function validateEvent(eventId, shouldValidate = true) {
    const event = events.find(e => e.id === eventId);
    const action = shouldValidate ? 'validate' : 'remove validation from';
    
    if (!confirm(`${action} event "${event?.title}"?`)) {
        return;
    }
    
    try {
        // First scrape all sources for this event
        const event = events.find(e => e.id === eventId);
        if (event && event.sources) {
            for (let i = 0; i < event.sources.length; i++) {
                const sourceId = `${eventId}_source${i + 1}`;
                const source = event.sources[i];
                
                // Check if not already scraped
                if (!sourceStatuses[sourceId]?.scraped) {
                    await scrapeSource(sourceId, source.url);
                }
            }
        }
        
        // Mark as validated or unvalidated
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                "event_id": eventId,
                "validated": shouldValidate,
                "validated_by": "user",
                "notes": ""
            })
        });
        const data = await response.json();
        
        if (data.success) {
            // Update the event in our local array
            const eventIndex = events.findIndex(e => e.id === eventId);
            if (eventIndex !== -1) {
                events[eventIndex].validated = shouldValidate;
                if (shouldValidate) {
                    events[eventIndex].validated_date = new Date().toISOString();
                }
            }
            // Re-render events
            renderEvents();
            updateStats();
        }
    } catch (error) {
        console.error('Error validating event:', error);
        alert('Error validating event');
    }
}

async function checkAllSources() {
    for (const event of events) {
        if (event.sources) {
            for (let i = 0; i < event.sources.length; i++) {
                const sourceId = `${event.id}_source${i + 1}`;
                if (!sourceStatuses[sourceId]?.checked) {
                    await checkSource(sourceId, event.sources[i].url);
                    // Small delay to avoid overwhelming the server
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }
        }
    }
}

function updateStats() {
    const totalEvents = events.length;
    const validatedEvents = events.filter(e => e.validated).length;
    const validationPercentage = totalEvents > 0 ? Math.round((validatedEvents / totalEvents) * 100) : 0;
    
    let totalSources = 0;
    let checkedSources = 0;
    let cachedSources = 0;
    let archivedSources = 0;
    
    events.forEach(event => {
        if (event.sources) {
            totalSources += event.sources.length;
            event.sources.forEach((source, idx) => {
                const sourceId = `${event.id}_source${idx + 1}`;
                const status = sourceStatuses[sourceId];
                if (status) {
                    if (status.checked) checkedSources++;
                    if (status.scraped) cachedSources++;
                    if (status.archived) archivedSources++;
                }
            });
        }
    });
    
    document.getElementById('total-events').textContent = totalEvents;
    document.getElementById('validated-count').textContent = `${validatedEvents} validated (${validationPercentage}%)`;
    document.getElementById('sources-checked').textContent = `${checkedSources}/${totalSources}`;
    document.getElementById('sources-cached').textContent = cachedSources;
    document.getElementById('sources-archived').textContent = archivedSources;
    
    // Update progress bar
    const progressBar = document.getElementById('validation-progress');
    if (progressBar) {
        progressBar.innerHTML = `
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${validationPercentage}%"></div>
                <span class="progress-text">${validatedEvents}/${totalEvents} Events Validated (${validationPercentage}%)</span>
            </div>
        `;
    }
}

// Load on page load
document.addEventListener('DOMContentLoaded', () => {
    loadEvents();
    
    // Add event listeners for filters
    document.getElementById('status-filter').addEventListener('change', renderEvents);
    document.getElementById('importance-filter').addEventListener('change', renderEvents);
});

// Make functions globally accessible for onclick handlers
window.renderEvents = renderEvents;
window.validateEvent = validateEvent;
window.checkSource = checkSource;
window.scrapeSource = scrapeSource;
window.archiveSource = archiveSource;
window.checkAllSources = checkAllSources;