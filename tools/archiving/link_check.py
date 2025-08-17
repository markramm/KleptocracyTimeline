#!/usr/bin/env python3
import argparse, sys, json
from pathlib import Path
import yaml
import urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = Path(__file__).resolve().parents[1]
TIMELINE = REPO / "timeline_data"
STATUS_LOG = REPO / "link_status.json"

def check_url(url, timeout=12):
    """Attempt to resolve ``url`` and return ``(status, redirect)``.

    Some publishers block ``HEAD`` requests or require a user agent. We
    start with ``HEAD`` and fall back to ``GET`` for common block codes.
    """
    ua = {"User-Agent": "Mozilla/5.0 (compatible; LinkChecker/1.0)"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=ua)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.getheader("Location")
        except urllib.error.HTTPError as e:
            # Retry with GET if HEAD is rejected.
            if method == "HEAD" and e.code in (401, 403, 405):
                continue
            return e.code, None
        except Exception as e:
            if method == "HEAD":
                continue
            return None, str(e)
    return None, None

def main():
    ap = argparse.ArgumentParser(description="Check timeline citation URLs for reachability.")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of files checked")
    ap.add_argument("--csv", default=None, help="Optional CSV output file")
    ap.add_argument("--workers", type=int, default=20, help="Parallel link checks")
    ap.add_argument("--log", type=Path, default=STATUS_LOG, help="Status cache file")
    ap.add_argument("--max-age", type=int, default=30, help="Days before rechecking a link")
    args = ap.parse_args()
    files = sorted(
        p for p in { *TIMELINE.glob("*.yaml"), *TIMELINE.glob("*.yml") }
        if p.name != "_SCHEMA.json"
    )
    if args.limit:
        files = files[:args.limit]
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=args.max_age)
    log = {}
    if args.log.exists():
        try:
            log = json.loads(args.log.read_text(encoding="utf-8"))
        except Exception:
            pass
    tasks = []
    results = []
    for y in files:
        d = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
        for cite in d.get("citations") or []:
            if isinstance(cite, dict):
                url = cite.get("url")
                target = cite.get("archived") or url
            else:
                url = target = cite
            rec = log.get(url)
            if rec and rec.get("target") == target:
                try:
                    ts = datetime.fromisoformat(rec.get("checked_at"))
                except Exception:
                    ts = None
                if ts and ts > cutoff:
                    results.append({"file": y.name, "url": url, "status": rec.get("status"), "info": rec.get("info")})
                    print(json.dumps(results[-1]))
                    continue
            idx = len(results)
            results.append(None)
            tasks.append((idx, y.name, url, target))

    if tasks:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(check_url, t): (i, f, u, t) for i, f, u, t in tasks}
            for fut in as_completed(futs):
                i, f, u, t = futs[fut]
                status, info = fut.result()
                results[i] = {"file": f, "url": u, "status": status, "info": info}
                log[u] = {"target": t, "status": status, "info": info, "checked_at": now.isoformat()}
                print(json.dumps(results[i]))

    if None in results:
        for i, r in enumerate(results):
            if r is None:
                results[i] = {"file": tasks[i][1], "url": tasks[i][2], "status": None, "info": None}
    if args.csv:
        import csv

        with open(args.csv, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=["file", "url", "status", "info"])
            writer.writeheader()
            writer.writerows(results)
    if args.log:
        args.log.write_text(json.dumps(log, indent=2, sort_keys=True), encoding="utf-8")
    # summary to stderr
    ok = sum(1 for r in results if r["status"] and 200 <= r["status"] < 400)
    bad = sum(1 for r in results if r["status"] and r["status"] >= 400)
    unk = sum(1 for r in results if r["status"] is None)
    print(f"# OK={ok} BAD={bad} UNKNOWN={unk}", file=sys.stderr)

if __name__ == "__main__":
    main()
