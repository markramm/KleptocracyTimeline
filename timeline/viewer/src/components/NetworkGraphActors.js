import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import './NetworkGraph.css';

const NetworkGraphActors = ({ events }) => {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  
  // Parse URL parameters
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  
  // Initialize state from URL parameters
  const [minEvents, setMinEvents] = useState(() => 
    parseInt(params.get('minEvents')) || 3
  );
  const [showLabels, setShowLabels] = useState(() => 
    params.get('labels') !== 'false'
  );
  const [searchQuery, setSearchQuery] = useState(
    params.get('search') || ''
  );
  const [networkData, setNetworkData] = useState({ nodes: [], links: [] });
  const [compareMode, setCompareMode] = useState(() =>
    params.get('investigate') === 'true'
  );
  const [compareNodes, setCompareNodes] = useState([]);
  
  // Update URL when parameters change
  const updateURL = useCallback(() => {
    const newParams = new URLSearchParams();
    
    if (minEvents !== 3) newParams.set('minEvents', minEvents);
    if (!showLabels) newParams.set('labels', 'false');
    if (searchQuery) newParams.set('search', searchQuery);
    if (compareMode) newParams.set('investigate', 'true');
    if (compareNodes.length > 0) {
      newParams.set('actors', compareNodes.map(n => n.id).join(','));
    }
    
    // Update browser URL without reload
    const newSearch = newParams.toString();
    const newURL = window.location.pathname + (newSearch ? `?${newSearch}` : '') + window.location.hash;
    window.history.replaceState({}, '', newURL);
  }, [minEvents, showLabels, searchQuery, compareMode, compareNodes]);
  
  // Update URL when state changes
  useEffect(() => {
    updateURL();
  }, [minEvents, showLabels, searchQuery, compareMode, compareNodes, updateURL]);
  
  // Load actors from URL on mount
  useEffect(() => {
    const actorIds = params.get('actors');
    if (actorIds && networkData.nodes.length > 0) {
      const ids = actorIds.split(',');
      const nodes = ids.map(id => networkData.nodes.find(n => n.id === id)).filter(Boolean);
      if (nodes.length > 0 && compareNodes.length === 0) {
        setCompareNodes(nodes);
      }
    }
  }, [params, networkData.nodes]); // eslint-disable-line react-hooks/exhaustive-deps

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
    
    // Save network data for use in render
    setNetworkData({ nodes, links });

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
      .scaleExtent([0.1, 5])  // Allow more zoom out to see all nodes
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    
    svg.call(zoom);
    
    // Set initial zoom to show more of the network
    svg.call(zoom.transform, d3.zoomIdentity.scale(0.6));

    // Find Trump node and set initial position
    const trumpNode = nodes.find(n => n.isTrump && n.id === 'Donald Trump') || 
                     nodes.find(n => n.isTrump);
    
    if (trumpNode) {
      trumpNode.fx = width / 2;
      trumpNode.fy = height / 2;
      trumpNode.fixed = true;
    }

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
          // Dynamic distance based on connection strength
          const baseDistance = 80;
          const reduction = Math.min(d.value * 3, 40);
          return baseDistance - reduction;
        })
        .strength(d => Math.min(d.value * 0.1, 0.5))
      )
      .force('charge', d3.forceManyBody()
        .strength(d => {
          // Balanced repulsion for better spacing
          if (d.isTrump) return -500;
          // Moderate repulsion for readability
          return -50 - (d.eventCount * 3);
        })
        .distanceMax(400)  // Limit repulsion distance
      )
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.05))
      .force('collision', d3.forceCollide()
        .radius(d => sizeScale(d.eventCount) + 10)  // More space between nodes
        .strength(0.8)
      )
      .force('x', d3.forceX(width / 2).strength(0.01))  // Gentle centering
      .force('y', d3.forceY(height / 2).strength(0.01));

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
        if (compareMode) {
          // In investigation mode, add/remove from investigation list
          const isInvestigating = compareNodes.some(n => n.id === d.id);
          if (isInvestigating) {
            setCompareNodes(compareNodes.filter(n => n.id !== d.id));
          } else {
            setCompareNodes([...compareNodes, d]);
          }
          // Highlight investigation network
          if (compareNodes.length > 0 || !isInvestigating) {
            highlightInvestigationNetwork([...compareNodes, d].filter(n => n.id !== (isInvestigating ? d.id : null)));
          }
        } else {
          setSelectedNode(d);
          highlightConnections(d);
        }
      })
      .on('mouseover', (event, d) => {
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
        d3.selectAll('.actor-tooltip').remove();
      })
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add labels with background for better readability
    const labelGroups = g.append('g')
      .attr('class', 'labels')
      .selectAll('g')
      .data(nodes)
      .enter().append('g');

    // Add white background rectangles for labels
    labelGroups.each(function(d) {
      const group = d3.select(this);
      const labelText = (() => {
        if (d.isTrump) return d.label;
        if (showLabels) {
          if (d.eventCount > 15) return d.label.length > 20 ? d.label.substring(0, 18) + '...' : d.label;
          if (d.eventCount > 8) return d.label.length > 15 ? d.label.substring(0, 13) + '...' : d.label;
        }
        return '';
      })();
      
      if (labelText) {
        const fontSize = d.isTrump ? 14 : (d.eventCount > 50 ? 11 : (d.eventCount > 20 ? 10 : 9));
        
        // Add background rect
        const text = group.append('text')
          .text(labelText)
          .attr('font-size', fontSize)
          .attr('font-weight', d.isTrump ? 'bold' : 'normal')
          .attr('text-anchor', 'middle')
          .attr('dy', sizeScale(d.eventCount) + 15)
          .style('pointer-events', 'none')
          .style('user-select', 'none');
        
        const bbox = text.node().getBBox();
        
        group.insert('rect', 'text')
          .attr('x', bbox.x - 2)
          .attr('y', bbox.y - 1)
          .attr('width', bbox.width + 4)
          .attr('height', bbox.height + 2)
          .attr('fill', 'rgba(255, 255, 255, 0.8)')
          .attr('rx', 2)
          .attr('ry', 2);
      }
    });

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

      labelGroups
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
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
      labelGroups.style('opacity', n => connectedNodes.has(n.id) ? 1 : 0.2);
      
      link.style('opacity', l => 
        (l.source.id === selectedNode.id || l.target.id === selectedNode.id) ? 0.8 : 0.05
      );
      
      // Center the selected node with smooth transition
      const centerX = width / 2;
      const centerY = height / 2;
      const scale = 1.2;
      
      const transform = d3.zoomIdentity
        .translate(centerX, centerY)
        .scale(scale)
        .translate(-selectedNode.x, -selectedNode.y);
      
      svg.transition()
        .duration(750)
        .call(zoom.transform, transform);
    }
    
    function highlightInvestigationNetwork(investigatedNodes) {
      const investigatedIds = new Set(investigatedNodes.map(n => n.id));
      const connectedNodes = new Set(investigatedIds);
      
      // Find all nodes connected to any investigated node
      links.forEach(l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        
        if (investigatedIds.has(sourceId)) {
          connectedNodes.add(targetId);
        }
        if (investigatedIds.has(targetId)) {
          connectedNodes.add(sourceId);
        }
      });
      
      // Style nodes based on investigation status
      node
        .style('opacity', n => {
          if (investigatedIds.has(n.id)) return 1;
          if (connectedNodes.has(n.id)) return 0.6;
          return 0.1;
        })
        .style('stroke', n => {
          if (investigatedIds.has(n.id)) return '#e74c3c';
          return '#fff';
        })
        .style('stroke-width', n => {
          if (investigatedIds.has(n.id)) return 4;
          return 2;
        });
      
      labelGroups.style('opacity', n => {
        if (investigatedIds.has(n.id)) return 1;
        if (connectedNodes.has(n.id)) return 0.7;
        return 0.1;
      });
      
      // Highlight links between investigated nodes
      link.style('opacity', l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        
        // Strong highlight for links between investigated nodes
        if (investigatedIds.has(sourceId) && investigatedIds.has(targetId)) {
          return 1;
        }
        // Medium highlight for links from investigated to connected
        if (investigatedIds.has(sourceId) || investigatedIds.has(targetId)) {
          return 0.4;
        }
        return 0.02;
      })
      .style('stroke', l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        
        if (investigatedIds.has(sourceId) && investigatedIds.has(targetId)) {
          return '#e74c3c';
        }
        return '#999';
      })
      .style('stroke-width', l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        
        if (investigatedIds.has(sourceId) && investigatedIds.has(targetId)) {
          return linkScale(l.value) * 2;
        }
        return linkScale(l.value);
      });
    }

    // Click on background to reset
    svg.on('click', function(event) {
      if (event.target === this || event.target.tagName === 'rect') {
        if (compareMode && compareNodes.length > 0) {
          // In investigation mode, clear selection
          setCompareNodes([]);
        }
        node.style('opacity', 1);
        labelGroups.style('opacity', 1);
        link.style('opacity', d => 0.2 + (d.value / 20))
          .style('stroke', '#999')
          .style('stroke-width', d => linkScale(d.value));
        node.style('stroke', '#fff')
          .style('stroke-width', 2);
        setSelectedNode(null);
      }
    });

  }, [events, minEvents, showLabels, searchQuery, compareMode, compareNodes]);

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
        
        <div className="control-group">
          <button
            onClick={() => {
              setCompareMode(!compareMode);
              setCompareNodes([]);
            }}
            style={{
              padding: '6px 12px',
              background: compareMode ? '#e74c3c' : '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: compareMode ? 'bold' : 'normal'
            }}
          >
            {compareMode ? 'Exit Investigation Mode' : '🔍 Investigation Mode'}
          </button>
        </div>
        
        {compareMode && compareNodes.length > 0 && (
          <div className="control-group" style={{ 
            padding: '8px', 
            background: '#f0f0f0', 
            borderRadius: '4px',
            maxWidth: '400px'
          }}>
            <strong>Investigating {compareNodes.length} actors:</strong>
            {compareNodes.length > 1 && (
              <div style={{ fontSize: '11px', color: '#666', marginTop: '3px' }}>
                {(() => {
                  const connectionCount = networkData.links.filter(l => {
                    const sourceId = l.source.id || l.source;
                    const targetId = l.target.id || l.target;
                    const actorIds = compareNodes.map(n => n.id);
                    return actorIds.includes(sourceId) && actorIds.includes(targetId);
                  }).length;
                  const totalEvents = compareNodes.reduce((sum, n) => sum + n.eventCount, 0);
                  return `${connectionCount} connections • ${totalEvents} total events`;
                })()}
              </div>
            )}
            <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginTop: '5px' }}>
              {compareNodes.map(node => (
                <span key={node.id} style={{
                  padding: '2px 8px',
                  background: '#667eea',
                  color: 'white',
                  borderRadius: '3px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }} onClick={() => setCompareNodes(compareNodes.filter(n => n.id !== node.id))}>
                  {node.label} ✕
                </span>
              ))}
            </div>
            <div style={{ marginTop: '8px', display: 'flex', gap: '5px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={() => {
                  const url = window.location.href;
                  navigator.clipboard.writeText(url);
                  alert('Investigation URL copied to clipboard! Share or bookmark this link.');
                }}
                style={{
                  padding: '4px 8px',
                  fontSize: '12px',
                  background: '#27ae60',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
              >
                📋 Copy URL
              </button>
              <button
                onClick={() => {
                  // Build URL to switch to timeline view with these actors as filters
                  const params = new URLSearchParams();
                  params.set('viewMode', 'timeline');
                  // Use 'actors' as the parameter name, with comma-separated values
                  params.set('actors', compareNodes.map(n => n.label).join(','));
                  const newURL = window.location.pathname + '?' + params.toString() + window.location.hash;
                  window.location.href = newURL;
                }}
                style={{
                  padding: '4px 8px',
                  fontSize: '12px',
                  background: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
              >
                📅 View Events in Timeline
              </button>
              <button
                onClick={() => {
                  // Export investigation data as JSON
                  const investigationData = {
                    date: new Date().toISOString(),
                    actors: compareNodes.map(n => ({
                      id: n.id,
                      label: n.label,
                      eventCount: n.eventCount
                    })),
                    connections: networkData.links.filter(l => {
                      const sourceId = l.source.id || l.source;
                      const targetId = l.target.id || l.target;
                      const actorIds = compareNodes.map(n => n.id);
                      return actorIds.includes(sourceId) && actorIds.includes(targetId);
                    }).map(l => ({
                      source: l.source.id || l.source,
                      target: l.target.id || l.target,
                      sharedEvents: l.value
                    })),
                    url: window.location.href
                  };
                  
                  const dataStr = JSON.stringify(investigationData, null, 2);
                  const dataBlob = new Blob([dataStr], { type: 'application/json' });
                  const url = URL.createObjectURL(dataBlob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `investigation-${new Date().toISOString().split('T')[0]}.json`;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  URL.revokeObjectURL(url);
                }}
                style={{
                  padding: '4px 8px',
                  fontSize: '12px',
                  background: '#95a5a6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
              >
                📥 Export Data
              </button>
              <span style={{ fontSize: '11px', color: '#666' }}>
                {compareNodes.length} actors
              </span>
            </div>
          </div>
        )}
      </div>

      <svg ref={svgRef} className="network-graph"></svg>

      {selectedNode && (
        <div className="node-details">
          <h3>{selectedNode.label}</h3>
          <div className="node-stats">
            <p><strong>Total Events:</strong> {selectedNode.eventCount}</p>
            <p><strong>Direct Connections:</strong> {
              networkData.links.filter(l => 
                (l.source.id === selectedNode.id || l.target.id === selectedNode.id) ||
                (l.source === selectedNode.id || l.target === selectedNode.id)
              ).length
            } actors</p>
          </div>
          
          {/* Connected Actors Section */}
          <div style={{ marginTop: '15px', marginBottom: '15px' }}>
            <p><strong>Most Connected Actors:</strong></p>
            <div style={{ maxHeight: '120px', overflowY: 'auto' }}>
              {(() => {
                const connectionCounts = {};
                networkData.links.forEach(l => {
                  if (l.source.id === selectedNode.id || l.source === selectedNode.id) {
                    const targetId = l.target.id || l.target;
                    connectionCounts[targetId] = (connectionCounts[targetId] || 0) + l.value;
                  } else if (l.target.id === selectedNode.id || l.target === selectedNode.id) {
                    const sourceId = l.source.id || l.source;
                    connectionCounts[sourceId] = (connectionCounts[sourceId] || 0) + l.value;
                  }
                });
                
                return Object.entries(connectionCounts)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([actor, count]) => (
                    <div key={actor} style={{ 
                      padding: '4px 8px', 
                      margin: '4px 0',
                      background: '#f0f0f0',
                      borderRadius: '4px',
                      fontSize: '13px',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between'
                    }}
                    onClick={() => {
                      const targetNode = networkData.nodes.find(n => n.id === actor);
                      if (targetNode) {
                        setSelectedNode(targetNode);
                      }
                    }}>
                      <span>{actor}</span>
                      <span style={{ color: '#667eea', fontWeight: 'bold' }}>{count} events</span>
                    </div>
                  ));
              })()}
            </div>
          </div>
          
          {/* Events Section with Actor Highlighting */}
          <div style={{ maxHeight: '250px', overflowY: 'auto', marginTop: '10px' }}>
            <p><strong>Events ({selectedNode.events.length} total):</strong></p>
            <ul>
              {selectedNode.events.slice(0, 10).map((event, i) => (
                <li key={i} style={{ marginBottom: '10px' }}>
                  <div>
                    <strong>{event.date}</strong>: {event.title?.substring(0, 60)}
                    {event.title?.length > 60 ? '...' : ''}
                  </div>
                  {event.actors && event.actors.length > 1 && (
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                      Also involves: {event.actors.filter(a => a !== selectedNode.label).slice(0, 3).join(', ')}
                      {event.actors.filter(a => a !== selectedNode.label).length > 3 && ' ...'}
                    </div>
                  )}
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