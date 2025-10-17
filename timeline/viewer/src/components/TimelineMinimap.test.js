import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TimelineMinimap from './TimelineMinimap';

// Mock D3 to avoid issues in test environment
jest.mock('d3', () => ({
  select: jest.fn(() => ({
    append: jest.fn(() => ({
      attr: jest.fn().mockReturnThis(),
      style: jest.fn().mockReturnThis()
    })),
    selectAll: jest.fn(() => ({
      remove: jest.fn()
    })),
    attr: jest.fn().mockReturnThis(),
    style: jest.fn().mockReturnThis()
  })),
  scaleTime: jest.fn(() => {
    const scale = (value) => value;
    scale.domain = jest.fn().mockReturnValue(scale);
    scale.range = jest.fn().mockReturnValue(scale);
    return scale;
  }),
  scaleLinear: jest.fn(() => {
    const scale = (value) => value;
    scale.domain = jest.fn().mockReturnValue(scale);
    scale.range = jest.fn().mockReturnValue(scale);
    return scale;
  }),
  extent: jest.fn((data, accessor) => {
    if (!data || data.length === 0) return [null, null];
    const values = data.map(accessor);
    return [Math.min(...values), Math.max(...values)];
  }),
  max: jest.fn((data, accessor) => {
    if (!data || data.length === 0) return null;
    return Math.max(...data.map(accessor));
  }),
  brushX: jest.fn(() => ({
    extent: jest.fn().mockReturnThis(),
    on: jest.fn().mockReturnThis()
  }))
}));

describe('TimelineMinimap', () => {
  const mockEvents = [
    {
      date: '2024-01-15',
      importance: 8,
      title: 'Event 1'
    },
    {
      date: '2024-02-20',
      importance: 6,
      title: 'Event 2'
    },
    {
      date: '2024-03-10',
      importance: 9,
      title: 'Event 3'
    }
  ];

  const mockProps = {
    events: mockEvents,
    onBrushChange: jest.fn(),
    selectedRange: null,
    height: 100
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders minimap container', () => {
    render(<TimelineMinimap {...mockProps} />);
    
    const container = screen.getByTestId('timeline-minimap');
    expect(container).toBeInTheDocument();
  });

  test('renders with custom height', () => {
    const customProps = { ...mockProps, height: 150 };
    render(<TimelineMinimap {...customProps} />);
    
    const container = screen.getByTestId('timeline-minimap');
    expect(container).toHaveStyle({ height: '150px' });
  });

  test('handles empty events array', () => {
    const emptyProps = { ...mockProps, events: [] };
    render(<TimelineMinimap {...emptyProps} />);
    
    const container = screen.getByTestId('timeline-minimap');
    expect(container).toBeInTheDocument();
    expect(screen.getByText(/No events to display/i)).toBeInTheDocument();
  });

  test('renders with selected range', () => {
    const propsWithRange = {
      ...mockProps,
      selectedRange: {
        start: new Date('2024-01-01'),
        end: new Date('2024-02-01')
      }
    };
    
    render(<TimelineMinimap {...propsWithRange} />);
    
    const container = screen.getByTestId('timeline-minimap');
    expect(container).toBeInTheDocument();
  });

  test('displays event count', () => {
    render(<TimelineMinimap {...mockProps} />);
    
    expect(screen.getByText(/3 events/i)).toBeInTheDocument();
  });

  test('handles brush interaction', () => {
    render(<TimelineMinimap {...mockProps} />);
    
    const svg = screen.getByTestId('timeline-minimap-svg');
    
    // Simulate brush interaction
    fireEvent.mouseDown(svg, { clientX: 100, clientY: 50 });
    fireEvent.mouseMove(svg, { clientX: 200, clientY: 50 });
    fireEvent.mouseUp(svg, { clientX: 200, clientY: 50 });
    
    // Verify callback was triggered (implementation specific)
    // Note: Actual D3 brush behavior is mocked
  });

  test('handles window resize', () => {
    render(<TimelineMinimap {...mockProps} />);
    
    // Trigger resize event
    global.innerWidth = 800;
    global.dispatchEvent(new Event('resize'));
    
    const container = screen.getByTestId('timeline-minimap');
    expect(container).toBeInTheDocument();
  });

  test('filters events by importance', () => {
    const propsWithImportance = {
      ...mockProps,
      minImportance: 7
    };
    
    render(<TimelineMinimap {...propsWithImportance} />);
    
    // Should show only events with importance >= 7
    expect(screen.getByText(/2 events/i)).toBeInTheDocument();
  });

  test('handles date parsing errors gracefully', () => {
    const invalidEvents = [
      {
        date: 'invalid-date',
        importance: 5,
        title: 'Invalid Event'
      }
    ];
    
    const propsWithInvalid = {
      ...mockProps,
      events: invalidEvents
    };
    
    render(<TimelineMinimap {...propsWithInvalid} />);
    
    const container = screen.getByTestId('timeline-minimap');
    expect(container).toBeInTheDocument();
  });

  test('updates when events prop changes', () => {
    const { rerender } = render(<TimelineMinimap {...mockProps} />);
    
    expect(screen.getByText(/3 events/i)).toBeInTheDocument();
    
    const newEvents = [...mockEvents, {
      date: '2024-04-01',
      importance: 7,
      title: 'Event 4'
    }];
    
    rerender(<TimelineMinimap {...mockProps} events={newEvents} />);
    
    expect(screen.getByText(/4 events/i)).toBeInTheDocument();
  });

  test('clears selection on clear button click', () => {
    const propsWithRange = {
      ...mockProps,
      selectedRange: {
        start: new Date('2024-01-01'),
        end: new Date('2024-02-01')
      }
    };
    
    render(<TimelineMinimap {...propsWithRange} />);
    
    const clearButton = screen.getByRole('button', { name: /clear selection/i });
    fireEvent.click(clearButton);
    
    expect(mockProps.onBrushChange).toHaveBeenCalledWith(null);
  });

  test('displays date range in tooltip', () => {
    render(<TimelineMinimap {...mockProps} />);
    
    const container = screen.getByTestId('timeline-minimap');
    
    // Hover to show tooltip
    fireEvent.mouseEnter(container);
    
    // Check for date range display
    expect(screen.getByText(/Jan 2024 - Mar 2024/i)).toBeInTheDocument();
  });
});