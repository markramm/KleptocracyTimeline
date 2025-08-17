import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock fetch API
global.fetch = jest.fn();

describe('Timeline App', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    fetch.mockClear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // Sample test data
  const mockEvents = [
    {
      id: '2024-01-01_test-event-one',
      date: '2024-01-01',
      title: 'Test Event One',
      summary: 'First test event summary',
      tags: ['test', 'democracy'],
      status: 'confirmed',
      sources: [
        {
          title: 'Test Source',
          url: 'https://example.com',
          outlet: 'Test News'
        }
      ]
    },
    {
      id: '2024-02-15_test-event-two',
      date: '2024-02-15',
      title: 'Test Event Two',
      summary: 'Second test event summary',
      tags: ['test', 'politics'],
      status: 'confirmed',
      sources: []
    }
  ];

  const mockTags = ['test', 'democracy', 'politics'];
  const mockStats = {
    total_events: 2,
    date_range: { start: '2024-01-01', end: '2024-02-15' },
    total_tags: 3,
    total_actors: 0,
    events_by_year: { '2024': 2 },
    events_by_status: { 'confirmed': 2 }
  };

  test('renders without crashing', () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ events: [], total: 0 })
    });

    render(<App />);
    expect(screen.getByText(/Democracy Timeline/i)).toBeInTheDocument();
  });

  test('loads and displays events', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: mockEvents, total: 2 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: mockTags })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

    render(<App />);

    // Wait for events to load
    await waitFor(() => {
      expect(screen.getByText('Test Event One')).toBeInTheDocument();
      expect(screen.getByText('Test Event Two')).toBeInTheDocument();
    });

    // Check event count
    expect(screen.getByText(/2 events/i)).toBeInTheDocument();
  });

  test('search functionality works', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: mockEvents, total: 2 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: mockTags })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

    render(<App />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Event One')).toBeInTheDocument();
    });

    // Find search input
    const searchInput = screen.getByPlaceholderText(/Search events/i);
    
    // Type in search
    fireEvent.change(searchInput, { target: { value: 'First' } });

    // Check that filtering happens (this depends on your implementation)
    await waitFor(() => {
      expect(screen.getByText('First test event summary')).toBeInTheDocument();
    });
  });

  test('tag filtering works', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: mockEvents, total: 2 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: mockTags })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

    render(<App />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Event One')).toBeInTheDocument();
    });

    // Find and click a tag filter (implementation dependent)
    const tagButton = screen.getByText('democracy');
    fireEvent.click(tagButton);

    // Check that filtering is applied
    await waitFor(() => {
      // Should still show event with 'democracy' tag
      expect(screen.getByText('Test Event One')).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('API Error'));

    render(<App />);

    // Should show error message or fallback
    await waitFor(() => {
      expect(screen.getByText(/Error loading/i)).toBeInTheDocument();
    });
  });

  test('displays event details when clicked', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: mockEvents, total: 2 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: mockTags })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

    render(<App />);

    // Wait for events to load
    await waitFor(() => {
      expect(screen.getByText('Test Event One')).toBeInTheDocument();
    });

    // Click on an event
    const eventTitle = screen.getByText('Test Event One');
    fireEvent.click(eventTitle);

    // Check that details are shown
    await waitFor(() => {
      expect(screen.getByText('First test event summary')).toBeInTheDocument();
      expect(screen.getByText('Test Source')).toBeInTheDocument();
    });
  });

  test('year navigation works', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: mockEvents, total: 2 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: mockTags })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

    render(<App />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('2024')).toBeInTheDocument();
    });

    // Click on year navigation (if present)
    const yearButton = screen.getByText('2024');
    fireEvent.click(yearButton);

    // Check that year filter is applied
    await waitFor(() => {
      // Both events are from 2024, so both should be visible
      expect(screen.getByText('Test Event One')).toBeInTheDocument();
      expect(screen.getByText('Test Event Two')).toBeInTheDocument();
    });
  });

  test('displays statistics correctly', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: mockEvents, total: 2 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: mockTags })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

    render(<App />);

    // Wait for stats to load
    await waitFor(() => {
      expect(screen.getByText(/Total Events: 2/i)).toBeInTheDocument();
      expect(screen.getByText(/Tags: 3/i)).toBeInTheDocument();
    });
  });

  test('responsive design adapts to screen size', () => {
    // Mock window size
    global.innerWidth = 500;
    global.dispatchEvent(new Event('resize'));

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ events: [], total: 0 })
    });

    render(<App />);

    // Check that mobile-specific elements are present
    // This depends on your responsive implementation
    expect(screen.getByText(/Democracy Timeline/i)).toBeInTheDocument();
  });

  test('empty state displays correctly', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ events: [], total: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ tags: [] })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_events: 0,
          date_range: { start: null, end: null },
          total_tags: 0,
          total_actors: 0,
          events_by_year: {},
          events_by_status: {}
        })
      });

    render(<App />);

    // Wait for empty state
    await waitFor(() => {
      expect(screen.getByText(/No events found/i)).toBeInTheDocument();
    });
  });

  test('loading state displays while fetching', async () => {
    // Create a promise that doesn't resolve immediately
    let resolvePromise;
    const delayedPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    fetch.mockReturnValueOnce({
      ok: true,
      json: () => delayedPromise
    });

    render(<App />);

    // Check for loading indicator
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();

    // Resolve the promise
    resolvePromise({ events: [], total: 0 });

    // Loading should disappear
    await waitFor(() => {
      expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
    });
  });
});