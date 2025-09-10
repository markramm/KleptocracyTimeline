import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SearchBar from './SearchBar';

describe('SearchBar', () => {
  const mockOnSearch = jest.fn();
  const defaultProps = {
    onSearch: mockOnSearch,
    placeholder: 'Search events...'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders search input with placeholder', () => {
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveAttribute('type', 'text');
  });

  test('renders search icon', () => {
    render(<SearchBar {...defaultProps} />);
    
    const searchIcon = screen.getByTestId('search-icon');
    expect(searchIcon).toBeInTheDocument();
  });

  test('handles input change', () => {
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    
    expect(searchInput.value).toBe('test query');
  });

  test('calls onSearch with debounce', async () => {
    jest.useFakeTimers();
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    expect(mockOnSearch).not.toHaveBeenCalled();
    
    jest.advanceTimersByTime(300);
    
    expect(mockOnSearch).toHaveBeenCalledWith('test');
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
    
    jest.useRealTimers();
  });

  test('debounces multiple rapid inputs', async () => {
    jest.useFakeTimers();
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    
    fireEvent.change(searchInput, { target: { value: 't' } });
    jest.advanceTimersByTime(100);
    
    fireEvent.change(searchInput, { target: { value: 'te' } });
    jest.advanceTimersByTime(100);
    
    fireEvent.change(searchInput, { target: { value: 'test' } });
    jest.advanceTimersByTime(300);
    
    expect(mockOnSearch).toHaveBeenCalledWith('test');
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
    
    jest.useRealTimers();
  });

  test('handles empty search', () => {
    jest.useFakeTimers();
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    fireEvent.change(searchInput, { target: { value: '' } });
    
    jest.advanceTimersByTime(300);
    
    expect(mockOnSearch).toHaveBeenCalledWith('');
    
    jest.useRealTimers();
  });

  test('handles clear button when present', () => {
    render(<SearchBar {...defaultProps} showClear={true} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    
    const clearButton = screen.getByRole('button', { name: /clear/i });
    fireEvent.click(clearButton);
    
    expect(searchInput.value).toBe('');
    expect(mockOnSearch).toHaveBeenCalledWith('');
  });

  test('handles form submission', () => {
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    const form = searchInput.closest('form');
    
    fireEvent.change(searchInput, { target: { value: 'submit test' } });
    fireEvent.submit(form);
    
    expect(mockOnSearch).toHaveBeenCalledWith('submit test');
  });

  test('handles keyboard shortcuts', () => {
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    
    // Test Escape key clears input
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.keyDown(searchInput, { key: 'Escape' });
    
    expect(searchInput.value).toBe('');
  });

  test('focuses on keyboard shortcut', () => {
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    
    // Simulate Ctrl+K or Cmd+K
    fireEvent.keyDown(document, { key: 'k', ctrlKey: true });
    
    expect(document.activeElement).toBe(searchInput);
  });

  test('trims whitespace from search query', () => {
    jest.useFakeTimers();
    render(<SearchBar {...defaultProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    fireEvent.change(searchInput, { target: { value: '  test query  ' } });
    
    jest.advanceTimersByTime(300);
    
    expect(mockOnSearch).toHaveBeenCalledWith('test query');
    
    jest.useRealTimers();
  });

  test('renders with custom placeholder', () => {
    render(<SearchBar {...defaultProps} placeholder="Custom search..." />);
    
    expect(screen.getByPlaceholderText('Custom search...')).toBeInTheDocument();
  });

  test('applies custom className', () => {
    render(<SearchBar {...defaultProps} className="custom-search" />);
    
    const searchContainer = screen.getByTestId('search-container');
    expect(searchContainer).toHaveClass('custom-search');
  });

  test('handles disabled state', () => {
    render(<SearchBar {...defaultProps} disabled={true} />);
    
    const searchInput = screen.getByPlaceholderText('Search events...');
    expect(searchInput).toBeDisabled();
    
    fireEvent.change(searchInput, { target: { value: 'test' } });
    expect(mockOnSearch).not.toHaveBeenCalled();
  });

  test('shows loading indicator when searching', () => {
    render(<SearchBar {...defaultProps} isLoading={true} />);
    
    expect(screen.getByTestId('search-loading')).toBeInTheDocument();
  });
});