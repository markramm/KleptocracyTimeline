import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DownloadMenu from './DownloadMenu';

// Mock file download functionality
global.URL.createObjectURL = jest.fn(() => 'mocked-url');
global.URL.revokeObjectURL = jest.fn();

describe('DownloadMenu', () => {
  const mockEvents = [
    {
      title: 'Event 1',
      date: '2024-01-15',
      description: 'Description 1',
      importance: 8,
      actors: ['John Doe'],
      tags: ['politics'],
      sources: ['https://example.com']
    },
    {
      title: 'Event 2',
      date: '2024-02-20',
      description: 'Description 2',
      importance: 6,
      actors: ['Jane Smith'],
      tags: ['technology'],
      sources: ['https://example.org']
    }
  ];

  const defaultProps = {
    events: mockEvents,
    filteredEvents: mockEvents
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock createElement for download link
    document.createElement = jest.fn().mockImplementation((tagName) => {
      if (tagName === 'a') {
        return {
          href: '',
          download: '',
          click: jest.fn(),
          style: {}
        };
      }
      return document.createElement.call(document, tagName);
    });
  });

  test('renders download button', () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    expect(downloadButton).toBeInTheDocument();
  });

  test('shows menu when button is clicked', () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    expect(screen.getByText(/CSV/i)).toBeInTheDocument();
    expect(screen.getByText(/JSON/i)).toBeInTheDocument();
    expect(screen.getByText(/Markdown/i)).toBeInTheDocument();
  });

  test('downloads CSV format', async () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const csvOption = screen.getByText(/CSV/i);
    fireEvent.click(csvOption);
    
    await waitFor(() => {
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  test('downloads JSON format', async () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const jsonOption = screen.getByText(/JSON/i);
    fireEvent.click(jsonOption);
    
    await waitFor(() => {
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  test('downloads Markdown format', async () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const markdownOption = screen.getByText(/Markdown/i);
    fireEvent.click(markdownOption);
    
    await waitFor(() => {
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  test('closes menu after download', async () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const csvOption = screen.getByText(/CSV/i);
    fireEvent.click(csvOption);
    
    await waitFor(() => {
      expect(screen.queryByText(/CSV/i)).not.toBeInTheDocument();
    });
  });

  test('closes menu when clicking outside', () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    expect(screen.getByText(/CSV/i)).toBeInTheDocument();
    
    fireEvent.click(document.body);
    
    expect(screen.queryByText(/CSV/i)).not.toBeInTheDocument();
  });

  test('handles empty events array', () => {
    render(<DownloadMenu events={[]} filteredEvents={[]} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    expect(screen.getByText(/No data to download/i)).toBeInTheDocument();
  });

  test('uses filtered events when available', async () => {
    const filteredEvents = [mockEvents[0]];
    render(<DownloadMenu events={mockEvents} filteredEvents={filteredEvents} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const csvOption = screen.getByText(/CSV.*\(1 event\)/i);
    expect(csvOption).toBeInTheDocument();
  });

  test('shows event count in menu options', () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    expect(screen.getByText(/CSV.*\(2 events\)/i)).toBeInTheDocument();
    expect(screen.getByText(/JSON.*\(2 events\)/i)).toBeInTheDocument();
  });

  test('handles download error gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    global.URL.createObjectURL = jest.fn(() => {
      throw new Error('Download failed');
    });
    
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const csvOption = screen.getByText(/CSV/i);
    fireEvent.click(csvOption);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });
    
    consoleSpy.mockRestore();
  });

  test('applies custom className', () => {
    render(<DownloadMenu {...defaultProps} className="custom-download" />);
    
    const downloadContainer = screen.getByTestId('download-menu-container');
    expect(downloadContainer).toHaveClass('custom-download');
  });

  test('shows loading state during download', async () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const csvOption = screen.getByText(/CSV/i);
    fireEvent.click(csvOption);
    
    expect(screen.getByText(/Downloading.../i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText(/Downloading.../i)).not.toBeInTheDocument();
    });
  });

  test('handles keyboard navigation', () => {
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    
    // Open menu with Enter key
    fireEvent.keyDown(downloadButton, { key: 'Enter' });
    expect(screen.getByText(/CSV/i)).toBeInTheDocument();
    
    // Close menu with Escape key
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByText(/CSV/i)).not.toBeInTheDocument();
  });

  test('formats CSV correctly', async () => {
    const createObjectURLSpy = jest.spyOn(global.URL, 'createObjectURL');
    
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const csvOption = screen.getByText(/CSV/i);
    fireEvent.click(csvOption);
    
    await waitFor(() => {
      const blob = createObjectURLSpy.mock.calls[0][0];
      expect(blob.type).toBe('text/csv;charset=utf-8;');
    });
  });

  test('formats JSON correctly', async () => {
    const createObjectURLSpy = jest.spyOn(global.URL, 'createObjectURL');
    
    render(<DownloadMenu {...defaultProps} />);
    
    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);
    
    const jsonOption = screen.getByText(/JSON/i);
    fireEvent.click(jsonOption);
    
    await waitFor(() => {
      const blob = createObjectURLSpy.mock.calls[0][0];
      expect(blob.type).toBe('application/json');
    });
  });
});