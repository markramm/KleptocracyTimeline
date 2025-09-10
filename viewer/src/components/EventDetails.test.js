import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import EventDetails from './EventDetails';

describe('EventDetails', () => {
  const mockEvent = {
    title: 'Test Event',
    date: '2024-01-15',
    description: 'This is a test event description',
    importance: 8,
    actors: ['John Doe', 'Jane Smith'],
    tags: ['politics', 'technology'],
    captureLanes: ['regulatory', 'judicial'],
    sources: ['https://example.com/source1', 'https://example.com/source2'],
    notes: 'Additional notes about the event',
    lastModified: '2024-01-14T10:00:00Z'
  };

  const mockProps = {
    event: mockEvent,
    onClose: jest.fn(),
    onNext: jest.fn(),
    onPrevious: jest.fn(),
    hasNext: true,
    hasPrevious: true,
    currentIndex: 1,
    totalEvents: 10
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders event details correctly', () => {
    render(<EventDetails {...mockProps} />);
    
    expect(screen.getByText(mockEvent.title)).toBeInTheDocument();
    expect(screen.getByText(mockEvent.description)).toBeInTheDocument();
    expect(screen.getByText(/January 15, 2024/i)).toBeInTheDocument();
  });

  test('displays importance level', () => {
    render(<EventDetails {...mockProps} />);
    
    expect(screen.getByText(/Importance: 8/i)).toBeInTheDocument();
  });

  test('displays actors list', () => {
    render(<EventDetails {...mockProps} />);
    
    mockEvent.actors.forEach(actor => {
      expect(screen.getByText(actor)).toBeInTheDocument();
    });
  });

  test('displays tags', () => {
    render(<EventDetails {...mockProps} />);
    
    mockEvent.tags.forEach(tag => {
      expect(screen.getByText(tag)).toBeInTheDocument();
    });
  });

  test('displays capture lanes', () => {
    render(<EventDetails {...mockProps} />);
    
    mockEvent.captureLanes.forEach(lane => {
      expect(screen.getByText(lane)).toBeInTheDocument();
    });
  });

  test('displays sources as links', () => {
    render(<EventDetails {...mockProps} />);
    
    const sourceLinks = screen.getAllByRole('link');
    expect(sourceLinks).toHaveLength(mockEvent.sources.length);
    
    sourceLinks.forEach((link, index) => {
      expect(link).toHaveAttribute('href', mockEvent.sources[index]);
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  test('handles close button click', () => {
    render(<EventDetails {...mockProps} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockProps.onClose).toHaveBeenCalledTimes(1);
  });

  test('handles next button click', () => {
    render(<EventDetails {...mockProps} />);
    
    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);
    
    expect(mockProps.onNext).toHaveBeenCalledTimes(1);
  });

  test('handles previous button click', () => {
    render(<EventDetails {...mockProps} />);
    
    const prevButton = screen.getByRole('button', { name: /previous/i });
    fireEvent.click(prevButton);
    
    expect(mockProps.onPrevious).toHaveBeenCalledTimes(1);
  });

  test('disables next button when no next event', () => {
    const propsNoNext = { ...mockProps, hasNext: false };
    render(<EventDetails {...propsNoNext} />);
    
    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();
  });

  test('disables previous button when no previous event', () => {
    const propsNoPrevious = { ...mockProps, hasPrevious: false };
    render(<EventDetails {...propsNoPrevious} />);
    
    const prevButton = screen.getByRole('button', { name: /previous/i });
    expect(prevButton).toBeDisabled();
  });

  test('displays event navigation info', () => {
    render(<EventDetails {...mockProps} />);
    
    expect(screen.getByText(/Event 1 of 10/i)).toBeInTheDocument();
  });

  test('handles missing optional fields', () => {
    const minimalEvent = {
      title: 'Minimal Event',
      date: '2024-01-01',
      description: 'Minimal description',
      importance: 5
    };
    
    const minimalProps = {
      ...mockProps,
      event: minimalEvent
    };
    
    render(<EventDetails {...minimalProps} />);
    
    expect(screen.getByText(minimalEvent.title)).toBeInTheDocument();
    expect(screen.queryByText(/Actors:/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Tags:/i)).not.toBeInTheDocument();
  });

  test('formats date correctly', () => {
    const eventWithDate = {
      ...mockEvent,
      date: '2023-12-25'
    };
    
    render(<EventDetails {...mockProps} event={eventWithDate} />);
    
    expect(screen.getByText(/December 25, 2023/i)).toBeInTheDocument();
  });

  test('handles keyboard navigation', () => {
    render(<EventDetails {...mockProps} />);
    
    fireEvent.keyDown(document, { key: 'ArrowRight', code: 'ArrowRight' });
    expect(mockProps.onNext).toHaveBeenCalled();
    
    fireEvent.keyDown(document, { key: 'ArrowLeft', code: 'ArrowLeft' });
    expect(mockProps.onPrevious).toHaveBeenCalled();
    
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    expect(mockProps.onClose).toHaveBeenCalled();
  });
});