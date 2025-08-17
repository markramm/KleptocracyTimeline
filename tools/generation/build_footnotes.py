#!/usr/bin/env python3
import argparse, sys, json, re
from pathlib import Path
import yaml
from datetime import datetime

REPO = Path(__file__).resolve().parents[2]  # Go up 2 levels from tools/generation
TIMELINE = REPO / "timeline_data" / "events"  # Use events subdirectory

def load_events():
    events = []
    for y in sorted({*TIMELINE.glob("*.yml"), *TIMELINE.glob("*.yaml")}):
        if y.name == "_SCHEMA.json":
            continue
        try:
            d = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
            d["_file"] = y.name
            events.append(d)
        except Exception as e:
            print(f"# WARN: failed to read {y.name}: {e}", file=sys.stderr)
    return events

def within(date, start, end):
    if not date:
        return False
    # Handle both string dates and date/datetime objects
    if isinstance(date, str):
        d = datetime.fromisoformat(date).date()
    elif hasattr(date, 'date'):
        d = date.date()
    else:
        d = date
    # Convert start and end to dates if they're datetimes
    if start and hasattr(start, 'date'):
        start = start.date()
    if end and hasattr(end, 'date'):
        end = end.date()
    return (start is None or d >= start) and (end is None or d <= end)

def main():
    ap = argparse.ArgumentParser(description="Build Google-Docs-style footnotes from timeline events.")
    ap.add_argument("--start", help="Start date YYYY-MM-DD", default=None)
    ap.add_argument("--end", help="End date YYYY-MM-DD", default=None)
    ap.add_argument("--ids", nargs="*", help="Explicit event IDs to include (overrides date range)", default=None)
    ap.add_argument("--tags", nargs="*", help="Filter by tag(s); requires date range or ids", default=None)
    ap.add_argument("--output", "-o", help="Output file (md); default stdout", default=None)
    args = ap.parse_args()

    events = load_events()
    sel = []
    if args.ids:
        wanted = set(args.ids)
        for e in events:
            if e.get("id") in wanted:
                sel.append(e)
    else:
        start = datetime.fromisoformat(args.start) if args.start else None
        end = datetime.fromisoformat(args.end) if args.end else None
        for e in events:
            if within(e.get("date"), start, end):
                sel.append(e)
    if args.tags:
        tags = set([t.lower() for t in args.tags])
        sel = [e for e in sel if tags & set((e.get("tags") or []))]

    # Build footnotes list with deduped citations (preserving order).
    # Each citation may be a plain URL string or an object with a
    # `url` field and optional `archived` mirror.
    seen = set()
    foots = []
    for e in sel:
        for cite in e.get("citations") or []:
            if isinstance(cite, dict):
                url = cite.get("url")
                target = cite.get("archived") or url
            else:
                url = cite
                target = url
            if url and url not in seen:
                seen.add(url)
                foots.append(target)
    md = []
    for i, url in enumerate(foots, 1):
        md.append(f"[{i}] {url}")
    out = "\n".join(md) + ("\n" if md else "")
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)

if __name__ == "__main__":
    main()
