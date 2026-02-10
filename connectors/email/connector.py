"""
Email Connector — IMAP/SMTP using Python stdlib.

Polls an IMAP mailbox for new messages, normalizes to standard format.
Sends outgoing messages via SMTP. No external dependencies required.

Config (connectors.yml):
  - name: email-main
    type: email
    imap_host: imap.gmail.com
    imap_port: 993
    smtp_host: smtp.gmail.com
    smtp_port: 587
    username: ${EMAIL_USERNAME}
    password: ${EMAIL_PASSWORD}
    poll_interval: 60          # seconds between IMAP checks
    folders: ["INBOX"]
    allowed_senders: []        # empty = allow all
"""

from __future__ import annotations

import email
import email.utils
import imaplib
import smtplib
import threading
import time
from email.mime.text import MIMEText
from typing import Any

from connectors.base.connector import Connector
from connectors.base.message import (
    ConnectorInfo,
    Content,
    Conversation,
    Message,
    OutgoingMessage,
    Sender,
)


class EmailConnector(Connector):
    """Email connector using stdlib IMAP/SMTP."""

    connector_type = "email"

    def connect(self) -> None:
        self._imap_host = self.get_config("imap_host", "imap.gmail.com")
        self._imap_port = int(self.get_config("imap_port", 993))
        self._smtp_host = self.get_config("smtp_host", "smtp.gmail.com")
        self._smtp_port = int(self.get_config("smtp_port", 587))
        self._username = self.get_config("username", env_key="EMAIL_USERNAME")
        self._password = self.get_config("password", env_key="EMAIL_PASSWORD")
        self._poll_interval = float(self.get_config("poll_interval", 60))
        self._folders = self.config.get("folders", ["INBOX"])
        self._allowed_senders = set(self.config.get("allowed_senders", []))

        if not self._username or not self._password:
            raise ValueError(
                "Email connector requires username and password. "
                "Set EMAIL_USERNAME and EMAIL_PASSWORD env vars."
            )

        # Test IMAP connection
        self._imap: imaplib.IMAP4_SSL | None = None
        self._connect_imap()
        self.logger.info(f"Connected to IMAP: {self._imap_host}")

    def _connect_imap(self) -> None:
        """Connect/reconnect to IMAP server."""
        try:
            if self._imap:
                self._imap.close()
                self._imap.logout()
        except Exception:
            pass
        self._imap = imaplib.IMAP4_SSL(self._imap_host, self._imap_port)
        self._imap.login(self._username, self._password)

    def disconnect(self) -> None:
        try:
            if self._imap:
                self._imap.close()
                self._imap.logout()
        except Exception:
            pass
        self.logger.info("Email connector disconnecting")

    def send_message(self, msg: OutgoingMessage) -> bool:
        try:
            mime = MIMEText(msg.text)
            mime["From"] = self._username
            mime["To"] = msg.conversation_id  # conversation_id = email address
            mime["Subject"] = msg.metadata.get("subject", "Re: Seed Agent")
            if msg.thread_id:
                mime["In-Reply-To"] = msg.thread_id
                mime["References"] = msg.thread_id

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._username, self._password)
                server.send_message(mime)
            return True
        except Exception as e:
            self.logger.error(f"SMTP send failed: {e}")
            return False

    def run_loop(self) -> None:
        # Start outbox poller
        poller = threading.Thread(target=self._poll_outbox_loop, daemon=True)
        poller.start()

        # Main IMAP polling loop
        while self._running:
            try:
                self._check_mail()
            except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as e:
                self.logger.warning(f"IMAP error, reconnecting: {e}")
                try:
                    self._connect_imap()
                except Exception as re:
                    self.logger.error(f"Reconnect failed: {re}")
            except Exception as e:
                self.logger.error(f"Mail check error: {e}")

            time.sleep(self._poll_interval)

    def _check_mail(self) -> None:
        """Check for unseen messages in configured folders."""
        if not self._imap:
            return

        for folder in self._folders:
            self._imap.select(folder)
            _, message_numbers = self._imap.search(None, "UNSEEN")

            for num in message_numbers[0].split():
                if not num:
                    continue

                _, msg_data = self._imap.fetch(num, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0]
                if isinstance(raw, tuple):
                    raw_email = raw[1]
                else:
                    continue

                parsed = email.message_from_bytes(raw_email)
                self._process_email(parsed)

    def _process_email(self, parsed: email.message.Message) -> None:
        """Convert a parsed email to a standard Message."""
        from_header = parsed.get("From", "")
        from_name, from_addr = email.utils.parseaddr(from_header)

        # Sender filter
        if self._allowed_senders and from_addr not in self._allowed_senders:
            return

        # Extract body
        body = ""
        if parsed.is_multipart():
            for part in parsed.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")
                    break
        else:
            payload = parsed.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="replace")

        message_id = parsed.get("Message-ID", "")

        msg = Message(
            connector=ConnectorInfo(type="email", instance=self.name),
            sender=Sender(
                id=from_addr,
                username=from_addr,
                display_name=from_name or from_addr,
            ),
            content=Content(text=body.strip()),
            conversation=Conversation(
                id=from_addr,
                type="dm",
                name=from_addr,
                thread_id=message_id,
            ),
            metadata={
                "subject": parsed.get("Subject", ""),
                "message_id": message_id,
                "date": parsed.get("Date", ""),
            },
        )
        self.write_to_inbox(msg)

    def _poll_outbox_loop(self) -> None:
        while self._running:
            try:
                self.process_outbox()
            except Exception as e:
                self.logger.error(f"Outbox poll error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed Agent Email Connector")
    parser.add_argument("--seed-home", default=".", help="Seed home directory")
    parser.add_argument("--name", default="email-main", help="Connector instance name")
    args = parser.parse_args()

    connector = EmailConnector(name=args.name, seed_home=args.seed_home)
    connector.run()
