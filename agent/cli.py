"""Command-line entrypoint: run the research agent and save a markdown report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent.graph import run_research


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Research a topic and write a cited report.")
    parser.add_argument("topic", help="The topic to research")
    parser.add_argument(
        "-o", "--output", default="report.md", help="Path to write the report (default: report.md)"
    )
    args = parser.parse_args()

    print(f"Researching: {args.topic}", file=sys.stderr)
    report = run_research(args.topic)

    Path(args.output).write_text(report)
    print(f"Report written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
