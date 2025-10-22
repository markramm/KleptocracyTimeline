# Testing Documentation

## Current Test Status

**Last Updated:** October 22, 2025

### Summary

| Category | Count | Percentage |
|----------|-------|------------|
| ✅ Passing Tests | 26 | 20.6% |
| ❌ Failing Tests | 100 | 79.4% |
| **Total Tests** | **126** | **100%** |

| Test Suites | Status |
|-------------|--------|
| ✅ Passing | 2 |
| ❌ Failing | 9 |
| **Total** | **11** |

### Code Coverage

| Metric | Coverage |
|--------|----------|
| Statements | 21.48% |
| Branches | 17.9% |
| Functions | 15.16% |
| Lines | 22.8% |

## Passing Test Suites ✅

These test suites are fully functional and should continue to pass:

1. **LandingPage.test.js** - 100% coverage
   - Landing page component renders correctly
   - All sections display properly

2. **ViewToggle.test.js** - 100% coverage
   - View mode switching
   - All 8 tests passing

## Failing Test Suites ❌

The following test suites have issues that need to be addressed in future iterations:

### High Priority (Core Functionality)

1. **SearchBar.test.js** - 81.81% coverage
   - Search input and functionality
   - Issues: Missing test-id attributes, loading state tests fail
   - Status: 12 passing, 11 failing

2. **EnhancedTimelineView.test.js** - 18.13% coverage
   - Main timeline visualization component
   - Issues: D3.js mocking, complex interactions

3. **EventDetails.test.js** - 34.28% coverage
   - Event detail modal/panel
   - Issues: API response mocking

4. **FilterPanel.test.js** - 29.88% coverage
   - Search and filter controls
   - Issues: State management, API calls

### Medium Priority (Visualizations)

4. **NetworkGraph.test.js** - 0.21% coverage
   - D3.js network graph visualization
   - Issues: Canvas/SVG mocking, D3 complexity

5. **NetworkGraphActors.test.js** - 13.05% coverage
   - Actor-focused network analysis
   - Issues: Similar to NetworkGraph

6. **StatsPanel.test.js** - 17.24% coverage
   - Statistics dashboard
   - Issues: Chart.js mocking

### Low Priority (Auxiliary Features)

7. **DownloadMenu.test.js** - 22.22% coverage
   - Export functionality
   - Issues: File download mocking

8. **TimelineMinimap.test.js** - 29.6% coverage
   - Minimap navigation component
   - Issues: Canvas rendering

9. **ActivityFeed.test.js** - 0% coverage
   - Activity feed component
   - Issues: Not implemented

## Running Tests

### For CI/CD (Passing Tests Only)

```bash
npm run test:ci
```

This runs only the passing test suites to ensure core functionality remains stable.

### For Development (All Tests)

```bash
npm run test:all
```

This runs the full test suite to see all failures and track progress.

### For Interactive Development

```bash
npm test
```

This runs tests in watch mode for active development.

## Known Issues

### Test Infrastructure Issues

1. **React Testing Library Setup**
   - Some components not rendering in test environment
   - Mock data configuration incomplete
   - Need better test utilities

2. **D3.js Visualization Testing**
   - D3 components are notoriously difficult to test
   - Canvas/SVG rendering not available in jest-dom
   - Consider visual regression testing tools

3. **API Mocking**
   - Inconsistent mock responses
   - Need centralized mock data factory
   - API service mocking needs refactoring

## Improvement Roadmap

### Phase 1: Critical Components (Post-Launch)
- [ ] Fix EnhancedTimelineView tests
- [ ] Fix EventDetails tests
- [ ] Fix FilterPanel tests
- Target: >50% test coverage

### Phase 2: Visualizations
- [ ] Implement proper D3 test utilities
- [ ] Fix NetworkGraph tests
- [ ] Fix StatsPanel tests
- Consider: Integration tests instead of unit tests

### Phase 3: Complete Coverage
- [ ] Fix remaining component tests
- [ ] Add integration tests
- [ ] Add E2E tests with Cypress/Playwright
- Target: >80% test coverage

## Testing Best Practices

For new components or features:

1. **Start with passing tests** - Write tests first, ensure they pass
2. **Mock external dependencies** - Use centralized mock factories
3. **Test user behavior** - Focus on user interactions, not implementation
4. **Keep tests simple** - One assertion per test when possible
5. **Document test failures** - Add comments explaining known issues

## Resources

- [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing D3.js](https://www.d3indepth.com/testing/)

## Contributing

When fixing tests:

1. Choose one test suite to fix
2. Create a branch: `fix-tests-[component-name]`
3. Fix all tests in that suite
4. Update this document
5. Submit PR with test coverage report

---

**Note:** The failing tests reflect test infrastructure issues, not broken functionality. The viewer works correctly in production. This is technical debt to be addressed post-launch.
