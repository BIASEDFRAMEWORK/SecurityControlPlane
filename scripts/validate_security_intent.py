#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


YES_LABEL = "Yes - this change touches secrets, credentials, tokens, environment variables, or sensitive configuration"
NO_LABEL = "No - this change does not touch secrets, credentials, tokens, environment variables, or sensitive configuration"

AREA_LABELS = [
    "Secrets, credentials, tokens, or keys",
    "Environment variables",
    "Sensitive configuration",
    "None of the above",
]

PLACEHOLDERS = {
    "",
    "tbd",
    "todo",
    "n/a",
    "na",
    "none",
    "no",
    "yes",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that a PR body contains a usable security intent explanation."
    )
    parser.add_argument("--body", help="Path to a Markdown PR body file.")
    parser.add_argument("--event", help="Path to a GitHub event JSON file.")
    parser.add_argument("--output", default="evidence/explainability.json")
    parser.add_argument("--summary", help="Path to GITHUB_STEP_SUMMARY.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_body(args: argparse.Namespace) -> tuple[str | None, dict[str, Any]]:
    event: dict[str, Any] = {}
    if args.event:
        event_path = Path(args.event)
        if event_path.exists():
            event = json.loads(event_path.read_text(encoding="utf-8"))
            pull_request = event.get("pull_request")
            if pull_request:
                return pull_request.get("body") or "", event

    if args.body:
        return Path(args.body).read_text(encoding="utf-8"), event

    return None, event


def checked(label: str, body: str) -> bool:
    pattern = r"(?im)^\s*-\s*\[[xX]\]\s*" + re.escape(label) + r"\s*$"
    return bool(re.search(pattern, body))


def section_text(body: str, heading: str) -> str:
    pattern = (
        r"(?ims)^###\s+"
        + re.escape(heading)
        + r"\s*$"
        + r"(.*?)"
        + r"(?=^###\s+|^##\s+|\Z)"
    )
    match = re.search(pattern, body)
    if not match:
        return ""
    value = match.group(1)
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    return value.strip()


def meaningful(value: str, minimum_words: int = 4) -> bool:
    normalized = re.sub(r"\s+", " ", value).strip().lower()
    if normalized in PLACEHOLDERS:
        return False
    words = re.findall(r"[A-Za-z0-9_'-]+", normalized)
    return len(words) >= minimum_words


def validate(body: str | None, event: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "generated_at_utc": utc_now(),
        "control": "explainability",
        "status": "passed",
        "findings": [],
        "details": {},
    }

    if body is None:
        report["details"]["reason"] = "No PR body was available for this event."
        return report

    yes = checked(YES_LABEL, body)
    no = checked(NO_LABEL, body)
    selected_areas = [label for label in AREA_LABELS if checked(label, body)]
    explanation = section_text(body, "Explanation")
    validation = section_text(body, "Safety validation / evidence")

    report["details"] = {
        "pull_request": event.get("pull_request", {}).get("number"),
        "security_intent_yes": yes,
        "security_intent_no": no,
        "areas_touched": selected_areas,
        "explanation_word_count": len(re.findall(r"[A-Za-z0-9_'-]+", explanation)),
        "validation_word_count": len(re.findall(r"[A-Za-z0-9_'-]+", validation)),
    }

    findings: list[str] = []
    if yes == no:
        findings.append("Select exactly one security intent answer: Yes or No.")

    if not selected_areas:
        findings.append("Select at least one area touched.")

    none_selected = "None of the above" in selected_areas
    sensitive_areas = [area for area in selected_areas if area != "None of the above"]
    if yes and none_selected:
        findings.append("Do not select 'None of the above' when the change touches sensitive areas.")
    if no and sensitive_areas:
        findings.append("Do not select sensitive areas when the security intent answer is No.")

    if not meaningful(explanation):
        findings.append("Add a meaningful explanation of the security impact or why none exists.")

    if not meaningful(validation):
        findings.append("Add meaningful safety validation or evidence.")

    if findings:
        report["status"] = "failed"
        report["findings"] = findings

    return report


def write_report(report: dict[str, Any], output: str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def markdown_summary(report: dict[str, Any]) -> str:
    status = report["status"]
    lines = [
        "## Explainability control",
        "",
        f"- Status: `{status}`",
        f"- Generated: `{report['generated_at_utc']}`",
        "",
    ]
    if report["findings"]:
        lines.append("### Required fixes")
        lines.append("")
        for finding in report["findings"]:
            lines.append(f"- {finding}")
        lines.append("")
    else:
        lines.append("The PR body contains the required security intent explanation and validation evidence.")
        lines.append("")
    return "\n".join(lines)


def append_summary(report: dict[str, Any], summary_path: str | None) -> None:
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write(markdown_summary(report))


def main() -> int:
    args = parse_args()
    body, event = load_body(args)
    report = validate(body, event)
    write_report(report, args.output)
    append_summary(report, args.summary)
    print(markdown_summary(report))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
