from dataclasses import dataclass
from os import environ
from typing import Mapping


@dataclass(frozen=True)
class AppConfig:
    service_name: str
    payment_provider_token: str | None
    audit_log_path: str


def load_config(env: Mapping[str, str] = environ) -> AppConfig:
    return AppConfig(
        service_name=env.get("SERVICE_NAME", "checkout-demo"),
        payment_provider_token=env.get("PAYMENT_PROVIDER_TOKEN"),
        audit_log_path=env.get("AUDIT_LOG_PATH", "audit-output/events.jsonl"),
    )


def config_source_summary(config: AppConfig) -> dict[str, str]:
    return {
        "service_name": config.service_name,
        "payment_provider_token": "environment" if config.payment_provider_token else "unset",
        "audit_log_path": config.audit_log_path,
    }
