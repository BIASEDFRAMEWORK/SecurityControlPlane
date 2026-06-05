#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    description: str


RULES = [
    Rule(
        "demo-canary-secret",
        re.compile(r"DEMO_SECRET_[A-Za-z0-9][A-Za-z0-9_-]{15,}"),
        "Demo canary secret used to prove the prevention gate blocks a leak.",
    ),
    Rule(
        "aws-access-key-id",
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "AWS access key identifier.",
    ),
    Rule(
        "github-token",
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
        "GitHub token pattern.",
    ),
    Rule(
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "Private key material.",
    ),
    Rule(
        "generic-sensitive-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|client[_-]?secret|credential)\b"
            r"\s*[:=]\s*[\"']?([A-Za-z0-9_./+=-]{24,})"
        ),
        "Long token-like value assigned to a sensitive name.",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan files for secret-like values.")
    parser.add_argument("--paths", nargs="*", help="Explicit files or directories to scan.")
    parser.add_argument("--changed", help="Git revision range to scan, for example main...HEAD.")
    parser.add_argument("--event", help="Path to a GitHub event JSON file.")
    parser.add_argument("--output", default="evidence/secret-scan.json")
    parser.add_argument("--summary", help="Path to GITHUB_STEP_SUMMARY.")
    parser.add_argument("--redact", action="store_true", help="Redact matched values in report excerpts.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], check=True, text=True, capture_output=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def files_from_paths(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists() and path.is_file():
            files.append(path)
    return sorted(set(files))


def changed_files(revision_range: str) -> list[Path]:
    names = run_git(["diff", "--name-only", "--diff-filter=ACMR", revision_range])
    return [Path(name) for name in names if Path(name).exists() and Path(name).is_file()]


def event_files(event_path: str | None) -> tuple[list[Path], dict[str, Any]]:
    if not event_path or not Path(event_path).exists():
        return all_tracked_files(), {}

    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pull_request = event.get("pull_request")
    if pull_request:
        base = pull_request.get("base", {}).get("sha")
        head = pull_request.get("head", {}).get("sha")
        if base and head:
            try:
                return changed_files(f"{base}...{head}"), event
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    return changed_files(f"{base}..HEAD"), event
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
    return all_tracked_files(), event


def all_tracked_files() -> list[Path]:
    try:
        names = run_git(["ls-files"])
        return [Path(name) for name in names if Path(name).exists() and Path(name).is_file()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return files_from_paths(["."])


def selected_files(args: argparse.Namespace) -> tuple[list[Path], str, dict[str, Any]]:
    if args.paths:
        return files_from_paths(args.paths), "explicit paths", {}
    if args.changed:
        return changed_files(args.changed), f"changed files in {args.changed}", {}
    files, event = event_files(args.event)
    return files, "GitHub event changed files" if event.get("pull_request") else "all tracked files", event


def text_lines(path: Path) -> list[str] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > MAX_FILE_BYTES or b"\0" in data:
        return None
    try:
        return data.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1").splitlines()
        except UnicodeDecodeError:
            return None


def secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def excerpt(line: str, match: re.Match[str], redact: bool) -> str:
    value = match.group(match.lastindex or 0)
    clean_line = line.strip()
    if not redact:
        return clean_line
    return clean_line.replace(value, "[REDACTED]")


def scan_file(path: Path, redact: bool) -> list[dict[str, Any]]:
    lines = text_lines(path)
    if lines is None:
        return []

    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        for rule in RULES:
            for match in rule.pattern.finditer(line):
                value = match.group(match.lastindex or 0)
                findings.append(
                    {
                        "file": str(path),
                        "line": line_number,
                        "rule": rule.name,
                        "description": rule.description,
                        "secret_hash": secret_hash(value),
                        "excerpt": excerpt(line, match, redact),
                    }
                )
    return findings


def scan(files: list[Path], redact: bool) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in files:
        normalized = str(path)
        if normalized.startswith(".git/") or normalized.startswith("evidence/"):
            continue
        findings.extend(scan_file(path, redact))
    return findings


def write_report(report: dict[str, Any], output: str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def markdown_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Prevention control",
        "",
        f"- Status: `{report['status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Files scanned: `{report['files_scanned']}`",
        f"- Findings: `{len(report['findings'])}`",
        f"- Generated: `{report['generated_at_utc']}`",
        "",
    ]
    if report["findings"]:
        lines.append("| File | Line | Rule | Excerpt |")
        lines.append("| --- | ---: | --- | --- |")
        for finding in report["findings"]:
            lines.append(
                f"| `{finding['file']}` | {finding['line']} | `{finding['rule']}` | `{finding['excerpt']}` |"
            )
        lines.append("")
        lines.append("The pull request is blocked until the secret-like value is removed from source.")
    else:
        lines.append("No secret-like values were found in the scanned files.")
    lines.append("")
    return "\n".join(lines)


def append_summary(report: dict[str, Any], summary_path: str | None) -> None:
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write(markdown_summary(report))


def main() -> int:
    args = parse_args()
    files, scope, event = selected_files(args)
    findings = scan(files, args.redact)
    report = {
        "generated_at_utc": utc_now(),
        "control": "prevention",
        "status": "failed" if findings else "passed",
        "scope": scope,
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "pull_request": event.get("pull_request", {}).get("number"),
        "files_scanned": len(files),
        "findings": findings,
    }
    write_report(report, args.output)
    append_summary(report, args.summary)
    print(markdown_summary(report))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
