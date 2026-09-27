"""Verify a generated deterministic run against the frozen VAB v0.1 expectation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_PATH = Path(__file__).parent / "results" / "v0.1" / "EXPECTED.json"


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _verify_checksums(directory: Path) -> list[str]:
    checksum_file = directory / "sha256sums.txt"
    if not checksum_file.is_file():
        return ["missing sha256sums.txt"]
    errors: list[str] = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            expected_hash, filename = line.split(maxsplit=1)
        except ValueError:
            errors.append("invalid sha256sums.txt entry: " + line)
            continue
        artifact = directory / filename.strip().lstrip("*")
        if not artifact.is_file():
            errors.append("missing artifact: " + artifact.name)
            continue
        actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append("checksum mismatch: " + artifact.name)
    return errors


def check(observed: Path) -> tuple[bool, list[str]]:
    expected = _load_json(EXPECTED_PATH)
    if not isinstance(expected, dict):
        return False, ["invalid bundled EXPECTED.json"]
    mismatches = _verify_checksums(observed)
    try:
        manifest = _load_json(observed / "manifest.json")
        score_data = _load_json(observed / "scores.json")
    except (OSError, json.JSONDecodeError) as error:
        return False, mismatches + ["cannot read observed result: " + str(error)]
    if not isinstance(manifest, dict) or not isinstance(score_data, dict):
        return False, mismatches + ["observed JSON must be an object"]
    for field in ("vab_version", "participant", "participant_version", "task_suite", "environment_version", "task_hashes"):
        if manifest.get(field) != expected.get(field):
            mismatches.append("manifest mismatch: " + field)
    for field in ("decisions", "scores"):
        if score_data.get(field) != expected.get(field):
            mismatches.append("scores mismatch: " + field)
    return not mismatches, mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", required=True, type=Path, help="Generated result directory to verify.")
    args = parser.parse_args(argv)
    matched, mismatches = check(args.observed)
    print(json.dumps({"expected": str(EXPECTED_PATH), "match_expected": matched, "mismatches": mismatches}, sort_keys=True))
    return 0 if matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
