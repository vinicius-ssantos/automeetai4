#!/usr/bin/env python
"""
Script to run tests with coverage reporting.

Este script executa os testes do projeto e gera relatórios de cobertura
de código em vários formatos.
"""

import os
import sys
import subprocess
import argparse


def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run tests with coverage reporting")
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--xml", action="store_true", help="Generate XML coverage report"
    )
    parser.add_argument(
        "--json", action="store_true", help="Generate JSON coverage report"
    )
    parser.add_argument(
        "--output-dir", default="coverage_reports", help="Directory for coverage reports"
    )
    parser.add_argument(
        "--min-coverage", type=float, default=70.0, help="Minimum required coverage percentage"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "test_path", nargs="?", default="tests", help="Path to test directory or file"
    )
    return parser.parse_args()


def run_tests_with_coverage(args):
    """
    Run tests with coverage reporting.
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Build the pytest command
    cmd = [
        "python", "-m", "pytest",
        args.test_path,
        "--cov=src",
        f"--cov-report=term-missing",
        f"--cov-fail-under={args.min_coverage}"
    ]
    
    # Add report formats
    if args.html:
        cmd.append(f"--cov-report=html:{os.path.join(args.output_dir, 'html')}")
    if args.xml:
        cmd.append(f"--cov-report=xml:{os.path.join(args.output_dir, 'coverage.xml')}")
    if args.json:
        cmd.append(f"--cov-report=json:{os.path.join(args.output_dir, 'coverage.json')}")
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Run the command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode


def main():
    """
    Main entry point.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()
    return run_tests_with_coverage(args)


if __name__ == "__main__":
    sys.exit(main())