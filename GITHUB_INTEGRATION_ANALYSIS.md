# Kleptocracy Timeline - GitHub Integration Features Documentation

## Executive Summary

The Kleptocracy Timeline viewer includes comprehensive GitHub integration for community contributions. The system provides three main pathways for contributing:

1. **Issue-based contributions** - Submit new events, corrections, and source issues
2. **GitHub editor integration** - Direct edits via GitHub's web interface
3. **Fork & PR workflow** - Advanced contributors can fork and submit pull requests

---

## 1. CONTRIBUTE BUTTON COMPONENT

### Location
- **Component**: `/Users/markr/kleptocracy-timeline/timeline/viewer/src/components/ContributeButton.js`
- **Tests**: `/Users/markr/kleptocracy-timeline/timeline/viewer/src/components/ContributeButton.test.js`
- **Styling**: `/Users/markr/kleptocracy-timeline/timeline/viewer/src/components/ContributeButton.css`

### Feature Overview

The `ContributeButton` component provides a modal interface with three main contribution options:

#### 1.1 Propose New Event
**URL Generation**:
```javascript
const params = new URLSearchParams({
  template: 'new-event.yml',
  title: `[New Event] ${title}`,
  labels: 'new-event,needs-validation'
});
```

**Pre-filled Form Template**:
```
## Event Proposal

**Date:** YYYY-MM-DD
**Title:** [Event title]
**Summary:** [1-2 sentence summary]

## Sources
1. [Source 1 URL]
2. [Source 2 URL]
3. [Source 3 URL]

## Why This Matters
[Explain the significance]

## Tags
[Suggested tags]

## Actors
[Key people/organizations involved]
```

#### 1.2 Submit Correction
**Pre-filled Form Template**:
```
## Correction Request

**Event ID:** ${eventId}
**Event Title:** ${eventTitle}

## What needs correction?
[Describe the issue]

## Correct information
[Provide the correct information]

## Sources
[Provide sources for the correction]
```

**Conditional Display**: Only shown when `eventId` prop is provided (i.e., when viewing a specific event)

#### 1.3 Add Source
**Pre-filled Form Template**:
```
## Additional Source

**Event ID:** ${eventId}
**Event Title:** ${eventTitle}

## New Source
**URL:** [Source URL]
**Title:** [Article/Document Title]
**Date:** [Publication Date]

## Why this source is valuable
[Explain what this source adds]
```

**Conditional Display**: Only shown when `eventId` prop is provided

### Component Props

```javascript
ContributeButton.propTypes = {
  eventId: PropTypes.string,      // ID of current event (optional)
  eventTitle: PropTypes.string     // Title of current event (optional)
}
```

### UI/UX Features

**Button Styling**:
- Gradient background: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Uses lucide-react `Github` icon
- Hover effect: translateY(-1px) with enhanced shadow
- Active state: translateY(0)

**Modal Features**:
- Fixed overlay backdrop with 0.7 opacity
- FadeIn animation (0.2s)
- Modal slides up (0.3s)
- Max-width: 600px, responsive (90% on mobile)
- Max-height: 80vh with scroll support
- Close button (×) in top-right
- Click-outside to close support

**Dark Mode Support**:
```css
@media (prefers-color-scheme: dark) {
  /* Dark theme colors applied */
}
```

### Contribution Guidelines Display

Modal shows embedded guidelines:
- All events must have at least 3 credible sources
- Events must be factual and verifiable
- No speculation or future predictions
- Maintain neutral, factual tone
- Link to full CONTRIBUTING.md

### Fork & PR Option

For experienced contributors:
```javascript
<a href={`${repoUrl}/fork`} target="_blank" rel="noopener noreferrer">
  Fork repository and submit PR
</a>
```

