#!/usr/bin/env python3
"""
ProtonMail Bridge to Slack forwarder
Monitors local IMAP from Proton Mail Bridge and forwards to Slack
"""

from .bridge import ProtonSlackBridge
from .config import Config
from .log import logger


def main():
    """Entry point"""
    config = Config.from_env()

    if not config.validate():
        logger.error("Configuration invalid. Set environment variables:")
        logger.error("  PROTON_EMAIL - your ProtonMail email address")
        logger.error("  PROTON_BRIDGE_PASSWORD - Bridge password (from Bridge app)")
        logger.error("  SLACK_WEBHOOK_URL - your Slack incoming webhook URL")
        return 1

    bridge = ProtonSlackBridge(config)
    bridge.run()
    return 0


if __name__ == "__main__":
    exit(main())
