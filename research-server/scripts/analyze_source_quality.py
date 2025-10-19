#!/usr/bin/env python3
"""
Source Quality Analysis Script

Analyzes source quality across all timeline events, identifies issues,
and provides recommendations for improvement.

Usage:
    python scripts/analyze_source_quality.py                 # Full report
    python scripts/analyze_source_quality.py --priority high # High-priority events only
    python scripts/analyze_source_quality.py --json report.json  # Save to JSON
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_monitor.services.source_quality import SourceQualityClassifier


class SourceQualityAnalyzer:
    """Analyzes source quality across timeline events"""

    def __init__(self, events_dir: Path):
        """
        Initialize analyzer

        Args:
            events_dir: Path to timeline_data/events directory
        """
        self.events_dir = events_dir
        self.classifier = SourceQualityClassifier()
        self.results = {
            'total_events': 0,
            'quality_scores': [],
            'quality_levels': Counter(),
            'tier_counts': defaultdict(int),
            'events_with_issues': [],
            'low_quality_events': [],
            'high_priority_low_quality': [],
            'tier_mix_patterns': defaultdict(int),
        }

    def analyze_all_events(self) -> Dict:
        """
        Analyze all events in directory

        Returns:
            Analysis results dict
        """
        for json_file in sorted(self.events_dir.glob('*.json')):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    event = json.load(f)

                self._analyze_event(event, json_file.stem)

            except Exception as e:
                print(f"Error analyzing {json_file.name}: {e}", file=sys.stderr)
                continue

        return self._generate_report()

    def _analyze_event(self, event: Dict, event_id: str):
        """Analyze a single event"""
        self.results['total_events'] += 1

        classification = self.classifier.classify_event_sources(event)

        # Track statistics
        self.results['quality_scores'].append(classification['quality_score'])
        self.results['quality_levels'][classification['quality_level']] += 1

        self.results['tier_counts'][1] += classification['tier_1_count']
        self.results['tier_counts'][2] += classification['tier_2_count']
        self.results['tier_counts'][3] += classification['tier_3_count']

        # Track tier mix
        tier_mix = (
            classification['tier_1_count'],
            classification['tier_2_count'],
            classification['tier_3_count']
        )
        self.results['tier_mix_patterns'][tier_mix] += 1

        # Track events with issues
        if classification['issues']:
            event_info = {
                'id': event.get('id', event_id),
                'title': event.get('title', 'Unknown'),
                'importance': event.get('importance', 0),
                'date': event.get('date', 'Unknown'),
                'issues': classification['issues'],
                'quality_score': classification['quality_score'],
                'quality_level': classification['quality_level'],
                'tier_1_count': classification['tier_1_count'],
                'tier_2_count': classification['tier_2_count'],
                'tier_3_count': classification['tier_3_count'],
                'sources': classification['sources_by_tier']
            }
            self.results['events_with_issues'].append(event_info)

        # Track low quality events
        if classification['quality_score'] < 5.0:
            self.results['low_quality_events'].append(event_info if 'event_info' in locals() else {
                'id': event.get('id', event_id),
                'title': event.get('title', 'Unknown'),
                'importance': event.get('importance', 0),
                'quality_score': classification['quality_score'],
                'tier_1_count': classification['tier_1_count'],
                'tier_2_count': classification['tier_2_count'],
                'tier_3_count': classification['tier_3_count'],
            })

        # Track high-priority low-quality events
        if classification['quality_score'] < 5.0 and event.get('importance', 0) >= 8:
            self.results['high_priority_low_quality'].append(event_info if 'event_info' in locals() else {
                'id': event.get('id', event_id),
                'title': event.get('title', 'Unknown'),
                'importance': event.get('importance', 0),
                'quality_score': classification['quality_score'],
            })

    def _generate_report(self) -> Dict:
        """Generate analysis report"""
        total_events = self.results['total_events']
        total_sources = sum(self.results['tier_counts'].values())
        avg_score = (
            sum(self.results['quality_scores']) / len(self.results['quality_scores'])
            if self.results['quality_scores'] else 0
        )

        # Sort events by priority
        self.results['high_priority_low_quality'].sort(
            key=lambda x: (x['importance'], -x['quality_score']),
            reverse=True
        )

        report = {
            'summary': {
                'total_events': total_events,
                'total_sources': total_sources,
                'average_quality_score': round(avg_score, 2),
                'events_with_issues': len(self.results['events_with_issues']),
                'events_with_issues_percent': round(
                    len(self.results['events_with_issues']) / total_events * 100, 1
                ) if total_events > 0 else 0,
                'low_quality_events': len(self.results['low_quality_events']),
                'low_quality_percent': round(
                    len(self.results['low_quality_events']) / total_events * 100, 1
                ) if total_events > 0 else 0,
                'high_priority_low_quality': len(self.results['high_priority_low_quality']),
            },
            'quality_distribution': dict(self.results['quality_levels']),
            'tier_distribution': {
                'tier_1': self.results['tier_counts'][1],
                'tier_2': self.results['tier_counts'][2],
                'tier_3': self.results['tier_counts'][3],
                'tier_1_percent': round(
                    self.results['tier_counts'][1] / total_sources * 100, 1
                ) if total_sources > 0 else 0,
                'tier_2_percent': round(
                    self.results['tier_counts'][2] / total_sources * 100, 1
                ) if total_sources > 0 else 0,
                'tier_3_percent': round(
                    self.results['tier_counts'][3] / total_sources * 100, 1
                ) if total_sources > 0 else 0,
            },
            'high_priority_low_quality': self.results['high_priority_low_quality'][:20],
            'classifier_stats': self.classifier.get_statistics(),
        }

        return report

    def print_report(self, report: Dict, priority_filter: str = 'all'):
        """Print human-readable report"""
        summary = report['summary']
        tier_dist = report['tier_distribution']
        quality_dist = report['quality_distribution']

        print("=" * 70)
        print("SOURCE QUALITY ANALYSIS REPORT")
        print("=" * 70)

        print(f"\n{'SUMMARY':^70}")
        print("-" * 70)
        print(f"Total events: {summary['total_events']}")
        print(f"Total sources: {summary['total_sources']}")
        print(f"Average quality score: {summary['average_quality_score']}/10")
        print(f"Events with issues: {summary['events_with_issues']} ({summary['events_with_issues_percent']}%)")
        print(f"Low quality events: {summary['low_quality_events']} ({summary['low_quality_percent']}%)")
        print(f"High-priority low-quality: {summary['high_priority_low_quality']}")

        print(f"\n{'QUALITY DISTRIBUTION':^70}")
        print("-" * 70)
        for level in ['excellent', 'good', 'fair', 'poor']:
            count = quality_dist.get(level, 0)
            percent = (count / summary['total_events'] * 100) if summary['total_events'] > 0 else 0
            print(f"{level.capitalize():10s}: {count:4d} events ({percent:5.1f}%)")

        print(f"\n{'SOURCE TIER DISTRIBUTION':^70}")
        print("-" * 70)
        print(f"Tier 1 (Major news/gov/academic): {tier_dist['tier_1']:4d} ({tier_dist['tier_1_percent']:5.1f}%)")
        print(f"Tier 2 (Established outlets):     {tier_dist['tier_2']:4d} ({tier_dist['tier_2_percent']:5.1f}%)")
        print(f"Tier 3 (Unknown/questionable):    {tier_dist['tier_3']:4d} ({tier_dist['tier_3_percent']:5.1f}%)")

        if priority_filter in ['high', 'all']:
            print(f"\n{'HIGH-PRIORITY LOW-QUALITY EVENTS (Importance ≥ 8)':^70}")
            print("-" * 70)
            print("These events need better sources urgently:\n")

            for event in report['high_priority_low_quality'][:15]:
                print(f"[Importance {event['importance']}, Score {event['quality_score']:.1f}] {event['id']}")
                print(f"  {event.get('title', 'No title')[:65]}")
                print(f"  Sources: Tier-1={event.get('tier_1_count', 0)}, "
                      f"Tier-2={event.get('tier_2_count', 0)}, "
                      f"Tier-3={event.get('tier_3_count', 0)}")
                print()

        print("=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)

        # Generate recommendations
        recommendations = []

        if summary['high_priority_low_quality'] > 0:
            recommendations.append(
                f"1. URGENT: {summary['high_priority_low_quality']} high-importance events "
                f"have low-quality sources. Prioritize improving these."
            )

        if tier_dist['tier_3_percent'] > 30:
            recommendations.append(
                f"2. {tier_dist['tier_3_percent']:.1f}% of sources are tier-3. "
                f"Target: < 30%. Add more tier-1 sources."
            )

        if tier_dist['tier_1_percent'] < 50:
            recommendations.append(
                f"3. Only {tier_dist['tier_1_percent']:.1f}% of sources are tier-1. "
                f"Target: ≥ 50%. Add major news sources."
            )

        if summary['low_quality_percent'] > 20:
            recommendations.append(
                f"4. {summary['low_quality_percent']:.1f}% of events are low quality. "
                f"Target: < 20%. Review and improve."
            )

        if recommendations:
            for rec in recommendations:
                print(f"\n{rec}")
        else:
            print("\n✅ Source quality meets all targets!")

        print("\n" + "=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze timeline event source quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--events-dir',
        type=Path,
        default=Path('timeline_data/events'),
        help='Path to events directory (default: timeline_data/events)'
    )
    parser.add_argument(
        '--priority',
        choices=['all', 'high', 'low'],
        default='all',
        help='Filter by priority (default: all)'
    )
    parser.add_argument(
        '--json',
        type=Path,
        help='Save detailed report to JSON file'
    )

    args = parser.parse_args()

    # Create analyzer
    analyzer = SourceQualityAnalyzer(args.events_dir)

    # Run analysis
    print("Analyzing source quality...")
    report = analyzer.analyze_all_events()

    # Print report
    analyzer.print_report(report, priority_filter=args.priority)

    # Save JSON if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {args.json}")


if __name__ == '__main__':
    main()
