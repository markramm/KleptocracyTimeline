// Statistics and analytics functionality
class TimelineStats {
    constructor() {
        this.overviewData = null;
        this.actorData = null;
        this.importanceData = null;
        this.timelineData = null;
    }

    async loadStats() {
        try {
            // Load all statistics in parallel
            const [overview, actors, importance, timeline] = await Promise.all([
                window.timelineAPI.getOverviewStats(),
                window.timelineAPI.getActorStats(),
                window.timelineAPI.getImportanceStats(),
                window.timelineAPI.getTimelineStats()
            ]);

            this.overviewData = overview;
            this.actorData = actors;
            this.importanceData = importance;
            this.timelineData = timeline;

            this.renderStats();
        } catch (error) {
            console.error('Failed to load statistics:', error);
            this.showError();
        }
    }

    renderStats() {
        this.renderOverviewStats();
        this.renderActorStats();
        this.renderImportanceStats();
        this.renderTimelineStats();
    }

    renderOverviewStats() {
        const container = document.getElementById('overview-stats');
        if (!container || !this.overviewData) return;

        container.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Total Events</span>
                <span class="stat-value">${this.formatNumber(this.overviewData.total_events)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Unique Actors</span>
                <span class="stat-value">${this.formatNumber(this.overviewData.unique_actors)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Unique Tags</span>
                <span class="stat-value">${this.formatNumber(this.overviewData.unique_tags)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Date Range</span>
                <span class="stat-value">${this.overviewData.earliest_date} to ${this.overviewData.latest_date}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Average Importance</span>
                <span class="stat-value">${this.overviewData.avg_importance?.toFixed(2) || 'N/A'}</span>
            </div>
            ${this.overviewData.events_by_year ? `
                <div class="stat-item">
                    <span class="stat-label">Most Active Year</span>
                    <span class="stat-value">${this.getMostActiveYear()}</span>
                </div>
            ` : ''}
        `;
    }

    renderActorStats() {
        const container = document.getElementById('actor-stats');
        if (!container || !this.actorData) return;

        if (!this.actorData.top_actors || this.actorData.top_actors.length === 0) {
            container.innerHTML = '<p class="stat-empty">No actor data available</p>';
            return;
        }

        const maxEvents = Math.max(...this.actorData.top_actors.map(a => a.event_count));

        container.innerHTML = `
            <div class="actor-list">
                ${this.actorData.top_actors.slice(0, 10).map(actor => `
                    <div class="actor-item">
                        <div class="actor-name" title="${actor.name}">${this.truncate(actor.name, 30)}</div>
                        <div class="actor-count">${actor.event_count}</div>
                    </div>
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width: ${(actor.event_count / maxEvents) * 100}%"></div>
                    </div>
                `).join('')}
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Actors with 5+ Events</span>
                <span class="stat-value">${this.actorData.filtered_count || 0}</span>
            </div>
        `;
    }

    renderImportanceStats() {
        const container = document.getElementById('importance-stats');
        if (!container || !this.importanceData) return;

        const total = this.importanceData.total_events || 0;
        const critical = this.importanceData.critical_events || 0;
        const high = this.importanceData.high_events || 0;
        const medium = this.importanceData.medium_events || 0;
        const low = this.importanceData.low_events || 0;

        container.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Critical (9-10)</span>
                <span class="stat-value importance-critical">${critical} (${this.getPercentage(critical, total)}%)</span>
            </div>
            <div class="stat-bar">
                <div class="stat-bar-fill" style="width: ${this.getPercentage(critical, total)}%; background-color: var(--critical-color);"></div>
            </div>
            
            <div class="stat-item">
                <span class="stat-label">High (7-8)</span>
                <span class="stat-value importance-high">${high} (${this.getPercentage(high, total)}%)</span>
            </div>
            <div class="stat-bar">
                <div class="stat-bar-fill" style="width: ${this.getPercentage(high, total)}%; background-color: var(--high-color);"></div>
            </div>
            
            <div class="stat-item">
                <span class="stat-label">Medium (5-6)</span>
                <span class="stat-value importance-medium">${medium} (${this.getPercentage(medium, total)}%)</span>
            </div>
            <div class="stat-bar">
                <div class="stat-bar-fill" style="width: ${this.getPercentage(medium, total)}%; background-color: var(--medium-color);"></div>
            </div>
            
            <div class="stat-item">
                <span class="stat-label">Low (1-4)</span>
                <span class="stat-value importance-low">${low} (${this.getPercentage(low, total)}%)</span>
            </div>
            <div class="stat-bar">
                <div class="stat-bar-fill" style="width: ${this.getPercentage(low, total)}%; background-color: var(--low-color);"></div>
            </div>

            <div class="stat-item">
                <span class="stat-label">Average Importance</span>
                <span class="stat-value">${this.importanceData.avg_importance?.toFixed(2) || 'N/A'}</span>
            </div>
        `;
    }

    renderTimelineStats() {
        const container = document.getElementById('timeline-stats');
        if (!container || !this.timelineData) return;

        // Calculate timeline coverage
        const years = this.timelineData.years_covered || [];
        const totalYears = years.length;
        const eventsPerYear = this.timelineData.events_per_year || {};

        container.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Years Covered</span>
                <span class="stat-value">${totalYears}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Date Range</span>
                <span class="stat-value">${this.timelineData.earliest_date} - ${this.timelineData.latest_date}</span>
            </div>
            ${Object.keys(eventsPerYear).length > 0 ? `
                <div class="timeline-coverage">
                    <h5>Events by Year</h5>
                    ${Object.entries(eventsPerYear)
                        .sort(([a], [b]) => b.localeCompare(a))
                        .slice(0, 10)
                        .map(([year, count]) => {
                            const maxCount = Math.max(...Object.values(eventsPerYear));
                            return `
                                <div class="stat-item">
                                    <span class="stat-label">${year}</span>
                                    <span class="stat-value">${count}</span>
                                </div>
                                <div class="stat-bar">
                                    <div class="stat-bar-fill" style="width: ${(count / maxCount) * 100}%"></div>
                                </div>
                            `;
                        }).join('')}
                </div>
            ` : ''}
        `;
    }

    getMostActiveYear() {
        if (!this.overviewData?.events_by_year) return 'N/A';
        
        const yearCounts = this.overviewData.events_by_year;
        const maxYear = Object.keys(yearCounts).reduce((a, b) => 
            yearCounts[a] > yearCounts[b] ? a : b
        );
        
        return `${maxYear} (${yearCounts[maxYear]} events)`;
    }

    formatNumber(num) {
        if (num === undefined || num === null) return 'N/A';
        return num.toLocaleString();
    }

    getPercentage(part, total) {
        if (!total || total === 0) return '0';
        return ((part / total) * 100).toFixed(1);
    }

    truncate(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length - 3) + '...';
    }

    showError() {
        const containers = [
            'overview-stats',
            'actor-stats', 
            'importance-stats',
            'timeline-stats'
        ];

        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = '<p class="stat-error">Failed to load statistics</p>';
            }
        });
    }
}

// Create global instance
window.timelineStats = new TimelineStats();