**Button Styling**: GitHub dark theme (#24292e)

---

## 2. GITHUB UTILITIES MODULE

### Location
`/Users/markr/kleptocracy-timeline/timeline/viewer/src/utils/githubUtils.js`

### Current Configuration

**Repository URL**:
```javascript
const GITHUB_REPO = 'https://github.com/markramm/KleptocracyTimeline';
```

**⚠️ CRITICAL ISSUE**: The repository URL in `githubUtils.js` (line 3) points to `markramm/KleptocracyTimeline`, but this needs verification against the actual production repository.

### Function Reference

#### 2.1 URL Generation Functions

**getEventEditUrl(eventId)**
- **Purpose**: Generate GitHub edit URL for an event file
- **Format**: Points to `.yaml` files
- **Returns**: `https://github.com/markramm/KleptocracyTimeline/edit/main/data/events/{eventId}.yaml`
- **Use Case**: Direct editing via GitHub web interface
- **Status**: ⚠️ Points to incorrect path (uses `data/events/` instead of `timeline/data/events/`)

```javascript
export const getEventEditUrl = (eventId) => {
  return `${GITHUB_REPO}/edit/main/data/events/${eventId}.yaml`;
};
```

**getEventViewUrl(eventId)**
- **Purpose**: View event file on GitHub
- **Returns**: `https://github.com/markramm/KleptocracyTimeline/blob/main/data/events/{eventId}.yaml`

```javascript
export const getEventViewUrl = (eventId) => {
  return `${GITHUB_REPO}/blob/main/data/events/${eventId}.yaml`;
};
```

**getEventHistoryUrl(eventId)**
- **Purpose**: View git commit history for an event
- **Returns**: `https://github.com/markramm/KleptocracyTimeline/commits/main/data/events/{eventId}.yaml`

```javascript
export const getEventHistoryUrl = (eventId) => {
  return `${GITHUB_REPO}/commits/main/data/events/${eventId}.yaml`;
};
```

#### 2.2 Issue Creation Functions

**createBrokenLinkIssue(eventId, brokenUrl, errorType)**
- **Purpose**: Create pre-filled GitHub issue for broken sources
- **Parameters**:
  - `eventId`: ID of affected event
  - `brokenUrl`: URL that no longer works
  - `errorType`: Type of error (default: '404 Not Found')
- **Template**: Uses `broken-link.yml` issue template
- **Labels**: `broken-link,sources`
- **Returns**: GitHub issue creation URL with pre-filled body

```javascript
export const createBrokenLinkIssue = (eventId, brokenUrl, errorType = '404 Not Found') => {
  const params = new URLSearchParams({
    template: 'broken-link.yml',
    title: `[Broken Link] ${eventId}`,
    labels: 'broken-link,sources'
  });
  
  const body = `
Event ID: ${eventId}
Broken URL: ${brokenUrl}
Error Type: ${errorType}
  `.trim();
  
  params.append('body', body);
  return `${GITHUB_REPO}/issues/new?${params.toString()}`;
};
```

**createCorrectionIssue(eventId, correctionType)**
- **Purpose**: Create pre-filled GitHub issue for event corrections
- **Parameters**:
  - `eventId`: ID of event to correct
  - `correctionType`: Type of correction (default: 'Other')
- **Template**: Uses `event-correction.yml` issue template
- **Labels**: `correction,needs-review`

```javascript
export const createCorrectionIssue = (eventId, correctionType = 'Other') => {
  const params = new URLSearchParams({
    template: 'event-correction.yml',
    title: `[Correction] ${eventId}`,
    labels: 'correction,needs-review'
  });
  
  return `${GITHUB_REPO}/issues/new?${params.toString()}`;
};
```

**createNewEventIssue(date, title)**
- **Purpose**: Create pre-filled GitHub issue for new event proposal
- **Parameters**:
  - `date`: Event date (optional)
  - `title`: Event title (optional)
- **Template**: Uses `new-event.yml` issue template
- **Labels**: `new-event,needs-validation`

```javascript
export const createNewEventIssue = (date = '', title = '') => {
  const params = new URLSearchParams({
    template: 'new-event.yml',
    title: `[New Event] ${title}`,
    labels: 'new-event,needs-validation'
  });
  
  if (date) {
    const body = `Date: ${date}`;
    params.append('body', body);
  }
  
  return `${GITHUB_REPO}/issues/new?${params.toString()}`;
};
```

#### 2.3 Utility Functions

**getEventIssuesUrl(eventId)**
- **Purpose**: Find all GitHub issues related to a specific event
- **Returns**: GitHub search URL for issues mentioning the event ID
- **Example**: Searches for `is:issue "{eventId}"`

```javascript
export const getEventIssuesUrl = (eventId) => {
  const params = new URLSearchParams({
    q: `is:issue "${eventId}"`
  });
  return `${GITHUB_REPO}/issues?${params.toString()}`;
};
```

**createEventPR(eventId)**
- **Purpose**: Create quick PR for event changes
- **Returns**: GitHub quick PR creation URL

```javascript
export const createEventPR = (eventId) => {
  return `${GITHUB_REPO}/compare/main...main?quick_pull=1&title=Update+event+${eventId}`;
};
```

**checkLinkStatus(url)**
- **Purpose**: Client-side link validation
- **Implementation**: Uses fetch with `no-cors` mode
- **Returns**: Promise resolving to error type or null
- **Limitations**: Cannot check status code in no-cors mode; relies on network errors
- **Note**: Does not actually verify link is alive, only that server exists

```javascript
export const checkLinkStatus = async (url) => {
  try {
    await fetch(url, {
      method: 'HEAD',
      mode: 'no-cors'
    });
    return null;  // Link likely works
  } catch (error) {
    return 'Site No Longer Exists';
  }
};
```

**getArchiveUrl(url, date)**
- **Purpose**: Get Wayback Machine archive URL for a source
- **Parameters**:
  - `url`: Original URL to archive
  - `date`: Event date (optional, for date-specific archive)
- **Returns**: Internet Archive URL
- **Example**: `https://web.archive.org/web/20250115/https://example.com`

```javascript
export const getArchiveUrl = (url, date = '') => {
  const dateParam = date ? date.replace(/-/g, '') : '2';
  return `https://web.archive.org/web/${dateParam}/${url}`;
};
```

#### 2.4 Navigation Functions

**getContributeUrl()**
- **Purpose**: Get link to CONTRIBUTING.md section
- **Returns**: `${GITHUB_REPO}#contributing`

