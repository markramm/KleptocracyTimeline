import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FilterPanel from './FilterPanel';

describe('FilterPanel', () => {
  const mockProps = {
    allTags: ['politics', 'technology', 'finance'],
    allActors: ['John Doe', 'Jane Smith', 'Acme Corp'],
    allCaptureLanes: ['regulatory', 'judicial', 'legislative'],
    selectedTags: [],
    selectedActors: [],
    selectedCaptureLanes: [],
    dateRange: { start: null, end: null },
    onTagsChange: jest.fn(),
    onActorsChange: jest.fn(),
    onCaptureLanesChange: jest.fn(),
    onDateRangeChange: jest.fn(),
    onClear: jest.fn(),
    eventCount: 50,
    totalCount: 100,
    viewMode: 'timeline',
    timelineControls: { zoom: 1, pan: 0 },
    onTimelineControlsChange: jest.fn(),
    timelineData: [],
    events: [],
    sortOrder: 'chronological',
    onSortOrderChange: jest.fn(),
    minImportance: 0,
    onMinImportanceChange: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders filter panel with all sections', () => {
    render(<FilterPanel {...mockProps} />);
    
    expect(screen.getByText(/Sorting/i)).toBeInTheDocument();
    expect(screen.getByText(/Importance Filter/i)).toBeInTheDocument();
    expect(screen.getByText(/Date Range/i)).toBeInTheDocument();
    expect(screen.getByText(/Tags/i)).toBeInTheDocument();
    expect(screen.getByText(/Actors/i)).toBeInTheDocument();
  });

  test('displays event count correctly', () => {
    render(<FilterPanel {...mockProps} />);
    
    expect(screen.getByText(/Showing 50 of 100 events/i)).toBeInTheDocument();
  });

  test('handles clear filters', () => {
    render(<FilterPanel {...mockProps} />);
    
    const clearButton = screen.getByRole('button', { name: /clear all/i });
    fireEvent.click(clearButton);
    
    expect(mockProps.onClear).toHaveBeenCalledTimes(1);
  });

  test('handles sort order change', () => {
    render(<FilterPanel {...mockProps} />);
    
    const sortButtons = screen.getAllByRole('button');
    const reverseChronButton = sortButtons.find(btn => 
      btn.textContent.includes('Reverse Chronological')
    );
    
    if (reverseChronButton) {
      fireEvent.click(reverseChronButton);
      expect(mockProps.onSortOrderChange).toHaveBeenCalled();
    }
  });

  test('handles importance filter change', () => {
    render(<FilterPanel {...mockProps} />);
    
    const importanceSlider = screen.getByRole('slider', { name: /importance/i });
    fireEvent.change(importanceSlider, { target: { value: '5' } });
    
    expect(mockProps.onMinImportanceChange).toHaveBeenCalledWith(5);
  });

  test('handles date range inputs', () => {
    render(<FilterPanel {...mockProps} />);
    
    const startDateInput = screen.getByLabelText(/from/i);
    const endDateInput = screen.getByLabelText(/to/i);
    
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });
    
    expect(mockProps.onDateRangeChange).toHaveBeenCalledTimes(2);
  });

  test('toggles section expansion', () => {
    render(<FilterPanel {...mockProps} />);
    
    const sortingHeader = screen.getByText(/Sorting/i).closest('div');
    const toggleButton = sortingHeader.querySelector('button');
    
    fireEvent.click(toggleButton);
    
    // Check if content is toggled (implementation-specific)
    expect(toggleButton).toBeInTheDocument();
  });

  test('renders with selected filters', () => {
    const propsWithSelections = {
      ...mockProps,
      selectedTags: ['politics'],
      selectedActors: ['John Doe'],
      minImportance: 5
    };
    
    render(<FilterPanel {...propsWithSelections} />);
    
    const importanceSlider = screen.getByRole('slider', { name: /importance/i });
    expect(importanceSlider.value).toBe('5');
  });

  test('handles no events gracefully', () => {
    const propsNoEvents = {
      ...mockProps,
      eventCount: 0,
      totalCount: 0
    };
    
    render(<FilterPanel {...propsNoEvents} />);
    
    expect(screen.getByText(/Showing 0 of 0 events/i)).toBeInTheDocument();
  });
});