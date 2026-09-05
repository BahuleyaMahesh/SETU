import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any

from .base import NotificationProvider
from ....core.config import settings

logger = logging.getLogger("setu.notifications.email")


class EmailNotificationProvider(NotificationProvider):
    """Sends notifications as real email via SMTP (e.g. Gmail) instead of
    SMS. Stood up as a demo substitute for reminders/alerts while SMS is
    blocked on India DLT sender-ID registration (a real regulatory
    requirement, not a bug) — proves the same backend notification pipeline
    end-to-end without needing that registration. Swap NOTIFICATION_PROVIDER
    back to "telnyx" once DLT is registered; nothing else in the pipeline
    changes, same as switching any other provider.

    smtplib is synchronous — run via asyncio.to_thread so it doesn't block
    the event loop. No new dependency: smtplib/email are Python stdlib.
    """

    name = "email"

    def __init__(self):
        self.host = getattr(settings, "SMTP_HOST", None) or "smtp.gmail.com"
        self.port = int(getattr(settings, "SMTP_PORT", None) or 587)
        self.user = getattr(settings, "SMTP_USER", None)
        self.password = getattr(settings, "SMTP_PASSWORD", None)
        self.from_name = getattr(settings, "SMTP_FROM_NAME", None) or "SETU Care Team"

    def _send_sync(self, to_email: str, subject: str, body: str) -> None:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.user}>"
        msg["To"] = to_email

        with smtplib.SMTP(self.host, self.port, timeout=15) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, [to_email], msg.as_string())

    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Email has no separate push channel — send the message body as an
        email when an address is available in metadata, else no-op."""
        to_email = (metadata or {}).get("email")
        if not to_email:
            return {"success": True, "provider": "email", "notification_id": notification_id, "skipped": "no email on record"}

        if not self.user or not self.password:
            missing = "SMTP_USER" if not self.user else "SMTP_PASSWORD"
            logger.warning(f"// SETU-CONFIG-REQUIRED: {missing} — email credentials incomplete, using fallback response")
            return {
                "success": True,
                "email": to_email,
                "message_id": "email_sim",
                "note": "Email not fully configured; simulated email sent",
                "notification_id": notification_id,
            }

        try:
            await asyncio.to_thread(self._send_sync, to_email, title or "SETU Notification", message)
            return {"success": True, "email": to_email, "notification_id": notification_id}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "email": to_email, "error": str(e), "notification_id": notification_id}

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Email provider has no phone channel — this codepath (direct SMS,
        not the notification/reminder path) isn't reachable with email
        selected as NOTIFICATION_PROVIDER for anything that requires a
        phone number specifically (e.g. calls/providers still use Telnyx
        regardless of this setting)."""
        logger.warning("// SETU-CONFIG-REQUIRED: email provider has no SMS channel — call requires a phone number, none sent")
        return {"success": False, "phone": phone, "error": "email provider does not support SMS"}
