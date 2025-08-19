import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './NetworkGraph.css';

const NetworkGraph = ({ events }) => {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphLayout, setGraphLayout] = useState('force'); // force, timeline, circular
  const [showLabels, setShowLabels] = useState(false); // Default to false for less clutter
  const [filterType, setFilterType] = useState('important'); // Changed default from 'all' to 'important'
  const [maxNodes, setMaxNodes] = useState(30); // Limit number of nodes displayed
  const [minConnectionStrength, setMinConnectionStrength] = useState(0.5); // Filter weak connections
  const [dateRange, setDateRange] = useState({ months: 6 }); // Show only recent events by default

  useEffect(() => {
    if (!events || events.length === 0) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    const getImpact = (event) => {
      // Use the importance field if available, otherwise calculate
      if (event.importance !== undefined) {
        return event.importance;
      }
      
      // Fallback calculation if importance field is missing
      let impact = 5;
      if (event.tags?.includes('constitutional-crisis')) impact = Math.max(impact, 9);
      if (event.tags?.includes('democracy-threat')) impact = Math.max(impact, 8);
      if (event.tags?.includes('major-scandal')) impact = Math.max(impact, 8);
      if (event.tags?.includes('criminal-investigation')) impact = Math.max(impact, 7);
      if (event.monitoring_status === 'active') impact = Math.max(impact, 7);
      // Recent events get a slight boost
      const eventDate = new Date(event.date);
      const monthsAgo = (new Date() - eventDate) / (1000 * 60 * 60 * 24 * 30);
      if (monthsAgo < 1) impact = Math.min(impact + 1, 10);
      return impact;
    };

    const getEventGroup = (event) => {
      // Group events by primary category
      if (event.tags?.includes('judicial')) return 'judicial';
      if (event.tags?.includes('regulatory')) return 'regulatory';
      if (event.tags?.includes('financial')) return 'financial';
      if (event.tags?.includes('political')) return 'political';
      if (event.tags?.includes('intelligence')) return 'intelligence';
      if (event.tags?.includes('criminal')) return 'criminal';
      return 'other';
    };

    // Filter events by date range
    const filterEventsByDate = (events) => {
      if (!dateRange.months) return events;
      const cutoffDate = new Date();
      cutoffDate.setMonth(cutoffDate.getMonth() - dateRange.months);
      return events.filter(event => new Date(event.date) >= cutoffDate);
    };

    // Build graph data from events
    const buildGraphData = (events, filter) => {
      const nodes = [];
      const links = [];
      const nodeMap = new Map();

      // Filter events by date first
      let filteredEvents = filterEventsByDate(events);

      // Sort events by impact and take only the most important ones
      if (filter === 'important' || filter === 'money') {
        filteredEvents = filteredEvents
          .map(event => ({ ...event, impact: getImpact(event) }))
          .sort((a, b) => b.impact - a.impact)
          .slice(0, maxNodes);
      }

      // Extract unique actors
      const actors = new Set();
      const actorEventCount = new Map();
      
      filteredEvents.forEach(event => {
        // Add event as node
        const eventNode = {
          id: event.id,
          type: 'event',
          label: event.title?.substring(0, 25) + '...',
          fullTitle: event.title,
          date: event.date,
          tags: event.tags || [],
          impact: getImpact(event),
          group: getEventGroup(event)
        };
        nodes.push(eventNode);
        nodeMap.set(event.id, eventNode);

        // Count actor involvement
        if (event.actors) {
          event.actors.forEach(actor => {
            actorEventCount.set(actor, (actorEventCount.get(actor) || 0) + 1);
          });
        }
      });

      // Only add actors that appear in multiple events (reduces clutter)
      const minActorEvents = filter === 'actors' ? 1 : 2;
      filteredEvents.forEach(event => {
        if (event.actors) {
          event.actors.forEach(actor => {
            if (actorEventCount.get(actor) >= minActorEvents && !actors.has(actor)) {
              actors.add(actor);
              const actorNode = {
                id: `actor-${actor}`,
                type: 'actor',
                label: actor.length > 20 ? actor.substring(0, 18) + '...' : actor,
                fullName: actor,
                eventCount: actorEventCount.get(actor),
                group: 'actor'
              };
              nodes.push(actorNode);
              nodeMap.set(actorNode.id, actorNode);
            }
            
            // Create link between actor and event
            if (actors.has(actor)) {
              links.push({
                source: `actor-${actor}`,
                target: event.id,
                type: 'involved',
                strength: 0.8
              });
            }
          });
        }
      });

      // Find only strong temporal connections (events within 3 days)
      filteredEvents.forEach((event, i) => {
        filteredEvents.slice(i + 1).forEach(otherEvent => {
          const daysDiff = Math.abs(
            new Date(event.date) - new Date(otherEvent.date)
          ) / (1000 * 60 * 60 * 24);
          
          if (daysDiff <= 3) {
            const strength = 1 - (daysDiff / 3);
            if (strength >= minConnectionStrength) {
              links.push({
                source: event.id,
                target: otherEvent.id,
                type: 'temporal',
                strength: strength,
                daysDiff: Math.round(daysDiff)
              });
            }
          }
        });
      });

      // Only strong tag-based connections (multiple shared tags)
      filteredEvents.forEach((event, i) => {
        if (event.tags && event.tags.length > 0) {
          filteredEvents.slice(i + 1).forEach(otherEvent => {
            if (otherEvent.tags && otherEvent.tags.length > 0) {
              const sharedTags = event.tags.filter(tag => 
                otherEvent.tags.includes(tag)
              );
              if (sharedTags.length >= 2) { // Only if 2+ shared tags
                const strength = sharedTags.length / Math.min(event.tags.length, otherEvent.tags.length);
                if (strength >= minConnectionStrength) {
                  links.push({
                    source: event.id,
                    target: otherEvent.id,
                    type: 'thematic',
                    strength: strength,
                    tags: sharedTags
                  });
                }
              }
            }
          });
        }
      });

      // Apply additional filters
      if (filter === 'money') {
        const moneyNodes = nodes.filter(node => {
          if (node.type === 'actor') return true;
          return node.tags?.some(tag => 
            ['crypto', 'money-laundering', 'financial', 'corruption', 'fraud'].includes(tag)
          );
        });
        
        const nodeIds = new Set(moneyNodes.map(n => n.id));
        const moneyLinks = links.filter(link => 
          nodeIds.has(link.source) && nodeIds.has(link.target)
        );
        
        return { nodes: moneyNodes, links: moneyLinks };
      }

      if (filter === 'actors') {
        // Show only nodes with actor connections
        const actorNodeIds = new Set(nodes.filter(n => n.type === 'actor').map(n => n.id));
        const connectedEventIds = new Set(
          links
            .filter(l => l.type === 'involved')
            .map(l => [l.source, l.target])
            .flat()
        );
        
        const actorNodes = nodes.filter(n => 
          n.type === 'actor' || connectedEventIds.has(n.id)
        );
        
        const nodeIds = new Set(actorNodes.map(n => n.id));
        const actorLinks = links.filter(link => 
          nodeIds.has(link.source) && nodeIds.has(link.target)
        );
        
        return { nodes: actorNodes, links: actorLinks };
      }

      if (filter === 'events') {
        const eventNodes = nodes.filter(n => n.type === 'event');
        const nodeIds = new Set(eventNodes.map(n => n.id));
        const eventLinks = links.filter(link => 
          link.type !== 'involved' && nodeIds.has(link.source) && nodeIds.has(link.target)
        );
        
        return { nodes: eventNodes, links: eventLinks };
      }

      return { nodes, links };
    };

    const renderForceLayout = (graphData) => {
      const width = svgRef.current.clientWidth || 800;
      const height = 600;

      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      // Show stats
      const statsText = `Showing ${graphData.nodes.length} nodes, ${graphData.links.length} connections`;
      svg.append('text')
        .attr('x', 10)
        .attr('y', 20)
        .attr('font-size', 12)
        .attr('fill', '#666')
        .text(statsText);

      // Create force simulation with better parameters for fewer nodes
      const simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links)
          .id(d => d.id)
          .distance(d => 80 + (40 * (1 - (d.strength || 0))))
        )
        .force('charge', d3.forceManyBody()
          .strength(d => d.type === 'actor' ? -400 : -600)
        )
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => {
          if (d.type === 'actor') return 25;
          return 15 + (d.impact || 1) * 3;
        }))
        .force('x', d3.forceX(width / 2).strength(0.05))
        .force('y', d3.forceY(height / 2).strength(0.05));

      // Create container groups
      const g = svg.append('g');

      // Add zoom behavior
      const zoom = d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });
      
      svg.call(zoom);

      // Color scales
      const colorScale = d3.scaleOrdinal()
        .domain(['judicial', 'regulatory', 'financial', 'political', 'intelligence', 'criminal', 'actor', 'other'])
        .range(['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#c0392b', '#95a5a6', '#7f8c8d']);

      // Draw links with better visibility
      const links = g.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('class', d => `link ${d.type}`)
        .attr('stroke', d => {
          if (d.type === 'temporal') return '#ffd700';
          if (d.type === 'thematic') return '#87ceeb';
          if (d.type === 'involved') return '#ddd';
          return '#999';
        })
        .attr('stroke-opacity', d => {
          if (d.type === 'involved') return 0.3;
          return 0.4 + (d.strength || 0) * 0.3;
        })
        .attr('stroke-width', d => {
          if (d.type === 'involved') return 1;
          return 1.5 + (d.strength || 0) * 2;
        });

      // Add link tooltips
      links.append('title')
        .text(d => {
          if (d.type === 'temporal') return `${d.daysDiff} days apart`;
          if (d.type === 'thematic') return `Shared: ${d.tags?.join(', ') || ''}`;
          if (d.type === 'involved') return 'Actor involved';
          return '';
        });

      // Draw nodes with better sizing
      const nodes = g.append('g')
        .selectAll('circle')
        .data(graphData.nodes)
        .enter().append('circle')
        .attr('class', d => `node ${d.type}`)
        .attr('r', d => {
          if (d.type === 'actor') return 8 + Math.min(d.eventCount || 1, 5) * 2;
          return 10 + Math.min(d.impact || 1, 8) * 2;
        })
        .attr('fill', d => colorScale(d.group))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
          event.stopPropagation();
          setSelectedNode(d);
          highlightConnections(d);
        })
        .on('mouseover', function(event, d) {
          // Show tooltip on hover
          const tooltip = d3.select('body').append('div')
            .attr('class', 'node-tooltip')
            .style('position', 'absolute')
            .style('padding', '10px')
            .style('background', 'rgba(0,0,0,0.8)')
            .style('color', 'white')
            .style('border-radius', '4px')
            .style('pointer-events', 'none')
            .style('font-size', '12px')
            .style('max-width', '300px')
            .html(() => {
              if (d.type === 'actor') {
                return `<strong>${d.fullName || d.label}</strong><br/>Events: ${d.eventCount || 0}`;
              }
              return `<strong>${d.fullTitle || d.label}</strong><br/>
                      Date: ${d.date}<br/>
                      Impact: ${d.impact}/10<br/>
                      ${d.tags?.length ? `Tags: ${d.tags.slice(0,3).join(', ')}` : ''}`;
            });
          
          tooltip.style('left', (event.pageX + 10) + 'px')
                 .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
          d3.selectAll('.node-tooltip').remove();
        })
        .call(d3.drag()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded));

      // Add labels only for important nodes or when enabled
      let labels = null;
      if (showLabels) {
        labels = g.append('g')
          .selectAll('text')
          .data(graphData.nodes.filter(d => 
            d.type === 'actor' || d.impact >= 5
          ))
          .enter().append('text')
          .text(d => d.label)
          .attr('font-size', 10)
          .attr('dx', 15)
          .attr('dy', 4)
          .style('pointer-events', 'none')
          .style('user-select', 'none');
      }

      simulation.on('tick', () => {
        links
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodes
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);

        if (labels) {
          labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
        }
      });

      // Drag functions
      function dragStarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragEnded(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }

      function highlightConnections(node) {
        // Fade out non-connected nodes and links
        const connectedNodes = new Set([node.id]);
        
        links.style('opacity', function(link) {
          if (link.source.id === node.id || link.target.id === node.id) {
            connectedNodes.add(link.source.id);
            connectedNodes.add(link.target.id);
            return 1;
          }
          return 0.1;
        });

        nodes.style('opacity', n => 
          connectedNodes.has(n.id) ? 1 : 0.2
        );
      }

      // Click on background to reset highlighting
      svg.on('click', function(event) {
        if (event.target === this) {
          links.style('opacity', d => {
            if (d.type === 'involved') return 0.3;
            return 0.4 + (d.strength || 0) * 0.3;
          });
          nodes.style('opacity', 1);
          setSelectedNode(null);
        }
      });
    };

    const renderTimelineLayout = (graphData) => {
      // Timeline layout: arrange nodes by date horizontally
      console.log('Timeline layout not yet implemented');
      renderForceLayout(graphData); // Fallback to force layout
    };

    const renderCircularLayout = (graphData) => {
      // Circular layout: arrange actors in circle, events in center
      console.log('Circular layout not yet implemented');
      renderForceLayout(graphData); // Fallback to force layout
    };

    // Build and render graph
    const graphData = buildGraphData(events, filterType);
    
    // Render based on layout type
    switch (graphLayout) {
      case 'timeline':
        renderTimelineLayout(graphData);
        break;
      case 'circular':
        renderCircularLayout(graphData);
        break;
      default:
        renderForceLayout(graphData);
    }
  }, [events, graphLayout, filterType, showLabels, maxNodes, minConnectionStrength, dateRange]);

  return (
    <div className="network-graph-container">
      <div className="graph-controls">
        <div className="control-group">
          <label>View:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="important">Most Important</option>
            <option value="actors">Actor Network</option>
            <option value="events">Event Connections</option>
            <option value="money">Financial Network</option>
            <option value="all">All Connections</option>
          </select>
        </div>
        
        <div className="control-group">
          <label>Time Range:</label>
          <select value={dateRange.months} onChange={(e) => setDateRange({ months: parseInt(e.target.value) })}>
            <option value="1">Last Month</option>
            <option value="3">Last 3 Months</option>
            <option value="6">Last 6 Months</option>
            <option value="12">Last Year</option>
            <option value="24">Last 2 Years</option>
            <option value="">All Time</option>
          </select>
        </div>

        <div className="control-group">
          <label>Max Nodes:</label>
          <select value={maxNodes} onChange={(e) => setMaxNodes(parseInt(e.target.value))}>
            <option value="20">20 nodes</option>
            <option value="30">30 nodes</option>
            <option value="50">50 nodes</option>
            <option value="75">75 nodes</option>
            <option value="100">100 nodes</option>
          </select>
        </div>

        <div className="control-group">
          <label>Min Connection:</label>
          <select value={minConnectionStrength} onChange={(e) => setMinConnectionStrength(parseFloat(e.target.value))}>
            <option value="0">All</option>
            <option value="0.3">Weak+</option>
            <option value="0.5">Medium+</option>
            <option value="0.7">Strong</option>
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
          <h3>{selectedNode.fullTitle || selectedNode.fullName || selectedNode.label}</h3>
          <p><strong>Type:</strong> {selectedNode.type}</p>
          {selectedNode.date && <p><strong>Date:</strong> {selectedNode.date}</p>}
          {selectedNode.impact && <p><strong>Impact Score:</strong> {selectedNode.impact}/10</p>}
          {selectedNode.eventCount && <p><strong>Connected Events:</strong> {selectedNode.eventCount}</p>}
          {selectedNode.tags && selectedNode.tags.length > 0 && (
            <p><strong>Tags:</strong> {selectedNode.tags.join(', ')}</p>
          )}
          <button onClick={() => setSelectedNode(null)}>Close</button>
        </div>
      )}

      <div className="graph-legend">
        <h4>Legend</h4>
        <div className="legend-item">
          <span className="legend-color judicial"></span> Judicial
        </div>
        <div className="legend-item">
          <span className="legend-color regulatory"></span> Regulatory
        </div>
        <div className="legend-item">
          <span className="legend-color financial"></span> Financial
        </div>
        <div className="legend-item">
          <span className="legend-color political"></span> Political
        </div>
        <div className="legend-item">
          <span className="legend-color criminal" style={{background: '#c0392b'}}></span> Criminal
        </div>
        <div className="legend-item">
          <span className="legend-color actor"></span> Actor
        </div>
        <div className="legend-section" style={{marginTop: '10px', borderTop: '1px solid #ddd', paddingTop: '10px'}}>
          <div className="legend-item">
            <span style={{display: 'inline-block', width: '30px', height: '2px', background: '#ffd700'}}></span> Temporal
          </div>
          <div className="legend-item">
            <span style={{display: 'inline-block', width: '30px', height: '2px', background: '#87ceeb'}}></span> Thematic
          </div>
          <div className="legend-item">
            <span style={{display: 'inline-block', width: '30px', height: '2px', background: '#ddd'}}></span> Actor Link
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkGraph;