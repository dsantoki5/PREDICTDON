"""
PredictCNC Email Service — Python native smtplib + email.mime for Gmail SMTP.
Handles TLS / STARTTLS authentication on port 587 with strict zero-leak security.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))

logger = logging.getLogger("predictcnc.email")

class EmailService:
    @staticmethod
    def get_smtp_config():
        host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        port = int(os.getenv("SMTP_PORT", 587))
        user = os.getenv("SMTP_USER", "").strip()
        password = os.getenv("SMTP_PASSWORD", "").strip()
        from_email = os.getenv("SMTP_FROM", "").strip() or user
        return {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "from_email": from_email
        }

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if SMTP credentials are provided in .env."""
        cfg = cls.get_smtp_config()
        return bool(cfg["user"] and cfg["password"])

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Sends an email using configured Gmail SMTP settings.
        Returns: (success: bool, error_message: Optional[str])
        """
        if not to_email or "@" not in to_email:
            err_msg = "Invalid recipient email address."
            logger.warning(f"Email dispatch aborted: {err_msg} ({to_email})")
            return False, err_msg

        if not cls.is_configured():
            err_msg = "SMTP credentials (SMTP_USER / SMTP_PASSWORD) not configured in .env."
            logger.info(f"Email notification skipped: {err_msg}")
            return False, err_msg

        cfg = cls.get_smtp_config()
        
        # Build MIME Message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"PredictCNC Alert System <{cfg['from_email']}>"
        message["To"] = to_email

        # Attach plain-text fallback and HTML content
        if text_content:
            part1 = MIMEText(text_content, "plain", "utf-8")
            message.attach(part1)

        part2 = MIMEText(html_content, "html", "utf-8")
        message.attach(part2)

        server: Optional[smtplib.SMTP] = None
        try:
            timeout = 12
            if cfg["port"] == 465:
                server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=timeout)
                server.ehlo()
            else:
                server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout)
                server.ehlo()
                server.starttls()
                server.ehlo()

            # Authenticate with Gmail App Password
            server.login(cfg["user"], cfg["password"])

            # Send Email
            server.sendmail(cfg["from_email"], [to_email], message.as_string())
            logger.info(f"Successfully dispatched alert email to {to_email} (Subject: {subject[:40]}...)")
            return True, None

        except smtplib.SMTPAuthenticationError:
            err_msg = "SMTP Authentication Failed: Please check your Gmail address and 16-character App Password."
            logger.error(f"Email delivery error to {to_email}: {err_msg}")
            return False, err_msg

        except smtplib.SMTPConnectError:
            err_msg = f"Unable to connect to SMTP server at {cfg['host']}:{cfg['port']}."
            logger.error(f"Email connection error: {err_msg}")
            return False, err_msg

        except smtplib.SMTPRecipientsRefused:
            err_msg = f"Recipient address was refused by SMTP server: {to_email}"
            logger.error(f"Email recipient error: {err_msg}")
            return False, err_msg

        except Exception as e:
            # Mask any internal sensitive details
            err_msg = f"SMTP Transmission error: {type(e).__name__} ({str(e)})"
            logger.error(f"General email error sending to {to_email}: {err_msg}")
            return False, err_msg

        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