```javascript
export const getContributeUrl = () => {
  return `${GITHUB_REPO}#contributing`;
};
```

**getValidationGuideUrl()**
- **Purpose**: Get link to validation guide
- **Returns**: `${GITHUB_REPO}#validation`

```javascript
export const getValidationGuideUrl = () => {
  return `${GITHUB_REPO}#validation`;
};
```

**openGitHub(url)**
- **Purpose**: Open GitHub URLs in new tab with security
- **Features**: Uses `noopener,noreferrer` for security

```javascript
export const openGitHub = (url) => {
  window.open(url, '_blank', 'noopener,noreferrer');
};
```

#### 2.5 Helper Functions

**formatEventId(date, title)**
- **Purpose**: Generate consistent event ID from date and title
- **Format**: `YYYY-MM-DD--slug-with-hyphens`
- **Rules**:
  - Converts date slashes to hyphens
  - Lowercases title
  - Replaces non-alphanumeric with hyphens
  - Removes leading/trailing hyphens
  - Limits to 50 characters

```javascript
export const formatEventId = (date, title) => {
  const dateStr = date.replace(/\//g, '-');
  const titleStr = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 50);
  
  return `${dateStr}--${titleStr}`;
};
```

---

## 3. GITHUB ISSUE TEMPLATES

### Location
`.github/ISSUE_TEMPLATE/`

### 3.1 New Event Template

**File**: `.github/ISSUE_TEMPLATE/new-event.yml`

**Template Configuration**:
- **Name**: Submit New Event
- **Title Prefix**: `[New Event]`
- **Labels**: `new-event`, `needs-validation`

**Form Fields**:
1. **Event Date** (required)
   - Format: YYYY-MM-DD
   - Example: "2025-01-20"

2. **Event Title** (required)
   - Placeholder: "Supreme Court Rules on XYZ Case"

3. **Event Summary** (required)
   - 2-3 sentence description
   - Should be factual and neutral

4. **Importance Rating** (required)
   - Dropdown: 1-10 scale
   - Options range from "1 - Minor" to "10 - Catastrophic/Foundational"

5. **Capture Lanes** (optional checkboxes)
   - Executive Power & Emergency Authority
   - Judicial Capture & Corruption
   - Financial Corruption & Kleptocracy
   - Foreign Influence Operations
   - Federal Workforce Capture
   - Corporate Capture & Regulatory Breakdown
   - Law Enforcement Weaponization
   - Election System Attack
   - Information & Media Control
   - Constitutional & Democratic Breakdown
   - Epstein Network & Kompromat
   - Immigration & Border Militarization
   - International Democracy Impact

6. **Sources** (required)
   - Minimum 2 credible sources
   - For each: Title, URL, Outlet, Date, Tier

7. **Key Actors** (optional)
   - Comma-separated list
   - People and organizations involved

8. **Tags** (optional)
   - Comma-separated categorization tags

9. **Additional Notes** (optional)
   - Context and connections to other events

### 3.2 Broken Link Template

**File**: `.github/ISSUE_TEMPLATE/broken-link.yml`

**Template Configuration**:
- **Name**: Report Broken Link
- **Title Prefix**: `[Broken Link]`
- **Labels**: `broken-link`, `sources`

**Form Fields**:
1. **Event ID** (required)
   - Format: `yyyy-mm-dd--event-name`

2. **Broken URL** (required)
   - The inaccessible URL

3. **Error Type** (required)
   - Dropdown options:
     - 404 Not Found
     - 403 Forbidden
     - Paywall
     - Site No Longer Exists
     - Content Removed
     - Other

4. **Alternative URL** (optional)
   - Archive link or alternative source

5. **Additional Information** (optional)
   - Context about the broken link

### 3.3 Event Correction Template

**File**: `.github/ISSUE_TEMPLATE/event-correction.yml`

**Template Configuration**:
- **Name**: Suggest Event Correction
- **Title Prefix**: `[Correction]`
- **Labels**: `correction`, `needs-review`

**Form Fields**:
1. **Event ID** (required)
   - Format: `yyyy-mm-dd--event-name`

2. **Type of Correction** (required)
   - Dropdown options:
     - Factual Error
     - Date Correction
     - Missing Sources
     - Better Sources Available
     - Additional Context Needed
     - Importance Rating Wrong
     - Wrong Capture Lane
     - Other

3. **Current Content** (required)
   - Copy the relevant portion being corrected

4. **Suggested Correction** (required)
   - What it should say instead

5. **Evidence/Sources** (required)
   - Supporting documentation:
     - URLs
     - Court documents
     - Official statements

6. **Additional Notes** (optional)
   - Context and explanation

---

## 4. GITHUB PAGES DEPLOYMENT

### Configuration Files

#### 4.1 Package.json Scripts

**File**: `/Users/markr/kleptocracy-timeline/timeline/viewer/package.json`

**Homepage Configuration**:
```json
"homepage": "https://markramm.github.io/KleptocracyTimeline"
```

**Build Scripts**:
```json
"build": "react-scripts build && npm run copy-data",
"build:gh-pages": "PUBLIC_URL=/KleptocracyTimeline react-scripts build && npm run copy-data",
"copy-data": "test -f public/timeline_events.csv && cp public/timeline_events.csv build/ || echo 'CSV not found'; test -f public/timeline_events.json && cp public/timeline_events.json build/ || echo 'JSON not found'"
```

**Key Notes**:
- GitHub Pages build uses `PUBLIC_URL=/KleptocracyTimeline`
- Viewer is deployed to subdirectory path on GitHub Pages
- CSS and JS are automatically deployed to `/KleptocracyTimeline/` path
- CSV and JSON files copied to build directory

#### 4.2 CI/CD Workflow

**File**: `.github/workflows/ci-cd.yml`

**Deployment Triggers**:
- Push to main branch
- Pull requests
- Manual workflow dispatch

**Build Pipeline**:
1. **Validation Job**:
   - Python 3.11 setup
   - Timeline date validation
   - ID/filename consistency checks
   - HTML validation
   - Pytest execution

2. **Build & Deploy Job**:
   - Node.js 18 setup
   - Python 3.11 setup
   - Generate static API data
   - Generate CSV and JSON exports
   - Generate YAML exports
   - Build React viewer with `npm run build:gh-pages`
   - Deploy artifact to GitHub Pages

3. **Summary Job**:
   - Generate build summary with event count

**Deployment Configuration**:
```yaml
permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false
```

**Artifact Upload**:
```yaml
- uses: actions/upload-pages-artifact@v3
  with:
    path: ./viewer/build
