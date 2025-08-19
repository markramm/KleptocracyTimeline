import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import './TimelineMinimap.css';

const TimelineMinimap = ({ events = [], groups = {}, onNavigate, onDateRangeSelect }) => {
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [dragEnd, setDragEnd] = useState(null);
  const [selectedRange, setSelectedRange] = useState(null);
  
  const years = useMemo(() => Object.keys(groups || {}).sort(), [groups]);
  
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
      const yearEvents = Object.values(groups[year] || {}).flat().filter(Boolean);
      
      // Draw year background
      ctx.fillStyle = index % 2 === 0 ? 'rgba(248, 250, 252, 0.1)' : 'rgba(255, 255, 255, 0.05)';
      ctx.fillRect(0, y, width, yearHeight);
      
      // Draw importance bars
      const monthWidth = width / 12;
      Object.entries(groups[year] || {}).forEach(([month, monthEvents]) => {
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
    
    // Draw selection overlay if dragging or selected
    if (selectedRange || (isDragging && dragStart !== null && dragEnd !== null)) {
      const start = selectedRange ? selectedRange.start : Math.min(dragStart, dragEnd);
      const end = selectedRange ? selectedRange.end : Math.max(dragStart, dragEnd);
      
      ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
      ctx.fillRect(0, start, width, end - start);
      
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.strokeRect(0, start, width, end - start);
    }
  }, [groups, years, isDragging, dragStart, dragEnd, selectedRange]);
  
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
        {selectedRange && (
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