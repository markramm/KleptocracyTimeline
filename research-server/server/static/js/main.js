// Main Application Controller
class TimelineApp {
    constructor() {
        this.currentView = 'timeline';
        this.currentPage = 1;
        this.pageSize = 20;
        this.currentFilters = {};
        this.currentSearch = '';
        
        this.initializeApp();
    }

    async initializeApp() {
        try {
            // Show loading screen
            this.showLoading(true);
            
            // Initialize event listeners
            this.setupEventListeners();
            
            // Initialize filter options
            await this.loadFilterOptions();
            
            // Load initial data
            await this.loadTimelineData();
            
            // Hide loading screen
            this.showLoading(false);
            
        } catch (error) {
            console.error('App initialization failed:', error);
            this.showError('Failed to load application. Please refresh the page.');
        }
    }

    setupEventListeners() {
        // Navigation
        document.getElementById('view-timeline').addEventListener('click', () => {
            this.switchView('timeline');
        });
        
        document.getElementById('view-network').addEventListener('click', () => {
            this.switchView('network');
        });
        
        document.getElementById('view-stats').addEventListener('click', () => {
            this.switchView('stats');
        });

        // Search
        document.getElementById('search-btn').addEventListener('click', () => {
            this.handleSearch();
        });
        
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });

        // Filters
        document.getElementById('importance-filter').addEventListener('change', () => {
            this.handleFilterChange();
        });
        
        document.getElementById('year-filter').addEventListener('change', () => {
            this.handleFilterChange();
        });
        
        document.getElementById('actor-filter').addEventListener('change', () => {
            this.handleFilterChange();
        });
        
        document.getElementById('tag-filter').addEventListener('change', () => {
            this.handleFilterChange();
        });

        // Pagination
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadTimelineData();
            }
        });
        
        document.getElementById('next-page').addEventListener('click', () => {
            this.currentPage++;
            this.loadTimelineData();
        });

        // Modal
        document.getElementById('event-modal').addEventListener('click', (e) => {
            if (e.target.id === 'event-modal' || e.target.classList.contains('modal-close')) {
                this.closeModal();
            }
        });
    }

    async loadFilterOptions() {
        try {
            // Load years from date range
            const dateRange = await window.timelineAPI.getDateRange();
            this.populateYearFilter(dateRange);
            
            // Load actors
            const actors = await window.timelineAPI.getActors();
            this.populateActorFilter(actors.actors);
            
            // Load tags
            const tags = await window.timelineAPI.getTags();
            this.populateTagFilter(tags.tags);
            
        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    }

    populateYearFilter(dateRange) {
        const yearFilter = document.getElementById('year-filter');
        const startYear = parseInt(dateRange.earliest_date.substring(0, 4));
        const endYear = parseInt(dateRange.latest_date.substring(0, 4));
        
        for (let year = endYear; year >= startYear; year--) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearFilter.appendChild(option);
        }
    }

    populateActorFilter(actors) {
        const actorFilter = document.getElementById('actor-filter');
        actors.slice(0, 100).forEach(actor => {  // Limit to top 100
            const option = document.createElement('option');
            option.value = actor;
            option.textContent = actor.length > 50 ? actor.substring(0, 47) + '...' : actor;
            actorFilter.appendChild(option);
        });
    }

    populateTagFilter(tags) {
        const tagFilter = document.getElementById('tag-filter');
        tags.slice(0, 100).forEach(tag => {  // Limit to top 100
            const option = document.createElement('option');
            option.value = tag;
            option.textContent = tag;
            tagFilter.appendChild(option);
        });
    }

    switchView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`view-${viewName}`).classList.add('active');
        
        // Update view containers
        document.querySelectorAll('.view-container').forEach(container => {
            container.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');
        
        this.currentView = viewName;
        
        // Load view-specific data
        switch (viewName) {
            case 'timeline':
                // Timeline data is already loaded
                break;
            case 'network':
                if (window.timelineNetwork) {
                    window.timelineNetwork.initialize();
                }
                break;
            case 'stats':
                if (window.timelineStats) {
                    window.timelineStats.loadStats();
                }
                break;
        }
    }

    async handleSearch() {
        const searchInput = document.getElementById('search-input');
        this.currentSearch = searchInput.value.trim();
        this.currentPage = 1;  // Reset to first page
        await this.loadTimelineData();
    }

    async handleFilterChange() {
        this.currentFilters = {
            importance: document.getElementById('importance-filter').value,
            year: document.getElementById('year-filter').value,
            actor: document.getElementById('actor-filter').value,
            tag: document.getElementById('tag-filter').value
        };
        
        // Remove empty filters
        Object.keys(this.currentFilters).forEach(key => {
            if (!this.currentFilters[key]) {
                delete this.currentFilters[key];
            }
        });
        
        this.currentPage = 1;  // Reset to first page
        await this.loadTimelineData();
    }

    async loadTimelineData() {
        try {
            this.showTimelineLoading(true);
            
            let data;
            if (this.currentSearch) {
                // Search with filters
                data = await window.timelineAPI.searchEvents(this.currentSearch, {
                    ...this.currentFilters,
                    page: this.currentPage,
                    per_page: this.pageSize
                });
            } else if (Object.keys(this.currentFilters).length > 0) {
                // Filter only
                data = await window.timelineAPI.filterEvents({
                    ...this.currentFilters,
                    page: this.currentPage,
                    per_page: this.pageSize
                });
            } else {
                // Standard pagination
                data = await window.timelineAPI.getEvents({
                    page: this.currentPage,
                    per_page: this.pageSize
                });
            }
            
            this.renderTimeline(data);
            this.updatePagination(data);
            this.updateResultsCount(data);
            
        } catch (error) {
            console.error('Failed to load timeline data:', error);
            this.showError('Failed to load timeline data. Please try again.');
        } finally {
            this.showTimelineLoading(false);
        }
    }

    renderTimeline(data) {
        const container = document.getElementById('timeline-container');
        
        if (!data.events || data.events.length === 0) {
            container.innerHTML = `
                <div class="timeline-empty">
                    <i class="fas fa-search"></i>
                    <h3>No events found</h3>
                    <p>Try adjusting your search terms or filters</p>
                </div>
            `;
            return;
        }

        container.innerHTML = data.events.map(event => this.renderEvent(event)).join('');
        
        // Add click handlers for events
        container.querySelectorAll('.timeline-event').forEach((element, index) => {
            element.addEventListener('click', () => {
                this.showEventDetail(data.events[index]);
            });
        });
    }

    renderEvent(event) {
        const formattedDate = window.timelineAPI.formatDate(event.date);
        const importanceClass = `importance-${event.importance}`;
        
        return `
            <div class="timeline-event" data-event-id="${event.id}">
                <div class="event-header">
                    <div class="event-date">${formattedDate}</div>
                    <div class="event-importance ${importanceClass}">${event.importance}</div>
                </div>
                
                <div class="event-title">${event.title}</div>
                
                <div class="event-summary">${event.summary}</div>
                
                <div class="event-meta">
                    ${event.actors && event.actors.length > 0 ? `
                        <div class="event-actors">
                            <i class="fas fa-users"></i>
                            ${event.actors.slice(0, 3).map(actor => 
                                `<span class="actor-tag">${actor}</span>`
                            ).join('')}
                            ${event.actors.length > 3 ? `<span class="actor-tag">+${event.actors.length - 3}</span>` : ''}
                        </div>
                    ` : ''}
                    
                    ${event.tags && event.tags.length > 0 ? `
                        <div class="event-tags">
                            <i class="fas fa-tags"></i>
                            ${event.tags.slice(0, 3).map(tag => 
                                `<span class="event-tag">${tag}</span>`
                            ).join('')}
                            ${event.tags.length > 3 ? `<span class="event-tag">+${event.tags.length - 3}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    showEventDetail(event) {
        const modal = document.getElementById('event-modal');
        const details = document.getElementById('event-details');
        
        const formattedDate = window.timelineAPI.formatDate(event.date);
        const importanceClass = `importance-${event.importance}`;
        
        details.innerHTML = `
            <div class="event-detail">
                <div class="event-detail-header">
                    <div class="event-detail-title">${event.title}</div>
                    <div class="event-detail-meta">
                        <div class="event-detail-item">
                            <i class="fas fa-calendar"></i>
                            <span>${formattedDate}</span>
                        </div>
                        <div class="event-detail-item">
                            <i class="fas fa-star"></i>
                            <span class="${importanceClass}">Importance: ${event.importance}/10</span>
                        </div>
                        ${event.status ? `
                            <div class="event-detail-item">
                                <i class="fas fa-info-circle"></i>
                                <span class="status-${event.status}">${event.status}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="event-detail-summary">${event.summary}</div>
                
                ${event.actors && event.actors.length > 0 ? `
                    <div class="event-detail-actors">
                        <h4><i class="fas fa-users"></i> Actors</h4>
                        <div class="actors-list">
                            ${event.actors.map(actor => `<span class="actor-tag">${actor}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${event.tags && event.tags.length > 0 ? `
                    <div class="event-detail-tags">
                        <h4><i class="fas fa-tags"></i> Tags</h4>
                        <div class="tags-list">
                            ${event.tags.map(tag => `<span class="event-tag">${tag}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${event.sources && event.sources.length > 0 ? `
                    <div class="event-detail-sources">
                        <h4><i class="fas fa-link"></i> Sources</h4>
                        <ul class="sources-list">
                            ${event.sources.map(source => `
                                <li>
                                    <a href="${source.url || '#'}" target="_blank" rel="noopener">
                                        ${source.title || 'Source'}
                                    </a>
                                    ${source.outlet ? `<span class="source-outlet"> - ${source.outlet}</span>` : ''}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        modal.style.display = 'block';
    }

    closeModal() {
        document.getElementById('event-modal').style.display = 'none';
    }

    updatePagination(data) {
        const pageInfo = document.getElementById('page-info');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        const totalPages = Math.ceil(data.total / this.pageSize);
        pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        
        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= totalPages;
    }

    updateResultsCount(data) {
        const resultsCount = document.getElementById('results-count');
        resultsCount.textContent = `${data.total} events found`;
    }

    showLoading(show) {
        const loadingScreen = document.getElementById('loading-screen');
        loadingScreen.style.display = show ? 'flex' : 'none';
    }

    showTimelineLoading(show) {
        const container = document.getElementById('timeline-container');
        if (show) {
            container.innerHTML = `
                <div class="timeline-loading">
                    <i class="fas fa-cog fa-spin"></i>
                    <p>Loading events...</p>
                </div>
            `;
        }
    }

    showError(message) {
        // Simple error display - could be enhanced with a proper notification system
        console.error(message);
        alert(message);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.timelineApp = new TimelineApp();
});