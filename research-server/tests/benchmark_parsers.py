#!/usr/bin/env python3
"""
Performance benchmarks for event parsers.

Compares JSON vs Markdown parsing performance with various event sizes and complexities.
"""

import sys
import json
import time
import tempfile
from pathlib import Path
from statistics import mean, median, stdev

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from parsers.factory import EventParserFactory


def benchmark_json_parsing(num_events: int, complexity: str = 'simple') -> dict:
    """
    Benchmark JSON event parsing.

    Args:
        num_events: Number of events to parse
        complexity: 'simple', 'medium', or 'complex'

    Returns:
        Dict with timing statistics
    """
    factory = EventParserFactory()
    times = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test events
        for i in range(num_events):
            event_file = tmppath / f'2025-01-01--json-event-{i:04d}.json'

            if complexity == 'simple':
                data = {
                    "id": f"2025-01-01--json-event-{i:04d}",
                    "date": "2025-01-01",
                    "title": f"Event {i}",
                    "summary": "Simple summary"
                }
            elif complexity == 'medium':
                data = {
                    "id": f"2025-01-01--json-event-{i:04d}",
                    "date": "2025-01-01",
                    "title": f"Event {i}",
                    "summary": "Summary paragraph. " * 20,
                    "importance": 7,
                    "tags": ["tag1", "tag2", "tag3"],
                    "actors": ["Actor 1", "Actor 2"]
                }
            else:  # complex
                data = {
                    "id": f"2025-01-01--json-event-{i:04d}",
                    "date": "2025-01-01",
                    "title": f"Event {i}",
                    "summary": "Detailed summary paragraph. " * 50,
                    "importance": 8,
                    "tags": [f"tag{j}" for j in range(10)],
                    "actors": [f"Actor {j}" for j in range(5)],
                    "sources": [
                        {
                            "url": f"https://example.com/{j}",
                            "title": f"Source {j}",
                            "publisher": f"Publisher {j}",
                            "date": "2025-01-01"
                        }
                        for j in range(3)
                    ]
                }

            event_file.write_text(json.dumps(data, indent=2))

        # Benchmark parsing
        for event_file in tmppath.glob('*.json'):
            start = time.perf_counter()
            data = factory.parse_event(event_file)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to milliseconds

    return {
        'format': 'JSON',
        'complexity': complexity,
        'num_events': num_events,
        'total_time_ms': sum(times),
        'mean_time_ms': mean(times),
        'median_time_ms': median(times),
        'stdev_ms': stdev(times) if len(times) > 1 else 0,
        'min_time_ms': min(times),
        'max_time_ms': max(times)
    }


def benchmark_markdown_parsing(num_events: int, complexity: str = 'simple') -> dict:
    """
    Benchmark Markdown event parsing.

    Args:
        num_events: Number of events to parse
        complexity: 'simple', 'medium', or 'complex'

    Returns:
        Dict with timing statistics
    """
    factory = EventParserFactory()
    times = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test events
        for i in range(num_events):
            event_file = tmppath / f'2025-01-01--md-event-{i:04d}.md'

            if complexity == 'simple':
                content = f"""---
id: 2025-01-01--md-event-{i:04d}
date: 2025-01-01
title: Event {i}
---

Simple summary.
"""
            elif complexity == 'medium':
                content = f"""---
id: 2025-01-01--md-event-{i:04d}
date: 2025-01-01
title: Event {i}
importance: 7
tags:
  - tag1
  - tag2
  - tag3
actors:
  - Actor 1
  - Actor 2
---

{'Summary paragraph. ' * 20}
"""
            else:  # complex
                sources_yaml = "\n".join([
                    f"""  - url: https://example.com/{j}
    title: Source {j}
    publisher: Publisher {j}
    date: 2025-01-01"""
                    for j in range(3)
                ])

                content = f"""---
id: 2025-01-01--md-event-{i:04d}
date: 2025-01-01
title: Event {i}
importance: 8
tags:
{chr(10).join([f'  - tag{j}' for j in range(10)])}
actors:
{chr(10).join([f'  - Actor {j}' for j in range(5)])}
sources:
{sources_yaml}
---

{'Detailed summary paragraph. ' * 50}
"""

            event_file.write_text(content)

        # Benchmark parsing
        for event_file in tmppath.glob('*.md'):
            start = time.perf_counter()
            data = factory.parse_event(event_file)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to milliseconds

    return {
        'format': 'Markdown',
        'complexity': complexity,
        'num_events': num_events,
        'total_time_ms': sum(times),
        'mean_time_ms': mean(times),
        'median_time_ms': median(times),
        'stdev_ms': stdev(times) if len(times) > 1 else 0,
        'min_time_ms': min(times),
        'max_time_ms': max(times)
    }


