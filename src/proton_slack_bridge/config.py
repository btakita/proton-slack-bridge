__all__ = ["Config"]

from typing import Self

import msgspec

from .env import PROTON_BRIDGE_PASSWORD, PROTON_EMAIL, SLACK_WEBHOOK_URL
from .log import logger


class Config(msgspec.Struct):
    """Configuration for the service"""

    imap_host: str = "127.0.0.1"
    imap_port: int = 1143
    imap_username: str = PROTON_EMAIL
    imap_password: str = PROTON_BRIDGE_PASSWORD
    slack_webhook: str = SLACK_WEBHOOK_URL
    check_interval: int = 30  # seconds
    mailbox: str = "INBOX"

    @classmethod
    def from_env(cls) -> Self:
        """Load config from environment variables"""
        return cls(
            imap_username=PROTON_EMAIL,
            imap_password=PROTON_BRIDGE_PASSWORD,
            slack_webhook=SLACK_WEBHOOK_URL,
        )

    def validate(self) -> bool:
        """Check if config is valid"""
        if not self.imap_username:
            logger.error("PROTON_EMAIL not set")
            return False
        if not self.imap_password:
            logger.error("PROTON_BRIDGE_PASSWORD not set")
            return False
        if not self.slack_webhook:
            logger.error("SLACK_WEBHOOK_URL not set")
            return False
        return True
