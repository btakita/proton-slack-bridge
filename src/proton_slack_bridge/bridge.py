__all__ = ["ProtonSlackBridge"]

import contextlib
import email
import imaplib
import time
from typing import cast

import requests
from docutils.parsers.rst.states import TYPE_CHECKING


if TYPE_CHECKING:
    from .config import Config

from .log import logger
from .messasge import EmailMessage


class ProtonSlackBridge:
    """Main bridge service"""

    def __init__(self, config: Config):
        self.config = config
        self.imap: imaplib.IMAP4 | None = None
        self.seen_uids = set()

    def connect_imap(self) -> bool:
        """Connect to Proton Mail Bridge IMAP"""
        try:
            logger.info(
                f"Connecting to IMAP {self.config.imap_host}:{self.config.imap_port}"
            )
            self.imap = imaplib.IMAP4(self.config.imap_host, self.config.imap_port)
            self.imap.login(self.config.imap_username, self.config.imap_password)
            logger.info("IMAP connection established")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            self.imap = None
            return False

    def check_new_messages(self) -> list[EmailMessage]:
        """Check for new unread messages"""
        if not self.imap:
            return []

        try:
            # Select mailbox
            self.imap.select(self.config.mailbox)

            # Search for unseen messages
            status, messages = self.imap.search(None, "UNSEEN")
            if status != "OK":
                return []

            message_ids = messages[0].split()
            new_messages = []

            for msg_id in message_ids:
                if msg_id in self.seen_uids:
                    continue

                # Fetch the email
                status, msg_data = self.imap.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                if len(msg_data) < 1:
                    logger.warning(
                        "ProtonSlackBridge.check_new_messages: msg_data is empty: continuing..."
                    )
                    continue

                if msg_data[0] is None:
                    logger.warning(
                        "ProtonSlackBridge.check_new_messages: msg_data[0] is None: continuing..."
                    )
                    continue

                msg_data_0 = cast("list[bytes | tuple[bytes, bytes]]", msg_data)[0]
                msg_data_0_1 = msg_data_0[1]
                if isinstance(msg_data_0_1, int):
                    logger.warning(
                        "ProtonSlackBridge.check_new_messages: msg_data[0][1] is an int: continuing..."
                    )
                    continue

                raw_email = email.message_from_bytes(msg_data_0_1)
                new_messages.append(EmailMessage(raw_email))
                self.seen_uids.add(msg_id)

            return new_messages

        except Exception as e:
            logger.error(f"Error checking messages: {e}")
            # Connection might be dead, reconnect next iteration
            self.imap = None
            return []

    def send_to_slack(self, message: EmailMessage) -> bool:
        """Send message to Slack"""
        try:
            slack_payload = message.to_slack_message()
            response = requests.post(
                self.config.slack_webhook, json=slack_payload, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Sent to Slack: {message.subject}")
                return True
            else:
                logger.error(
                    f"Slack webhook failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return False

    def run(self):
        """Main service loop"""
        logger.info("Starting ProtonSlack bridge...")

        while True:
            try:
                # Ensure IMAP connection
                if not self.imap and not self.connect_imap():
                    logger.info(f"Retrying in {self.config.check_interval}s...")
                    time.sleep(self.config.check_interval)
                    continue

                # Check for new messages
                new_messages = self.check_new_messages()

                # Forward to Slack
                for msg in new_messages:
                    self.send_to_slack(msg)

                # Wait before next check
                time.sleep(self.config.check_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(self.config.check_interval)

        # Cleanup
        if self.imap:
            with contextlib.suppress(BaseException):
                self.imap.logout()
