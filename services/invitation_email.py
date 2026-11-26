"""Optional TLS-only SMTP delivery for Beacon account invitations."""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


def send_invitation_email(recipient: str, code: str) -> str:
    host = os.getenv("BEACON_INVITE_SMTP_HOST", "").strip()
    sender = os.getenv("BEACON_INVITE_SMTP_FROM", "").strip()
    base = os.getenv("BEACON_INVITE_APP_URL", "").strip()
    if not any((host, sender, base)):
        return "not_configured"
    try:
        url = urlsplit(base)
        username = os.getenv("BEACON_INVITE_SMTP_USERNAME", "")
        password = os.getenv("BEACON_INVITE_SMTP_PASSWORD", "")
        if (
            not host or not sender or not url.hostname or url.scheme != "https"
            or url.username or url.password or url.query or url.fragment
            or bool(username) != bool(password)
        ):
            raise ValueError("Invalid invitation email configuration")
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = "Your Beacon account invitation"
        message.set_content(
            f"Your Beacon access was approved. Create your account at {base.rstrip('/')}/register\n\n"
            f"Invitation code: {code}\n\n"
            "This code can be used once and expires in 24 hours. Do not forward it."
        )
        port = int(os.getenv("BEACON_INVITE_SMTP_PORT", "465"))
        with smtplib.SMTP_SSL(host, port, timeout=5, context=ssl.create_default_context()) as smtp:
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException) as exc:
        logger.warning("Beacon invitation email failed (%s)", type(exc).__name__)
        return "failed"
    return "sent"
