#!/usr/bin/env python3
"""
Main timeline management script.

This is the primary entry point for all timeline operations:
- validate: Check event files for errors
- archive: Archive sources to Archive.org
- generate: Generate outputs (index, API, citations)
- qa: Run quality assurance checks
- serve: Start the development server
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import log_info, log_error, log_success, print_header


def run_validate(args):
    """Run validation."""
    cmd = [sys.executable, "scripts/validate.py"]
    if args.verbose:
        cmd.append("--verbose")
    if args.fix:
        cmd.append("--fix")
    return subprocess.call(cmd)


def run_archive(args):
    """Run archiving."""
    cmd = [sys.executable, "scripts/archive.py"]
    if args.check_coverage:
        cmd.append("--check-coverage")
    elif args.retry_failed:
        cmd.append("--retry-failed")
    if args.rate:
        cmd.extend(["--rate", str(args.rate)])
    return subprocess.call(cmd)


def run_generate(args):
    """Run generation."""
    cmd = [sys.executable, "scripts/generate.py"]
    if args.all:
        cmd.append("--all")
    else:
        if args.index:
            cmd.append("--index")
        if args.api:
            cmd.append("--api")
        if args.citations:
            cmd.extend(["--citations", args.citations])
        if args.stats:
            cmd.append("--stats")
    return subprocess.call(cmd)


def run_serve(args):
    """Start development server."""
    print_header("STARTING DEVELOPMENT SERVER")
    
    # Start API server
    log_info("Starting API server on http://localhost:5173...")
    api_process = subprocess.Popen(
        [sys.executable, "api/enhanced_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Start React app if requested
        if args.viewer:
            log_info("Starting React viewer on http://localhost:3000...")
            viewer_process = subprocess.Popen(
                ["npm", "start"],
                cwd="viewer",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            log_success("Both servers started! Press Ctrl+C to stop.")
            viewer_process.wait()
        else:
            log_success("API server started! Visit http://localhost:5173")
            log_info("Use --viewer flag to also start the React app")
            api_process.wait()
            
    except KeyboardInterrupt:
        log_info("Shutting down servers...")
        api_process.terminate()
        if args.viewer and 'viewer_process' in locals():
            viewer_process.terminate()
    
    return 0


def run_qa(args):
    """Run quality assurance checks."""
    print_header("QUALITY ASSURANCE")
    
    # Run validation
    log_info("Running validation checks...")
    result = subprocess.call([sys.executable, "scripts/validate.py", "--verbose"])
    if result != 0:
        log_error("Validation failed")
        return result
    
    # Check archive coverage
    log_info("\nChecking archive coverage...")
    result = subprocess.call([sys.executable, "scripts/archive.py", "--check-coverage"])
    if result != 0:
        log_error("Archive check failed")
        return result
    
    log_success("\nQuality assurance complete!")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='timeline',
        description='Timeline management tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  validate    Check event files for errors
  archive     Archive sources to Archive.org  
  generate    Generate outputs (index, API, citations)
  qa          Run quality assurance checks
  serve       Start development server

Examples:
  %(prog)s validate --verbose        # Validate with warnings
  %(prog)s archive --check-coverage  # Check archive status
  %(prog)s generate --all            # Generate all outputs
  %(prog)s qa                        # Run all QA checks
  %(prog)s serve --viewer            # Start both servers
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate event files')
    validate_parser.add_argument('-v', '--verbose', action='store_true', help='Show warnings')
    validate_parser.add_argument('--fix', action='store_true', help='Auto-fix simple issues')
    
    # Archive command
    archive_parser = subparsers.add_parser('archive', help='Archive sources')
    archive_parser.add_argument('--check-coverage', action='store_true', help='Check coverage only')
    archive_parser.add_argument('--retry-failed', action='store_true', help='Retry failed URLs')
    archive_parser.add_argument('--rate', type=int, help='Requests per minute (max 15)')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate outputs')
    generate_parser.add_argument('--all', action='store_true', help='Generate all outputs')
    generate_parser.add_argument('--index', action='store_true', help='Generate index')
    generate_parser.add_argument('--api', action='store_true', help='Generate API files')
    generate_parser.add_argument('--citations', choices=['md', 'json', 'html'], help='Generate citations')
    generate_parser.add_argument('--stats', action='store_true', help='Generate statistics')
    
    # QA command
    qa_parser = subparsers.add_parser('qa', help='Run quality assurance')
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start development server')
    serve_parser.add_argument('--viewer', action='store_true', help='Also start React viewer')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run the appropriate command
    if args.command == 'validate':
        return run_validate(args)
    elif args.command == 'archive':
        return run_archive(args)
    elif args.command == 'generate':
        return run_generate(args)
    elif args.command == 'qa':
        return run_qa(args)
    elif args.command == 'serve':
        return run_serve(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())