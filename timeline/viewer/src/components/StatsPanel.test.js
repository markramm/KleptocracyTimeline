import React from 'react';
import { render, screen } from '@testing-library/react';
import StatsPanel from './StatsPanel';

describe('StatsPanel', () => {
  const mockEvents = [
    {
      title: 'Event 1',
      date: '2024-01-15',
      importance: 8,
      actors: ['John Doe', 'Jane Smith'],
      tags: ['politics', 'technology'],
      captureLanes: ['regulatory']
    },
    {
      title: 'Event 2',
      date: '2024-02-20',
      importance: 6,
      actors: ['Jane Smith', 'Acme Corp'],
      tags: ['finance', 'technology'],
      captureLanes: ['judicial', 'regulatory']
    },
    {
      title: 'Event 3',
      date: '2024-03-10',
      importance: 9,
      actors: ['John Doe'],
      tags: ['politics'],
      captureLanes: ['legislative']
    },
    {
      title: 'Event 4',
      date: '2023-12-01',
      importance: 7,
      actors: ['Acme Corp'],
      tags: ['finance'],
      captureLanes: ['regulatory']
    }
  ];

  test('renders stats panel with title', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Timeline Statistics/i)).toBeInTheDocument();
  });

  test('displays total event count', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Total Events/i)).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  test('calculates date range correctly', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Date Range/i)).toBeInTheDocument();
    expect(screen.getByText(/Dec 2023 - Mar 2024/i)).toBeInTheDocument();
  });

  test('calculates average importance', () => {
    render(<StatsPanel events={mockEvents} />);
    
    const avgImportance = (8 + 6 + 9 + 7) / 4;
    expect(screen.getByText(/Average Importance/i)).toBeInTheDocument();
    expect(screen.getByText(avgImportance.toFixed(1))).toBeInTheDocument();
  });

  test('counts unique actors', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Unique Actors/i)).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // John Doe, Jane Smith, Acme Corp
  });

  test('counts unique tags', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Unique Tags/i)).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // politics, technology, finance
  });

  test('displays top actors', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Top Actors/i)).toBeInTheDocument();
    expect(screen.getByText(/John Doe.*2/)).toBeInTheDocument();
    expect(screen.getByText(/Jane Smith.*2/)).toBeInTheDocument();
  });

  test('displays top tags', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Top Tags/i)).toBeInTheDocument();
    expect(screen.getByText(/technology.*2/)).toBeInTheDocument();
    expect(screen.getByText(/politics.*2/)).toBeInTheDocument();
  });

  test('displays capture lane distribution', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Capture Lane Distribution/i)).toBeInTheDocument();
    expect(screen.getByText(/regulatory.*3/)).toBeInTheDocument();
    expect(screen.getByText(/judicial.*1/)).toBeInTheDocument();
    expect(screen.getByText(/legislative.*1/)).toBeInTheDocument();
  });

  test('handles empty events array', () => {
    render(<StatsPanel events={[]} />);
    
    expect(screen.getByText(/Total Events/i)).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText(/No events to display/i)).toBeInTheDocument();
  });

  test('handles events without optional fields', () => {
    const minimalEvents = [
      {
        title: 'Minimal Event',
        date: '2024-01-01',
        importance: 5
      }
    ];
    
    render(<StatsPanel events={minimalEvents} />);
    
    expect(screen.getByText(/Total Events/i)).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText(/Unique Actors/i)).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  test('displays events by year', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Events by Year/i)).toBeInTheDocument();
    expect(screen.getByText(/2024:.*3/)).toBeInTheDocument();
    expect(screen.getByText(/2023:.*1/)).toBeInTheDocument();
  });

  test('displays events by month', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Events by Month/i)).toBeInTheDocument();
    // Check for at least one month
    expect(screen.getByText(/January 2024/i)).toBeInTheDocument();
  });

  test('calculates importance distribution', () => {
    render(<StatsPanel events={mockEvents} />);
    
    expect(screen.getByText(/Importance Distribution/i)).toBeInTheDocument();
    expect(screen.getByText(/High.*2/)).toBeInTheDocument(); // importance >= 8
    expect(screen.getByText(/Medium.*2/)).toBeInTheDocument(); // importance 5-7
  });

  test('handles single event correctly', () => {
    const singleEvent = [mockEvents[0]];
    
    render(<StatsPanel events={singleEvent} />);
    
    expect(screen.getByText(/Total Events/i)).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText(/Jan 2024 - Jan 2024/i)).toBeInTheDocument();
  });
});