```

### API Configuration in Config.js

**File**: `/Users/markr/kleptocracy-timeline/timeline/viewer/src/config.js`

**GitHub Pages Detection**:
```javascript
const isGitHubPages = window.location.hostname.includes('github.io') || 
                     window.location.pathname.includes('/kleptocracy-timeline');
```

**GitHub Raw Data URL**:
```javascript
export const RAW_DATA_URL = `https://raw.githubusercontent.com/${process.env.REACT_APP_REPO || 'yourusername/kleptocracy-timeline'}/main/data`;
```

---

## 5. EDITOR INTEGRATION

### GitHub Web Editor Support

The application supports direct editing through GitHub's web interface:

**Direct Edit URL Pattern**:
```
https://github.com/markramm/KleptocracyTimeline/edit/main/timeline/data/events/YYYY-MM-DD--event-slug.md
```

**⚠️ ISSUE**: Current code generates paths pointing to `data/events/` instead of `timeline/data/events/`

**File Format Support**:
- **Markdown (.md)** - Full GitHub preview support
  - YAML frontmatter editing
  - Live preview of formatted content
  - Easier for manual contributions
  - Better GitHub UX for community

- **JSON (.json)** - Programmatic support
  - Strict structure requirements
  - Automated workflows
  - Full validation support

---

## 6. CONFIGURATION UPDATES NEEDED

### Critical Issues

#### 6.1 Repository URL Mismatch

**Current URL**: `https://github.com/markramm/KleptocracyTimeline`

