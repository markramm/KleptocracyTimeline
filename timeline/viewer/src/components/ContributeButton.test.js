import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ContributeButton from './ContributeButton';

// Mock window.open
global.open = jest.fn();

describe('ContributeButton', () => {
  const mockOnSubmit = jest.fn();
  const defaultProps = {
    onSubmit: mockOnSubmit
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders contribute button', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    expect(contributeButton).toBeInTheDocument();
  });

  test('opens modal when clicked', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    expect(screen.getByText(/Contribute to Timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/Add New Event/i)).toBeInTheDocument();
  });

  test('shows contribution options', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    expect(screen.getByText(/Submit via GitHub/i)).toBeInTheDocument();
    expect(screen.getByText(/Email Submission/i)).toBeInTheDocument();
    expect(screen.getByText(/Manual Form/i)).toBeInTheDocument();
  });

  test('opens GitHub link', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const githubButton = screen.getByRole('button', { name: /Submit via GitHub/i });
    fireEvent.click(githubButton);
    
    expect(global.open).toHaveBeenCalledWith(
      expect.stringContaining('github.com'),
      '_blank'
    );
  });

  test('shows email instructions', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const emailButton = screen.getByRole('button', { name: /Email Submission/i });
    fireEvent.click(emailButton);
    
    expect(screen.getByText(/Send your event details to/i)).toBeInTheDocument();
    expect(screen.getByText(/contribute@example.com/i)).toBeInTheDocument();
  });

  test('shows manual form', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    expect(screen.getByLabelText(/Event Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    // Fill form
    fireEvent.change(screen.getByLabelText(/Event Title/i), {
      target: { value: 'Test Event' }
    });
    fireEvent.change(screen.getByLabelText(/Date/i), {
      target: { value: '2024-01-15' }
    });
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'Test description' }
    });
    fireEvent.change(screen.getByLabelText(/Importance/i), {
      target: { value: '7' }
    });
    
    const submitButton = screen.getByRole('button', { name: /Submit Event/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Test Event',
        date: '2024-01-15',
        description: 'Test description',
        importance: 7,
        actors: [],
        tags: [],
        sources: []
      });
    });
  });

  test('validates required fields', async () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    const submitButton = screen.getByRole('button', { name: /Submit Event/i });
    fireEvent.click(submitButton);
    
    expect(screen.getByText(/Title is required/i)).toBeInTheDocument();
    expect(screen.getByText(/Date is required/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('closes modal on close button', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(screen.queryByText(/Contribute to Timeline/i)).not.toBeInTheDocument();
  });

  test('closes modal on escape key', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(screen.queryByText(/Contribute to Timeline/i)).not.toBeInTheDocument();
  });

  test('handles actors input', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    const actorsInput = screen.getByLabelText(/Actors/i);
    fireEvent.change(actorsInput, {
      target: { value: 'John Doe, Jane Smith' }
    });
    
    expect(actorsInput.value).toBe('John Doe, Jane Smith');
  });

  test('handles tags input', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    const tagsInput = screen.getByLabelText(/Tags/i);
    fireEvent.change(tagsInput, {
      target: { value: 'politics, technology' }
    });
    
    expect(tagsInput.value).toBe('politics, technology');
  });

  test('handles sources input', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    const sourcesInput = screen.getByLabelText(/Sources/i);
    fireEvent.change(sourcesInput, {
      target: { value: 'https://example.com' }
    });
    
    expect(sourcesInput.value).toBe('https://example.com');
  });

  test('resets form after submission', async () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/Event Title/i), {
      target: { value: 'Test Event' }
    });
    fireEvent.change(screen.getByLabelText(/Date/i), {
      target: { value: '2024-01-15' }
    });
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'Test description' }
    });
    
    const submitButton = screen.getByRole('button', { name: /Submit Event/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByLabelText(/Event Title/i).value).toBe('');
    });
    expect(screen.getByLabelText(/Date/i).value).toBe('');
  });

  test('shows success message after submission', async () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/Event Title/i), {
      target: { value: 'Test Event' }
    });
    fireEvent.change(screen.getByLabelText(/Date/i), {
      target: { value: '2024-01-15' }
    });
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'Test description' }
    });
    
    const submitButton = screen.getByRole('button', { name: /Submit Event/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Thank you for your contribution/i)).toBeInTheDocument();
    });
  });

  test('validates importance range', () => {
    render(<ContributeButton {...defaultProps} />);
    
    const contributeButton = screen.getByRole('button', { name: /contribute/i });
    fireEvent.click(contributeButton);
    
    const formButton = screen.getByRole('button', { name: /Manual Form/i });
    fireEvent.click(formButton);
    
    const importanceInput = screen.getByLabelText(/Importance/i);
    fireEvent.change(importanceInput, { target: { value: '11' } });
    
    expect(screen.getByText(/Importance must be between 1 and 10/i)).toBeInTheDocument();
  });
});