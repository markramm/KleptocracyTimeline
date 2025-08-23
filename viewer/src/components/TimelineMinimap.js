import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import './TimelineMinimap.css';

const TimelineMinimap = ({ events = [], groups = {}, onNavigate, onDateRangeSelect, currentDateRange }) => {
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [dragEnd, setDragEnd] = useState(null);
  const [selectedRange, setSelectedRange] = useState(null);
  
  // Create properly structured groups from events
  const structuredGroups = useMemo(() => {
    const result = {};
    events.forEach(event => {
      if (!event.date) return;
      const year = event.date.substring(0, 4);
      const month = event.date.substring(5, 7);
      if (!result[year]) result[year] = {};
      if (!result[year][month]) result[year][month] = [];
      result[year][month].push(event);
    });
    return result;
  }, [events]);

  const years = useMemo(() => Object.keys(structuredGroups).sort(), [structuredGroups]);
  
  // Convert date range to Y coordinates
  const getYFromDate = useCallback((dateStr) => {
    if (!dateStr || !canvasRef.current || years.length === 0) return null;
    const year = dateStr.substring(0, 4);
    const month = parseInt(dateStr.substring(5, 7)) || 1;
    const yearIndex = years.indexOf(year);
    if (yearIndex === -1) return null;
    
    const yearHeight = canvasRef.current.height / years.length;
    const monthProgress = (month - 1) / 12;
    return yearIndex * yearHeight + monthProgress * yearHeight;
  }, [years]);

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || years.length === 0) {
      return;
    }
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Simple background
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);
    
    // Draw timeline visualization
    const yearHeight = height / years.length;
    
    years.forEach((year, index) => {
      const y = index * yearHeight;
      const yearEvents = Object.values(structuredGroups[year] || {}).flat().filter(Boolean);
      
      // Draw year background
      ctx.fillStyle = index % 2 === 0 ? 'rgba(248, 250, 252, 0.1)' : 'rgba(255, 255, 255, 0.05)';
      ctx.fillRect(0, y, width, yearHeight);
      
      // Draw importance bars
      const monthWidth = width / 12;
      Object.entries(structuredGroups[year] || {}).forEach(([month, monthEvents]) => {
        // Ensure monthEvents is an array
        const eventsArray = Array.isArray(monthEvents) ? monthEvents : [];
        if (eventsArray.length === 0) return;
        
        const monthIndex = parseInt(month) - 1;
        const x = monthIndex * monthWidth;
        const avgImportance = eventsArray.reduce((sum, e) => sum + (e.importance || 5), 0) / eventsArray.length;
        const barHeight = (avgImportance / 10) * yearHeight * 0.8;
        
        // Color based on average importance
        if (avgImportance >= 8) ctx.fillStyle = '#dc2626';
        else if (avgImportance >= 7) ctx.fillStyle = '#f59e0b';
        else if (avgImportance >= 6) ctx.fillStyle = '#3b82f6';
        else ctx.fillStyle = '#94a3b8';
        
        ctx.fillRect(x + 2, y + yearHeight - barHeight - 2, monthWidth - 4, barHeight);
      });
      
      // Draw year label
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px sans-serif';
      ctx.fillText(year, 4, y + yearHeight / 2);
    });
    
    // Draw current date range selection from filter
    if (currentDateRange && currentDateRange.start && currentDateRange.end) {
      const startY = getYFromDate(currentDateRange.start);
      const endY = getYFromDate(currentDateRange.end);
      
      if (startY !== null && endY !== null) {
        ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
        ctx.fillRect(0, startY, width, endY - startY);
        
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.strokeRect(0, startY, width, endY - startY);
      }
    }
    
    // Draw drag selection overlay
    if (isDragging && dragStart !== null && dragEnd !== null) {
      const start = Math.min(dragStart, dragEnd);
      const end = Math.max(dragStart, dragEnd);
      
      ctx.fillStyle = 'rgba(251, 191, 36, 0.2)';
      ctx.fillRect(0, start, width, end - start);
      
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.strokeRect(0, start, width, end - start);
    }
  }, [structuredGroups, years, isDragging, dragStart, dragEnd, currentDateRange, getYFromDate]);
  
  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);
  
  const getDateFromY = (y) => {
    const yearIndex = Math.floor(y / (canvasRef.current.height / years.length));
    const yearProgress = (y % (canvasRef.current.height / years.length)) / (canvasRef.current.height / years.length);
    const year = years[Math.min(yearIndex, years.length - 1)];
    const month = Math.floor(yearProgress * 12) + 1;
    return `${year}-${String(month).padStart(2, '0')}-01`;
  };
  
  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const y = e.clientY - rect.top;
    
    setIsDragging(true);
    setDragStart(y);
    setDragEnd(y);
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const y = e.clientY - rect.top;
    
    setDragEnd(y);
  };
  
  const handleMouseUp = (e) => {
    if (!isDragging) return;
    
    const startDate = getDateFromY(Math.min(dragStart, dragEnd));
    const endDate = getDateFromY(Math.max(dragStart, dragEnd));
    
    if (Math.abs(dragEnd - dragStart) > 5) {
      // Range selection
      setSelectedRange({ start: Math.min(dragStart, dragEnd), end: Math.max(dragStart, dragEnd) });
      onDateRangeSelect({ start: startDate, end: endDate });
    } else {
      // Single click navigation
      setSelectedRange(null);
      onNavigate(startDate);
      onDateRangeSelect({ start: null, end: null });
    }
    
    setIsDragging(false);
    setDragStart(null);
    setDragEnd(null);
  };
  
  const handleClearSelection = () => {
    setSelectedRange(null);
    onDateRangeSelect({ start: null, end: null });
  };
  
  return (
    <div className="timeline-minimap">
      <div className="minimap-header">
        <h5>Timeline Navigation</h5>
        {(selectedRange || (currentDateRange && currentDateRange.start && currentDateRange.end)) && (
          <button className="clear-selection-btn" onClick={handleClearSelection}>
            Clear Range
          </button>
        )}
      </div>
      <canvas 
        ref={canvasRef}
        width={200}
        height={200}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      />
      <div className="minimap-instructions">
        Click to jump • Drag to filter range
      </div>
      <div className="minimap-legend">
        <div><span style={{ background: '#dc2626' }}></span> Critical</div>
        <div><span style={{ background: '#f59e0b' }}></span> High</div>
        <div><span style={{ background: '#3b82f6' }}></span> Notable</div>
      </div>
    </div>
  );
};

export default TimelineMinimap;