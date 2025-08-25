# GitHub Integration Features

## 🔗 Features Added for Launch

### 1. Direct GitHub Links for Every Event
Each event in the timeline now has:
- **View Source**: Opens the YAML file on GitHub
- **Edit Event**: Opens GitHub's web editor for the YAML file
- **Report Issue**: Pre-fills an issue template for corrections

### 2. Broken Link Reporting
For each source URL:
- **Report Broken Link** button (⚠️) next to each source
- Automatically opens GitHub issue with:
  - Event ID pre-filled
  - Broken URL documented
  - Option to suggest alternative URL
- **Try Archive** link appears after reporting to check Archive.org

### 3. Submit New Event
Header button that opens GitHub issue template for:
- Event date
- Title and summary
- Importance rating
- Capture lanes selection
- Sources (minimum 2 required)
- Actors and tags

### 4. GitHub Issue Templates
Created three issue templates in `.github/ISSUE_TEMPLATE/`:

#### `broken-link.yml`
- Report inaccessible sources
- Suggest alternative URLs
- Track link rot systematically

#### `new-event.yml`
- Submit new timeline events
- Structured form with validation
- Ensures proper sourcing

#### `event-correction.yml`
- Suggest corrections to existing events
- Provide evidence for changes
- Community fact-checking

## 📍 Where to Find These Features

### In the Timeline Viewer:
1. **Event Details Modal**
   - Footer: "View Source", "Edit Event", "Report Issue" buttons
   - Sources: Report broken link button (⚠️) next to each URL

2. **Main Header**
   - "Submit Event" button (green with + icon)

3. **Automatic GitHub Integration**
   - All links open in new tabs
   - Pre-filled issue forms
   - Direct edit links for contributors

## 🛠️ Technical Implementation

### Files Added:
- `/viewer/src/utils/githubUtils.js` - GitHub URL generation utilities
- `/.github/ISSUE_TEMPLATE/*.yml` - Issue templates

### Files Modified:
- `/viewer/src/components/EventDetails.js` - Added GitHub buttons
- `/viewer/src/components/EventDetails.css` - Styled new buttons
- `/viewer/src/App.js` - Added Submit Event button

## 📝 Usage Examples

### Report a Broken Link:
1. Click on any event to open details
2. Find the broken source
3. Click the ⚠️ button
4. GitHub issue opens with event ID and URL pre-filled
5. Add any alternative URLs you've found

### Submit a New Event:
1. Click "Submit Event" in header
2. Fill out the structured form
3. Provide at least 2 sources
4. Submit for validation

### Suggest a Correction:
1. Open event details
2. Click "Report Issue"
3. Select correction type
4. Provide evidence for the change

## 🎯 Benefits

1. **Lower Contribution Barrier**: No need to understand YAML or Git
2. **Structured Contributions**: Templates ensure quality submissions
3. **Link Rot Management**: Systematic tracking of broken sources
4. **Community Validation**: Easy reporting of errors
5. **Direct Editing**: Experienced users can edit YAML directly
6. **Transparency**: All changes tracked through GitHub

## 🔄 Workflow

1. User reports issue/submits event via GitHub issue
2. Maintainers review and validate
3. Create PR with changes
4. Merge updates
5. GitHub Actions rebuilds site
6. Changes appear on timeline

This creates a complete contribution pipeline from casual users to experienced developers, all through GitHub's interface.