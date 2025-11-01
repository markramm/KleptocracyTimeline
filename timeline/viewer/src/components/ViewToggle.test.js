import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ViewToggle from './ViewToggle';

describe('ViewToggle', () => {
  const mockOnViewChange = jest.fn();

  beforeEach(() => {
    mockOnViewChange.mockClear();
  });

  test('renders all view buttons', () => {
    render(<ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />);
    
    expect(screen.getByTitle('Timeline')).toBeInTheDocument();
    expect(screen.getByTitle('List')).toBeInTheDocument();
    expect(screen.getByTitle('Grid')).toBeInTheDocument();
    expect(screen.getByTitle('Graph')).toBeInTheDocument();
    expect(screen.getByTitle('Actors')).toBeInTheDocument();
  });

  test('highlights current view', () => {
    render(<ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />);
    
    const timelineButton = screen.getByTitle('Timeline');
    expect(timelineButton).toHaveClass('active');
    
    const listButton = screen.getByTitle('List');
    expect(listButton).not.toHaveClass('active');
  });

  test('calls onViewChange when button clicked', () => {
    render(<ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />);
    
    const listButton = screen.getByTitle('List');
    fireEvent.click(listButton);
    
    expect(mockOnViewChange).toHaveBeenCalledWith('list');
    expect(mockOnViewChange).toHaveBeenCalledTimes(1);
  });

  test('each button calls onViewChange with correct view id', () => {
    render(<ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />);
    
    const views = [
      { title: 'Timeline', id: 'timeline' },
      { title: 'List', id: 'list' },
      { title: 'Grid', id: 'grid' },
      { title: 'Graph', id: 'graph' },
      { title: 'Actors', id: 'actors' }
    ];
    
    views.forEach(({ title, id }) => {
      const button = screen.getByTitle(title);
      fireEvent.click(button);
      expect(mockOnViewChange).toHaveBeenCalledWith(id);
    });
    
    expect(mockOnViewChange).toHaveBeenCalledTimes(5);
  });

  test('updates active class when currentView changes', () => {
    const { rerender } = render(
      <ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />
    );
    
    let timelineButton = screen.getByTitle('Timeline');
    let graphButton = screen.getByTitle('Graph');
    
    expect(timelineButton).toHaveClass('active');
    expect(graphButton).not.toHaveClass('active');
    
    // Change current view to graph
    rerender(<ViewToggle currentView="graph" onViewChange={mockOnViewChange} />);
    
    timelineButton = screen.getByTitle('Timeline');
    graphButton = screen.getByTitle('Graph');
    
    expect(timelineButton).not.toHaveClass('active');
    expect(graphButton).toHaveClass('active');
  });

  test('displays view labels', () => {
    render(<ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />);
    
    expect(screen.getByText('Timeline')).toBeInTheDocument();
    expect(screen.getByText('List')).toBeInTheDocument();
    expect(screen.getByText('Grid')).toBeInTheDocument();
    expect(screen.getByText('Graph')).toBeInTheDocument();
    expect(screen.getByText('Actors')).toBeInTheDocument();
  });

  test('renders with actors view selected', () => {
    render(<ViewToggle currentView="actors" onViewChange={mockOnViewChange} />);
    
    const actorsButton = screen.getByTitle('Actors');
    expect(actorsButton).toHaveClass('active');
  });

  test('handles clicking on already active view', () => {
    render(<ViewToggle currentView="timeline" onViewChange={mockOnViewChange} />);
    
    const timelineButton = screen.getByTitle('Timeline');
    fireEvent.click(timelineButton);
    
    // Should still call onViewChange even if it's the current view
    expect(mockOnViewChange).toHaveBeenCalledWith('timeline');
  });
});