import argparse

from src.config import settings
from src.logging_config import setup_logging
from src.scheduler import run_pipeline_once, run_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="TP.HCM infectious disease monitoring system")
    parser.add_argument("command", choices=["run-once", "scheduler"], nargs="?", default="run-once")
    parser.add_argument("--no-alerts", action="store_true", help="Do not send Telegram or email alerts")
    args = parser.parse_args()

    setup_logging(settings.log_level)
    if args.command == "scheduler":
        run_scheduler()
    else:
        run_pipeline_once(send_alerts=not args.no_alerts)


if __name__ == "__main__":
    main()
