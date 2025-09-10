import React from 'react';
import { render } from '@testing-library/react';

// Custom render function with providers
export function renderWithProviders(ui, options = {}) {
  const AllTheProviders = ({ children }) => {
    return <>{children}</>;
  };

  return render(ui, { wrapper: AllTheProviders, ...options });
}

// Mock event data factory
export function createMockEvent(overrides = {}) {
  return {
    id: Math.random().toString(36).substr(2, 9),
    title: 'Test Event',
    date: '2024-01-15',
    description: 'Test event description',
    importance: 5,
    actors: [],
    tags: [],
    captureLanes: [],
    sources: [],
    notes: '',
    lastModified: new Date().toISOString(),
    ...overrides
  };
}

// Create multiple mock events
export function createMockEvents(count = 5, overrides = {}) {
  return Array.from({ length: count }, (_, i) => 
    createMockEvent({
      title: `Event ${i + 1}`,
      date: `2024-0${(i % 12) + 1}-${String((i % 28) + 1).padStart(2, '0')}`,
      importance: (i % 10) + 1,
      ...overrides
    })
  );
}

// Mock timeline data
export function createMockTimelineData() {
  return {
    events: createMockEvents(10),
    metadata: {
      title: 'Test Timeline',
      description: 'Test timeline description',
      created: '2024-01-01',
      modified: new Date().toISOString(),
      version: '1.0.0'
    },
    statistics: {
      totalEvents: 10,
      dateRange: {
        start: '2024-01-01',
        end: '2024-12-31'
      },
      topActors: ['John Doe', 'Jane Smith'],
      topTags: ['politics', 'technology']
    }
  };
}

// Mock filter state
export function createMockFilterState(overrides = {}) {
  return {
    selectedTags: [],
    selectedActors: [],
    selectedCaptureLanes: [],
    dateRange: { start: null, end: null },
    searchQuery: '',
    sortOrder: 'chronological',
    minImportance: 0,
    ...overrides
  };
}

// Wait for async updates
export async function waitForAsync() {
  return new Promise(resolve => setTimeout(resolve, 0));
}

// Mock fetch response
export function mockFetchResponse(data, status = 200) {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(data),
      text: () => Promise.resolve(JSON.stringify(data)),
      headers: new Headers({
        'content-type': 'application/json'
      })
    })
  );
}

// Mock localStorage
export function mockLocalStorage() {
  const storage = {};
  
  return {
    getItem: jest.fn(key => storage[key] || null),
    setItem: jest.fn((key, value) => {
      storage[key] = value.toString();
    }),
    removeItem: jest.fn(key => {
      delete storage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key]);
    })
  };
}

// Mock D3 selections
export function mockD3Selection() {
  const selection = {
    append: jest.fn().mockReturnThis(),
    attr: jest.fn().mockReturnThis(),
    style: jest.fn().mockReturnThis(),
    text: jest.fn().mockReturnThis(),
    html: jest.fn().mockReturnThis(),
    on: jest.fn().mockReturnThis(),
    selectAll: jest.fn().mockReturnThis(),
    select: jest.fn().mockReturnThis(),
    data: jest.fn().mockReturnThis(),
    enter: jest.fn().mockReturnThis(),
    exit: jest.fn().mockReturnThis(),
    remove: jest.fn().mockReturnThis(),
    merge: jest.fn().mockReturnThis(),
    transition: jest.fn().mockReturnThis(),
    duration: jest.fn().mockReturnThis(),
    call: jest.fn().mockReturnThis(),
    each: jest.fn().mockReturnThis(),
    empty: jest.fn(() => false),
    node: jest.fn(() => document.createElement('div'))
  };
  
  return selection;
}

// Mock window methods
export function setupWindowMocks() {
  // Mock scrollTo
  window.scrollTo = jest.fn();
  
  // Mock matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
  
  // Mock IntersectionObserver
  global.IntersectionObserver = class IntersectionObserver {
    disconnect() {}
    observe() {}
    unobserve() {}
    takeRecords() {
      return [];
    }
  };
  
  // Mock ResizeObserver
  global.ResizeObserver = class ResizeObserver {
    disconnect() {}
    observe() {}
    unobserve() {}
  };
}

// Clean up mocks
export function cleanupMocks() {
  jest.clearAllMocks();
  jest.restoreAllMocks();
  if (global.fetch && global.fetch.mockClear) {
    global.fetch.mockClear();
  }
}

// Test error boundary
export class TestErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Test error boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div>Error occurred in test</div>;
    }

    return this.props.children;
  }
}

// Export all utilities
const testUtils = {
  renderWithProviders,
  createMockEvent,
  createMockEvents,
  createMockTimelineData,
  createMockFilterState,
  waitForAsync,
  mockFetchResponse,
  mockLocalStorage,
  mockD3Selection,
  setupWindowMocks,
  cleanupMocks,
  TestErrorBoundary
};

export default testUtils;