**Files Affected**:
- `timeline/viewer/src/utils/githubUtils.js` (line 3)
- `timeline/viewer/src/components/ContributeButton.js` (line 8)

**Paths Need Fixing**:
- Current: `data/events/`
- Correct: `timeline/data/events/` (actual structure per repository reorganization)

#### 6.2 File Path Corrections Needed

**For each function in githubUtils.js**:
```javascript
// Current (WRONG)
edit/main/data/events/${eventId}.yaml

// Should be
edit/main/timeline/data/events/${eventId}.md  // (or .json)
```

### Recommended Changes

1. **Update GITHUB_REPO URL**:
   - Change to actual production GitHub repository
   - Update both `githubUtils.js` and `ContributeButton.js`

2. **Fix Event Paths**:
   - Change from `data/events/` to `timeline/data/events/`
   - Update all path-based functions

3. **Support Markdown Format**:
   - URLs should point to `.md` files (per CONTRIBUTING.md)
   - Consider supporting both `.json` and `.md` file extensions

4. **Environment Variables**:
   - Make repository URL configurable via environment variable
   - Add `REACT_APP_GITHUB_REPO` for production builds

---

## 7. DOCUMENTATION STATUS

### Comprehensive Documentation Files

#### Present and Complete:
- ✅ `CONTRIBUTING.md` - Full contribution guide
- ✅ `timeline/docs/EVENT_FORMAT.md` - Event format specification
- ✅ `timeline/docs/SOURCE_QUALITY.md` - Source quality guidelines
- ✅ `timeline/docs/TAG_TAXONOMY.md` - Tag categorization system
- ✅ `.github/ISSUE_TEMPLATE/` - Three issue templates
- ✅ `.github/workflows/ci-cd.yml` - GitHub Actions workflow

