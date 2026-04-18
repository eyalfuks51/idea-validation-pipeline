#!/usr/bin/env python3
"""Orchestrator: run analyze + compare for an idea."""

import argparse
import sys
import webbrowser
import os

from analyze import analyze
from compare import load_all_ideas, generate_dashboard


def main():
    parser = argparse.ArgumentParser(description="Run full idea validation pipeline")
    parser.add_argument("--idea", required=True, help="Idea folder name (slug)")
    parser.add_argument("--force", action="store_true", help="Re-run even if analysis exists")
    parser.add_argument("--no-open", action="store_true", help="Don't open dashboard in browser")
    args = parser.parse_args()

    # Step 1: Analyze the idea
    print("=" * 60)
    print("STEP 1: Analyzing idea")
    print("=" * 60)
    analyze(args.idea, force=args.force)

    # Step 2: Generate comparison dashboard
    print("\n" + "=" * 60)
    print("STEP 2: Generating comparison dashboard")
    print("=" * 60)
    ideas = load_all_ideas()
    if ideas:
        dashboard_path = generate_dashboard(ideas)
        print(f"Dashboard: {dashboard_path}")

        if not args.no_open:
            webbrowser.open(f"file://{os.path.abspath(dashboard_path)}")
    else:
        print("No ideas to compare.")

    print("\nPipeline complete!")


if __name__ == "__main__":
    main()
