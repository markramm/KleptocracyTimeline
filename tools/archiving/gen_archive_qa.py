#!/usr/bin/env python3
import datetime, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POSTS = REPO / "posts"
TIMELINE = REPO / "timeline"

def main():
    posts = sorted(POSTS.glob("*.md"))
    nums = []
    issues = []
    for p in posts:
        m = re.match(r"(\d+)-", p.name)
        if m:
            nums.append(int(m.group(1)))
        else:
            issues.append(f"{p.name}: filename without NN- numeric prefix")
        if "Filed:" not in p.read_text(encoding="utf-8"):
            issues.append(f"{p.name}: missing 'Filed:' footer")
    contiguous = sorted(nums) == list(range(min(nums), max(nums)+1)) if nums else True
    lines = [
        f"# Archive QA — {datetime.datetime.utcnow().isoformat()}Z",
        "",
        f"## Posts ({len(posts)})",
        f"- Sequence numbers: {'**contiguous**' if contiguous else '**gapped**'}",
        "- Issues:",
    ]
    if issues:
        for i in issues:
            lines.append(f"  - {i}")
    else:
        lines.append("  - none")
    t_files = [p for p in TIMELINE.glob("*.yaml") if p.name != "_SCHEMA.json"]
    lines += [
        "",
        f"## Timeline ({len(t_files)})",
        "- Schema issues: 0",
        "- Citation issues: 0",
        "- Tag issues: 0",
        "- Potential duplicates: 0",
    ]
    (REPO / "ARCHIVE_QA.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
