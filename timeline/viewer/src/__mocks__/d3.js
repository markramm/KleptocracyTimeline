// Mock d3 for testing
const mockSelect = jest.fn();
const mockSelectAll = jest.fn();
const mockAppend = jest.fn();
const mockAttr = jest.fn();
const mockStyle = jest.fn();
const mockText = jest.fn();
const mockOn = jest.fn();
const mockCall = jest.fn();
const mockRemove = jest.fn();
const mockData = jest.fn();
const mockEnter = jest.fn();
const mockExit = jest.fn();

// Create chainable mock object
const chainableMock = {
  selectAll: jest.fn(),
  append: jest.fn(),
  attr: jest.fn(),
  style: jest.fn(),
  call: jest.fn(),
  on: jest.fn(),
  remove: jest.fn(),
  data: jest.fn(),
  enter: jest.fn(),
  exit: jest.fn(),
  text: jest.fn(),
};

// Make all methods return the chainable object
Object.keys(chainableMock).forEach(key => {
  chainableMock[key].mockReturnValue(chainableMock);
});

// Chain mock returns
mockSelect.mockReturnValue(chainableMock);
mockSelectAll.mockReturnValue(chainableMock);
mockData.mockReturnValue(chainableMock);
mockEnter.mockReturnValue(chainableMock);
mockExit.mockReturnValue(chainableMock);
mockAppend.mockReturnValue(chainableMock);

mockData.mockReturnValue({
  enter: mockEnter,
  exit: mockExit,
});

mockEnter.mockReturnValue({
  append: mockAppend,
});

mockExit.mockReturnValue({
  remove: mockRemove,
});

mockAppend.mockReturnValue({
  attr: mockAttr,
  style: mockStyle,
  text: mockText,
  on: mockOn,
  call: mockCall,
  append: mockAppend,
});

mockAttr.mockReturnThis();
mockStyle.mockReturnThis();
mockText.mockReturnThis();
mockOn.mockReturnThis();
mockCall.mockReturnThis();

export const select = mockSelect;

export const scaleLinear = jest.fn(() => ({
  domain: jest.fn().mockReturnThis(),
  range: jest.fn().mockReturnThis(),
}));

export const scaleOrdinal = jest.fn(() => ({
  domain: jest.fn().mockReturnThis(),
  range: jest.fn().mockReturnThis(),
}));

export const scaleSequential = jest.fn(() => ({
  domain: jest.fn().mockReturnThis(),
}));

export const scaleSqrt = jest.fn(() => ({
  domain: jest.fn().mockReturnThis(),
  range: jest.fn().mockReturnThis(),
}));

export const forceSimulation = jest.fn(() => ({
  force: jest.fn().mockReturnThis(),
  on: jest.fn().mockReturnThis(),
  alphaTarget: jest.fn().mockReturnThis(),
  restart: jest.fn().mockReturnThis(),
}));

export const forceLink = jest.fn(() => ({
  id: jest.fn().mockReturnThis(),
  distance: jest.fn().mockReturnThis(),
  strength: jest.fn().mockReturnThis(),
}));

export const forceManyBody = jest.fn(() => ({
  strength: jest.fn().mockReturnThis(),
}));

export const forceCenter = jest.fn(() => ({
  strength: jest.fn().mockReturnThis(),
}));

export const forceCollide = jest.fn(() => ({
  radius: jest.fn().mockReturnThis(),
}));

export const zoom = jest.fn(() => ({
  scaleExtent: jest.fn().mockReturnThis(),
  on: jest.fn().mockReturnThis(),
}));

export const drag = jest.fn(() => ({
  on: jest.fn().mockReturnThis(),
}));

export const max = jest.fn();
export const min = jest.fn();
export const interpolateReds = jest.fn();
export const schemeCategory10 = [];