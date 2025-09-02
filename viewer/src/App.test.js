import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import axios from 'axios';

// Mock axios and d3
jest.mock('axios');
jest.mock('d3');

describe('Timeline App', () => {
  beforeEach(() => {
    // Reset axios mock before each test
    jest.clearAllMocks();
    
    // Default mock responses
    axios.get.mockImplementation((url) => {
      if (url.includes('events.json')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('tags.json')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('stats.json')) {
        return Promise.resolve({ 
          data: {
            total_events: 0,
            date_range: { start: null, end: null },
            total_tags: 0,
            total_actors: 0,
            events_by_year: {},
            events_by_status: {}
          }
        });
      }
      return Promise.resolve({ data: [] });
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('renders landing page initially', async () => {
    render(<App />);
    
    // Should show loading first
    expect(screen.getByText(/Loading timeline data/i)).toBeInTheDocument();
    
    // Wait for app to load
    await waitFor(() => {
      expect(screen.getByText(/The Kleptocracy Timeline/i)).toBeInTheDocument();
    });
  });

  test('enters timeline from landing page', async () => {
    const mockEvents = [
      {
        id: '2024-01-01_test-event',
        date: '2024-01-01',
        title: 'Test Event',
        summary: 'Test summary',
        tags: ['test'],
        actors: ['Test Actor'],
        status: 'confirmed'
      }
    ];

    axios.get.mockImplementation((url) => {
      if (url.includes('events.json')) {
        return Promise.resolve({ data: mockEvents });
      }
      if (url.includes('tags.json')) {
        return Promise.resolve({ data: ['test'] });
      }
      if (url.includes('stats.json')) {
        return Promise.resolve({ 
          data: {
            total_events: 1,
            date_range: { start: '2024-01-01', end: '2024-01-01' },
            total_tags: 1,
            total_actors: 1,
            events_by_year: { '2024': 1 },
            events_by_status: { 'confirmed': 1 }
          }
        });
      }
      return Promise.resolve({ data: [] });
    });

    render(<App />);
    
    // Wait for landing page to load
    await waitFor(() => {
      expect(screen.getByText(/View Interactive Timeline/i)).toBeInTheDocument();
    });

    // Click enter timeline
    const enterButton = screen.getByText(/View Interactive Timeline/i);
    fireEvent.click(enterButton);

    // Should show timeline with events
    await waitFor(() => {
      expect(screen.getByText(/1 Event/i)).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    axios.get.mockRejectedValue(new Error('Network error'));

    render(<App />);

    // Should show error state
    await waitFor(() => {
      expect(screen.getByText(/Error Loading Timeline/i)).toBeInTheDocument();
    });

    // Should have retry button
    expect(screen.getByText(/Retry/i)).toBeInTheDocument();
  });

  test('view toggle switches between views', async () => {
    render(<App />);
    
    // Wait for app to load
    await waitFor(() => {
      expect(screen.getByText(/View Interactive Timeline/i)).toBeInTheDocument();
    });

    // Enter timeline
    fireEvent.click(screen.getByText(/View Interactive Timeline/i));

    // Wait for timeline to load
    await waitFor(() => {
      expect(screen.getByText(/Timeline/i)).toBeInTheDocument();
    });

    // Find view toggle buttons
    const graphButton = screen.getByTitle('Graph');
    fireEvent.click(graphButton);

    // Should switch to graph view
    await waitFor(() => {
      expect(graphButton).toHaveClass('active');
    });
  });

  test('search filters events', async () => {
    const mockEvents = [
      {
        id: '2024-01-01_first-event',
        date: '2024-01-01',
        title: 'First Event',
        summary: 'First test summary',
        tags: ['test'],
        actors: ['Actor One'],
        status: 'confirmed'
      },
      {
        id: '2024-02-01_second-event',
        date: '2024-02-01',
        title: 'Second Event',
        summary: 'Second test summary',
        tags: ['test'],
        actors: ['Actor Two'],
        status: 'confirmed'
      }
    ];

    axios.get.mockImplementation((url) => {
      if (url.includes('events.json')) {
        return Promise.resolve({ data: mockEvents });
      }
      if (url.includes('tags.json')) {
        return Promise.resolve({ data: ['test'] });
      }
      if (url.includes('stats.json')) {
        return Promise.resolve({ 
          data: {
            total_events: 2,
            date_range: { start: '2024-01-01', end: '2024-02-01' },
            total_tags: 1,
            total_actors: 2,
            events_by_year: { '2024': 2 },
            events_by_status: { 'confirmed': 2 }
          }
        });
      }
      return Promise.resolve({ data: [] });
    });

    render(<App />);
    
    // Enter timeline
    await waitFor(() => {
      expect(screen.getByText(/View Interactive Timeline/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText(/View Interactive Timeline/i));

    // Wait for events to load
    await waitFor(() => {
      expect(screen.getByText(/2 Events/i)).toBeInTheDocument();
    });

    // Search for "First"
    const searchInput = screen.getByPlaceholderText(/Search events/i);
    fireEvent.change(searchInput, { target: { value: 'First' } });

    // Should filter to 1 event
    await waitFor(() => {
      expect(screen.getByText(/1 Event.*filtered from 2/i)).toBeInTheDocument();
    });
  });

  test('filter panel toggles visibility', async () => {
    render(<App />);
    
    // Enter timeline
    await waitFor(() => {
      expect(screen.getByText(/View Interactive Timeline/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText(/View Interactive Timeline/i));

    // Wait for timeline to load
    await waitFor(() => {
      expect(screen.getByTitle('Toggle filters')).toBeInTheDocument();
    });

    // Click filter toggle
    const filterToggle = screen.getByTitle('Toggle filters');
    fireEvent.click(filterToggle);

    // Filter panel should be visible
    await waitFor(() => {
      expect(screen.getByText(/Filter by Tags/i)).toBeInTheDocument();
    });
  });

  test('stats panel toggles visibility', async () => {
    render(<App />);
    
    // Enter timeline
    await waitFor(() => {
      expect(screen.getByText(/View Interactive Timeline/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText(/View Interactive Timeline/i));

    // Wait for timeline to load
    await waitFor(() => {
      expect(screen.getByTitle('Toggle statistics')).toBeInTheDocument();
    });

    // Click stats toggle
    const statsToggle = screen.getByTitle('Toggle statistics');
    fireEvent.click(statsToggle);

    // Stats panel should be visible
    await waitFor(() => {
      expect(screen.getByText(/Statistics/i)).toBeInTheDocument();
    });
  });
});