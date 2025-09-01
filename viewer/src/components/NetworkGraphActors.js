import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import './NetworkGraph.css';

const NetworkGraphActors = ({ events }) => {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [minEvents, setMinEvents] = useState(3);
  const [showLabels, setShowLabels] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!events || events.length === 0) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    // Process events to extract actor relationships
    const processActorNetwork = () => {
      const actorEventMap = new Map(); // actor -> events they're in
      const actorConnections = new Map(); // "actor1-actor2" -> shared event count
      
      // Build actor-event mapping
      events.forEach(event => {
        if (event.actors && event.actors.length > 0) {
          event.actors.forEach(actor => {
            if (!actorEventMap.has(actor)) {
              actorEventMap.set(actor, []);
            }
            actorEventMap.get(actor).push(event);
          });

          // Track connections between actors in same event
          if (event.actors.length > 1) {
            for (let i = 0; i < event.actors.length - 1; i++) {
              for (let j = i + 1; j < event.actors.length; j++) {
                const key = [event.actors[i], event.actors[j]].sort().join('|||');
                actorConnections.set(key, (actorConnections.get(key) || 0) + 1);
              }
            }
          }
        }
      });

      // Filter actors by minimum event count
      const significantActors = Array.from(actorEventMap.entries())
        .filter(([actor, events]) => events.length >= minEvents)
        .sort((a, b) => b[1].length - a[1].length);

      // Create nodes
      const nodes = significantActors.map(([actor, actorEvents]) => ({
        id: actor,
        label: actor,
        eventCount: actorEvents.length,
        events: actorEvents,
        // Special handling for Trump to ensure he's recognized
        isTrump: actor === 'Donald Trump' || 
                 actor === 'Trump Administration' ||
                 actor.includes('Trump')
      }));

      // Create links between actors who appear in same events
      const links = [];
      const actorSet = new Set(significantActors.map(([actor]) => actor));
      
      actorConnections.forEach((count, key) => {
        const [source, target] = key.split('|||');
        if (actorSet.has(source) && actorSet.has(target)) {
          links.push({
            source,
            target,
            value: count,
            sharedEvents: count
          });
        }
      });

      return { nodes, links };
    };

    const { nodes, links } = processActorNetwork();

    if (nodes.length === 0) return;

    // Setup dimensions
    const width = svgRef.current.clientWidth || 1200;
    const height = 800;

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Add title/stats
    svg.append('text')
      .attr('x', 10)
      .attr('y', 20)
      .attr('font-size', 14)
      .attr('fill', '#666')
      .text(`Actor Network: ${nodes.length} actors, ${links.length} connections (min ${minEvents} events)`);

    // Create main container with zoom
    const g = svg.append('g');

    const zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    
    svg.call(zoom);

    // Find Trump node and set initial position
    const trumpNode = nodes.find(n => n.isTrump && n.id === 'Donald Trump') || 
                     nodes.find(n => n.isTrump);
    
    if (trumpNode) {
      trumpNode.fx = width / 2;
      trumpNode.fy = height / 2;
      trumpNode.fixed = true;
    }

    // Color scale for node importance
    const colorScale = d3.scaleSequential(d3.interpolateReds)
      .domain([0, d3.max(nodes, d => d.eventCount)]);

    // Size scale for nodes (based on event count)
    const sizeScale = d3.scaleSqrt()
      .domain([d3.min(nodes, d => d.eventCount), d3.max(nodes, d => d.eventCount)])
      .range([5, 40]);

    // Thickness scale for links
    const linkScale = d3.scaleLinear()
      .domain([1, d3.max(links, d => d.value)])
      .range([1, 10]);

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links)
        .id(d => d.id)
        .distance(d => {
          // Shorter distance for stronger connections
          return 100 - (d.value * 5);
        })
        .strength(d => d.value / 10)
      )
      .force('charge', d3.forceManyBody()
        .strength(d => {
          // Trump attracts other nodes
          if (d.isTrump) return -1000;
          // Other nodes repel based on their importance
          return -100 - (d.eventCount * 10);
        })
      )
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.05))
      .force('collision', d3.forceCollide()
        .radius(d => sizeScale(d.eventCount) + 5)
      );

    // Draw links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', d => 0.2 + (d.value / 20))
      .attr('stroke-width', d => linkScale(d.value));

    // Add link hover effects
    link.append('title')
      .text(d => `${d.source.id || d.source} ↔ ${d.target.id || d.target}: ${d.sharedEvents} shared events`);

    // Draw nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(nodes)
      .enter().append('circle')
      .attr('r', d => sizeScale(d.eventCount))
      .attr('fill', d => {
        if (d.isTrump) return '#ff6b6b';
        if (d.eventCount > 50) return '#e74c3c';
        if (d.eventCount > 20) return '#f39c12';
        if (d.eventCount > 10) return '#3498db';
        return '#95a5a6';
      })
      .attr('stroke', d => {
        if (searchQuery && d.label.toLowerCase().includes(searchQuery.toLowerCase())) {
          return '#ffff00';
        }
        return '#fff';
      })
      .attr('stroke-width', d => {
        if (searchQuery && d.label.toLowerCase().includes(searchQuery.toLowerCase())) {
          return 4;
        }
        return 2;
      })
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
        highlightConnections(d);
      })
      .on('mouseover', (event, d) => {
        setHoveredNode(d);
        // Create tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'actor-tooltip')
          .style('position', 'absolute')
          .style('padding', '10px')
          .style('background', 'rgba(0,0,0,0.9)')
          .style('color', 'white')
          .style('border-radius', '4px')
          .style('pointer-events', 'none')
          .style('font-size', '12px')
          .style('z-index', 1000)
          .html(`
            <strong>${d.label}</strong><br/>
            Events: ${d.eventCount}<br/>
            Connections: ${links.filter(l => 
              l.source.id === d.id || l.target.id === d.id
            ).length} actors
          `);
        
        tooltip.style('left', (event.pageX + 10) + 'px')
               .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', () => {
        setHoveredNode(null);
        d3.selectAll('.actor-tooltip').remove();
      })
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add labels
    const labels = g.append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(nodes)
      .enter().append('text')
      .text(d => {
        // Always show Trump label
        if (d.isTrump) return d.label;
        // Show labels for important actors or when enabled
        if (showLabels && d.eventCount > 10) {
          return d.label.length > 20 ? d.label.substring(0, 18) + '...' : d.label;
        }
        return '';
      })
      .attr('font-size', d => {
        if (d.isTrump) return 16;
        if (d.eventCount > 50) return 12;
        if (d.eventCount > 20) return 10;
        return 9;
      })
      .attr('font-weight', d => d.isTrump ? 'bold' : 'normal')
      .attr('text-anchor', 'middle')
      .attr('dy', d => sizeScale(d.eventCount) + 15)
      .style('pointer-events', 'none')
      .style('user-select', 'none');

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      labels
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });

    // Drag functions
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      // Keep Trump fixed if it's Trump
      if (!event.subject.isTrump) {
        event.subject.fx = null;
        event.subject.fy = null;
      }
    }

    function highlightConnections(selectedNode) {
      const connectedNodes = new Set([selectedNode.id]);
      
      // Find all connected nodes
      links.forEach(l => {
        if (l.source.id === selectedNode.id) {
          connectedNodes.add(l.target.id);
        } else if (l.target.id === selectedNode.id) {
          connectedNodes.add(l.source.id);
        }
      });

      // Fade non-connected elements
      node.style('opacity', n => connectedNodes.has(n.id) ? 1 : 0.2);
      labels.style('opacity', n => connectedNodes.has(n.id) ? 1 : 0.2);
      
      link.style('opacity', l => 
        (l.source.id === selectedNode.id || l.target.id === selectedNode.id) ? 0.8 : 0.05
      );
    }

    // Click on background to reset
    svg.on('click', function(event) {
      if (event.target === this || event.target.tagName === 'rect') {
        node.style('opacity', 1);
        labels.style('opacity', 1);
        link.style('opacity', d => 0.2 + (d.value / 20));
        setSelectedNode(null);
      }
    });

  }, [events, minEvents, showLabels, searchQuery]);

  // Get top actors for stats
  const topActors = useMemo(() => {
    if (!events) return [];
    
    const actorCounts = new Map();
    events.forEach(event => {
      if (event.actors) {
        event.actors.forEach(actor => {
          actorCounts.set(actor, (actorCounts.get(actor) || 0) + 1);
        });
      }
    });
    
    return Array.from(actorCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
  }, [events]);

  return (
    <div className="network-graph-container">
      <div className="graph-controls">
        <div className="control-group">
          <input
            type="text"
            placeholder="Search actors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            style={{
              padding: '6px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              width: '200px'
            }}
          />
        </div>

        <div className="control-group">
          <label>Min Events:</label>
          <select value={minEvents} onChange={(e) => setMinEvents(parseInt(e.target.value))}>
            <option value="1">1+ events</option>
            <option value="2">2+ events</option>
            <option value="3">3+ events</option>
            <option value="5">5+ events</option>
            <option value="10">10+ events</option>
            <option value="20">20+ events</option>
          </select>
        </div>

        <div className="control-group">
          <label>
            <input 
              type="checkbox" 
              checked={showLabels}
              onChange={(e) => setShowLabels(e.target.checked)}
            />
            Show Labels
          </label>
        </div>
      </div>

      <svg ref={svgRef} className="network-graph"></svg>

      {selectedNode && (
        <div className="node-details">
          <h3>{selectedNode.label}</h3>
          <p><strong>Events:</strong> {selectedNode.eventCount}</p>
          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            <p><strong>Recent Events:</strong></p>
            <ul style={{ fontSize: '12px' }}>
              {selectedNode.events.slice(0, 5).map((event, i) => (
                <li key={i}>
                  {event.date}: {event.title?.substring(0, 50)}...
                </li>
              ))}
            </ul>
          </div>
          <button onClick={() => setSelectedNode(null)}>Close</button>
        </div>
      )}

      <div className="graph-legend">
        <h4>Top Actors</h4>
        {topActors.map(([actor, count]) => (
          <div key={actor} className="legend-item" style={{ fontSize: '11px' }}>
            <span style={{
              display: 'inline-block',
              width: Math.min(count/5, 20) + 'px',
              height: '10px',
              background: count > 100 ? '#e74c3c' : count > 50 ? '#f39c12' : '#3498db',
              marginRight: '5px'
            }}></span>
            {actor}: {count}
          </div>
        ))}
      </div>
    </div>
  );
};

export default NetworkGraphActors;