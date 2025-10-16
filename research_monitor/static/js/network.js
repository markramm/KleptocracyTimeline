// Network visualization functionality
class TimelineNetwork {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.nodes = [];
        this.links = [];
    }

    initialize() {
        this.canvas = document.getElementById('network-canvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.setupCanvas();
        this.loadNetworkData();
    }
    
    setupCanvas() {
        // Set canvas size
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        
        // Setup event listeners
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        
        // Setup controls
        document.getElementById('network-reset')?.addEventListener('click', () => {
            this.resetView();
        });
        
        document.getElementById('min-connections')?.addEventListener('change', (e) => {
            this.filterByConnections(parseInt(e.target.value));
        });
    }
    
    async loadNetworkData() {
        try {
            const minConnections = document.getElementById('min-connections')?.value || 3;
            const data = await window.timelineAPI.getActorNetwork({ 
                min_connections: minConnections 
            });
            
            this.processNetworkData(data);
            this.render();
        } catch (error) {
            console.error('Failed to load network data:', error);
            this.showError('Failed to load network visualization');
        }
    }
    
    processNetworkData(data) {
        // Convert API data to network format
        this.nodes = data.actors?.map((actor, index) => ({
            id: actor.name,
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            radius: Math.min(20, Math.max(5, actor.event_count / 2)),
            color: this.getNodeColor(actor.event_count),
            eventCount: actor.event_count
        })) || [];
        
        this.links = data.connections?.map(conn => ({
            source: conn.actor1,
            target: conn.actor2,
            strength: conn.shared_events
        })) || [];
    }
    
    getNodeColor(eventCount) {
        if (eventCount >= 20) return '#e53e3e'; // Critical
        if (eventCount >= 10) return '#f56500'; // High
        if (eventCount >= 5) return '#38a169';  // Medium
        return '#3182ce'; // Low
    }
    
    render() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw links
        this.ctx.strokeStyle = '#333333';
        this.ctx.lineWidth = 1;
        
        this.links.forEach(link => {
            const sourceNode = this.nodes.find(n => n.id === link.source);
            const targetNode = this.nodes.find(n => n.id === link.target);
            
            if (sourceNode && targetNode) {
                this.ctx.beginPath();
                this.ctx.moveTo(sourceNode.x, sourceNode.y);
                this.ctx.lineTo(targetNode.x, targetNode.y);
                this.ctx.stroke();
            }
        });
        
        // Draw nodes
        this.nodes.forEach(node => {
            this.ctx.fillStyle = node.color;
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
            this.ctx.fill();
            
            // Draw label
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '12px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(
                node.id.length > 15 ? node.id.substring(0, 12) + '...' : node.id, 
                node.x, 
                node.y + node.radius + 15
            );
        });
    }
    
    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Find clicked node
        const clickedNode = this.nodes.find(node => {
            const distance = Math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2);
            return distance <= node.radius;
        });
        
        if (clickedNode) {
            this.showNodeDetails(clickedNode);
        }
    }
    
    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Check if hovering over a node
        const hoveredNode = this.nodes.find(node => {
            const distance = Math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2);
            return distance <= node.radius;
        });
        
        this.canvas.style.cursor = hoveredNode ? 'pointer' : 'default';
    }
    
    showNodeDetails(node) {
        alert(`Actor: ${node.id}\nEvents: ${node.eventCount}`);
    }
    
    resetView() {
        this.loadNetworkData();
    }
    
    filterByConnections(minConnections) {
        this.loadNetworkData();
    }
    
    showError(message) {
        const canvas = this.canvas;
        this.ctx.fillStyle = '#666666';
        this.ctx.font = '16px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    }
}

// Create global instance
window.timelineNetwork = new TimelineNetwork();