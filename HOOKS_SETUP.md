# Git Hooks Setup

## Automatic JSON to Markdown Conversion

The pre-commit hook has been updated to automatically convert JSON event files to Markdown format during commits.

### What It Does

When you commit JSON event files, the pre-commit hook will:
1. Validate all staged event files (JSON and Markdown)
2. **Automatically convert any staged JSON files to Markdown**
3. Stage the generated Markdown files in the same commit
4. Validate dates
5. Test API generation

### Benefits

- **No manual conversion needed**: Just create events in JSON format and commit
- **Automatic sync**: JSON and Markdown formats stay in sync
- **Seamless workflow**: One less step in the research pipeline

### How It Works

The hook looks for any staged JSON files in `timeline/data/events/*.json` and:
1. Runs `convert_to_markdown.py` on each JSON file
2. Automatically stages the generated `.md` file
3. Reports how many files were converted

### Example Output

```bash
📝 Step 1.5/4: Auto-converting JSON events to Markdown...
✓ Converted 2025-11-05--example-event.json → 2025-11-05--example-event.md
✅ Auto-converted 1 JSON events to Markdown!
```

### Current Hook Location

The pre-commit hook is located at:
```
.git/hooks/pre-commit
```

This file is automatically used by git and does not need to be committed to the repository.

### Manual Conversion (if needed)

If you need to convert all JSON files manually:
```bash
python3 timeline/scripts/convert_to_markdown.py --all
```

## Hook Update Date

Last updated: November 11, 2025
