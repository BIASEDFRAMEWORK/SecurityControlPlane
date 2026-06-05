#!/usr/bin/env bash
set -euo pipefail

mkdir -p app

demo_secret="DEMO_SECRET_""8X4P0Q9Z7M2N6R1T5V3Y"

cat > app/payment_provider.py <<PY
"""Intentionally unsafe demo change.

This file is generated for the prevention demo. It contains a fake canary
secret so the GitHub Actions gate has something concrete to block.
"""

PAYMENT_PROVIDER_TOKEN = "${demo_secret}"


def payment_provider_token() -> str:
    return PAYMENT_PROVIDER_TOKEN
PY

echo "Created app/payment_provider.py with an intentionally unsafe fake canary secret."
echo "Commit this file on a demo branch to show the secret scan blocking the PR."
