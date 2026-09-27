"""Command-line entry point for the minimal VAB runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import write_procurement_smoke_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m vab")
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run")
    run.add_argument("--agent", required=True)
    run.add_argument("--suite", required=True, choices=["procurement-smoke"])
    run.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Versionable directory for manifest, tasks, traces, scores, failures, and checksums.",
    )
    arguments = parser.parse_args(argv)
    result = write_procurement_smoke_artifacts(arguments.agent, arguments.output_dir)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
