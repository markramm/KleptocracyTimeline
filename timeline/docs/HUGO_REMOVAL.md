# Hugo Removal Decision

**Date**: 2025-10-19
**Decision**: Remove Hugo static site generator in favor of React viewer

## Rationale

- **React provides better interactivity**: Filtering, search, sorting capabilities
- **Hugo created duplicate Markdown files from JSON**: Unnecessary data duplication
- **React uses JSON directly**: Simpler pipeline, no conversion needed
- **Team more familiar with React**: Easier to maintain and enhance
- **Size reduction**: Removing Hugo reduces timeline directory from 759MB to ~50MB

## What Was Removed

The following Hugo-related files and directories were removed:

- `content/events/` - 1,552+ Markdown files (6MB)
- `public/` - Hugo static output (61MB)
- `layouts/` - Hugo templates
- `archetypes/` - Hugo archetypes
- `hugo.toml` - Hugo configuration
- `.hugo_build.lock` - Hugo lock file

**Total removed**: ~67MB of Hugo-specific files

## Backup

**Git branch**: `backup-before-hugo-removal`
**Archive**: `timeline-backup-20251019.tar.gz` (112MB)

To restore if needed:
```bash
git checkout backup-before-hugo-removal
# or
tar -xzf timeline-backup-20251019.tar.gz
```

## Migration Path

If Hugo needed again in the future:

1. Use `scripts/convert_to_markdown.py` to regenerate Markdown from JSON
2. Restore Hugo configuration from backup branch:
   ```bash
   git checkout backup-before-hugo-removal -- hugo.toml layouts/ archetypes/
   ```
3. Generate content:
   ```bash
   python3 scripts/convert_to_markdown.py
   hugo build
   ```

## New Architecture

**Single Source of Truth**: JSON files in `data/events/YYYY/`

**Viewer**: React application in `viewer/`

**Static API**: Generated from JSON via `scripts/generate_static_api.py`

**Benefits**:
- Simpler architecture (one viewer, not two)
- Smaller repository size
- Faster development (no Markdown conversion step)
- More interactive user experience

## Impact Assessment

- ✅ No data loss (JSON files are source of truth)
- ✅ React viewer provides better UX than Hugo
- ✅ Significant size reduction (759MB → ~50MB)
- ✅ Simpler maintenance (one system instead of two)
- ⚠️ Loss of static Markdown files (can regenerate if needed)

## Timeline

- **2025-10-17**: Hugo site generation implemented
- **2025-10-19**: Decision to remove Hugo in favor of React-only
- **2025-10-19**: Hugo files removed (this document created)
