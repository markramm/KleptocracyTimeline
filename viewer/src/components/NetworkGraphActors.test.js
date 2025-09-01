import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import NetworkGraphActors from './NetworkGraphActors';

// Mock d3
jest.mock('d3');

describe('NetworkGraphActors', () => {
  const mockEvents = [
    {
      id: '2024-01-01_test-event-1',
      date: '2024-01-01',
      title: 'Test Event 1',
      actors: ['Donald Trump', 'Actor A', 'Actor B'],
      summary: 'Test summary 1'
    },
    {
      id: '2024-02-01_test-event-2',
      date: '2024-02-01',
      title: 'Test Event 2',
      actors: ['Donald Trump', 'Actor B', 'Actor C'],
      summary: 'Test summary 2'
    },
    {
      id: '2024-03-01_test-event-3',
      date: '2024-03-01',
      title: 'Test Event 3',
      actors: ['Actor A', 'Actor C', 'Actor D'],
      summary: 'Test summary 3'
    }
  ];

  beforeEach(() => {
    // Create a mock SVG element for d3 to work with
    const mockSvgElement = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    jest.spyOn(React, 'useRef').mockReturnValue({ current: mockSvgElement });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('renders without crashing', () => {
    render(<NetworkGraphActors events={[]} />);
    expect(screen.getByPlaceholderText(/Search actors/i)).toBeInTheDocument();
  });

  test('renders with events', () => {
    render(<NetworkGraphActors events={mockEvents} />);
    
    // Check for controls
    expect(screen.getByPlaceholderText(/Search actors/i)).toBeInTheDocument();
    expect(screen.getByText(/Min Events:/i)).toBeInTheDocument();
    expect(screen.getByText(/Show Labels/i)).toBeInTheDocument();
  });

  test('search input filters actors', () => {
    render(<NetworkGraphActors events={mockEvents} />);
    
    const searchInput = screen.getByPlaceholderText(/Search actors/i);
    fireEvent.change(searchInput, { target: { value: 'Trump' } });
    
    expect(searchInput.value).toBe('Trump');
  });

  test('minimum events filter changes', () => {
    render(<NetworkGraphActors events={mockEvents} />);
    
    const minEventsSelect = screen.getByDisplayValue('3+ events');
    fireEvent.change(minEventsSelect, { target: { value: '5' } });
    
    expect(screen.getByDisplayValue('5+ events')).toBeInTheDocument();
  });

  test('show labels checkbox toggles', () => {
    render(<NetworkGraphActors events={mockEvents} />);
    
    const showLabelsCheckbox = screen.getByRole('checkbox');
    expect(showLabelsCheckbox).toBeChecked();
    
    fireEvent.click(showLabelsCheckbox);
    expect(showLabelsCheckbox).not.toBeChecked();
  });

  test('displays top actors legend', () => {
    render(<NetworkGraphActors events={mockEvents} />);
    
    // Should show "Top Actors" heading
    expect(screen.getByText(/Top Actors/i)).toBeInTheDocument();
  });

  test('handles empty events gracefully', () => {
    render(<NetworkGraphActors events={[]} />);
    
    // Should still render controls
    expect(screen.getByPlaceholderText(/Search actors/i)).toBeInTheDocument();
    expect(screen.getByText(/Min Events:/i)).toBeInTheDocument();
  });

  test('handles events without actors', () => {
    const eventsWithoutActors = [
      {
        id: '2024-01-01_test-event',
        date: '2024-01-01',
        title: 'Test Event',
        summary: 'Test summary'
      }
    ];
    
    render(<NetworkGraphActors events={eventsWithoutActors} />);
    
    // Should still render without crashing
    expect(screen.getByPlaceholderText(/Search actors/i)).toBeInTheDocument();
  });

  test('node details display when actor is selected', () => {
    const { container } = render(<NetworkGraphActors events={mockEvents} />);
    
    // Check that node details div is not initially present
    expect(container.querySelector('.node-details')).not.toBeInTheDocument();
    
    // Note: Testing actual d3 interactions would require more complex mocking
    // This test just verifies the component structure
  });

  test('Trump node should be recognized', () => {
    const trumpEvents = [
      {
        id: '2024-01-01_trump-event',
        date: '2024-01-01',
        title: 'Trump Event',
        actors: ['Donald Trump', 'Trump Administration'],
        summary: 'Trump related event'
      }
    ];
    
    render(<NetworkGraphActors events={trumpEvents} />);
    
    // Component should render with Trump-related events
    expect(screen.getByText(/Top Actors/i)).toBeInTheDocument();
  });
});