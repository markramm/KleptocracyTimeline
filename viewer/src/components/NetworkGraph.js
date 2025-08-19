import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './NetworkGraph.css';

const NetworkGraph = ({ events }) => {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphLayout, setGraphLayout] = useState('force'); // force, timeline, circular
  const [showLabels, setShowLabels] = useState(true);
  const [filterType, setFilterType] = useState('all'); // all, actors, events, money

  useEffect(() => {
    if (!events || events.length === 0) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    const calculateImpact = (event) => {
      // Simple impact calculation based on tags and sources
      let impact = 1;
      if (event.tags?.includes('constitutional-crisis')) impact += 3;
      if (event.tags?.includes('democracy-threat')) impact += 2;
      if (event.sources?.length > 3) impact += 1;
      if (event.monitoring_status === 'active') impact += 2;
      return Math.min(impact, 5); // Cap at 5
    };

    const getEventGroup = (event) => {
      // Group events by primary category
      if (event.tags?.includes('judicial')) return 'judicial';
      if (event.tags?.includes('regulatory')) return 'regulatory';
      if (event.tags?.includes('financial')) return 'financial';
      if (event.tags?.includes('political')) return 'political';
      if (event.tags?.includes('intelligence')) return 'intelligence';
      return 'other';
    };

    // Build graph data from events
    const buildGraphData = (events, filter) => {
      const nodes = [];
      const links = [];
      const nodeMap = new Map();

      // Extract unique actors
      const actors = new Set();
      
      events.forEach(event => {
        // Add event as node
        const eventNode = {
          id: event.id,
          type: 'event',
          label: event.title?.substring(0, 30) + '...',
          fullTitle: event.title,
          date: event.date,
          tags: event.tags || [],
          impact: calculateImpact(event),
          group: getEventGroup(event)
        };
        nodes.push(eventNode);
        nodeMap.set(event.id, eventNode);

        // Add actors as nodes
        if (event.actors) {
          event.actors.forEach(actor => {
            if (!actors.has(actor)) {
              actors.add(actor);
              const actorNode = {
                id: `actor-${actor}`,
                type: 'actor',
                label: actor,
                events: [],
                group: 'actor'
              };
              nodes.push(actorNode);
              nodeMap.set(actorNode.id, actorNode);
            }
            
            // Create link between actor and event
            links.push({
              source: `actor-${actor}`,
              target: event.id,
              type: 'involved',
              strength: 1
            });
          });
        }

        // Find temporal connections (events within 7 days)
        events.forEach(otherEvent => {
          if (event.id !== otherEvent.id) {
            const daysDiff = Math.abs(
              new Date(event.date) - new Date(otherEvent.date)
            ) / (1000 * 60 * 60 * 24);
            
            if (daysDiff <= 7) {
              links.push({
                source: event.id,
                target: otherEvent.id,
                type: 'temporal',
                strength: 1 - (daysDiff / 7) // Stronger if closer in time
              });
            }
          }
        });

        // Tag-based connections
        if (event.tags) {
          events.forEach(otherEvent => {
            if (event.id !== otherEvent.id && otherEvent.tags) {
              const sharedTags = event.tags.filter(tag => 
                otherEvent.tags.includes(tag)
              );
              if (sharedTags.length > 0) {
                links.push({
                  source: event.id,
                  target: otherEvent.id,
                  type: 'thematic',
                  strength: sharedTags.length / Math.max(event.tags.length, otherEvent.tags.length),
                  tags: sharedTags
                });
              }
            }
          });
        }
      });

      // Apply filters
      if (filter !== 'all') {
        const filteredNodes = nodes.filter(node => {
          if (filter === 'actors') return node.type === 'actor';
          if (filter === 'events') return node.type === 'event';
          if (filter === 'money') {
            return node.tags?.some(tag => 
              ['crypto', 'money-laundering', 'financial', 'corruption'].includes(tag)
            );
          }
          return true;
        });
        
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredLinks = links.filter(link => 
          nodeIds.has(link.source) && nodeIds.has(link.target)
        );
        
        return { nodes: filteredNodes, links: filteredLinks };
      }

      return { nodes, links };
    };

    const renderForceLayout = (graphData) => {
      const width = svgRef.current.clientWidth || 800;
      const height = 600;

      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      // Create force simulation
      const simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links)
          .id(d => d.id)
          .distance(d => 100 * (1 - (d.strength || 0)))
        )
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => 
          d.type === 'event' ? 20 + (d.impact || 1) * 5 : 30
        ));

      // Create container groups
      const g = svg.append('g');

      // Add zoom behavior
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });
      
      svg.call(zoom);

      // Color scales
      const colorScale = d3.scaleOrdinal()
        .domain(['judicial', 'regulatory', 'financial', 'political', 'intelligence', 'actor', 'other'])
        .range(['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#95a5a6', '#34495e']);

      // Draw links
      const links = g.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('class', d => `link ${d.type}`)
        .attr('stroke', d => {
          if (d.type === 'temporal') return '#ffd700';
          if (d.type === 'thematic') return '#87ceeb';
          return '#999';
        })
        .attr('stroke-opacity', d => 0.3 + (d.strength || 0) * 0.4)
        .attr('stroke-width', d => 1 + (d.strength || 0) * 2);

      // Draw nodes
      const nodes = g.append('g')
        .selectAll('circle')
        .data(graphData.nodes)
        .enter().append('circle')
        .attr('class', d => `node ${d.type}`)
        .attr('r', d => {
          if (d.type === 'event') return 8 + (d.impact || 1) * 3;
          return 12;
        })
        .attr('fill', d => colorScale(d.group))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .on('click', (event, d) => {
          setSelectedNode(d);
          highlightConnections(d);
        })
        .call(d3.drag()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded));

      // Add labels if enabled
      let labels = null;
      if (showLabels) {
        labels = g.append('g')
          .selectAll('text')
          .data(graphData.nodes)
          .enter().append('text')
          .text(d => d.label)
          .attr('font-size', 10)
          .attr('dx', 15)
          .attr('dy', 4)
          .style('pointer-events', 'none');
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
        
        links.style('opacity', link => {
          if (link.source.id === node.id || link.target.id === node.id) {
            connectedNodes.add(link.source.id);
            connectedNodes.add(link.target.id);
            return 1;
          }
          return 0.1;
        });

        nodes.style('opacity', n => 
          connectedNodes.has(n.id) ? 1 : 0.1
        );
      }
    };

    const renderTimelineLayout = (graphData) => {
      // Timeline layout: arrange nodes by date horizontally
      // Implementation would go here
      console.log('Timeline layout not yet implemented');
      renderForceLayout(graphData); // Fallback to force layout
    };

    const renderCircularLayout = (graphData) => {
      // Circular layout: arrange actors in circle, events in center
      // Implementation would go here
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
  }, [events, graphLayout, filterType, showLabels]);

  return (
    <div className="network-graph-container">
      <div className="graph-controls">
        <div className="control-group">
          <label>Layout:</label>
          <select value={graphLayout} onChange={(e) => setGraphLayout(e.target.value)}>
            <option value="force">Force Directed</option>
            <option value="timeline">Timeline</option>
            <option value="circular">Circular</option>
          </select>
        </div>
        
        <div className="control-group">
          <label>Filter:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="all">All Connections</option>
            <option value="actors">Actors Only</option>
            <option value="events">Events Only</option>
            <option value="money">Financial Network</option>
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
          <p>Type: {selectedNode.type}</p>
          {selectedNode.date && <p>Date: {selectedNode.date}</p>}
          {selectedNode.tags && <p>Tags: {selectedNode.tags.join(', ')}</p>}
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
          <span className="legend-color actor"></span> Actor
        </div>
      </div>
    </div>
  );
};

export default NetworkGraph;