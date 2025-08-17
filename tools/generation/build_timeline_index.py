#!/usr/bin/env python3
import json, hashlib, sys
from pathlib import Path
import yaml

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main(timeline_dir="timeline_data/events", out_json="timeline_data/events/index.json"):
    tdir = Path(timeline_dir)
    events = []
    files = sorted({*tdir.glob("*.yaml"), *tdir.glob("*.yml")})
    for y in files:
        if y.name == "_SCHEMA.json":
            continue
        try:
            data = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"# WARN: failed to read {y.name}: {e}", file=sys.stderr)
            continue
        if "citations" not in data and "sources" in data:
            data["citations"] = data["sources"]

        tags = data.get("tags")
        if isinstance(tags, list):
            data["tags"] = tags
        elif tags is None:
            data["tags"] = []
        else:
            data["tags"] = [tags]

        data["_file"] = y.name
        data["_id_hash"] = sha256(data.get("id", ""))
        # Convert date objects to strings for JSON serialization
        if "date" in data and hasattr(data["date"], "isoformat"):
            data["date"] = data["date"].isoformat()
        events.append(data)
    Path(out_json).write_text(json.dumps({"events": events}, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out_json} with {len(events)} events")

if __name__ == "__main__":
    main()
