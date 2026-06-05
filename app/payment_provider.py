"""Safe payment provider configuration.

The token is read from the runtime environment and is never stored in source.
"""

import os


def payment_provider_token() -> str:
    token = os.environ.get("PAYMENT_PROVIDER_TOKEN")
    if not token:
        raise RuntimeError("PAYMENT_PROVIDER_TOKEN is required")
    return token
