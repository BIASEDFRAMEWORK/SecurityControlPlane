#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
EVIDENCE_DIR="${REPO_ROOT}/evidence/demo-run"

cd "${REPO_ROOT}"

mkdir -p "${EVIDENCE_DIR}"

restore_safe_change() {
  bash scripts/make_safe_demo_change.sh >/dev/null
}

trap restore_safe_change EXIT

section() {
  printf '\n'
  printf '============================================================\n'
  printf '%s\n' "$1"
  printf '============================================================\n'
}

say() {
  printf '\n%s\n' "$1"
}

pause() {
  if [[ "${NO_PAUSE:-}" == "1" ]]; then
    return
  fi
  printf '\nPress Enter to continue...'
  read -r _
}

run_success() {
  printf '\n$ %s\n' "$*"
  "$@"
}

run_expected_failure() {
  printf '\n$ %s\n' "$*"
  set +e
  "$@"
  status=$?
  set -e
  if [[ "${status}" -eq 0 ]]; then
    printf '\nExpected this command to fail, but it passed.\n'
    exit 1
  fi
  printf '\nExpected failure observed. Exit code: %s\n' "${status}"
}

section "Demo framing"
say "Talk track: AI is increasing the speed and volume of code change. Security has to put repeatable controls where code already moves: pull requests and CI/CD."
say "This demo shows three outcomes around secrets: explainability, prevention, and auditability."
pause

section "1. Explainability: make the change explain itself"
say "Talk track: Before review, the developer must say whether the change touches secrets, credentials, tokens, environment variables, or sensitive configuration."
say "First, show the failure state: an incomplete PR description."
run_expected_failure "${PYTHON_BIN}" scripts/validate_security_intent.py \
  --body demo/pr-body-fail.md \
  --output "${EVIDENCE_DIR}/explainability-failed.json"
say "Now show the fixed state: the developer completed the security intent and validation sections."
run_success "${PYTHON_BIN}" scripts/validate_security_intent.py \
  --body demo/pr-body-pass.md \
  --output "${EVIDENCE_DIR}/explainability-passed.json"
pause

section "2. Prevention: block the secret before it reaches main"
say "Talk track: A required check turns this from a warning into a prevention control. The secret is stopped before it enters shared branch history."
say "Start from the safe version, which reads the token from the runtime environment."
restore_safe_change
run_success "${PYTHON_BIN}" scripts/secret_scan.py \
  --paths app/payment_provider.py \
  --redact \
  --output "${EVIDENCE_DIR}/secret-scan-safe-before.json"
say "Now generate the intentionally unsafe demo change with a fake canary secret."
run_success bash scripts/make_leaky_demo_change.sh
say "The prevention control should fail and redact the secret-like value from the output."
run_expected_failure "${PYTHON_BIN}" scripts/secret_scan.py \
  --paths app/payment_provider.py \
  --redact \
  --output "${EVIDENCE_DIR}/secret-scan-blocked.json"
pause

section "3. Auditability: record who, what, when, and decision"
say "Talk track: The control leaves evidence: what checks ran, what was blocked or approved, and when enforcement happened."
say "Generate the blocked evidence record that would appear after the failed prevention check."
run_success "${PYTHON_BIN}" scripts/audit_report.py \
  --explainability-result success \
  --prevention-result failure \
  --output-dir "${EVIDENCE_DIR}/blocked"
say "Restore the safe implementation and show the approved evidence record."
restore_safe_change
run_success "${PYTHON_BIN}" scripts/secret_scan.py \
  --paths app/payment_provider.py \
  --redact \
  --output "${EVIDENCE_DIR}/secret-scan-safe-after.json"
run_success "${PYTHON_BIN}" scripts/audit_report.py \
  --explainability-result success \
  --prevention-result success \
  --output-dir "${EVIDENCE_DIR}/approved"

section "Demo complete"
say "Evidence written to: ${EVIDENCE_DIR}"
say "Open these files after the run if you want to show the audit artifacts:"
say "- ${EVIDENCE_DIR}/blocked/security-audit-report.md"
say "- ${EVIDENCE_DIR}/approved/security-audit-report.md"
say "The safe app/payment_provider.py file has been restored."
