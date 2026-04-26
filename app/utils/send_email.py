import asyncio
import smtplib
from email.headerregistry import Address
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.settings import logger, settings


def _from_header() -> str:
    """Build a properly formatted From header: "Name" <email@domain.com>"""
    return str(Address(display_name=settings.smtp_from_name, addr_spec=settings.smtp_from_email))


async def send_email(
    to: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    reply_to: str | None = None,
) -> None:
    """Send an email via SMTP (runs in a thread executor to avoid blocking the event loop)."""
    def _send() -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = _from_header()
        msg["To"] = to
        if reply_to:
            msg["Reply-To"] = reply_to

        if body_text:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [to], msg.as_string())

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info("Email sent to %s | subject: %s", to, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        raise


def build_talk_decision_email(
    speaker_name: str,
    talk_title: str,
    status: str,
    event_title: str,
) -> tuple[str, str, str]:
    """Return (subject, text_body, html_body) for a talk-decision notification."""
    subject = f"[{event_title}] Your talk submission — {status.capitalize()}"

    status_messages: dict[str, str] = {
        "accepted": "We are delighted to inform you that your talk has been <strong>accepted</strong>.",
        "rejected": "After careful review, we regret that we are unable to accept your talk this time.",
        "waitlisted": "Your talk has been placed on our <strong>waitlist</strong>. We will contact you if a spot becomes available.",
    }
    html_message = status_messages.get(
        status, f"The status of your talk has been updated to: <strong>{status}</strong>."
    )
    text_message = html_message.replace("<strong>", "").replace("</strong>", "")

    text_body = f"""Hello {speaker_name},

{text_message}

Talk:  {talk_title}
Event: {event_title}

Thank you for your submission.

Best regards,
The {event_title} Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; padding: 24px;">
  <h2 style="color: #2c3e50;">{event_title}</h2>
  <p>Hello <strong>{speaker_name}</strong>,</p>
  <p>{html_message}</p>
  <ul>
    <li><strong>Talk:</strong> {talk_title}</li>
    <li><strong>Event:</strong> {event_title}</li>
  </ul>
  <p>Thank you for your submission.</p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
  <p style="font-size: 0.9em; color: #777;">Best regards,<br>The {event_title} Team</p>
</body>
</html>"""

    return subject, text_body, html_body
