from app.config import config_source_summary, load_config


def main() -> None:
    config = load_config()
    summary = config_source_summary(config)
    print(f"{summary['service_name']} started")
    print(f"payment_provider_token_source={summary['payment_provider_token']}")
    print(f"audit_log_path={summary['audit_log_path']}")


if __name__ == "__main__":
    main()
