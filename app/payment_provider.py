"""Intentionally unsafe demo change.

This file is generated for the prevention demo. It contains a fake canary
secret so the GitHub Actions gate has something concrete to block.
"""

PAYMENT_PROVIDER_TOKEN = "DEMO_SECRET_8X4P0Q9Z7M2N6R1T5V3Y"


def payment_provider_token() -> str:
    return PAYMENT_PROVIDER_TOKEN