#### Missing/Incomplete:
- ❌ GitHub Pages setup documentation
- ❌ Fork and contribution workflow guide
- ❌ Visual guide for GitHub web editor
- ❌ API for getting/fetching events via GitHub

### Documentation Recommendations

1. **Create GITHUB_INTEGRATION.md**:
   - Overview of all contribution methods
   - Step-by-step fork and PR guide
   - GitHub web editor tutorial

2. **Update README.md**:
   - Link to GitHub integration features
   - Quick links to issue templates

3. **Create FORK_AND_PR_GUIDE.md**:
   - Detailed instructions for fork workflow
   - Branch naming conventions
   - PR checklist

---

## 8. INTEGRATION WITH MAIN APPLICATION

### ContributeButton Integration

**Location**: Used in `App.js` header/navigation area

**Props Usage**:
```javascript
// When viewing specific event:
<ContributeButton eventId={selectedEvent.id} eventTitle={selectedEvent.title} />

// In general context:
<ContributeButton />
```

**Features Enabled**:
- All three contribution types when event selected
- New event proposal always available
- Modal prevents accidental navigation

### API Service Integration

The viewer uses `apiService` for data fetching, but GitHub integration is client-side only:

- No backend API calls for GitHub interactions
- All GitHub links open in new tabs
- Direct GitHub URLs (no proxy)

---

## 9. SUMMARY TABLE

| Feature | Status | Location | Configuration |
|---------|--------|----------|---|
| Contribute Button | ✅ Implemented | `components/ContributeButton.js` | Need repo URL update |
| GitHub Utils | ✅ Implemented | `utils/githubUtils.js` | Need path fixes |
| Issue Templates | ✅ Complete | `.github/ISSUE_TEMPLATE/` | Ready to use |
| GitHub Pages Deploy | ✅ Configured | `.github/workflows/ci-cd.yml` | Working |
| Web Editor Support | ✅ Supported | Via direct GitHub URLs | Need path fixes |
| Dark Mode Support | ✅ Implemented | `ContributeButton.css` | Complete |
| Documentation | ⚠️ Partial | Various `.md` files | Needs GitHub integration guide |

---

## 10. CRITICAL CONFIGURATION FOR DEPLOYMENT

### Environment Variables Required

For production deployment, set:
```bash
REACT_APP_GITHUB_REPO=yourusername/kleptocracy-timeline
REACT_APP_GITHUB_PAGES_URL=https://yourusername.github.io/kleptocracy-timeline
```

### GitHub Settings Required

1. **Enable GitHub Pages**:
   - Source: GitHub Actions
   - Branch: main (via workflow)

2. **Issue Templates**:
   - Already configured in `.github/ISSUE_TEMPLATE/`
   - Templates use form-based submission

3. **Branch Protection**:
   - Recommended: Require PR reviews before merge
   - Enforce status checks from CI/CD workflow

---

## Files and Snippets Reference

### Key Code Snippets

**ContributeButton Modal Trigger**:
```javascript
<button 
  className="contribute-button"
  onClick={() => setShowModal(true)}
  title="Contribute to timeline"
>
  <Github size={16} />
  <span>Contribute</span>
</button>
```

**Issue URL Creation Example**:
```javascript
const issueUrl = createNewEventIssue('2025-01-15', 'My New Event');
window.open(issueUrl, '_blank');
// Opens: https://github.com/markramm/KleptocracyTimeline/issues/new?
//        template=new-event.yml&title=[New Event] My New Event&...
```

**Event ID Formatting**:
```javascript
const id = formatEventId('2025/01/15', 'Supreme Court Ruling');
// Returns: '2025-01-15--supreme-court-ruling'
```

