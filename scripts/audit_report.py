#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHECKS = [
    ("Explainability - PR security intent", "explainability_result", "explainability"),
    ("Prevention - secret scan", "prevention_result", "prevention"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate audit evidence for the security control workflow.")
    parser.add_argument("--explainability-result", required=True)
    parser.add_argument("--prevention-result", required=True)
    parser.add_argument("--output-dir", default="evidence")
    parser.add_argument("--summary", help="Path to GITHUB_STEP_SUMMARY.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_event() -> dict[str, Any]:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        return json.loads(Path(event_path).read_text(encoding="utf-8"))
    return {}


def git_changed_files(event: dict[str, Any]) -> list[str]:
    pull_request = event.get("pull_request")
    if pull_request:
        base = pull_request.get("base", {}).get("sha")
        head = pull_request.get("head", {}).get("sha")
        if base and head:
            for revision_range in (f"{base}...{head}", f"{base}..HEAD"):
                try:
                    result = subprocess.run(
                        ["git", "diff", "--name-only", "--diff-filter=ACMR", revision_range],
                        check=True,
                        text=True,
                        capture_output=True,
                    )
                    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
    try:
        result = subprocess.run(["git", "ls-files"], check=True, text=True, capture_output=True)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def run_url() -> str | None:
    server = os.getenv("GITHUB_SERVER_URL")
    repository = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    if server and repository and run_id:
        return f"{server}/{repository}/actions/runs/{run_id}"
    return None


def normalize_result(result: str) -> str:
    return result if result else "unknown"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    event = load_event()
    pull_request = event.get("pull_request", {})
    sender = event.get("sender", {})
    check_results = {
        "explainability_result": normalize_result(args.explainability_result),
        "prevention_result": normalize_result(args.prevention_result),
    }
    controls_passed = all(value == "success" for value in check_results.values())
    decision = "approved" if controls_passed else "blocked"

    checks = [
        {
            "name": name,
            "control": control,
            "result": check_results[key],
        }
        for name, key, control in CHECKS
    ]
    checks.append(
        {
            "name": "Auditability - enforcement evidence",
            "control": "auditability",
            "result": "generated",
        }
    )

    return {
        "generated_at_utc": utc_now(),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "workflow": os.getenv("GITHUB_WORKFLOW"),
        "workflow_run_url": run_url(),
        "event_name": os.getenv("GITHUB_EVENT_NAME"),
        "actor": os.getenv("GITHUB_ACTOR") or sender.get("login"),
        "sha": os.getenv("GITHUB_SHA"),
        "ref": os.getenv("GITHUB_REF"),
        "pull_request": {
            "number": pull_request.get("number"),
            "title": pull_request.get("title"),
            "url": pull_request.get("html_url"),
            "author": pull_request.get("user", {}).get("login"),
            "base": pull_request.get("base", {}).get("ref"),
            "head": pull_request.get("head", {}).get("ref"),
        }
        if pull_request
        else None,
        "changed_files": git_changed_files(event),
        "checks": checks,
        "enforcement": {
            "decision": decision,
            "reason": "All required controls passed."
            if controls_passed
            else "One or more required controls failed.",
        },
    }


def write_outputs(report: dict[str, Any], output_dir: str) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "security-audit-report.json"
    markdown_path = directory / "security-audit-report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def markdown_report(report: dict[str, Any]) -> str:
    pr = report.get("pull_request") or {}
    lines = [
        "# Security Enforcement Evidence",
        "",
        f"- Decision: `{report['enforcement']['decision']}`",
        f"- Reason: {report['enforcement']['reason']}",
        f"- Generated: `{report['generated_at_utc']}`",
        f"- Repository: `{report.get('repository')}`",
        f"- Actor: `{report.get('actor')}`",
        f"- Event: `{report.get('event_name')}`",
        f"- Commit: `{report.get('sha')}`",
    ]
    if report.get("workflow_run_url"):
        lines.append(f"- Workflow run: {report['workflow_run_url']}")
    if pr:
        lines.extend(
            [
                f"- Pull request: `#{pr.get('number')}` {pr.get('title') or ''}".rstrip(),
                f"- PR author: `{pr.get('author')}`",
                f"- Branches: `{pr.get('head')}` -> `{pr.get('base')}`",
            ]
        )
    lines.extend(["", "## Checks", "", "| Check | Control | Result |", "| --- | --- | --- |"])
    for check in report["checks"]:
        lines.append(f"| {check['name']} | `{check['control']}` | `{check['result']}` |")
    lines.extend(["", "## Changed Files", ""])
    if report["changed_files"]:
        lines.extend(f"- `{path}`" for path in report["changed_files"])
    else:
        lines.append("- No changed files were available for this event.")
    lines.append("")
    return "\n".join(lines)


def append_summary(report: dict[str, Any], summary_path: str | None) -> None:
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write(markdown_report(report))


def main() -> int:
    args = parse_args()
    report = build_report(args)
    write_outputs(report, args.output_dir)
    append_summary(report, args.summary)
    print(markdown_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
