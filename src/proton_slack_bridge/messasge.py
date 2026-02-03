__all__ = ["EmailMessage"]


import email  # noqa: TC003
from email.header import decode_header

import msgspec


class EmailMessage(msgspec.Struct):
    """Parsed email message"""

    raw_email: email.message.Message

    _subject_maybe: str | None = None
    _from_addr_maybe: str | None = None
    _date_maybe: str | None = None
    _body_maybe: str | None = None

    def __post_init__(self) -> None:
        self._subject_maybe = self.raw_email.get("Subject", "")
        self._from_addr_maybe = self.raw_email.get("From", "")
        self._date_maybe = self.raw_email.get("Date", "")
        self._body_maybe = self.raw_email.get("Body", "")

    @property
    def subject(self) -> str:
        assert self._subject_maybe is not None
        return self._subject_maybe

    @property
    def from_addr(self) -> str:
        assert self._from_addr_maybe is not None
        return self._from_addr_maybe

    @property
    def date(self) -> str:
        assert self._date_maybe is not None
        return self._date_maybe

    @property
    def body(self) -> str:
        assert self._body_maybe is not None
        return self._body_maybe

    @staticmethod
    def _decode_header(header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        decoded_parts = decode_header(header)
        result = []
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                result.append(content.decode(encoding or "utf-8", errors="replace"))
            else:
                result.append(str(content))
        return "".join(result)

    def _get_body(self) -> str:
        """Extract email body (prefer plain text)"""
        if self.raw_email.is_multipart():
            for part in self.raw_email.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
        else:
            payload = self.raw_email.get_payload(decode=True)
            if isinstance(payload, bytes):
                charset = self.raw_email.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""

    def to_slack_message(self, max_body_length: int = 500) -> dict:
        """Convert to Slack message format"""
        body_preview = self.body[:max_body_length]
        if len(self.body) > max_body_length:
            body_preview += "..."

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📧 {self.subject}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*From:*\n{self.from_addr}"},
                        {"type": "mrkdwn", "text": f"*Date:*\n{self.date}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```{body_preview}```"},
                },
            ]
        }
