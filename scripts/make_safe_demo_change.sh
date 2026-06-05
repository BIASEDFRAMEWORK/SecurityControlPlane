#!/usr/bin/env bash
set -euo pipefail

mkdir -p app

cat > app/payment_provider.py <<'PY'
"""Safe payment provider configuration.

The token is read from the runtime environment and is never stored in source.
"""

import os


def payment_provider_token() -> str:
    token = os.environ.get("PAYMENT_PROVIDER_TOKEN")
    if not token:
        raise RuntimeError("PAYMENT_PROVIDER_TOKEN is required")
    return token
PY

echo "Replaced app/payment_provider.py with the safe environment-variable version."