def print_benchmark_results(results: dict):
    """Print benchmark results in a formatted table."""
    print(f"\n{results['format']} Parser - {results['complexity'].upper()} Events ({results['num_events']} events)")
    print("=" * 60)
    print(f"Total Time:    {results['total_time_ms']:8.2f} ms")
    print(f"Mean Time:     {results['mean_time_ms']:8.2f} ms/event")
    print(f"Median Time:   {results['median_time_ms']:8.2f} ms/event")
    print(f"Std Dev:       {results['stdev_ms']:8.2f} ms")
    print(f"Min Time:      {results['min_time_ms']:8.2f} ms")
    print(f"Max Time:      {results['max_time_ms']:8.2f} ms")


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("Event Parser Performance Benchmarks")
    print("=" * 60)

    # Benchmark configurations
    configs = [
        (100, 'simple'),
        (100, 'medium'),
        (100, 'complex'),
        (1000, 'simple'),
        (1000, 'medium'),
    ]

    all_results = []

    for num_events, complexity in configs:
        # Benchmark JSON
        print(f"\nBenchmarking JSON parser: {num_events} {complexity} events...")
        json_results = benchmark_json_parsing(num_events, complexity)
        print_benchmark_results(json_results)
        all_results.append(json_results)

        # Benchmark Markdown
        print(f"\nBenchmarking Markdown parser: {num_events} {complexity} events...")
        md_results = benchmark_markdown_parsing(num_events, complexity)
        print_benchmark_results(md_results)
        all_results.append(md_results)

        # Comparison
        json_mean = json_results['mean_time_ms']
        md_mean = md_results['mean_time_ms']
        speedup = md_mean / json_mean

        print(f"\n{'Markdown is SLOWER' if speedup > 1 else 'Markdown is FASTER'} by {abs(speedup - 1) * 100:.1f}%")
        print(f"JSON: {json_mean:.2f} ms/event")
        print(f"Markdown: {md_mean:.2f} ms/event")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    json_results = [r for r in all_results if r['format'] == 'JSON']
    md_results = [r for r in all_results if r['format'] == 'Markdown']

    json_avg = mean([r['mean_time_ms'] for r in json_results])
    md_avg = mean([r['mean_time_ms'] for r in md_results])

    print(f"\nAverage JSON parsing time:     {json_avg:.2f} ms/event")
    print(f"Average Markdown parsing time: {md_avg:.2f} ms/event")
    print(f"Overall difference:            {abs(md_avg - json_avg):.2f} ms/event")

    if md_avg > json_avg:
        print(f"Markdown is {(md_avg / json_avg - 1) * 100:.1f}% slower than JSON")
    else:
        print(f"Markdown is {(1 - md_avg / json_avg) * 100:.1f}% faster than JSON")

    # Performance verdict
    print("\n" + "=" * 60)
    print("PERFORMANCE VERDICT")
    print("=" * 60)

    if md_avg < json_avg * 2:  # Within 2x is acceptable
        print("✅ Markdown parser performance is ACCEPTABLE")
        print(f"   Markdown adds only {abs(md_avg - json_avg):.2f} ms overhead per event")
    else:
        print("⚠️  Markdown parser performance may need optimization")
        print(f"   Markdown is {(md_avg / json_avg):.1f}x slower than JSON")

    # Throughput
    json_throughput = 1000 / json_avg  # events per second
    md_throughput = 1000 / md_avg

    print(f"\nThroughput:")
    print(f"  JSON:     {json_throughput:.0f} events/second")
    print(f"  Markdown: {md_throughput:.0f} events/second")

    # Real-world projection
    total_events = 1589  # Current timeline size
    json_time = (total_events * json_avg) / 1000
    md_time = (total_events * md_avg) / 1000

    print(f"\nProjected time to parse all {total_events} events:")
    print(f"  JSON:     {json_time:.2f} seconds")
    print(f"  Markdown: {md_time:.2f} seconds")
    print(f"  Difference: {abs(md_time - json_time):.2f} seconds")


if __name__ == '__main__':
    main()
